# Diagnosing a Codex GitHub network policy denial on a Mac

> Type: troubleshooting
> Status: current
> Updated: 2026-11-10
> Tags: codex, github, network-policy, troubleshooting

Investigation: 9 November 2026. Publication source check: 10 November 2026.

## Diagnosis

The established failure is a **Codex execution-path network-policy denial** for `api.github.com:443`. It is not a demonstrated GitHub credential failure or a global macOS proxy problem. The correct repair target is the network permission and approval context governing the operation, rather than the GitHub CLI installation or account credentials.

This conclusion rests on more than the phrase “blocked by policy.” The preserved error matches a message constructed by Codex’s public network-approval implementation. The command environment also had process-level loopback proxy settings. Local command execution and GitHub CLI installation checks succeeded.

The remaining question is specific: **which effective policy or request-lifecycle condition produced the denial?** Resolving that attribution determines the repair.

The practical sequence is to inspect the relevant session’s effective configuration, check the documented Work network control where available, and resolve any managed network requirement with its actual owner. Then validate access once, after an authorized change. No network retry or settings change was performed for this investigation.

## The incident evidence

Two failed `gh auth status` attempts were reported. The preserved result from one attempt contains this exact message:

```text
Network access to "https://api.github.com:443" was blocked by policy.
```

The earlier result was recovered from the existing record. The denial was not independently reproduced during the follow-up.

| Observation | Diagnostic meaning |
| --- | --- |
| The Mac connected successfully and local commands ran. | Computer attachment and local execution worked. This does not grant outbound GitHub access. |
| GitHub CLI reported `2.103.3`, dated 26 October 2026. | The executable was installed and runnable. |
| Local configuration included GitHub.com, HTTPS and an account entry. | The CLI was configured. Credential validity was not tested. |
| HTTP and HTTPS proxy variables used loopback HTTP endpoints; the all-protocol proxy used loopback SOCKS5h. | Proxy configuration existed in the command process environment. Exact endpoints are withheld. |
| `scutil --proxy` showed only exceptions and FTP passive configuration, with no enabled global HTTP, HTTPS or SOCKS proxy at inspection time. | The observed proxy settings were not an enabled macOS global web or SOCKS proxy configuration. |
| A narrow scan of incident-day app logs found no matching GitHub network-policy diagnostic entries. | No request trace was recovered from those local logs. This does not establish whether another component retained one. |

The later local inspection identified macOS `26.6.2`, ChatGPT app `26.1103.60933`, bundled Codex CLI `0.167.0-alpha.3.2`, and a separately installed Codex CLI `0.167.0`. The bundled and standalone CLI are distinct installations. Neither version identifies the original cloud controller.

## How the error is produced

In the examined public source, [`NetworkApprovalService::handle_inline_policy_request`][approval-handler] constructs the exact error text. For HTTPS CONNECT requests, it formats the destination as `https://host:port`. This is a Codex network-approval message, not GitHub CLI’s authentication reporting.

The handler can produce it when there is no active turn, when the permission profile cannot use the approval flow, when the effective approval policy forbids approval, and in later approval or session conflicts. The [helper checks][approval-helper] reject approval policy `Never` and require a managed permission profile for this approval flow. These checks do not identify this task’s effective settings.

The first three branches share the rejection reason `not_allowed`. This reuse is a concrete **observability limitation**: the displayed error cannot select the repair. It does not itself prove incorrect enforcement.

### A process failure does not establish launch timing

The earlier description that the command was blocked “before execution” was too definite. Codex’s [running-process polling path][polling] can handle cancellation after collecting output, and another path handles a [deferred network rejection after process exit][deferred-rejection]. A `ProcessFailed` result therefore does not prove that `gh` never started.

No exit code or process trace was preserved here. The supported conclusion is that the operation failed through network-policy handling, without a reliable reconstruction of its process timeline.

## Three controls to check in the correct scope

