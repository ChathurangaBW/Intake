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

printf 'Checking health...\n'
request "${BASE_URL}/health" >/dev/null

printf 'Checking docs...\n'
request "${BASE_URL}/docs" >/dev/null

printf 'Creating QA engagement...\n'
json_request "${BASE_URL}/engagements" \
  -d '{"engagement_id":"qa-smoke","name":"QA Smoke"}' >/dev/null || true

printf 'Uploading artifact...\n'
SAMPLE_FILE="$(mktemp)"
printf 'hello qa smoke sample' > "${SAMPLE_FILE}"
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

printf 'Executing authorized tool call...\n'
json_request -X POST "${BASE_URL}/tool-calls/${TOOL_CALL_ID}/execute" >/dev/null

printf 'Checking evidence, audit, stats, report...\n'
request "${BASE_URL}/engagements/qa-smoke/evidence" >/dev/null
request "${BASE_URL}/audit" >/dev/null
request "${BASE_URL}/stats" >/dev/null
request "${BASE_URL}/engagements/qa-smoke/report.md" >/dev/null

printf 'Smoke test passed.\n'
