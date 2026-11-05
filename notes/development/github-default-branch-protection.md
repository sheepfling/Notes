# A small branch-protection baseline for my GitHub projects

> Type: reference
> Status: current
> Updated: 2026-11-05
> Tags: github, git, branch-protection, project-setup

I added a common default-branch protection baseline to 35 public repositories.
The aim was a straightforward branch-and-PR workflow without requiring a
second reviewer for every small project.

Four repositories already had protection and were left alone. One empty
repository was also left untouched. This was a pass over the existing public
projects, not an account-wide policy that automatically covers future
repositories.

## What changed

Each newly protected default branch received a classic branch-protection rule:

- Require a pull request before merging.
- Require no approving reviews.
- Allow administrator bypass.
- Leave force pushes and branch deletion disabled.
- Leave required status checks off until suitable checks can be verified.

Requiring a PR and requiring an approval are separate settings. This baseline
provides a place to inspect the diff, discuss a change, and see checks without
making an independent reviewer a prerequisite.

The administrator exception matters. An administrator can still bypass the
PR requirement, so this is not a guarantee that every change will go through
review. The intended working habit remains: make a feature branch, open a PR,
check the result, then merge deliberately. GitHub documents the
[settings and their exceptions](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches).

## How the setup was done

The changes were made through GitHub's browser settings using classic branch
protection, not repository rulesets. The GitHub CLI in the task environment
reported an invalid token, so it was not used to apply the rules. Browser
authentication and CLI authentication are separate; a working browser session
does not establish that a terminal has working API credentials.

For another project, the repeatable procedure is:

1. Confirm the repository, its actual default branch, and any existing
   protection. Do not assume the branch is called `main`, or replace an
   existing policy with a weaker baseline.
2. Open **Settings → Branches → Add classic branch protection rule**.
3. Set the branch-name pattern to the actual default branch.
4. Enable **Require a pull request before merging** and leave
   **Require approvals** unchecked.
5. Leave **Do not allow bypassing the above settings** unchecked to retain
   administrator bypass. Keep **Allow force pushes** and **Allow deletions**
   unchecked.
6. Leave required status checks off unless their names and behavior have been
   verified for that repository.
7. Save, reopen the rule, and read the settings back. Check that the rule
   matches the intended branch, rather than relying only on a save message.

The [GitHub setup guide](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/managing-a-branch-protection-rule)
covers the current UI. If the default branch changes later, check the rule's
target again.

## Why required CI is a separate pass

The status-check selector did not provide enough evidence to choose stable
required checks confidently. Adding guessed names would make the policy
depend on checks that might not report on the relevant PRs.

No required CI checks were added in this pass. Existing workflows can still
run, but running CI and making its result a merge requirement are different
things.

For each project, the next step is to inspect a real PR run, identify the
checks that should gate a merge, and confirm that those checks report
consistently for the changes they are meant to cover. Then add the verified
checks and confirm that an ordinary PR can satisfy the rule. This follow-up
remains open.

## Verification and limits

All 35 newly created rules were read back after saving. That verifies the
configuration at the time of the change; it is not a destructive test of force
pushing or deleting a live default branch.

The result is a consistent starting point: PRs required, no mandatory
reviewer, administrator bypass retained, and force pushes and deletion
disabled. Existing protections were preserved. CI enforcement still needs
project-by-project work.

If a future required check blocks a legitimate PR, diagnose the check and its
trigger first, then correct that specific requirement. Keep the other
protections in place rather than removing the whole rule.

Related draft: [Diagnose GitHub access in ChatGPT and Codex](https://github.com/sheepfling/Notes/pull/6).
