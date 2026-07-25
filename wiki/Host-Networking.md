# Host networking

`aicage` does not provide a dedicated host-network flag. Networking behavior is host-OS specific, and Docker already
supports it via runtime flags.

Use Docker run pass-through args to control networking:

```bash
aicage --network host -- <agent>
```

## Notes

- `--network host` behavior depends on your Docker environment and OS.
- If host networking is not available or not desired, use bridge networking with explicit ports.

Example with published port:

```bash
aicage -p 3000:3000 -- <agent>
```

Example with a named Docker network:

```bash
aicage --network my-net -- <agent>
```

For Docker arg syntax, see [Docker run pass-through args](Docker-Args).
