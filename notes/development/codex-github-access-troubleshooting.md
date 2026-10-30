# Diagnose GitHub access in ChatGPT and Codex

> Type: troubleshooting
> Status: current
> Updated: 2026-10-30
> Tags: chatgpt, codex, git, github, troubleshooting

A GitHub failure in a ChatGPT or Codex task may happen before GitHub receives a
request. Identify the client, execution environment, target and first failing
gate before changing a login. A working route in one task or terminal does not
prove that another route has the same access.

## What the observed incidents showed

These examples are anonymized from actual task observations. They illustrate
routes and boundaries, not permanent permissions or universal fixes.

- **Network before authentication:** A sandboxed `git ls-remote` failed DNS
  resolution. A later, separately approved network execution reached GitHub and
  Git fetch and push succeeded with the existing HTTPS credentials. The first
  failure did not establish that the credentials were invalid; the later
  success applies to that execution context and operation.
- **Different clients, different results:** In one task `gh auth status`
  reported an invalid token, while Git transport successfully pushed using its
  existing credentials and the connected GitHub tool created a draft PR. A
  later terminal reported a healthy `gh` login. Neither observation establishes
  the state of `gh` in every other executor, and no credential repair mechanism
  was verified.
- **Private collaborator access:** In one case, an authenticated collaborator
  account used `gh` on a Mac to read a private repository owned by someone else;
  GitHub reported that account's `viewerPermission` as `WRITE`. The default
  sandbox separately failed DNS resolution, while a connector returned `404`
  and a task reader returned an error. Those failures did not establish that
  the collaborator lacked repository access, or that the `404` was caused by
  the sandbox. The successful read and reported permission apply only to the
  tested account and route at that time; they do not prove every write will pass.
- **Approval is not authentication:** An approval review rejected a proposed
  push before execution; a separate approval handoff failed before its action
  ran. Neither event is a GitHub credential response or evidence of a remote
  write. The first case remained blocked after additional approval evidence
  because a separate task restriction was cited; the handoff failure's cause
  was not established. Use the supported review or permission controls and
  report the precise blocker. Do not route the same denied action through
  another tool, browser, agent, or terminal to evade a denial.
- **Destination and capability are separate:** An upstream contribution was
  blocked because the required fork destination did not exist and upstream
  push access was unavailable. Once separately authorized forks existed, the
  contribution could proceed through them. In another task the connected tool
  could read a repository but did not expose repository creation. A successful
  read or broad reported permissions do not add an operation the tool lacks.

## Similar public reports

