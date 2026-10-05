# Task 39: Show use in IDEs more prominently

## Current situation

### a bit of history

aicage first started as a CLI only tool. I was using the caged agents in terminals with IDE open besides looking at the
same files as the agent.

Then I added the in-terminal menu to add a better option for configuration than the previous argument only config path.
But I still used agents in terminals.

now a while ago I found ways to run those agents integrated in IDEs – which is a much more comfortable way of working as
the terminal only. I basically feel no difference from running agents without aicage in IDEs.

### clarification of IDE and plugin

When I say IDE – I mean JetBrains IDEs as that's what I personally use. I think some of how I do it is transferable to
other IDEs, though.

And also "running agent in IDE" basically means: having a plugin having a "panel" as part of the IDEs screen for chats
and most of them some ways in the IDE to send code or paths to the plugin panel.

Those plugins to me fall into 2 categories:
- ACP (Agent Client Protocol): Those tend to be quite versatile as ACP standardizes things, and one can add custom agent
  configs for any/most agents in them. But the agent must support ACP
  - JetBrains semi-builtin AI Assistant is one of them. I use it for OpenCode and Hermes agents but could use it for
    more agents.
- Other plugins for specific agents.
  - [jetbrains-cc-gui](https://github.com/aicage-dev/jetbrains-cc-gui): I found and use one where the path to the binary
    of Claude and Codex (only those and I added the latter option) can be set. Then I wrote shim scripts which do the
    small wrapper to the agents in aicage. The one I found used public SDKs for Codex and Claude, which come with a
    bundled agent – here it was really nice that the plugin allows setting paths of binaries thus bypassing the bundled
    agent. Again a shim script by me does the wrapping so the agent runs in aicage.

## Task: Improve docs

After seeing how comfortable it is to run agents in IDEs compared to running them in the terminal only, I no longer
think anyone wants to use aicage to run agents mainly in terminals. Even I don't.

So I assume this to become the major use case for aicage. And while IDE plugins itself is outside of aicage, I want to
document to users how to run agents in aicage in IDEs as best as I can and also place that documentation prominently in
the docs.

I think terminal for aicage will be used only for:

1. installation
2. configuration per project folder (plugins have no means to show aicage configuration)
3. maybe the odd test or debugging session of IDE-plugin-shims

We can't cover every IDE and every agent which needs special plugins. But I think ACP capable agents and plugins go far.
Sadly, the 2 main agents `Claude` and `Codex` are not (yet) ACP capable. I use a plugin which lets me set paths to
binaries – and I also saw tools or projects to bridge at least between Codex and ACP (I did not test them).

So I think our docs should cover:

- ACP capable agents and plugins
- generic how-to handle the others
  - general approach
    - tool to bridge to ACP or
    - plugin where one can set a path to binary and use a shim
  - my own setup for JetBrains IDEs
