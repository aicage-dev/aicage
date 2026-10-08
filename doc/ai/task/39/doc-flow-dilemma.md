# Flow Dilemma

We added the IDE plugin docs in prominent places in the entries of the docs:

- aicage/README.md
- aicage.wiki/Home.md

But we just added it and the rest of those docs. The first-use guidance flow is messy as it still focuses on terminal
use only when the new approach is that users will use aicage-agents in IDEs and resort to terminal for the
per-repo-folder configuration.

And I also see a small flow dilemma. The user must know about the config in the terminal - but if we spread that out
before guiding him to IDE use, then `aicage` looks too much like a terminal-only tool.

And if we guide him to IDE use first, then he will likely not know about the config in the terminal, get stuck in IDE
use and abandon the tool.

## Example of a first-time user

This is how I imagine a first-time user will use `aicage`:

1. Start reading docs to get up and running without reading everything
2. Install aicage from the docs
3. Get to use an agent asap. Fastest is without extra config.
4. Soon he will miss software in the aicage image, or want the agent to user docker.  
   To him: agent has a problem and reports a missing tool in his environment.
5. This is the crucial moment. If he has briefly seen how to configure aicage, then he will try to solve it that way and
   even be willing to read some docs for it.  
   But if he has not seen that, then he will be stuck and likely abandon the tool.

## Summary

So this basically is my small dilemma. It would be easy to let the user (by flow in docs) install aicage in terminal and
in terminal let him see the config. But by doing so, I'd likely at this point at least have to explain the basic config
options or the first screen. Which is all terminal-only with screenshots of menus in terminals. And to me this would be
enough "initial" terminal content to make aicage look like a terminal-only tool. The nicer in IDE use would come a bit
too late.
