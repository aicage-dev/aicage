# Task 40: Inherit project configuration

When one has many projects, configuring aicage per project folder from the CLI becomes a hassle.
Especially when aicage-agent is running in an IDE and one has to open a terminal to configure aicage.

I've also had the idea of setting a global config which is inherited by all projects.
Some project trees may need different settings from others, so there should be a solution for that too.

## Global config

The global config part is by now pretty clear in my head, details can still change.

User opens aicage from CLI in a special mode (`aicage --global <agent>` or `aicage --config global <agent>` or so)
and sees the normal configuration screen.
There, they can configure the global config.

- It should be clear from the screen header, etc., that this is the global config.
- The confirmation screen for special shares and Docker should likely appear.
- The agent should not be started at the end.
- Eventually, we could build the image at the end or provide a button to build it, so it is present for agent sessions.

The tricky part will be how to actually handle this in project configs and the menu for those.

My idea is to show inherited settings but make them disabled in the menu.
That way one can change the global settings and inheritance by projects becomes manageable, I think.
For Docker args, this will likely be an inherited string with project config appended. As Docker args are defined in a
text area, we might have to show global config in a separate text area or as text. I do not think the Textual menu can
make parts of a text area read-only.

## Folder tree

It would be nice to have a second way to inherit config which is not global.

## Inherit by path

One way would be a folder tree: a config for a parent folder which is inherited by that folder and projects below it.
This is separate from normal project config, because parent folders often are not
projects themselves.

Folder trees recursively inherit their parents and global settings too. A project can add its own configuration on
top. They should be configured through a dedicated CLI mode, similar to global config, rather than through the project
menu. A menu option to make the current folder a tree could be added later.

The menu shows the combined inherited configuration, but saving a project only persists its local configuration.
