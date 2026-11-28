# Shared AI Project Governance and CI

This public repository is the shared governance and CI support repository for private projects integrated with RAE. It keeps common validation infrastructure public so private repositories do not need their own Actions allowance. Each project retains its own repository-local manifest, workflow adapter, control issue, exact-SHA validation, and least-privilege token; project source and secrets remain private.

This repository currently provides isolated exact-commit validation adapters for:

- [Love-DC/colony-sim](https://github.com/Love-DC/colony-sim)
- [Love-DC/Lambent](https://github.com/Love-DC/Lambent)
- [Love-DC/Unbroken-Frontier](https://github.com/Love-DC/Unbroken-Frontier)

It contains governance and CI configuration only. It does **not** contain private
project source, assets, or source artifacts. Its root `rae-governance.json`
identifies this repository as the shared public governance/CI service; each source
repository independently identifies the adapter and control issue it uses.

## What it runs

The workflow `Validate private colony-sim PR` supports two explicitly
validated targets:

- `pull_request`: the supplied 40-character SHA must be the current HEAD of an
  open PR targeting `main` in the private source repository.
- `post_merge`: the supplied SHA must be proven by GitHub's compare API to be
  an ancestor of the current private `main` branch. Diverged, ahead-of-main,
  stale, or unprovable commits are rejected.

For either mode, the workflow marks the exact commit pending, checks out that
SHA, verifies it, validates the source repository's `rae-governance.json` and
referenced policy/CI files, then runs the Godot 4.7.2 and/or AI Context suites.
Final commit statuses link back to this public run.

A trusted AI coordinator can also trigger the same workflow without Actions
write permission by creating a command comment on the dedicated
[CI trigger control issue #3](https://github.com/Love-DC/ai-project-governance/issues/3):

```text
/validate-private-pr <PR_NUMBER> <FULL_40_CHARACTER_HEAD_SHA> <all|godot|ai-context>
```

For a commit already merged to the private repository's `main`, use:

```text
/validate-private-merge <FULL_40_CHARACTER_MERGE_SHA> <all|godot|ai-context>
```

The comment must be authored as `Love-DC`. The workflow accepts commands only
on issue #3 (not PR comments). The PR command re-reads the private PR and rejects
closed, wrong-base, wrong-origin, or stale-SHA requests. The post-merge command
proves that the supplied SHA is reachable from the current private `main`
branch before running tests. Any AI session using the connected `Love-DC`
GitHub account with permission to comment on this public issue can submit the
command. Sessions with another identity or without issue comment permission
cannot use this route. Manual `workflow_dispatch` remains available as a
fallback.

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
the one-line command to [CI trigger control issue #3](https://github.com/Love-DC/ai-project-governance/issues/3).

**Manual fallback:**
1. Open **Actions → Validate private colony-sim PR**.
2. Select **Run workflow**.
3. Choose `pull_request` or `post_merge` validation mode.
4. For `pull_request`, enter the PR number and its exact current HEAD SHA.
   For `post_merge`, leave PR number empty and enter a full SHA already
   reachable from `main`.
5. Choose `all`, `godot`, or `ai-context`.
6. Start the run.

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


## Lambent private repository validation

The same public runner now also supports the private [Love-DC/Lambent](https://github.com/Love-DC/Lambent) repository through an independent workflow:

- Workflow: `.github/workflows/validate-private-lambent.yml`
- Control issue: [Lambent CI trigger control room #9](https://github.com/Love-DC/ai-project-governance/issues/9)
- PR command: `/validate-lambent-pr <PR_NUMBER> <FULL_40_CHARACTER_HEAD_SHA>`
- Post-merge command: `/validate-lambent-merge <FULL_40_CHARACTER_MERGE_SHA>`
- Status context on the private commit: `external-ci/lambent-governance`
- Secret: `LAMBENT_PRIVATE_TOKEN`, a separate fine-grained PAT scoped only to `Love-DC/Lambent`

This initial Lambent suite is deliberately **governance-only** because the source repository has been reset and currently contains no application code or tests. It verifies the exact checked-out SHA, `rae-governance.json`, all declared required governance files, and the declared runner workflow. It does not claim application build/test coverage.

The Lambent trigger accepts only top-level comments on issue #9 authored as `Love-DC`, or a manual dispatch by a trusted maintainer. Its secret is never shared with the Colony Sim workflow. All private checkouts use ephemeral runners, `persist-credentials: false`, and no private-source artifact/cache upload.


## Unbroken Frontier native bridge validation

The private [Love-DC/Unbroken-Frontier](https://github.com/Love-DC/Unbroken-Frontier) repository uses a separate public runner workflow:

- Workflow: `.github/workflows/validate-private-unbroken-frontier.yml`
- Control issue: [Unbroken Frontier CI control room #15](https://github.com/Love-DC/ai-project-governance/issues/15)
- PR command: `/validate-unbroken-frontier-pr <PR_NUMBER> <FULL_40_CHARACTER_HEAD_SHA> <all|windows|android|ios>`
- Post-merge command: `/validate-unbroken-frontier-merge <FULL_40_CHARACTER_MERGE_SHA> <all|windows|android|ios>`
- Status contexts: `external-ci/unbroken-frontier-windows`, `external-ci/unbroken-frontier-android`, and `external-ci/unbroken-frontier-ios`
- Secret: `UNBROKEN_FRONTIER_PRIVATE_TOKEN`, a separate fine-grained PAT scoped only to `Love-DC/Unbroken-Frontier`.

The workflow validates an open PR's exact current HEAD or proves a post-merge SHA is reachable from private `main`. It then builds the Windows GDExtension and performs a Godot headless `ping()` smoke test, assembles and inspects Android arm64 debug/release v2 plugin AARs, and builds the iOS device-arm64 static archive while checking the GDExtension entry point. The suites can be selected individually. The initial Windows run publishes only the generated `Cargo.lock` dependency metadata as a short-retention artifact so the resolved graph can be reviewed and committed; it does not upload private source or platform binaries.

The Unbroken Frontier workflow has a distinct control issue, secret, source repository, and status contexts. It never uses Colony Sim or Lambent credentials. Compile/package checks do not establish Android/iOS on-device runtime compatibility; gdext mobile support remains experimental.
