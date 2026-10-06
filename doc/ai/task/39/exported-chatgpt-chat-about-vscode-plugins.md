# Expprted ChatGPT Chat about VSCode Plugins

This is a raw text export of a chat between ChatGPT and me about VSCode plugins.

The important parts are:

- which plugins to use/install for VScode for Claude and Codex
- what setting to set per plugin

Ignore the initial attempts with wrong plugins and all the bickering about the POS IDE.

Here's my `~/.config/Code/User/settings.json` at the end:

```json
{
    "workbench.colorTheme": "Light 2026",
    "chat.agentHost.codexAgent.enabled": false,
    "chat.agentHost.allowSignedOutWhenUsable": true,
    "chatgpt.cliExecutable": "/home/stefan/development/github/aicage/aicage/config/ide-plugins/aicage-vscode-codex.debug.sh",
    "claudeCode.claudeProcessWrapper": "/home/stefan/development/github/aicage/aicage/config/ide-plugins/aicage-vscode-claude.debug.sh",
    "claudeCode.preferredLocation": "sidebar",
    "claudeCode.disableLoginPrompt": true,
    "claudeCode.autosave": false
}
```

---

in the KDE lauchnger config I set /home/stefan/development/ as "work path" for VS code but it still uses HOME as pwd

That can happen, and the reason is likely VS Code’s single-instance behavior rather than KDE ignoring the “Work path”.

VS Code documents ${cwd} as “the task runner's current working directory upon the startup of VS Code,” i.e. it is tied
to the process startup cwd, not the currently opened workspace.

The important wrinkle: if any VS Code process is already running, clicking your KDE launcher can hand the request to
that existing VS Code instance. In that case, the new launcher’s working directory may never become the cwd of the
already-running process.

So I would test it like this:

pkill -f '/usr/share/code/code'

or simply fully quit all VS Code windows and make sure no code process remains:

pgrep -af code

Then launch VS Code only from the KDE menu and trigger your Codex shim again.

If your KDE Path=/home/stefan/development/ setting is actually being honored, your shim should then see:
pwd: /home/stefan/development

If it still sees /home/stefan, then the next thing I’d inspect is the actual .desktop file KDE generated/edited, because
KDE’s GUI “Work path” should correspond to the desktop-entry Path= field.

You can find the effective VS Code launcher with:

grep -R -l 'Visual Studio Code' \
  ~/.local/share/applications \
  /usr/share/applications 2>/dev/null

Then inspect it, especially:
Exec=...
Path=/home/stefan/development/

One other clue: VS Code's own source explicitly uses the process cwd() in several startup-path decisions, so this cwd
really is a process-level property; opening/changing a workspace later does not redefine it.

So I’d bet first on: you edited the launcher correctly, but an already-running VS Code instance kept its old
/home/stefan cwd.
when setting a path in the launcher, it now works. nice.

I like how the plugin is an official plugin from Codex and it allows settting path to codex. is there such an official
plugin with path override for JetBrains?

As far as I can verify, no official OpenAI JetBrains plugin currently exposes the same kind of arbitrary codex
executable-path override that the official VS Code extension does.

JetBrains’ official route is different: Codex is integrated into the JetBrains AI Assistant itself, starting with
2025.3, and JetBrains treats Codex as a built-in/managed agent option rather than as a separately configurable CLI path.

So today the situation is roughly:

```text
    VS Code official OpenAI Codex extension → yes, configurable CLI path via chatgpt.cliExecutable
    JetBrains official AI Assistant Codex integration → Codex is integrated, but I could not find an official setting to
    point it at an arbitrary local codex binary
    JetBrains ACP → much better escape hatch for custom agent binaries, if the agent supports ACP
    non-ACP JetBrains agent integrations → back to the “does this particular plugin happen to let me override the
    executable?” problem you already ran into
```

That’s actually an interesting advantage of the VS Code Codex plugin for your aicage use case: despite the ugly cwd
behavior, the official OpenAI plugin at least gives you a supported-looking CLI substitution hook. JetBrains’ official
Codex integration seems more closed around its managed agent implementation.
now to Claude with VScode and path override. what are my options?

For Claude in VS Code, you actually have a better option than I expected: the official Anthropic Claude Code extension
now has a wrapper/executable hook.

The relevant setting is:

"claudeCode.claudeProcessWrapper": "/absolute/path/to/your/wrapper"

