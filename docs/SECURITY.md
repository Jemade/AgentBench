# Execution and account boundaries

## Candidate code

External source is executed only with `RUNNER=docker`. The container has:

- No network, no capabilities and `no-new-privileges`.
- UID/GID 65534, a read-only root filesystem and read-only fixture mount.
- A small no-execute `/tmp` filesystem, 128 MB memory, no additional swap, half a CPU, 64 processes and a 64-file limit.
- A ten-second wall-clock deadline, file-backed output monitoring and bounded output reads.
- No provider API key, host credentials, Docker socket or database connection string.

The worker kills timed-out Docker clients and forcibly removes the named container in a finally block. Output is checked periodically, so a burst can temporarily exceed the target before cleanup; use host disk quotas and an isolated host for operational protection. Containers share the host kernel. They reduce exposure but are not a security-equivalent replacement for VMs or a hardened microVM service.

The worker controls Docker and therefore holds substantial host privileges. Keep it on a dedicated trusted worker host. Do not mount Docker into the public API. An Internet-facing multi-user service needs stronger isolation, per-user budgets/quotas, credential management, monitoring and an independent review.

## Local demo mode

`RUNNER=trusted-local` also requires `ALLOW_TRUSTED_LOCAL=true`. It accepts only the exact source of the selected authored reference/naive fixture. Provider source, changed baseline source and unknown agents are refused. Baseline files are trusted project code, so review repository changes before executing them. This is not a general Python execution endpoint.

## Accounts and browser requests

Accounts are explicitly seeded from environment variables; there is no public registration or default admin password. Passwords use salted scrypt. Session secrets are random and only SHA-256 digests are stored. Sessions expire after twelve hours and use HTTP-only, SameSite Strict cookies; enable Secure cookies under HTTPS. Logout deletes the server session.

Each history, detail, cancellation, comparison and export operation filters by account ownership. A caller cannot fetch another user's result by knowing its ID. Mutation requests require the custom browser header and JSON body length, with no cross-origin API policy enabled. Login failures are limited per normalized email and direct client IP. If placed behind a proxy, configure trusted forwarded-IP handling and gateway-level rate limits deliberately.

Provider base URL/model/key are server configuration. They cannot be changed through a user-submitted URL, preventing a run submission from becoming an arbitrary outbound request facility. Provider error text is not persisted because it may contain sensitive information. Candidate source/results are private account data but are stored unencrypted in the database; protect backups and database access.

## Known limits

No team roles, password-reset email, per-provider spending enforcement, signed evaluation attestation, independent audit, or anti-cheating isolation between candidate and grader. A six-task public suite is appropriate for an inspectable portfolio demonstration and development experiments, not certification or autonomous execution on business secrets.
