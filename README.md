# Colony Simulation CI

Public GitHub Actions runner for validating exact commits from the private
[Love-DC/colony-sim](https://github.com/Love-DC/colony-sim) repository.

This repository contains CI configuration only. It does **not** contain game
source, assets, or source artifacts.

## What it runs

The manual workflow `Validate private colony-sim PR` verifies that the supplied
40-character SHA is the current HEAD of an open PR targeting `main` in the
private source repository, marks that exact commit pending, checks out the SHA,
verifies it, and runs the Godot 4.7.2 and/or AI Context suites. Final commit
statuses link back to this public run.

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

1. Open **Actions → Validate private colony-sim PR**.
2. Select **Run workflow**.
3. Enter the PR number (e.g. `373`) and its exact current HEAD SHA.
4. Choose `all`, `godot`, or `ai-context`.
5. Start the run.

The workflow rejects stale SHAs, closed PRs, PRs not targeting `main`, and PRs
not originating from `Love-DC/colony-sim`.

It publishes these statuses to the private commit:

- `external-ci/godot-headless`
- `external-ci/ai-context`

## Security model

- The workflow is `workflow_dispatch` only. It does not run on fork PRs.
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
