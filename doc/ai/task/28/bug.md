# Bug introduced

## extra pull on second run

it seems there is an extra pull on second run with extensions, local-built builtin agents and possibly more.

sequence:

1. first start: docker pull parent-image, build, then pulled parent-image:tag is gone
2. second start: docker pull parent-image, pulled parent-image stays
3. 3rd start: no pull, pulled parent-image remains

## suspicion

With last task,we added cleanup of old or unused images.  
But we might have gone a bit to far by untagging source images of local builds.  
See:

- ca72e673
- doc/ai/task/28/28-TASK-Image Cleanup.md

As I understand it, we decide if a locally built image should be rebuilt based on:
1. Compare local and remote digest of source image and decide if source image needs to be updated locally. <ref 1>
2. Read last FS layer of source image (which must be local for this)
3. Check if that layer is in locally built image

> <ref 1>I hope this involves cleaning up of old local source images after pulling a new version of it - you must
> validate this by code analysis and report to me.

And by removing the source image after a local build, we force `aicage` to re-pull it on next run for the above check.  
That re-pull is very fast as the FS layers are still locally present (in the built image) - but having to re-pull is
clearly wrong.

My conclusion is that we keep the local source image.

> To users this might look as having an extra image of 5 GB even so technically no extra space on disk is taken as the
> FS layers are present anyway. But this is sadly almost impossible to see in the view that Docker gives for its images.

The alternative would be to store information about source images locally in text-files (last layer FS) but I really
do not like the added complexity this brings.

## Task workflow

- Don’t forget to read `AGENTS.md` and `doc/python-test-structure-guidelines.md` and respect those rules.
- Always use the existing venv.

You shall follow this order:

1. Read documentation and code to understand the task. Do your own bug analysis! Mine was superficial.
2. Ask me questions if something is not clear to you.
3. Present me with an implementation solution; this needs my approval.
4. Implement the change autonomously including a loop of running-tests, fixing bugs, running tests.
5. Run linters, use `scripts/lint.sh` with active venv.
6. Present me the change for review.
7. Interactively react to my review feedback.
8. Do not commit any changes unless explicitly instructed by the user.
