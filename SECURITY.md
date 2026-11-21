# Security policy

This public repository is a CI controller for a private source repository.

- Never commit credentials, PATs, installation tokens, or other secrets.
- The only intended secret is `COLONY_SIM_PRIVATE_TOKEN`, stored in repository
  Actions Secrets.
- The token must be fine-grained and restricted to `Love-DC/colony-sim` with
  Contents read-only, Pull requests read-only, and Commit statuses read/write.
- Do not grant untrusted contributors workflow write access.
- Do not add `pull_request_target`, untrusted `workflow_run` artifact handling,
  or fork-triggered workflows that expose the private token.
- Keep private checkout credentials disabled after checkout.
- Do not upload or cache private source contents.
- Treat all workflow logs as public.
- Review every workflow change before merging it to the default branch.
