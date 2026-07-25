# Docker run pass-through args

`aicage` lets you pass extra `docker run` options straight to Docker. This is useful for things like
extra env vars, port publishing, or attaching to a specific Docker network.

## In the setup screen

Open `Docker Args` in the setup screen when the container needs runtime flags that `aicage` itself
does not model directly.

![Docker args](screenshots/textual/Screenshot_docker_args.png)

Typical examples:

- add environment variables such as `-e FOO=bar`
- publish ports such as `-p 3000:3000`
- attach to a network such as `--network my-net`

The values entered there are saved with the rest of the project config when you accept the
overview.

## CLI syntax

Any arguments between `aicage` and the agent are treated as Docker args. You must separate them
from the agent with `--`.

```bash
aicage [aicage options] <docker-args> -- <agent> [<agent-args>]
```

`aicage` does not validate these args; they are forwarded verbatim to `docker run`.

## Proxy env vars

`aicage` automatically forwards these host proxy env vars to local image builds and runtime when they are set:
`HTTP_PROXY`, `HTTPS_PROXY`, `ALL_PROXY`, and `NO_PROXY`.

## CLI examples

Set an environment variable inside the container (replace `<agent>` with your agent):

```bash
aicage -e FOO=bar -- <agent>
```

Publish a port:

```bash
aicage -p 3000:3000 -- <agent>
```

Attach to a network:

```bash
aicage --network my-net -- <agent>
```

Use host network mode (when supported by your Docker environment, see also [Host networking](Host-Networking):

```bash
aicage --network host -- <agent>
```

Mount an extra directory (in addition to your project mount):

```bash
aicage --share ~/.cache <agent>
```

Prefer `--share` over raw Docker mount args (`-v`/`--mount`) for host path sharing. `--share` is
more convenient and lets `aicage` apply its host/container path handling consistently.

Extensions can also define extra shares (host mounts).

Use raw Docker mount args only when you need mount options that `--share` does not support.

Raw Docker mount example:

```bash
aicage -v pgdata:/var/lib/postgresql/data -- <agent>
```

## Persistence

When you pass docker args, `aicage` uses them for the current run.

- In the default setup screen, they appear in `Docker Args` and are saved if you accept the
  overview.
- With `--menu simple`, `aicage` asks whether to persist them for this project and agent.
- With `--menu none`, defaults are accepted automatically, so passed docker args are persisted.

To change or remove persisted args later, run `aicage <agent>` and edit `Docker Args` in the setup
screen.
