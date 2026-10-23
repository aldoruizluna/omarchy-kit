# dock/: the Dock, the ⌘Tab app switcher and Mission Control

> **TL;DR.** A Mac-style Dock at the bottom of the screen and a ⌘Tab app switcher, in one small Quickshell program started with your session. The Dock
> has the magnification, the running dots, the bounce while an app launches, a right-click menu and the Downloads and Trash icons. ⌘Tab (Super+Tab) cycles
> through running apps, most recently used first, and letting go of ⌘ switches. F3 (the Mission Control key), Super+Ctrl+Up or four fingers up open **Mission Control**: every
> space across the top and the windows of the selected one, as real pictures of them, below. It follows the Omarchy theme's colours and the icon theme. No root; `install-dock --remove` undoes it.

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
| F3, Super+Ctrl+Up, four fingers up on the trackpad | **Mission Control** (see below). F3 is the Mac keyboard's Mission Control key; it produced `XF86LaunchA`, which nothing was bound to | free; the swipe used to open the Omarchy menu |
| F4 | the **Apps menu**, like a four-finger pinch (F4 is the Mac keyboard's Launchpad key; it produced `XF86LaunchB`, which nothing was bound to; macOS 26 replaced Launchpad with an Apps view) | free |
| Super+Ctrl+Down | **App Exposé**: only the windows of the focused app, from every space | free |

"Super" is the ⌘ key on this keyboard. With the keyboard remap in [keys/](../keys/README.md) both ⌘ keys send these chords for you (and ⌃↑/↓/←/→ send the Mission Control and workspace ones).

## Mission Control and App Exposé

F3, Super+Ctrl+Up or a four-finger swipe up opens a full-screen overview over the dimmed wallpaper: a **Spaces bar** with one card per workspace ("Desktop 1",
"Desktop 2", ..., the apps on it as small icons, the current one outlined, a **+** at the end), and below it the windows of the selected space, scaled to fit in rows
with their real proportions, each with its app icon and title. The previews are **real pictures of the windows**, taken once when the overview opens (not live), including
windows on spaces you are not looking at.

| Do | Result |
|---|---|
| click a window | go to it (and to its space) and close the overview |
| click a space card | show that space's windows; double-click it (or press Return on it) to go there |
| click **+** | go to the next empty space |
| hover a window, click the **x** at its corner | close that window; the others re-flow |
| arrows | Left and Right move along a row, Up and Down move between the Spaces bar and the windows and between rows of windows; Return does what a click does |
| Esc, a click on empty space, F3 again or the same swipe again | close it |

App Exposé (Super+Ctrl+Down) shows the focused app's windows only, from every space, with the space number after each title. Windows hidden with Super+H are not shown in either.

Cost, measured on this laptop: nothing is mapped or captured while it is closed (the Dock program stays at 0.10 % of one core and about 255 MB); opening takes about a quarter of a
second and one second of CPU time, adds about 75 MB while it is open, and the memory goes back when it closes. Held open it uses no CPU: there is no live capture. It is one surface
on the primary screen; on several monitors it covers the one it opens on and lists the windows of all of them.

## What it does not do (yet)

- No drag to reorder or to drag an icon out; reorder by editing `pinned`.
- No minimised windows in the Dock (hidden ones keep the app's dot), no badges, no live window previews in the switcher.
- Mission Control cannot drag a window onto another space's card, has no animation from the real window to its card (it fades in), and shows the picture of the window as it was when it
  opened. A window that cannot be captured shows its app icon on a dark card instead (none failed in the tests).
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
- Mission Control, on real windows spread over three spaces (this terminal and Files on space 1, Obsidian on 2, Disks on 3): screenshots with real previews of windows on the visible and
  on the other spaces; the global shortcut that F3 and the swipe send opens and closes it; Esc, the arrow keys (between the bar and the windows, along the cards), Return and Left/Right
  sent as real key events while it had the keyboard; Return on a window of another space switched to that space and focused it; the **x** (through a test hook) closed a window and
  re-flowed the cards; **+** went to workspace 4; App Exposé listed the two Files windows from two spaces; the layout function is run in `node` by the tests (proportions kept, nothing
  overlaps or leaves the screen, up to eleven windows).
- Web apps: a real Omarchy Kit window lit the pinned icon.
- `test/test_macdesktop.py`: the installer in a sandbox (files, `dock.json` kept, one require line, clean removal), QML and Lua syntax, and that every QML file is installed.

**Not verified, because it needs a real keyboard or pointer:** pressing the actual F3, Super+Ctrl+Up, Super+Ctrl+Down and Super+Tab chords, the real four-finger swipe (the swipe handler runs the same
global shortcut as F3, which was tested; the gesture itself was not), hovering to show the close button and clicking cards (the same code runs through the tested IPC calls), Mission Control in a light theme
(it uses the same theme colours as the Dock), pressing the actual Super+Tab chord (Hyprland ignores `wtype`'s virtual keyboard for key binds, and the
release watcher uses `hl.is_key_down`, which does not see it either), mouse clicks and right-click menus (no pointer injection here), and starting at login
(`hyprland.start`). The checklist for those is on the Setup log page.

## Files

`shell.qml` (entry), `Dock.qml`, `DockIcon.qml`, `ItemMenu.qml`, `Switcher.qml`, `MissionControl.qml`, `AppIcon.qml`, `Apps.qml` (what is running, pinned and hidden), `Config.qml`
(`dock.json`), `Theme.qml` (colours from the Omarchy theme), `IconIndex.qml` (which icons the theme has), `macdock.lua` (the Hyprland side), `install-dock`.

Undo: `dock/install-dock --remove`.

---

Related: [icons/](../icons/README.md) · [menubar/](../menubar/README.md) · [keys/](../keys/README.md) · [docs/MAC-FEEL](../docs/MAC-FEEL.md) · [docs/INDEX](../docs/INDEX.md)
