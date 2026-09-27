# Tool permissions and sandboxing

A prompt requesting safe behavior is not an execution boundary. Validate arguments, authorize the actor and run code in disposable isolation. Never execute model-generated shell commands directly on the host.

Use an unprivileged identity, scoped workspace mounts, no host secrets or container-engine socket, restricted egress and bounded CPU, memory, process count, disk, time and output. A container may share a kernel; state residual risk and when a VM boundary is warranted. An allowlist does not make arbitrary shell syntax safe.

## Worked example
An allowed path starts with /workspace, but /workspace/link points outside it. String-prefix checks miss symlink escape. Resolve paths under policy, prevent link/race escapes through OS isolation and limit what is mounted. Never rely on path normalization alone for hostile execution.

Treat repository comments, retrieved documents and tool output as indirect injection. They cannot grant more tool access. Secrets stay at the trusted adapter boundary and are excluded from model context and audit payloads. Bind approvals to actor, exact action/arguments and expiry; changed arguments need new approval.

## Evidence gate
With harmless fixtures, test traversal/symlinks, forbidden host reads, egress, secret access, endless output, process exhaustion and timeout process-tree cleanup. Record allowed/denied actions with correlation IDs. DeepSWE M4 is blocked until critical boundary tests pass.

