# Task 37: Improve user configuration UI

## Current situation

Aicage needs user to set up a config per folder it's started from.

### Configuration per agent and folder

The agent and folder used are always given by user when aicage is started like `aicage claude`.

So further down the term "config/configuration" normally stands for such a per folder and per agent configuration.

### First start with agent in a folder

If aicage has no existing config for the agent and this folder, then:

- aicage offers user selections in several categories
  - base image (including custom bases if present on system)
  - extensions (if custom extensions are present on system)
- additional extras can be added by arguments to aicage:
  - `-e` environment vars for the containers
  - `--share` paths from host to mount to container
  - `--docker` shorthand to configure container for docker
  - ...

### Consecutive starts with agent in a folder

Base image and extensions are hard set, other settings can be added but not removed:

- Some settings currently cannot be changed without deleting the config - base image and extension.
- Other settings like `--docker`, env-vars and shares can only be added. Removing them requires deleting the config to
  define a new one (unless one tinkers with the config file which not even I as dev do for sanity's sake).

And there also cannot be more than one config for an agent in a folder.

## Target situation

I want to make turn this into a convenient user UI with clear user guidance and better functionality.

### Textual: Potential library

It's not yet settled fully, but `Textual` looks promising, the demo of it looks quite nice.

What I'm not so keen about in the demo:

1. Cannot exit with Ctrl-C or twice Ctrl-C. After Ctrl-C a small popup in bottom right says to press Ctrl-Q afterward.
   And I don't really like my users having to learn the quirks of the UI shortcuts.
2. Tab not arrow to get to next section. This one I likely have to live with as I think arrows will be used for
   selection or navigation in a section. And this is quite common.
3. No path to simply press Enter to accept all and continue. Well this just is not built into the demo, but the new UI
   will likely be shown in a minimal section-verview style for consecutive starts in a folder when a config is already
   present. Atm then no config menu is shown to user and in future there likely will be an overview of existing config.
   But then it's important to me that just one pressed key ("Enter" strongly favored) just accepts and continues.

### CLI config args to aicage

Not critical, but I like the idea of this still being able to run without human intervention. And for our tests this
likely is important too.

So the new UI should be compatible with CLI args unless this becomes problematic or adds a lot of complexity or test
gaps where our tests gravely bypass the normal path humans use.

We can alter and add to the existing CLI args, but I favor keeping this funcionality.

### My vision for new config UI

#### Initial view

The first view when running `aicage <agent>` should be slim. I envision seeing the current (or for first start
suggested) values for the categories

- `base`: base imae
- `agent`: for now given as CLI input, maybe later selectable with last used as default
- `extensions`: currently empty unless user adds that to his system. I still want it displayed then as this is a nice
  to show users this feature exists (details in submenu or section) and maybe in future users can download online items
  by the config menu.
- `shares`: the host paths mounted to the container
- extras: like the `--docker` setting or the git/ssh/gnupg (which are technically shares) in a list

Each category could be opened into a sub-view where I have much more room for details, nice user handling and new
features.

Layout wise this initial view can well cover the entire with of a screen - we can assume user has at least 120 chars
width or a bit more. Or maybe Textual handles that dynamically with acceptable results.

#### Subviews

The initial version can pretty much follow what we have now. Meaning show lists of options to user so he can select.
Saving and exit should ideally have a button and also work on simple keys like Enter and Esc.

## Task planning

This will be a larger effort to get an initial working version, tweak it up to a user facing release and then for some
time update it with tweaks and new features.

And likely this will also cover several sessions with the coding agent.

So we should follow this rough order:

1. Discuss, ask questions until we align
2. Document initial approach in Markdown file(s) in `doc/ai/task/37`.
3. Code initial approach or parts of it, review, iterate until first alpha version. Loosely document progress.
4. Test, tweak code, update docs, also user facing docs. More alpha/beta version.
5. First user facing release.
6. During process gather ideas in documents.

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
