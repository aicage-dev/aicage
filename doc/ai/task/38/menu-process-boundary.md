# Menu and Main Process Boundary

## Hard rules

1. The main process owns the full application flow.
2. The main process may call a menu, but the menu never owns process flow.
3. Menus only interact with the user, display information, and return data.
4. Process and runtime code must not import menu-specific modules.
5. `textual`, `simple`, and `none` are interchangeable interaction implementations.

## Boundary sketch

```text
CLI -> main process -> interaction interface
                    -> runtime/setup logic

interaction implementation <-> user
runtime/setup logic -> progress/status -> interaction implementation
runtime/setup logic -> decision needed -> interaction implementation -> answer
```

## Consequences

- Menu mode is selected at the edge and not inside the main process flow.
- `--menu none` is an interaction implementation, not a special process path.
- Runtime decisions are requested by the main process and answered through the
  interaction interface.
- Progress is emitted by runtime/setup logic and rendered by the interaction
  implementation.

## Edge selection rule

Selection of `textual`, `simple`, or `none` happens once at the edge.

After that point:

- the main process does not branch on menu kind
- runtime code does not branch on menu kind
- `none` is handled like any other interaction implementation

## `none` behavior

`none` is not a special process path.

It is an interaction implementation with minimal behavior:

- config call uses defaults and existing config without interactive UI
- post-config `show` calls may be ignored or logged
- post-config `ask` calls are answered by explicit defaults or fixed rules

`none` still returns data to the main process like any other interaction
implementation.

## Cancellation semantics

### Config call

- cancel means the config interaction ended without a usable config result
- the main process decides how to stop after that

## Responsibility split

### Main process responsibilities

- decide the next process step
- decide when user interaction is needed
- call the menu and use the returned data
- execute setup and runtime steps
- decide when to continue, stop, or fail

### Menu responsibilities

- display information
- ask the user for input
- return the user result
- render progress and log output

The menu does not decide process flow.

## Return-data boundary

The menu may return:

- selected or confirmed values
- yes/no answers
- cancel
- written config file as result of the config call

The menu must not return:

- executable process steps
- callbacks for continuing process flow
- process decisions that were not explicitly asked by the main process
- bundled results that hide multiple process steps behind one return value

## Forbidden coupling patterns

These patterns violate the target boundary:

- main-process branching on a specific menu implementation
- runtime code importing prompt or Textual modules
- menu code starting or continuing runtime setup on its own
- menu code receiving runtime callbacks that let it steer process flow
- process code relying on hidden menu defaults instead of explicit answers

## Examples

### Valid call

- main process asks the menu whether a newer image should be pulled
- main process tells the menu that image verification has started

### Invalid call

- main process gives the menu a callback for continuing setup execution
- main process lets the menu decide whether setup should run at all

### Valid return

- yes
- no
- cancel
- selected values

### Invalid return

- callback to continue execution
- prepared runtime action
- hidden multi-step result that already decided later process flow

## Call model

There are two kinds of calls from main process to menu.

### 1. Config call

- The main process starts the config menu.
- The menu runs on its own until it ends.
- The result is either cancel or a written config file.
- There are no intermediate process steps during this call.

### 2. Post-config calls

- After the config file exists, the main process stays in control.
- The main process may call the menu to ask a simple question.
- The main process may call the menu to show status or progress.
- Each such call is isolated and does not transfer process control to the menu.

## Interaction list

Current interactions from main process to menu fall into these groups.

### Before config exists

- show available base choices and return selected base
- show extension choices and return selected extensions
- show image-ref prompt and return image ref when needed
- show missing-extension question and return chosen behavior
- show docker-args persist question and return yes/no
- show shares persist question and return yes/no
- show git and extension mount selection and return selected mounts
- show docker-socket persist question and return yes/no
- show host-access confirmation and return confirmed values

These belong to the single config call and should not be treated as separate
process-control steps.

### After config exists

- show aicage self-update question and return yes/no
- show image-update question and return yes/no
- show setup phase started
- show setup phase progress
- show setup phase log output
- show setup phase finished
- show setup phase failed

These belong to the main-process-controlled flow after config exists.

## Allowed post-config menu calls

After the config file exists, main process to menu calls should stay within
these categories:

- show status
- show progress
- show log output
- ask a simple question and return one answer

The menu must not:

- decide what the next process step is
- trigger setup steps on its own
- combine multiple process steps into one hidden flow

## Classification of current post-config interactions

### `show`

- show setup phase started
- show setup phase progress
- show setup phase log output
- show setup phase finished
- show setup phase failed
- show image signature verification started
- show image signature verification finished
- show cosign helper image pull when it happens

### `ask`

- show aicage self-update question and return yes/no
- show image-update question and return yes/no

### invalid in current form

- config menu starts setup planning after the config interaction is done
- config menu decides whether setup is needed after the config interaction is done
- config menu starts setup execution after the config interaction is done
- runtime and registry code directly call prompt functions instead of asking
  through the main process
- image signature verification is partly hidden from the UI

## Required cleanup direction

The current post-config flow must be cleaned up in these ways:

- remove menu-owned setup orchestration after the config call
- remove direct prompt calls from runtime and registry logic
- remove menu-kind branching from main-process flow after edge selection
- make post-config interaction happen only through explicit `show` and `ask`
  calls from the main process

## Non-goals of this task

This task does not yet define:

- the exact interface shape
- the exact class or module names
- the migration order
- UI layout details for `textual` or `simple`
- broader runtime refactoring outside the menu/process boundary

## Done when

This note is only temporary working material for the refactoring.

The task is not done when this note looks complete.

The task is done when the code reflects the boundary described here:

- main process owns process flow
- menus are interaction implementations and not flow owners
- post-config interaction happens through explicit calls from main process
- menu-kind branching is removed from the main flow after edge selection
- prompt and Textual imports are removed from runtime and registry flow control

This note may be changed or deleted once the code no longer needs it.

## Verification visibility expectations

When image signature verification happens during post-config processing, the
user should be able to see that it is happening.

This includes:

- verification of the target image before pull or refresh
- pull of the cosign helper image when that helper image is missing locally
- completion of image signature verification

The visible flow should make it clear that verification is a deliberate setup
step and not an unexplained delay.
