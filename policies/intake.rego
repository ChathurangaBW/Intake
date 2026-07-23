package intake

default decision := {
  "decision": "deny",
  "approval_required": false,
  "maximum_runtime_seconds": 0,
  "network_policy": "deny_all",
  "reason": "no policy matched"
}

# Read-only artifact operations are allowed by default when scoped by engagement.
decision := {
  "decision": "allow",
  "approval_required": false,
  "maximum_runtime_seconds": 300,
  "network_policy": "deny_all",
  "reason": "read-only operation allowed"
} if {
  input.risk == "read_only"
  input.engagement_id != ""
  startswith(input.tool, "artifact.")
}

# Dynamic execution requires explicit human approval.
decision := {
  "decision": "approve",
  "approval_required": true,
  "maximum_runtime_seconds": 900,
  "network_policy": "deny_all",
  "reason": "dynamic execution requires approval and isolation"
} if {
  input.risk == "dynamic_execution"
}

# Active network operations require target allowlisting and approval.
decision := {
  "decision": "approve",
  "approval_required": true,
  "maximum_runtime_seconds": 600,
  "network_policy": "target_allowlist",
  "reason": "active network operations require explicit approval"
} if {
  input.risk == "network_active"
}
