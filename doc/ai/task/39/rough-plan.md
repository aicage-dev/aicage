Several small, reviewable commits.

1. docs(wiki): add IDE-first integration guide
   - Rework IDE-Plugins.md into the general guide.
   - Cover ACP, ACP bridges, binary-path plugins, first-run configuration, and shim constraints.
   - Validate and update external integration facts/links.
2. docs(wiki): refresh JetBrains CC GUI example
   - Keep the concrete Claude/Codex shim walkthrough.
   - Remove or update the time-sensitive pending-PR/install-from-disk workaround.
   - Update shims/screenshots only if validation shows they need changes.
3. docs: promote IDE usage
   - Promote the guide in wiki Home.md and _Sidebar.md.
   - Update the repository README.md to present IDE usage prominently and point to the guide.

The first two belong to the wiki repository; the last may need one wiki commit plus one aicage repository commit, since
they are separate repositories.

I’d keep each commit independently accurate, with no dangling navigation or instructions.

---

## doc flow overhaul

I’d do it in two steps.

1. Wiki flow overhaul:
   - Add the brief configuration loop to IDE-Plugins.md.
   - Reframe Home.md’s terminal/menu material as later project-container configuration.
   - Remove the duplicate IDE link.
   These changes describe one user journey and should be reviewed together.
2. Root README alignment:
   - Mirror only the concise first-use flow and links from the wiki.
   - Keep the README short; don’t duplicate the configuration reference.
   They are separate repositories, so separate commits also keep the documentation sources independently coherent.