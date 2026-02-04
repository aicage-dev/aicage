# aicage: Ideas for future enhancements

## Support symlinks in project-folder

If the project-folder contains symlinks to outside it's structure, then those fail in containers.  
To fix this we could collect such symlinks and propose to mount the targets to the containers.

## Put agent command in agent.yml

Right now with `agents/<AGENT>`, `AGENT` is the command of the agent. This was done for simplicity in early stages of
development. But by now this:

- prevents having an agent with a second config (also locally)
- is ugly
- the code is mature enough by now to change this

## Plugins idea

Aicage could have plugins in the style: Copy of RunConfig is handed to plugin, which returns RunConfig or defined parts
of it.  
The current features:

- ask user about mounting .gitconfig and .gnupg
- handle --docker parameter

could potentially be moved to such plugins.

Maybe we could even allow user added custom plugins.

## Shellcheck version.sh

The `version.sh` scripts for agents are run on the users system or as fallback in the Alpine `version-check` util-image
(from repo `aicage-image-util`). Those scripts should be strictly POSIX compliant and we should verify that with
`shellcheck` in a GitHub release pipeline for `aicage-image` (where those scripts are defined).

## Tune locking of ~/.aicage

The implementation is from an earlier state where we had less files. New files are not locked.

## Fix config file locking

It was disabled due to problems on Windows, see commit with message:  
"Disable locking of config files - needs to use the lock-connection to files on Windows"

## Make update-checks optional

They are intended to be optional, but at least the version-update check causes `aicage` to crash even though a suitable
docker image was locally present.  
To reproduce: Start aicage at least once so image is present. Exit it. Then disable network and start it again.

Sample output:

```shell
PS C:\tmp\aicage-test2> aicage --share ~/aicage-test-mount:ro -e AICAGE_ENTRYPOINT_CMD=bash -- codex
Persist docker run args '-e AICAGE_ENTRYPOINT_CMD=bash' for this project? [Y/n] n
[aicage] /bin/bash: C:Usersstefapipxvenvsaicageconfigagent-buildagentscodexversion.sh: No such file or directory;
npm error code ENOTFOUND
npm error syscall getaddrinfo
npm error errno ENOTFOUND
npm error network request to https://registry.npmjs.org/@openai%2fcodex failed, reason: getaddrinfo ENOTFOUND registry.npmjs.org
npm error network This is a problem related to network connectivity.
npm error network In most cases you are behind a proxy or have bad network settings.
npm error network
npm error network If you are behind a proxy, please make sure that the
npm error network 'proxy' config is set properly.  See: 'npm help config'
npm error A complete log of this run can be found in: /root/.npm/_logs/2026-02-03T17_38_20_318Z-debug-0.log
PS C:\tmp\aicage-test2>
```

## Image Cleanup 2

We already delete old images when pulling new ones. But if another aicage instance is using the image, then the image
remains. To fix this we could on exit of `docker-run` check somehow if the iamge is still used (image digest still
tagged or such, cosign image has no tag thus special) and if not delete it.