A local Mac, a cloud-coordinated task and a separately launched CLI session can have different effective requirements. OpenAI’s [local security documentation][local-security] distinguishes cloud coordination from local execution. Inspect the context that produced the denial; a permissive setting in another session is not a repair.

### 1. Inspect the relevant session and configuration layers

Where the original Codex surface supports them, use `/status` and `/debug-config`. The [documented commands][debug-config] expose session information and configuration layers, including their sources and network requirements.

Look for the effective permission profile, approval policy, applicable network requirements and the origin of each controlling value. The goal is to identify the layer that actually governs this operation, rather than find a file containing a plausible setting.

Do not start a new Terminal CLI session and treat its configuration as proof of the cloud-coordinated task’s state. If the original surface does not expose these commands, move to the targeted support request below. The investigation did not establish a supported per-task inspection control for the original controller.

### 2. Check Work network access where the app exposes it

OpenAI documents **Settings → Data controls → Work network access** as a control for shell and code access to the public internet, subject to workspace restrictions. The [Work overview][work-network] says changes take effect after the current run finishes and the environment refreshes.

If this control exists for the relevant context and internet access is disabled, enabling the intended access through that supported control is a concrete candidate repair. Finish the current run and obtain a refreshed environment before testing. A local reconnect alone does not establish that the cloud task adopted the change.

This setting’s current state could not be inspected in the app during the investigation. The user should check it in the actual app. If it is absent or does not govern the connected-Mac operation, do not search for an assumed equivalent switch. Obtain the effective policy attribution instead.

### 3. Resolve managed network requirements with the controlling owner

The [managed configuration documentation][managed-network] identifies **Agent Security → Requirements → Network use controls** for managed network requirements. Managed networking activates enforcement, and domain rules determine permitted targets. An exclusive administrator allowlist cannot be expanded by user settings or per-domain approvals.

If this is the controlling layer, ask its administrator whether `api.github.com:443` is intended to be permitted and request the narrowest appropriate change. If another layer controls the task, use that layer’s supported approval or settings flow instead. Record the changed rule, its scope and when it became effective.

A supported approval prompt may satisfy an approval requirement; it is not evidence that an authoritative network restriction can be overridden. Do not broaden global access, edit an unrelated CLI configuration, or disable security controls to make the symptom disappear.

## Validate the repair without mixing failure classes

After a supported, authorized policy or approval change, run one live check in the relevant execution context:

```sh
gh auth status --hostname github.com --no-refresh
```

The [GitHub CLI manual][gh-status] documents account-state testing and automatic refresh of eligible tokens unless `--no-refresh` is supplied. This flag suppresses refresh; it does not make the test offline or bypass policy. Capture the raw result and exit code. Do not use `--show-token`.

Interpret the result before doing anything else:

- **The same policy denial:** stop repeating the command. Correlate the new failure with the effective settings and network-policy diagnostics. The attempted change did not resolve the controlling condition.
- **An explicit authentication error:** network policy is no longer the only observed problem. Investigate the credential issue through GitHub’s normal [authentication workflow][gh-login]. Reauthentication is justified by that new evidence, not by the original policy message.
- **Successful authentication status:** the GitHub API authentication check works in that context. Validate the intended repository operation separately, within its authorization. Success here does not prove access to every GitHub host, repository or protocol.

Reinstalling `gh` cannot change a controlling network policy. A new token cannot grant network permission. Reconnection may fix an unavailable computer, but the computer was already reachable in this case. Those remedies belong to different demonstrated failures.

## Diagnostic data needed to attribute the denial

The public network proxy defines an audit event named [`codex.network_proxy.policy_decision`][policy-event], under tracing target `codex_otel.network_proxy`. Its fields include:

- Time, application version and request correlation identifiers.
- `network.policy.scope`, `decision`, `source`, `reason` and `override`.
- `network.transport.protocol`, `server.address`, `server.port` and `http.request.method`.

The [source categories][policy-sources] include `baseline_policy`, `mode_guard`, `proxy_state` and `decider`. They classify the decision mechanism, not necessarily the administrator or configuration file responsible for it. Such an event is useful only if it was recorded and retained.

