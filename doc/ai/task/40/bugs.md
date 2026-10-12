# Bugs

Quite a series.

## config removal not by agent

One cannot remove the config of one agent alone but must clear all of them. Also for global or tree configs.

We should likely allow removal of config only per agent.

## config not resilient

I don't know how below config came to be as regctl is only in the image-ref but not actually in the config.
Plus aicage tries to download such an image when the image-ref is only local, a locally built image with extension.

There are 1 or even 2 bugs hidden here.

<!-- pyml disable line-length -->
```text
(.venv) stefan@Legion2-Nobara /tmp/aicage-test$ aicage --menu none -e GLOBAL_VAR=0 -e AICAGE_ENTRYPOINT_CMD=bash -- codex
Unable to find image 'aicage-extended-dev:codex-fedora-regctl' locally
docker: Error response from daemon: pull access denied for aicage-extended-dev, repository does not exist or may require 'docker login'

Run 'docker run --help' for more information
[aicage] Docker command failed with exit code 125.
(.venv) stefan@Legion2-Nobara /tmp/aicage-test$ aicage --config codex
[aicage] Unknown config action: codex
(.venv) stefan@Legion2-Nobara /tmp/aicage-test$ aicage --config
Project config path:
/home/stefan/.aicage/projects/494a32d3723ae7ed200be4bb77b3cced0cfe38b99655d07b552b477de4d2a494.yml

Project config content:
agents:
  codex:
    base: fedora
    docker_args: -e GLOBAL_VAR=0 -e AICAGE_ENTRYPOINT_CMD=bash
    image_ref: aicage-extended-dev:codex-fedora-regctl
    mounts:
      gitconfig: true
path: /tmp/aicage-test
(.venv) stefan@Legion2-Nobara /tmp/aicage-test$ 
```
<!-- pyml enable line-length -->

## Can one set global config by CLI args?

I tried but failed, see here:

<!-- pyml disable line-length -->
```text
(.venv) stefan@Legion2-Nobara /tmp/aicage-test$ aicage --config remove codex
Agent config removed:
codex
Project config updated:
/home/stefan/.aicage/projects/494a32d3723ae7ed200be4bb77b3cced0cfe38b99655d07b552b477de4d2a494.yml
(.venv) stefan@Legion2-Nobara /tmp/aicage-test$ aicage --config
Project config path:
/home/stefan/.aicage/projects/494a32d3723ae7ed200be4bb77b3cced0cfe38b99655d07b552b477de4d2a494.yml

Project config content:
agents: {}
path: /tmp/aicage-test
(.venv) stefan@Legion2-Nobara /tmp/aicage-test$ aicage --menu none -e GLOBAL_VAR=0 -e AICAGE_ENTRYPOINT_CMD=bash -- codex
[stefan@4b0896ef3a49 aicage-test]$ set | grep GLOBAL
GLOBAL_VAR=0
[stefan@4b0896ef3a49 aicage-test]$ exit
exit
(.venv) stefan@Legion2-Nobara /tmp/aicage-test$ aicage --menu none -e GLOBAL_VAR=0 -e AICAGE_ENTRYPOINT_CMD=bash --config -- codex
[aicage] No additional arguments are allowed with --config.
(.venv) stefan@Legion2-Nobara /tmp/aicage-test$ aicage --menu none -e GLOBAL_VAR=0 -e AICAGE_ENTRYPOINT_CMD=bash --config codex
[aicage] Unknown config action: codex
(.venv) stefan@Legion2-Nobara /tmp/aicage-test$ 
```
<!-- pyml disable line-length -->

## Global and tree in Textual menu not visible enough

That gray text which currently changes for global or tree config was deliberately designed to not catch the eye because
it adds no or little value for normal project config.

But being in global or tree config should be clear to users. I'm not sure that small text up there is enough unless it's
screaming red or yellow. We may well add some text besides that small header/title, maybe give text an off color and
then header and nothing else needs to visually scream to be visible.
