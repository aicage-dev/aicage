# Task 33 - Improve documentation

We recently added the `--yes` option to `aicage` to simply accept suggested defaults.

And I think this might be a way to simplify first time use by new users as with `--yes` they don't get bombed with many
questions right at first start.

Plus a refresh of documentation seems due anyhow.

## Scope of documentation

Users here are technically savy developers, but not developers of `aicage` itself!

- `README.md` in this repo is the user facing first-touch point
- Other Markdown documents in this repo are not intended for users
- `../aicage.wiki` is the main user facing documentation
- Markdown documents in other repos in `../*` are also not user-facing.

## Details/Ideas

### First time use quick start guide

Something along:

1. install with `pipx install aicage`
2. ultra-quick-start: in a project folder run `aicage --yes <agent>` while mentioning that this with --yes is the
   quickest way to get up and running.
3. full config start:
   1. optionally print config of first folder with `aicage --config info` and either go to other folder
      or delete config with `aicage --config remove`
   2. start aicage again without --yes to run through full config
   3. Here add a placeholder so I can add a screenshot of how this looks on my box

### Further common scenarios

After the first time quick start guide it would be nice to guide user through common scenarios:

- Want to pass arguments to the agent?  
  → easy, same as on host.  
  Example: Resume a session with `aicage <agent> resume <session-id>`
- Need an extra folder mounted?  
  → easy, use `--share <path>[:ro}` where `aicage` handles the rest  
  Example: Share maven folder `~/.m2` from host to container: `aicage --share ~/.m2 <agent>`
- Want agent to use `docker`?  
  → easy, use `--docker`
- Want to set ENV-vars?  
  → easy, pass them as docker-args like `aicage -e FOO=bar -- <agent>`
- Need to use a proxy?  
  → easy, `aicage` passes ENV-vars, link to exact docu.
- Need an extra tool in the container?
  → medium-easy, link to documentation for custom local extensions
- Want to use another agent?
  → medium-easy, link to documentation for custom local agents
- Want to use your own base image?
  → medium, link to documentation for custom local bases

Additionally, I don't think we document how to share host network with container. I think we researched it once or twice
and decided it's not worth building it into `aicage` as it's host OS specific and for each case can be achieved by
passing custom docker-run args. But it would be nice to have a detailed documentation about this and a reference to this
from the "overview scenario list".

### Base images: document what they contain

All pre-built base images contain (almost) the same stack of tools and this code has not changed in a while. Time to
document the tools nicely. Probably in a dedicated page in `../aicage.wiki`.

As the installations (in `../aicage-image-base/scripts/os-installers`) are already nicely grouped in named scripts, I
think it should be easy to also group them in the documentation.

A table layout would be nice for this.

### List known issues/hiccups

While not really bugs or things we can change, I know of 2 small things happening, see below.

#### Know Hiccups: Claude first start

With agent `claude` when no claude config is present on host, then claude complains because `~/.claude.json` on host is
created empty.

```text
Claude configuration file at ~/.claude.json is corrupted: JSON Parse error: Unexpected EOF
The corrupted file has been backed up to: ~/.claude/backups/.claude.json.corrupted.1772142951358

──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
 Configuration Error

 The configuration file at ~/.claude.json contains invalid JSON.

 JSON Parse error: Unexpected EOF

 Choose an option:
 ❯ 1. Exit and fix manually
   2. Reset with default configuration

 Enter to confirm · Esc to cancel
```

No big deal, select `2. Reset with default configuration` and for future starts of `claude` the issue is fixed.

#### Know Hiccups: Agent authentication methods restricted

On first use, agents typically require authentication setup. Let's look at agent `codex` for example.

It first shows this option screen:

```text
  Welcome to Codex, OpenAI's command-line coding agent

  Sign in with ChatGPT to use Codex as part of your paid plan
  or connect an API key for usage-based billing

> 1. Sign in with ChatGPT
     Usage included with Plus, Pro, Team, and Enterprise plans

  2. Sign in with Device Code
     Sign in from another device with a one-time code

  3. Provide your own API key
     Pay for what you use

  Press Enter to continue
```

Now when one chooses the default option 1. then this appears:

```text
  Welcome to Codex, OpenAI's command-line coding agent

  Finish signing in via your browser

  If the link doesn't open automatically, open the following link to authenticate:

  https://auth.openai.com/oauth/authorize?response_type=code&client_id=app_EMoamEEZ73f0CkXaXp7hrann&redirect_uri=http%3A%2F%2Flocalhost%3A1455%2Fauth%2Fcallback&scope=openid%20profile%20email%20offline_access&code_challenge=GsT6cQ02A_NhisQmfdoWbOfEZX4ilDkP05m0iy69z1Y&code_challenge_method=S256&id_token_add_organizations=true&codex_cli_simplified_flow=true&state=oRMUcNb80hTouhY_ObNo86-EnWaFTwB6eaR5cjV_YVI&originator=codex_cli_rs

  On a remote or headless machine? Press Esc and choose Sign in with Device Code.

  Press Esc to cancel
```

The above authentication method will not work. `codex` is running in a container and not capable of opening a browser
on host.

So this should be documented too: Authentication methods using browser or similar do not work. Here for `codex` it's
simple: Choose option 2 at start, then it prints a URL to open manually in browser and a code. One logs in to openai
in the browser and enters the code. Done - one time setup only.

As this might confuse users this too should be documented. Even before the issue with `claude` as several/many/most
agents are affected.

### Other documentation suggestions by you

Feel free to suggest more improvements yourself.

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