To attribute the decision, support needs the effective turn settings and request lifecycle alongside any audit record. The local log scan did not recover that attribution.

### Exact support diagnostic request

> Please investigate the network-policy failure for the original operation on the selected connected Mac on 9 November 2026. The command was `gh auth status`, and the preserved error was: `Network access to "https://api.github.com:443" was blocked by policy.`
>
> Correlate the operation and its original timestamp with any retained `codex.network_proxy.policy_decision` event. Please provide the decision, source, reason, policy scope and execution attribution, with secrets and unrelated identifiers removed.
>
> Please identify the effective permission profile, approval policy, and applicable environment or controller network requirements at the time of failure. Use the effective settings and request lifecycle to attribute the denial, rather than restating the error message.
>
> Which supported setting or managed requirement controls this operation? What narrowly scoped change, approval or environment refresh would permit the intended GitHub API access, if that access is allowed?

Attach verified app and OS versions, the original command and raw error, the available timestamp, and the redacted offline findings. Include correlation identifiers privately if support requests them and they are available. Do not publish tokens, proxy endpoints, full environment dumps or unrelated logs.

## When this would be a configuration issue or a product bug

If an authoritative effective rule prohibits the target, the denial is expected enforcement. The remedy is a permitted policy change or approval through the controlling layer.

If an intended change is missing from the actual task, investigate its scope and refresh lifecycle. If the target is allowed through all applicable layers and the request has a valid active-turn and approval context, yet the same denial persists, there is a concrete basis to investigate a product-routing or lifecycle bug.

For this incident, the network-denial mechanism is established by the exact source-message match and contextual evidence. The next step is to identify the controlling condition and apply its supported repair, then validate the intended GitHub operation.

## Source notes

The code links are pinned to commit `caae161dd0c82f2e04e57e6f9d738fafbce503ba`. This is the public source version examined, not a verified build fingerprint for the original execution. Official documentation and source were reviewed on 9 November 2026 and checked again for publication on 10 November 2026. The links above separate implementation evidence, documented controls and incident observations.

[approval-handler]: https://github.com/openai/codex/blob/caae161dd0c82f2e04e57e6f9d738fafbce503ba/codex-rs/core/src/tools/network_approval.rs#L732-L848
[approval-helper]: https://github.com/openai/codex/blob/caae161dd0c82f2e04e57e6f9d738fafbce503ba/codex-rs/core/src/tools/network_approval.rs#L222-L229
[polling]: https://github.com/openai/codex/blob/caae161dd0c82f2e04e57e6f9d738fafbce503ba/codex-rs/core/src/unified_exec/process_manager.rs#L1068-L1089
[deferred-rejection]: https://github.com/openai/codex/blob/caae161dd0c82f2e04e57e6f9d738fafbce503ba/codex-rs/core/src/unified_exec/process_manager.rs#L752-L761
[policy-event]: https://github.com/openai/codex/blob/caae161dd0c82f2e04e57e6f9d738fafbce503ba/codex-rs/network-proxy/src/network_policy.rs#L267-L328
[policy-sources]: https://github.com/openai/codex/blob/caae161dd0c82f2e04e57e6f9d738fafbce503ba/codex-rs/network-proxy/src/network_policy.rs#L81-L98
[local-security]: https://learn.chatgpt.com/docs/enterprise/chatgpt-work-local-security#administrator-access-and-managed-device-policies
[debug-config]: https://learn.chatgpt.com/docs/developer-commands#inspect-config-layers-with-debug-config
[work-network]: https://learn.chatgpt.com/docs/enterprise/chatgpt-work-overview#network-access-and-external-destinations
[managed-network]: https://learn.chatgpt.com/docs/enterprise/managed-configuration#configure-network-access-requirements
[gh-status]: https://cli.github.com/manual/gh_auth_status
[gh-login]: https://cli.github.com/manual/gh_auth_login
