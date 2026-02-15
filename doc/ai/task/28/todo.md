# TODO

## extra pull on second run

it seems there is an extra pull on second run with extensions, local-built builtin agents and possibly more.

sequence:

1. first start: docker pull parent-image, build, then pulled parent-image:tag is gone
2. second start: docker pull parent-image, pulled parent-image stays
3. 3rd start: no pull, pulled parent-image remains

## bug after image prune

```shell
stefan@legion-nobara ~/development/github/aicage/aicage$ aicage --config info
Project config path:
/home/stefan/.aicage/projects/c963fcec26f29be9c3e43ecda59e2dff4ccdc54f400c98bd2a7bbe400b0b1ddf.yml

Project config content:
agents:
  codex:
    base: fedora
    image_ref: aicage-extended:codex-fedora-act
    mounts:
      docker: true
      gitconfig: true
      gnupg: true
    shares:
    - /home/stefan/development/github/aicage
    - /mnt/winC/Users/stefa/.codex
  copilot:
    base: fedora
    extensions:
    - act
    image_ref: aicage-extended:copilot-node-act
    mounts:
      docker: true
      gitconfig: true
      gnupg: true
    shares:
    - /home/stefan/development/github/aicage
path: /home/stefan/development/github/aicage/aicage
stefan@legion-nobara ~/development/github/aicage/aicage$ aicage codex
Unable to find image 'aicage-extended:codex-fedora-act' locally
docker: Error response from daemon: pull access denied for aicage-extended, repository does not exist or may ...

Run 'docker run --help' for more information
[aicage] Docker command failed with exit code 125.
stefan@legion-nobara ~/development/github/aicage/aicage$
```
