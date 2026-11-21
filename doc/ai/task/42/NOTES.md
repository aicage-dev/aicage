# Notes from 2026-11-21

## Coupling of ssh and gpg

Searching the code by regex `ssh.gnupg|ssh.gpg|gnupg.ssh|gpg.ssh` I find many hits, mostly `ssh_gnupg`.

Do we really gain much from this coupling? The one place where coupling makes sense is in the confirmation screen as both are credentials and we can put them in the same category. but apart from that - do we gain much from this coupling in the code?

## Dependency check

We might have accidentally added a hard dependency on ssh or gnupg. We should check if `aicage` hard fails because it runs a shell command for either of those and crashes if they are absent.