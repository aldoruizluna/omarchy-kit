# dock/: the Dock and the ⌘Tab app switcher

> **TL;DR.** A Mac-style Dock at the bottom of the screen and a ⌘Tab app switcher, in one small Quickshell program started with your session. The Dock
> has the magnification, the running dots, the bounce while an app launches, a right-click menu and the Downloads and Trash icons. ⌘Tab (Super+Tab) cycles
> through running apps, most recently used first, and letting go of ⌘ switches. It follows the Omarchy theme's colours and the icon theme. No root; `install-dock --remove` undoes it.

| Command | What |
|---|---|
| `install-dock` | copies the program to `~/.local/share/macdock`, creates `~/.config/macdock/dock.json` if missing, adds the Hyprland module `macdock.lua` and starts the Dock |
| `install-dock --remove` | stops it and removes the program and the module; **your `dock.json` stays** |
| `quickshell -p ~/.local/share/macdock` | run it by hand in a terminal to see its log (stop the running one first) |
| `quickshell ipc -p ~/.local/share/macdock call dock toggleAutohide` | hide or show the Dock (also ⌥⌘D, Super+Alt+D) |

## The Dock

| Part | Behaviour |
|---|---|
| Pinned apps, then the other running apps after a separator, then Downloads and Trash | the first group is `pinned` in `dock.json` (desktop file ids; ones that are not installed are skipped) |
| Hover | the icon under the pointer grows (magnification), its neighbours spread, its name shows above it. The grown icon stays under the pointer |
| Click | focuses the app (its most recently used window), or launches it with a bounce until its window appears; middle click opens a new instance |
| Right click | the app's windows, its own actions (New Window and so on), **Keep in Dock** / **Remove from Dock**, **Quit** |
| Dot under an icon | the app has a window (hidden ones too) |
| Web apps | Omarchy's web apps (WhatsApp, Omarchy Kit, ...) are matched to their launcher, so the pinned icon lights up instead of a second icon appearing |
| Icons the theme does not have | set on a neutral rounded tile, like macOS does for old-style icons |
| Trash | full icon when there is something in it; right click: Open, Empty Trash |

`~/.config/macdock/dock.json`: `pinned` (list), `iconSize` (32-96, default 52), `zoom` (1 = no magnification, default 1.6), `autohide` (default false),
`showTrash` (default true). It is re-read when it changes. With `autohide` the Dock slides away and the windows get its space back (85 px at the default size).

## ⌘Tab and the app shortcuts

| Keys | What | What it replaced |
|---|---|---|
| Super+Tab, Super+Shift+Tab | the app switcher, forwards and backwards. Hold Super, press Tab to step, let go to switch. Also: arrows, Return, Esc (cancel), **Q** quits the selected app, **H** hides it | they were *Next / Previous workspace* |
| Super+Ctrl+Shift+Right, Left | next / previous workspace | (moved here; three- and four-finger swipes and Super+1..9 still work) |
| ``Super+` `` | the next window of the same app | free |
| Super+Q | quit the app: closes every window of the focused app (apps that ask about unsaved work still ask) | free |
| Super+H | hide the app: its windows go to a hidden workspace; clicking it in the Dock or picking it in the switcher brings them back | free |
| Super+M | hide this one window (the nearest tiling has to "minimise") | free |
| Super+Alt+D | hide or show the Dock | free |

"Super" is the ⌘ key on this keyboard. With the keyboard remap in [keys/](../keys/README.md) the left ⌘ sends these chords for you.

## What it does not do (yet)

- No drag to reorder or to drag an icon out; reorder by editing `pinned`.
- No minimised windows in the Dock (hidden ones keep the app's dot), no badges, no live window previews in the switcher.
- No real blur behind the glass. Hyprland's blur costs GPU time on this laptop's Intel graphics at 2880x1800, so the glass is a tinted, translucent surface (the
  switcher and menus are nearly opaque so text behind them cannot be read through them). It is a decision to measure before changing, not a missing line.
- Bottom only (no left or right Dock).

## How it was checked

On the real desktop (screenshots of the real compositor, not a simulation):

- Magnification, names, running dots, extra apps after the separator, autohide on and off (the reserved space went 85 px to 0 and back), light and dark
  themes (a real round trip through `flexoki-light`).
- The switcher: opened over three apps, Tab moved the selection, Return switched, and releasing Ctrl or Super committed (key events sent with `wtype` while the
  switcher had the keyboard).
- ``Super+` ``, `Super+Q`, hide and restore, on real Files and Obsidian windows, driven through `hyprctl eval`.
- Web apps: a real Omarchy Kit window lit the pinned icon.
- `test/test_macdesktop.py`: the installer in a sandbox (files, `dock.json` kept, one require line, clean removal), QML and Lua syntax, and that every QML file is installed.

**Not verified, because it needs a real keyboard or pointer:** pressing the actual Super+Tab chord (Hyprland ignores `wtype`'s virtual keyboard for key binds, and the
release watcher uses `hl.is_key_down`, which does not see it either), mouse clicks and right-click menus (no pointer injection here), and starting at login
(`hyprland.start`). The checklist for those is on the Setup log page.

## Files

`shell.qml` (entry), `Dock.qml`, `DockIcon.qml`, `ItemMenu.qml`, `Switcher.qml`, `AppIcon.qml`, `Apps.qml` (what is running, pinned and hidden), `Config.qml`
(`dock.json`), `Theme.qml` (colours from the Omarchy theme), `IconIndex.qml` (which icons the theme has), `macdock.lua` (the Hyprland side), `install-dock`.

Undo: `dock/install-dock --remove`.

---

Related: [icons/](../icons/README.md) · [menubar/](../menubar/README.md) · [keys/](../keys/README.md) · [docs/MAC-FEEL](../docs/MAC-FEEL.md) · [docs/INDEX](../docs/INDEX.md)
