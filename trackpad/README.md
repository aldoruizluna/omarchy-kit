# trackpad/: what do three fingers do?

> **TL;DR.** libinput can do only one of two things with three fingers, and macOS makes the same choice: **swipe** between spaces (the default here) or
> **drag** (select and move things without clicking, with spaces moving to four fingers). `three-fingers` flips between them.

`three-fingers [swipe|drag]` edits `local THREE_FINGERS = "..."` in `~/.config/hypr/input.lua`, reloads Hyprland and rebuilds the kit pages. With no argument it
shows the current choice. The Trackpad page and the Learn lessons follow the choice. Setup log row: **Three fingers: swipe spaces or drag (your choice)**; test: `node test/verify-trackpad.mjs` (both modes).

---

Related: [keys/](../keys/README.md) · [docs/MAC-FEEL](../docs/MAC-FEEL.md) · [docs/INDEX](../docs/INDEX.md)