A [Codex discussion](https://github.com/openai/codex/discussions/42402) describes a background worker reporting an invalid `gh` token while its shell could authenticate; the author attributed that particular worker's failure to unavailable DNS in its sandbox. A separate [issue report](https://github.com/openai/codex/issues/50119) describes a delegated executor reportedly not accepting authorization given in the main conversation. The latter is based on the reporter's evidence rather than independently retrieved approval-service logs. These are individual reports, not proof of the same cause in another task or of how often either problem occurs. Neither establishes that broadening network access or repeating approvals is a universal fix.

## Separate the routes

| Route or gate | What it establishes | What it does not establish |
| --- | --- | --- |
| ChatGPT/Codex session and executor | Which local, remote, or cloud context is running and what sandbox and approval controls apply. | GitHub account identity or repository access. |
| Connected GitHub tool | Access and capabilities for that connection, installation, and operation. | The local `gh` login or Git transport credentials. |
| Git over HTTPS or SSH | Access through the effective remote, credentials or key, and current environment. | That `gh` or a connector uses the same account. |
| `gh` CLI | API authentication for the selected host and account in that process. | That another executor, Git helper, or connector is healthy. |
| Browser session | Authentication in that browser. | A terminal or connector login, unless an authorized sign-in flow establishes one. |
| Commit author | The name and email recorded in a commit. | The GitHub identity or permission used to push it. |
| Hooks, branch rules and CI | Local or remote checks on a particular change. | A diagnosis of credential failure. |

Git can use `gh` as a credential helper when deliberately configured, so these
routes can be coupled. Do not assume they are. See [Git credentials](https://git-scm.com/docs/gitcredentials), [GitHub CLI setup for Git](https://cli.github.com/manual/gh_auth_setup-git), and [Git commit usernames](https://docs.github.com/en/get-started/git-basics/setting-your-username-in-git).

## Diagnose the first failing gate

1. **Record intent and context.** Identify the actual executor, checkout,
   client, account, repository, branch, intended operation, and current
   authorization. Separate a requested action from an approved request, an
   executed action, and a verified result.
2. **Check execution and capability.** If approval was denied or a handoff
   failed before execution, report that outcome; GitHub has not responded. If a
   connected tool lacks the needed operation, report the capability gap. A
   separately authorized supported route may be appropriate, but not to evade a
   denial or task restriction.
3. **Check network reachability.** DNS, timeout, TLS, proxy, sandbox and
   allowlist failures do not prove a bad token. Use a narrow read-only check in
   the intended environment and seek any required access through its supported
   controls. Avoid speculative DNS, VPN, firewall or helper changes.
4. **Check the selected client and target.** For `gh`, inspect the active
   account and the presence—not values—of token overrides. For a connected
   tool, inspect its selected account, installation, repository inclusion and
   available operation. For Git, verify the effective fetch and push
   destinations, URL rewrites, account and helper or SSH alias without
   exposing credentials.
5. **Interpret the actual response.** A verified bad-credentials response
   concerns that client's selected credential. A `403` may reflect access or
   rate limits; a `404` may conceal a private repository. Check organization
   SSO, installation scope, repository rights, branch rules and whether the
   target is upstream or an existing fork. A public read may succeed
   anonymously and does not prove push access. [GitHub REST troubleshooting](https://docs.github.com/en/rest/using-the-rest-api/troubleshooting-the-rest-api)
6. **Check the next gate.** Local hooks, test failures, non-fast-forward
   rejection, branch protection and CI are not automatically authentication
   failures. Read the error and fix or report it; do not disable safeguards to
   manufacture success. [Git hooks](https://git-scm.com/docs/githooks)
7. **Verify the result.** After an authorized push, compare the intended local
   full commit ID with the exact remote branch ref. Read the PR back separately
   and check owner, repository, head, base and head SHA. Report checks
   independently. If verification fails, say the remote result is unverified.

Codex sandbox permissions and approval review are separate controls; changing
who reviews a request does not expand the sandbox. Local and cloud tasks may
also have different tool, network and credential contexts. Check the actual
product and session rather than assuming one mode applies everywhere. [Codex sandbox](https://developers.openai.com/codex/sandboxing), [Codex auto-review](https://developers.openai.com/codex/sandboxing/auto-review), [Codex cloud environments](https://developers.openai.com/codex/environments/cloud-environments)

## Safe checks in the affected executor

These are diagnostic examples, not proof that a write is authorized. Commands
that contact GitHub may use or refresh existing credentials. Keep output local
or redact account, repository and path details before sharing. Never print
tokens, private keys, cookies, device codes, credential-store entries or
secret-bearing remote URLs. Avoid shell tracing and HTTP authorization logs.

```sh
git --version
gh --version
git rev-parse --is-inside-work-tree

# Show presence only; do not print values.
for name in GH_TOKEN GITHUB_TOKEN GH_ENTERPRISE_TOKEN GITHUB_ENTERPRISE_TOKEN GH_HOST GH_REPO GH_CONFIG_DIR; do
  if printenv "$name" >/dev/null 2>&1; then
    printf '%s is set\n' "$name"
  else
    printf '%s is not set\n' "$name"
  fi
done
```

To verify a publication after confirming that `origin` points to the exact
credential-free destination, replace the placeholder with the branch that was
actually pushed and compare the full IDs. If the push destination differs,
query that destination instead; a missing ref is not success.

```sh
branch='example-branch'
git rev-parse --verify "refs/heads/$branch^{commit}"
git ls-remote --exit-code origin "refs/heads/$branch"
```

For the selected host, `gh auth status --active --hostname github.com` checks
`gh`'s active account. Depending on version it may refresh a near-expiry token;
use `--no-refresh` if supported and a non-refreshing check is required. Do not
use `--show-token`. With `--json`, the command can return zero despite an
authentication issue, so inspect the output. `GH_TOKEN` and `GITHUB_TOKEN` can
override stored `gh` credentials. [CLI status](https://cli.github.com/manual/gh_auth_status), [CLI environment](https://cli.github.com/manual/gh_help_environment)

For a known private repository, after confirming the active account and an
approved network route, a read-only check can report that account's repository
permission. Replace the placeholders locally and keep the output private:

```sh
gh repo view OWNER/REPO --json viewerPermission --jq .viewerPermission
```

This reports the permission for the account and route used by that command; it
does not establish connector or task-reader visibility, or guarantee that a
particular write will pass branch rules and required approvals. A `404` alone
does not identify which access or visibility condition failed. Use supported
network and executor controls, and never reroute an action to evade a denial.

Inspect remotes with a redacting diagnostic before displaying them: URLs can
contain user-info, query parameters or other secrets. Once the effective target
is confirmed safe and correct, `git ls-remote origin HEAD` is a read-only
transport check, not a write-permission test. If the push URL differs, inspect
that target separately. For a configured SSH route, use strict host-key
verification; GitHub's successful `ssh -T` greeting normally exits with status
1 because shell access is unavailable. [GitHub SSH test](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/testing-your-ssh-connection)

## Carry the guidance forward

ChatGPT web memory and local Codex memory are separate. ChatGPT Work uses the
memory settings available to the account and workspace, not the local Codex
memory store. Memory is useful context, but it may not be present or updated in
a particular task. Do not rely on it as the only home for required project
guidance. [OpenAI: Memories](https://learn.chatgpt.com/docs/customization/memories)

For a repository, put concise, relevant instructions in `AGENTS.md` or
checked-in documentation, such as the first-failing-gate diagnostic and the
requirement to preserve working credentials. A documented skill can package a
reusable workflow, supporting references and optional scripts when the same
task recurs. Check the applicable discovery and scope rules rather than
assuming every executor has the same instructions. Neither memory, project
instructions nor a skill grants access, overrides safety policy, or guarantees
an approval. [OpenAI: AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md), [OpenAI: Skills](https://learn.chatgpt.com/docs/build-skills)

## Keep working and prevent recurrence

- Preserve a working route. Refresh `gh`, change a Git helper, or change a
  connection only when evidence identifies that layer as the problem and the
  change is authorized. Use the official login flow; never ask someone to paste
  a token into chat. [GitHub CLI login](https://cli.github.com/manual/gh_auth_login)
- Keep personal and work accounts and commit identities distinct. For a new
  HTTPS setup, use a supported credential manager or deliberately configured
  `gh` helper; for SSH use appropriate keys and host selection. Grant only the
  repository and operation access needed. [Multiple GitHub accounts](https://docs.github.com/en/account-and-profile/how-tos/account-management/managing-multiple-accounts), [credential caching](https://docs.github.com/en/get-started/git-basics/caching-your-github-credentials-in-git)
- Configure the actual Codex cloud environment's repositories, services,
  network and credentials rather than assuming it inherits the workstation's
  Keychain, SSH agent, or `gh` session. Local implementation and tests can
  continue while a separate publication gate is resolved, provided they do
  not conflict with an active task.
- For a recurrence, record a redacted incident: **when and where; intended
  operation and target; client and first failing gate; whether execution began;
  exact safe error; authorized change; verification; remaining unknowns.**
  Do not infer a successful remote write from a local commit or a failed
  approval handoff.

A useful prompt is: “Diagnose the first failing gate in this executor. Keep
network, approvals, Git, `gh`, the connector, target permissions and hooks
separate. Preserve working access and local work; do not expose credentials or
reroute a denied action. Verify the exact remote ref and PR after any authorized
publication.”
