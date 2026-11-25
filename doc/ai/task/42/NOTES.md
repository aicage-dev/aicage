# Notes from 2026-11-26

## SSH/GPG in Textual menu

Current menu:

```text
  ┃  ▐X▌ SSH agent   : SSH agent                                                             ┃ 
  ┃  ▐X▌ GnuPG agent : GnuPG agent                                                           ┃
```

I'd like this to clearer. like `SSH keys : SSH socket` and `GPG keys : GnuPG socket`. Right now it's a repetition while my suggestion indicates sort of what is shared and how. The first part must be short, if we add more info then to the second part.

## Bug: Treat macOS like Linux for SSH/GPG handling

Right now parts of the code check "if os != linux" thus excluding macOS. unless there is a reson to treat macOS differently, we should treat it like Linux.

## Why does odex keep linking ssh/gpg strongly to git? we may need to clean up some docs

### Me to Codex

gut feeling notes when reading this:

- full of aicage internal lingo. does not take first-time-readers/new-users point of view. 
- talks about sidecar as if the whole world knew wtf a sidecar here is.
- on line 6 use `agent` not `container`.
- why does this see ssh/gpg as only git related? that is one use of it and historically ssh/gpg were linked to git in aicage - but task42 removes the last piece of connecting those and I thought the current code or docs would not make taht strict or even strong connection anymore. why do you still get that idea? (I want to know to remove those pieces in the code or docs as this is not the first time you keep making this connection more than weak and every time you do this it now costs lost work).
- entire "enable it" sections is crap. removing the git connection leaves only the info to user that ssh/gpg options are in the menu. user knows that form landing pages, he's here for the details. so we mention that ssh/gpg options are in menu here briefly without the AI slop you bloated that info up with.
- section `Direct host-agent forwarding`: chart is ok for now, maybe tune it later. but text is deeply technical while using aicage does not require that deeper linux/socket or ssh/gpg-advanced knowledge. but atm your text is only comprehensible to advanced users. so tone it down for semi noob devs but keep using correct terms and enough info so advanced users get the gist.
- you freely mix `agent` use all over the doc. we have `agent` as `coding agent` and `agent` as ssh/gpg agent and again only I as `aicage` dev can easily know in current document when you mean which. and honestly the key part here is the socket(s), not what tool actually does to the work for the socket.

I did not yet cover the lower about half of the doc. I think you should refactor the doc taking the above gut-feeling points into account before I review again.

### Response by codex


You’re right: I wrote from the old documentation framing instead of the current runtime model, and I also overloaded “agent” badly. I’m checking the current option ownership and menu wording now so the next revision uses the product’s actual language rather than carrying Git-era assumptions forward.

You’re correct: the current implementation does not make credential forwarding conditional on Git.

`aicage` enables the two paths independently through `mounts.ssh` and `mounts.gnupg`. The forwarding coordinator checks only those settings; it does not inspect Git configuration or require Git signing. The current UI also classifies them as **Credentials**, separately from Git configuration and Git root.

I kept making the Git connection because I followed the old documentation vocabulary rather than the current code. The stale framing remains in several places:

- [CONFIG.md](/home/stefan/development/github/aicage/aicage/CONFIG.md:79)
- [README.md](/home/stefan/development/github/aicage/aicage/README.md:208)
- `Home`, `How-It-Works`, `Security-and-Trust`, and `Known-Hiccups` in the wiki
- the CLI’s legacy `--git` switch still groups Git config/root with SSH and GnuPG mount preferences.

For the dedicated page, the refactor should remove Git as the framing entirely. It should describe SSH and GnuPG credentials as capabilities made available to the coding agent, with Git only an optional example—if mentioned at all.

The rewrite will also use unambiguous terms:

- **coding agent**: the tool Aicage runs;
- **credential socket**: the thing exposed to its container;
- **host credential service** or **sidecar container**: the service behind that socket.

And it will replace the current opening with a first-reader explanation of the outcome, define “sidecar container” when first introduced, collapse the “Enable it” section into one sentence, and tone the direct-forwarding text down without hiding the architectural facts.

I will not touch the wider stale Git framing or the legacy `--git` behavior without your direction; that is a separate documentation/code-scope decision from this page rewrite.