Anthropic’s current VS Code extension docs/issues describe claudeProcessWrapper as the executable path used to launch
the Claude process.

So for aicage, you should be able to do something analogous to Codex:

{
  "claudeCode.claudeProcessWrapper": "/home/stefan/.aicage/ide-plugins/vscode/aicage-claude.debug.sh"
}

That wrapper can then invoke your actual aicage entry point and forward all arguments.

There is also:

"claudeCode.environmentVariables": []

which lets you inject environment variables into the spawned Claude process, and:

"claudeCode.disableLoginPrompt": true

which is useful when you’re intentionally routing through something other than Anthropic’s normal authentication flow.

Historically this was missing — there was a feature request specifically asking Anthropic to allow configuring the
Claude executable path because the extension used its bundled CLI. That request was later closed, and the newer
extension now exposes the wrapper mechanism.

So your current comparison becomes quite nice:
Official OpenAI Codex extension
    chatgpt.cliExecutable
        ↓
    aicage shim
        ↓
    Codex

Official Anthropic Claude Code extension
    claudeCode.claudeProcessWrapper
        ↓
    aicage shim
        ↓
    Claude

One semantic difference: Codex’s setting replaces the CLI executable, whereas Claude calls it a process wrapper. That
may actually be better for aicage, because a wrapper is explicitly expected to sit in front of Claude rather than
impersonate the binary completely.

And yes, the Claude extension is the official Anthropic extension (anthropic.claude-code).

The next thing I’d do in your place is exactly what you did for Codex: point claudeProcessWrapper at a debug shim and
log pwd, argv, environment, and stdin. That will tell us whether Anthropic also inherits VS Code’s launcher cwd or
actually passes the workspace properly.
nice. but I am not willing to remember the shitty keyboard shortcuts used at every corner of VS code. include them in
your guide

Yes. For VS Code instructions I’ll include both where to click and the keyboard shortcut, so you don’t have to remember
its shortcut maze.

For the Claude setup, use this path:

```text
    Open Extensions: click the Extensions icon in the left Activity Bar, or press Ctrl+Shift+X
    Search for Claude Code
    Install/enable the official Anthropic extension
    Open Settings: click the gear icon → Settings, or press Ctrl+,
    Search for:
    claudeCode.claudeProcessWrapper
    Set it to your shim, e.g.
    /home/stefan/.aicage/ide-plugins/vscode/aicage-claude.debug.sh
    If useful, also search for:
    claudeCode.disableLoginPrompt
    Reload VS Code via gear → Command Palette, or press Ctrl+Shift+P, then run:
    Developer: Reload Window
    Open Claude Code via its sidebar icon if visible; if not, use Command Palette (Ctrl+Shift+P) and type Claude
```

For anything I tell you to do in VS Code from now on, I’ll give the menu/UI route plus shortcut.
1 selection
there is no "Claude" just a lot of "Claude Code: XYZ"

Right — search for the specific command, not just Claude.

Use:

```text
    click View → Command Palette…
    or Ctrl+Shift+P
    then type Claude Code: Open in Side Bar
```

That is the command that opens/focuses the Claude Code sidebar. Anthropic’s extension also has commands like Claude
Code: Open in New Tab, Claude Code: Open in New Window, etc., which is why searching only Claude gives you a pile of
entries.

If you want the sidebar to be the default location, open:

```text
    File → Preferences → Settings
    or Ctrl+,
```

then search for:

claudeCode.preferredLocation

and set it to:

sidebar

Anthropic documents sidebar and panel as the supported locations.

If Claude Code: Open in Side Bar exists but does nothing, that can be an extension regression; there have been versions
where the command or Activity Bar integration broke.
how do I set the path for the Codex plugin again?

For the official OpenAI Codex VS Code extension, set this in VS Code settings:

"chatgpt.cliExecutable": "/absolute/path/to/your/codex-or-wrapper"

For your aicage shim, you had:

"chatgpt.cliExecutable": "/home/stefan/.aicage/ide-plugins/jetbrains/cc-ui/aicage-codex.debug.sh"

To edit it via the UI:

```text
    click the gear icon → Settings
    or press Ctrl+,
    search for chatgpt.cliExecutable
```

Or edit settings.json directly:

```text
    Ctrl+Shift+P
    run Preferences: Open User Settings (JSON)
```

Then add/change the setting there.
