package intake

default decision := {
  "decision": "deny",
  "approval_required": false,
  "maximum_runtime_seconds": 0,
  "network_policy": "deny_all",
  "reason": "no policy matched"
}

blocked_tools contains name if {
  name := input.tool
  name == "shell"
}

blocked_tools contains name if {
  name := input.tool
  name == "unrestricted_shell"
}

# Never allow unrestricted command execution through the agent path.
decision := {
  "decision": "deny",
  "approval_required": false,
  "maximum_runtime_seconds": 0,
  "network_policy": "deny_all",
  "reason": "unrestricted shell access is not exposed through Intake"
} if {
  blocked_tools[input.tool]
}

# Read-only artifact and reverse-engineering operations can run without network.
decision := {
  "decision": "allow",
  "approval_required": false,
  "maximum_runtime_seconds": 900,
  "network_policy": "deny_all",
  "reason": "scoped read-only analysis allowed"
} if {
  input.risk == "read_only"
  input.engagement_id != ""
  input.operation != ""
  input.tool in {"artifact", "ghidra", "rizin", "source"}
}

# State-changing operations must be reviewed.
decision := {
  "decision": "approve",
  "approval_required": true,
  "maximum_runtime_seconds": 600,
  "network_policy": "deny_all",
  "reason": "state-changing operation requires human review"
} if {
  input.risk == "state_changing"
}

# Dynamic execution requires explicit human review and VM isolation.
decision := {
  "decision": "approve",
  "approval_required": true,
  "maximum_runtime_seconds": 900,
  "network_policy": "deny_all",
  "reason": "dynamic execution requires approval and isolation"
} if {
  input.risk == "dynamic_execution"
}

# Active network operations require target allowlisting and human review.
decision := {
  "decision": "approve",
  "approval_required": true,
  "maximum_runtime_seconds": 600,
  "network_policy": "target_allowlist",
  "reason": "active network operations require explicit approval"
} if {
  input.risk == "network_active"
}
