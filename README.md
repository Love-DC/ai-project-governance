# Colony Simulation CI

Public GitHub Actions runner for validating exact commits from the private
[Love-DC/colony-sim](https://github.com/Love-DC/colony-sim) repository.

This repository contains CI configuration only. It does **not** contain game
source, assets, or source artifacts. Its root `rae-governance.json` identifies this
repository as the independent Colony Sim validation service and records its
workflow entrypoint; RAE discovers that contract from this repository rather
than treating this runner as a directory inside the game repository.

## What it runs

The workflow `Validate private colony-sim PR` verifies that the supplied
40-character SHA is the current HEAD of an open PR targeting `main` in the
private source repository, marks that exact commit pending, checks out the SHA,
verifies it, and runs the Godot 4.7.2 and/or AI Context suites. Final commit
statuses link back to this public run.

A trusted AI coordinator can also trigger the same workflow without Actions
write permission by creating a command comment on the dedicated
[CI trigger control issue #3](https://github.com/Love-DC/colony-sim-ci/issues/3):

```text
/validate-private-pr <PR_NUMBER> <FULL_40_CHARACTER_HEAD_SHA> <all|godot|ai-context>
```

The comment must be authored as `Love-DC`. The workflow accepts commands only
on issue #3 (not PR comments), then re-reads the private PR and rejects closed,
wrong-base, wrong-origin, or stale-SHA requests. Any AI session using the
connected `Love-DC` GitHub account with permission to comment on this public
issue can submit the command. Sessions with another identity or without issue
comment permission cannot use this route. Manual `workflow_dispatch` remains
available as a fallback.

Standard GitHub-hosted runners are free and unlimited for public repositories:
[GitHub Actions billing](https://docs.github.com/en/billing/concepts/product-billing/github-actions).

## One-time secret setup

Create a fine-grained PAT restricted to **only** `Love-DC/colony-sim` with:

- **Contents: Read-only** — fetch the private source.
- **Pull requests: Read-only** — verify the PR state, base and exact current HEAD.
- **Commit statuses: Read and write** — publish pending and final statuses.

Add it under **Settings → Secrets and variables → Actions** in this repository:

- Name: `COLONY_SIM_PRIVATE_TOKEN`
- Value: the PAT

Do not paste the token into code, Issues, PRs, logs, or chat. Do not grant
Contents write, Actions write, Administration, or access to other repositories.

## Run a validation

After the workflow is merged to this repository's default branch and the secret
is configured:

**Preferred for AI coordinators:** re-fetch the current PR HEAD SHA, then add
the one-line command to [CI trigger control issue #3](https://github.com/Love-DC/colony-sim-ci/issues/3).

**Manual fallback:**
1. Open **Actions → Validate private colony-sim PR**.
2. Select **Run workflow**.
3. Enter the PR number and its exact current HEAD SHA.
4. Choose `all`, `godot`, or `ai-context`.
5. Start the run.

The workflow rejects stale SHAs, closed PRs, PRs not targeting `main`, and PRs
not originating from `Love-DC/colony-sim`.

It publishes these statuses to the private commit:

- `external-ci/godot-headless`
- `external-ci/ai-context`

## Security model

- Triggers are limited to manual `workflow_dispatch` and `issue_comment.created`.
  The issue-comment path runs the secret-bearing prepare job only for issue #3,
  only when the comment author is `Love-DC`, and never for PR comments.
  It does not run on push, pull_request, pull_request_target, or workflow_run.
- Keep write access to this public repository limited to trusted maintainers.
  Anyone able to change and run default-branch workflows can potentially misuse
  its configured secret.
- Protect `main` with pull-request review before merging workflow changes.
- The private source is checked out on an ephemeral runner. No private source
  artifact or cache is uploaded by this workflow.
- Checkout uses `persist-credentials: false`. Test jobs receive the token only
  as the checkout action input, not as an environment variable.
- Status reporting runs on a separate fresh runner after tests finish.
- Workflow logs are public. Never print source files, secrets, or private data.
- This CI service does not merge PRs, modify Issues, or dispatch Workers.
- A successful status proves only the exact test jobs and SHA shown in the run;
  it does not replace Owner review or manual gameplay/device testing.

## Test coverage maintenance

The Godot scenes and Python commands mirror the private repository workflows
at the time this version is authored. When
`.github/workflows/godot-headless.yml` or
`.github/workflows/ai-context-checks.yml` changes in the source repository,
update this runner and review its diff before merge. Do not claim omitted tests
are covered.
