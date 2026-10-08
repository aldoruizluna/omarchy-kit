# keys/: Mac ⌘ shortcuts inside apps

> **TL;DR.** `mackeys.lua` turns Super+A, Z, ⇧Z, R, ⇧R, N, ⇧T, D, B, I, U, [ and ] into the Ctrl chord the focused app expects, and skips terminals. It only uses
> keys Omarchy leaves free. Seven more (⌘W T F S L G P) are opt-in because Omarchy already uses those Super keys.

| Script | What | Undo |
|---|---|---|
| `install-mackeys` | no root: installs `mackeys.lua` into the Hyprland config | `--remove` |
| `mackeys.lua` | the shortcut definitions | n/a |
| `mac-key-extras` | choose which of ⌘W ⌘T ⌘F ⌘S ⌘L ⌘G ⌘P also work in apps (`W T F S`, `all`, `none`); in terminals they keep their Omarchy meaning, and the Omarchy action stays reachable at a new chord in every window | `mac-key-extras none` |

Verified against a real compositor: `node test/verify-mackeys.mjs` calls each handler through `hyprctl eval` and a scratch Brave window reports the exact chord it
receives (32 checks). Needs a running Hyprland session. Setup log rows: **⌘ shortcuts inside apps**, **⌘W ⌘T ⌘F ⌘S ⌘L ⌘G ⌘P in apps (optional)**.

---

Related: [trackpad/](../trackpad/README.md) · [docs/MAC-FEEL](../docs/MAC-FEEL.md) · [test/](../test/README.md) · [docs/INDEX](../docs/INDEX.md)
