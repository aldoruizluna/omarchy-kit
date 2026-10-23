# look/: the Mac details that are not a theme

> **TL;DR.** `install-look` gives the Omarchy shell (bar, menus, panels) and the Dock a proportional UI font like macOS's San Francisco, moves the window close button of GTK apps to the left like the red
> traffic light, and installs the switch for **blur behind the glass** (off until you turn it on with `mac-glass on`). No root; `--remove` undoes it all. The corners, shadows, popups and colours of the Golden Gate look are in the two
> themes, [Golden Gate and Golden Gate Night](../themes/golden-gate/THEME.md), not here.

| Command | What |
|---|---|
| `install-look` | the font rule, the window-button layout, the glass module; restarts the Omarchy shell once (a couple of seconds) |
| `install-look --remove` | removes them and puts your previous button layout back exactly |
| `mac-glass on`, `mac-glass off`, `mac-glass status` | blur behind the Dock, switcher, Mission Control, menus, notifications and launcher (and the drop-downs of the bar, but not the bar itself) |

## What each part does and costs

- **UI font** (`60-kit-mac-ui-font.conf`, installed in `~/.config/fontconfig/conf.d/`). The Omarchy shell draws everything in the system *monospace* font and gives themes no way to change that. This
  fontconfig rule applies only to programs named `quickshell` (the shell and the Dock) and only to requests for the monospace alias: they get **Adwaita Sans** (GNOME's UI font, derived from Inter, the closest free
  relative of San Francisco). Terminals, editors and every other program keep their monospace font; the `sans-serif` alias and the shell's icon font are untouched (checked with `fc-match` in the tests). Apple's own font
  cannot be redistributed. Needs a shell restart to take effect (the installer does it).
- **Window buttons on the left** (`org.gnome.desktop.wm.preferences button-layout`, from `appmenu:close` to `close:`). GTK and libadwaita apps such as Files then show the close button at the top left, where a
  Mac has it. Only close is shown: a tiling desktop has no minimise, and the green button's job (full screen) is a keyboard shortcut here. Your previous value is saved once in `~/.config/omarchy-kit/look-saved.conf`.
- **Glass** (`macglass.lua`, loaded from `hyprland.lua`). Off by default. `mac-glass on` turns on Hyprland's blur and a layer rule that blurs the shell's own surfaces; windows keep their opacity and are not blurred. It costs GPU time, and on
  this laptop's Intel graphics at 2880x1800 that means heat: see the measurement in [MAC-FEEL](../docs/MAC-FEEL.md#blur-behind-the-glass) before deciding to leave it on. The state is one word in `~/.config/omarchy-kit/glass`.

## How it was checked

- The bar redrawn with the font rule on the real desktop (screenshot): proportional text, every icon still drawn, the clock and the Mac menu bar in the same font.
- `test/test_macsweep.py`: the rule is well-formed and narrow (and, with fontconfig, changes monospace for `quickshell` only), `install-look` in a sandbox with a fake `gsettings` that remembers (install, twice,
  `--remove` restores the layout exactly), `mac-glass` argument handling and its state file, the module parses and never blurs the bar itself.
- **Not verified:** the effect of `mac-glass on` on battery life (see MAC-FEEL), and the button layout in a real Files window (no pointer to click it; the setting itself is read back).

Undo: `look/install-look --remove`.

---

Related: [themes/](../themes/README.md) · [dock/](../dock/README.md) · [icons/](../icons/README.md) · [docs/MAC-FEEL](../docs/MAC-FEEL.md) · [docs/INDEX](../docs/INDEX.md)
