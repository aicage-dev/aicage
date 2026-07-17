# Task 38: Menu and Main Process Boundary

This task defines the target boundary between the main process and the menu
implementations before refactoring the current runtime flow.

The goal is to align on architecture first and only then start moving code.
The key concern is that process control and menu logic are currently too mixed,
especially after the menu phase.

The document [menu-process-boundary.md](menu-process-boundary.md) contains the
current target boundary:

- hard rules for process and menu separation
- a small interaction sketch
- the current call model
- the interaction list before and after config exists

This task note is intentionally short. It is a boundary-definition task, not
yet an implementation or migration plan.
