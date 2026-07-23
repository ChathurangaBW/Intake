#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${INTAKE_BASE_URL:-http://127.0.0.1:8000}"
AUTH_HEADER=()
if [[ -n "${INTAKE_API_KEY:-}" ]]; then
  AUTH_HEADER=(-H "x-intake-api-key: ${INTAKE_API_KEY}")
fi

request() {
  curl -fsS "${AUTH_HEADER[@]}" "$@"
}

json_request() {
  curl -fsS "${AUTH_HEADER[@]}" -H 'content-type: application/json' "$@"
}

printf 'Checking liveness and readiness...\n'
request "${BASE_URL}/health/live" >/dev/null
request "${BASE_URL}/health/ready" >/dev/null

printf 'Checking docs and metrics...\n'
request "${BASE_URL}/docs" >/dev/null
request "${BASE_URL}/metrics" >/dev/null

printf 'Creating QA engagement...\n'
json_request "${BASE_URL}/engagements" \
  -d '{"engagement_id":"qa-smoke","name":"QA Smoke"}' >/dev/null || true

printf 'Uploading artifact...\n'
SAMPLE_FILE="$(mktemp)"
trap 'rm -f "${SAMPLE_FILE}"' EXIT
printf 'hello qa smoke sample %s' "$(date +%s%N)" > "${SAMPLE_FILE}"
ARTIFACT_JSON="$(curl -fsS "${AUTH_HEADER[@]}" "${BASE_URL}/engagements/qa-smoke/artifacts" -F "file=@${SAMPLE_FILE};type=application/octet-stream")"
ARTIFACT_ID="$(python - <<'PY' "${ARTIFACT_JSON}"
import json, sys
print(json.loads(sys.argv[1])["id"])
PY
)"

printf 'Proposing read-only tool call...\n'
TOOL_JSON="$(json_request "${BASE_URL}/tool-calls" \
  -d "{\"engagement_id\":\"qa-smoke\",\"actor\":\"smoke\",\"tool\":\"ghidra\",\"operation\":\"analyze\",\"risk\":\"read_only\",\"arguments\":{\"artifact_id\":\"${ARTIFACT_ID}\",\"profile\":\"quick\"}}")"
TOOL_CALL_ID="$(python - <<'PY' "${TOOL_JSON}"
import json, sys
print(json.loads(sys.argv[1])["tool_call_id"])
PY
)"

printf 'Enqueueing authorized tool call...\n'
JOB_JSON="$(json_request "${BASE_URL}/tool-calls/${TOOL_CALL_ID}/enqueue" -d '{"priority":10,"max_attempts":2}')"
JOB_ID="$(python - <<'PY' "${JOB_JSON}"
import json, sys
print(json.loads(sys.argv[1])["id"])
PY
)"

printf 'Waiting for durable worker...\n'
JOB_STATUS=""
for _ in $(seq 1 60); do
  JOB_STATUS="$(request "${BASE_URL}/jobs/${JOB_ID}" | python -c 'import json,sys; print(json.load(sys.stdin)["status"])')"
  case "${JOB_STATUS}" in
    completed) break ;;
    failed|cancelled)
      printf 'Job ended with status %s\n' "${JOB_STATUS}" >&2
      exit 1
      ;;
  esac
  sleep 1
done
if [[ "${JOB_STATUS}" != "completed" ]]; then
  printf 'Timed out waiting for job; last status=%s\n' "${JOB_STATUS}" >&2
  exit 1
fi

printf 'Checking and verifying evidence...\n'
EVIDENCE_JSON="$(request "${BASE_URL}/engagements/qa-smoke/evidence")"
EVIDENCE_ID="$(python - <<'PY' "${EVIDENCE_JSON}"
import json, sys
rows = json.loads(sys.argv[1])
if not rows:
    raise SystemExit("no evidence was produced")
print(rows[0]["id"])
PY
)"
VERIFY_JSON="$(json_request -X POST "${BASE_URL}/evidence/${EVIDENCE_ID}/verify")"
python - <<'PY' "${VERIFY_JSON}"
import json, sys
result = json.loads(sys.argv[1])
if not result["valid"]:
    raise SystemExit(f"evidence integrity failed: {result}")
PY

printf 'Checking audit, stats, jobs, and report...\n'
request "${BASE_URL}/audit" >/dev/null
request "${BASE_URL}/stats" >/dev/null
request "${BASE_URL}/jobs?limit=10" >/dev/null
request "${BASE_URL}/engagements/qa-smoke/report.md" >/dev/null

printf 'Release smoke test passed.\n'
