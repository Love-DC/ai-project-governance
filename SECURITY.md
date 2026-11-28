# Security policy

This public repository hosts CI workflows that read selected private source repositories. Keep each source credential isolated.

## Secrets and repository scope

- `COLONY_SIM_PRIVATE_TOKEN` must be a fine-grained token restricted only to `Love-DC/colony-sim`.
- `LAMBENT_PRIVATE_TOKEN` must be a different fine-grained token restricted only to `Love-DC/Lambent`.
- `UNBROKEN_FRONTIER_PRIVATE_TOKEN` must be a third fine-grained token restricted only to `Love-DC/Unbroken-Frontier`.
- Each token requires only Contents: Read-only, Pull requests: Read-only, and Commit statuses: Read and write. Never share a source token across projects.
- Never reuse one source token across repositories. Never grant Contents write, Administration, Actions write, or unrelated repository access.
- Store tokens only in this repository's Actions Secrets. Never put credentials into source files, Issues, PRs, workflow inputs, logs, tasks, or chat.

## Workflow trust boundary

- Secret-bearing workflows may run only through their dedicated control issue and the `Love-DC` comment-author guard, or through manual `workflow_dispatch` by a trusted maintainer.
- The issue-comment trigger must reject PR comments, other issue numbers, other authors, malformed commands, stale SHAs, wrong-base PRs, and unexpected source repositories.
- Do not add `push`, `pull_request`, `pull_request_target`, `workflow_run`, or fork-triggered execution paths that can expose private-source tokens.
- Keep the public repository write-access list restricted to trusted maintainers. Anyone who can change secret-bearing workflows and dispatch them may be able to misuse configured secrets.
- Keep `GITHUB_TOKEN` permissions read-only unless a reviewed workflow has a concrete need. Commit status writes use each source repository's separately scoped PAT.

## Private source handling

- Check out private source only on ephemeral GitHub-hosted runners at an exact, verified commit SHA.
- Use `persist-credentials: false` for every checkout.
- Never print private source files, secret values, environment dumps, or private logs.
- Never upload or cache private source content or build artifacts.
- Report only pass/fail status, source SHA, and the public workflow run URL back to the relevant private commit. The Unbroken Frontier runner may add only allow-listed Rust error codes and broad failure categories to that private status; never publish compiler messages, source paths, symbol names, source snippets, or raw logs.
- Keep each workflow's output/status context distinct so one project's validation cannot satisfy another project's checks.

## Changes to this public repository

- Review every workflow, validator, test, secret name, and control-issue guard change before merging to `main`.
- The public CI configuration test suite must validate both source workflows and their exact source/project/control-issue boundaries.
- Never claim coverage beyond the checks actually run for the exact SHA.


## Unbroken Frontier runner

- The Unbroken Frontier control endpoint is issue #15 and accepts only top-level comments authored as `Love-DC`.
- Its workflow may check out only `Love-DC/Unbroken-Frontier`, only at an exact verified PR HEAD or a commit proven reachable from private `main`.
- Its token is `UNBROKEN_FRONTIER_PRIVATE_TOKEN`; it must never be reused by Colony Sim, Lambent, or other projects.
- It publishes only the three Unbroken Frontier-specific platform status contexts. It does not merge PRs or publish private build outputs.
- The only permitted workflow artifact is the generated Cargo.lock dependency metadata required to pin the exact resolved dependency graph; it is not a private source or binary artifact.
