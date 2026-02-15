# Task 28 — Image Cleanup

## Delete old image after pull of update

We already delete old images when pulling new ones. But if another aicage instance is using the image, then the image
remains. To fix this we could on exit of `docker-run` check somehow if the image is still used (image digest still
tagged or such, cosign image has no tag thus special) and if not delete it.

## Delete old image after local build of update

Similarly, when we build an image to update an existing local image, then we should delete the old image by digest after
the build.

## Smarter handling of source images

Before we build an image locally, we currently pull the source image (the FROM image in Dockerfiles). This is done for:

- custom bases - we pull FROM_IMAGE
- locally built agent images: we pull aicage base-image
- locally built images with extensions: we pull the aicage final image

But actually docker-build would pull this by itself. Having a separate pull is nice towards user so he knows why he is
kept waiting (knows without looking at log file). But the current process leaves such source images on the local PC
forever.

Here we have 2 options:

- stop pulling, let docker build handle it
- after building delete the source image (it's still on local PC as layer in the built image)

## Better ideas?

Do you have better ideas or see other places where we could prevent old images sitting on users PC?

## Task workflow

- Don’t forget to read `AGENTS.md` and `doc/python-test-structure-guidelines.md` and respect those rules.
- Always use the existing venv.

You shall follow this order:

1. Read documentation and code to understand the task.
2. Ask me questions if something is not clear to you.
3. Present me with an implementation solution; this needs my approval.
4. Implement the change autonomously including a loop of running-tests, fixing bugs, running tests.
5. Run linters, use `scripts/lint.sh` with active venv.
6. Present me the change for review.
7. Interactively react to my review feedback.
8. Do not commit any changes unless explicitly instructed by the user.
