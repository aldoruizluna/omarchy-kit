# icons/: Mac-style icons and pointer

> **TL;DR.** `install-icons` gives the desktop the macOS icon look: the WhiteSur icon theme (the closest free relative of the macOS icon style) and an
> open-source macOS pointer set. No root. It follows the light or dark mode of whichever Omarchy theme you pick, because a theme-set hook re-applies the
> right WhiteSur variant every time Omarchy changes theme (Omarchy would otherwise put its Yaru icons back). `--remove` undoes all of it.

| Command | What |
|---|---|
| `install-icons` | downloads two pinned releases, checks their checksums, installs the icons, the cursor, the hook and `maccursor.lua`, applies them now |
| `install-icons --remove` | removes only what it installed and puts Omarchy's own icon choice back |
| `mac-icons-hook` | the hook itself (installed as `~/.config/omarchy/hooks/theme-set.d/50-mac-icons`): light themes get `WhiteSur-light`, dark ones `WhiteSur-dark` |
| `maccursor.lua` | the Hyprland module (cursor theme and size); loaded from `hyprland.lua` |

## What it changes, and what it costs

- **Icons for every app that follows the system icon theme** (Files, the Omarchy menu, GTK and Qt apps, the Dock and the app switcher). Omarchy's Yaru
  folders and icons are replaced while this is installed. Apps that bring their own icons keep them.
- **The pointer** becomes the macOS arrow, hand and I-beam, at size 24. From the next login on in new sessions; `install-icons` also sets it live.
- **About 240 MB** under `~/.local/share/icons` (WhiteSur 124 MB, its dark and light variants 57 MB and 15 MB, two cursor sets 21 MB each).
- **Downloads** (GitHub, over HTTPS): WhiteSur tag `2026-09-10` and the `macOS` cursors `v2.0.1`. Both checksums are pinned in the script and the install stops,
  with nothing written, if either differs. Nothing from either project is stored in this repository.

## Honest limits

- **Not Apple's art.** macOS app icons are Apple's. WhiteSur is a community re-drawing in the same style (Big Sur era: rounded squares with a soft gradient); it
  does not reproduce the layered "Liquid Glass" icons of macOS 26 and 27. Nothing free does.
- **Coverage.** Of the 72 apps installed when this was written, WhiteSur drew 49. 19 more use icons that came with the app (mostly the Omarchy web apps) and 4
  (Kagi, Omarchy Kit, RetroArch, Tailscale) have none in any installed theme. The Dock and the switcher put every icon the theme does not have on a neutral
  rounded tile, which is what macOS does with apps that have not been given a new-style icon.
- **Fonts** are not changed. Apple's system font is not redistributable; GTK apps already use Adwaita Sans, a close free relative. See [MAC-FEEL](../docs/MAC-FEEL.md).

## How it was checked

- The install ran against the real desktop: both checksums matched, `gsettings` reported `WhiteSur-dark` and `macOS`, the Files window and the Dock showed
  the new icons in a screenshot.
- A real theme round trip (`mecha-unit` to `flexoki-light` and back): the icon theme went `WhiteSur-dark`, `WhiteSur-light`, `WhiteSur-dark`.
- `test/test_macdesktop.py` runs the installer in a sandbox with fake downloads: a wrong checksum installs nothing, an install is idempotent, `--remove` never
  deletes a folder it did not create, and the hook picks the right variant.

Undo: `icons/install-icons --remove`.

---

Related: [dock/](../dock/README.md) · [menubar/](../menubar/README.md) · [keys/](../keys/README.md) · [themes/](../themes/README.md) · [docs/MAC-FEEL](../docs/MAC-FEEL.md) · [docs/INDEX](../docs/INDEX.md)
