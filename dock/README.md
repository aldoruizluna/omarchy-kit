# dock/: the Dock, the ⌘Tab app switcher and Mission Control

> **TL;DR.** A Mac-style Dock at the bottom of the screen and a ⌘Tab app switcher, in one small Quickshell program started with your session. The Dock
> has the magnification, the running dots (a lighter one for an app that runs with no window), drag to reorder, the bounce while an app launches, a right-click menu and the Downloads and Trash icons, and
> **hot corners** (off until you choose). **Spotlight** (⌘Space, Super+Alt+Space) searches Apps, Files, Actions and the Clipboard in one field. ⌘Tab (Super+Tab) cycles
> through running apps, most recently used first, and letting go of ⌘ switches. F3 (the Mission Control key), Super+Ctrl+Up or four fingers up open **Mission Control**: every
> space across the top and the windows of the selected one, as real pictures of them, below. It follows the Omarchy theme's colours and the icon theme. No root; `install-dock --remove` undoes it.

| Command | What |
|---|---|
| `install-dock` | copies the program to `~/.local/share/macdock`, creates `~/.config/macdock/dock.json` if missing, adds the Hyprland module `macdock.lua` and starts the Dock |
| `install-dock --remove` | stops it and removes the program and the module; **your `dock.json` stays** |
| `quickshell -p ~/.local/share/macdock` | run it by hand in a terminal to see its log (stop the running one first) |
| `quickshell ipc -p ~/.local/share/macdock call dock toggleAutohide` | hide or show the Dock (also ⌥⌘D, Super+Alt+D) |
| `hot-corners` | show or set what the four screen corners do (see Hot corners below); `hot-corners off` turns them all off |

## The Dock

| Part | Behaviour |
|---|---|
| Pinned apps, then the other running apps after a separator, then Downloads and Trash | the first group is `pinned` in `dock.json` (desktop file ids; ones that are not installed are skipped) |
| Hover | the icon under the pointer grows (magnification), its neighbours spread, its name shows above it. The grown icon stays under the pointer |
| Click | focuses the app (its most recently used window), or launches it with a bounce until its window appears; middle click opens a new instance |
| Right click | the app's windows, its own actions (New Window and so on), **Keep in Dock** / **Remove from Dock**, **Quit** |
| Dot under an icon | the app has a window (hidden ones too). A **lighter dot** means the app runs with no window (closed to the tray, a service): the Dock reads the process names (`/proc/*/comm`, about 4 ms) every eight seconds and a second after a window opens or closes and an app counts when a process has the name of the program in its launcher. Launchers that start something else (`sh`, `flatpak`, web apps) never count, because their process is not the app's |
| Drag a pinned icon | **sideways** to reorder (it is dropped before or after the pinned app nearest to where you let go); **pulled well above the Dock** and released, it is taken off the Dock, as on a Mac. The click that ends a drag does not launch anything |
| Web apps | Omarchy's web apps (WhatsApp, Omarchy Kit, ...) are matched to their launcher, so the pinned icon lights up instead of a second icon appearing |
| Icons the theme does not have | set on a neutral rounded tile, like macOS does for old-style icons |
| Trash | full icon when there is something in it; right click: Open, Empty Trash |

`~/.config/macdock/dock.json`: `pinned` (list), `iconSize` (32-96, default 52), `zoom` (1 = no magnification, default 1.6), `autohide` (default false),
`showTrash` (default true), `hotCorners` (see below), `hotCornerDelay`. It is re-read when it changes. With `autohide` the Dock slides away and the windows get its space back (85 px at the default size).

## Control Center

The two-switches button in the menu bar, just left of the clock, opens a panel under it (also `quickshell ipc -p ~/.local/share/macdock call controlcenter toggle`, or "Control Center" in Spotlight's Actions). Click outside it or press Esc to close.

| Part | What it does |
|---|---|
| **Wi-Fi** tile | turns the radio on or off (the same `Networking.wifiEnabled` Omarchy's own panel uses); shows the network you are on |
| **Bluetooth** tile | turns the adapter on or off; shows the connected device |
| **Focus** tile | Do Not Disturb: Omarchy's notification silencing (`omarchy-shell notifications setDnd`) |
| **Night Shift** tile | Omarchy's night light (`omarchy-toggle-nightlight`) |
| **Display**, **Keyboard Brightness** sliders | `omarchy-brightness-display --no-osd N%` and `brightnessctl` on the keyboard backlight; the keyboard slider is not shown when there is no such backlight; sent when you pause, not on every pixel of the drag |
| **Sound** slider | the default PipeWire output's volume and mute |
| **Now Playing** | the track of the MPRIS player that is playing (or the first one), with previous, play or pause and next; not shown when no player runs |
| Battery row | the charge and whether it is charging (UPower); the pill cycles the power mode (Low Power, Automatic, High Power: `powerprofilesctl`) |
| **Lock Screen**, **Wi-Fi, Bluetooth, Sound…** | lock now; Omarchy's hardware menu for everything the tiles do not cover |

Nothing is built while it is closed (the contents are in a `Loader` that is only active while the panel is open); it asks the services once when it opens, about 0.2 s of work, and after each change. It cannot shut down, restart or log out, by design (a test checks the word is not in the file).
It does not have AirDrop, Screen Mirroring, Stage Manager, Accessibility Shortcuts or the Controls Gallery, and it is not resizable.

## Spotlight

⌘Space (Super+Alt+Space; with the keyboard remap, ⌘Space itself) opens one search field with four views, as in macOS 26. Type to search, ↑ ↓ to move, Return to open, Esc to close, Tab for the next view,
and ⌘1 to ⌘4 (Ctrl, Option or ⌘ with the digit) jump to a view.

| View | What it searches | Return does |
|---|---|---|
| **Apps** (⌘1) | the launcher entries, by name (whole, start, a word's start, anywhere), then by generic name, keywords and comment. With nothing typed: the apps you start most. A sum such as `12*7+sqrt(16)` shows its answer first | starts the app; for a sum, copies the answer (never `eval`: a small parser, with `+ - * / % ^`, brackets, `pi`, `e`, `sqrt sin cos tan ln log abs round floor ceil exp`) |
| **Files** (⌘2) | file and folder names under your home folder, by `fd` (hidden folders and `node_modules` left out), one search at a time, only in this view and only from two letters | opens it; Ctrl+Return opens the folder it is in |
| **Actions** (⌘3) | 23 things the desktop can do: Lock Screen, Mission Control, the night-light, do-not-disturb and lock-on-idle switches, screenshot, screen recording, copy text from the screen, colour picker, emoji, calculator, notification history, theme, wallpaper, hardware, keyboard shortcuts, About This Mac, the Omarchy menu | runs it (after Spotlight has closed, so a screenshot sees your window). **Nothing here shuts the machine down or logs you out by itself**: "Restart, Shut Down or Log Out…" opens Omarchy's system menu |
| **Clipboard** (⌘4) | the history Omarchy's clipboard overlay keeps (`~/.local/state/omarchy/clipboard-history.json`), newest first; Spotlight only reads it | pastes the entry into the window you came from (Omarchy's own `omarchy-clipboard-paste-text`); an image is copied |

It is a separate surface in the Dock program, not in the Omarchy shell, and it is not mapped while closed. The only file it writes is `~/.local/state/macdock/spotlight.json`, a count of how often you start each app from here. It replaces Omarchy's **Apps menu on Super+Alt+Space** (F4 still opens that menu and Omarchy's own menu is
Super+Space); `install-dock --remove` brings the old binding back. Files and Clipboard show whatever is there, on screen, like any launcher does; nothing is sent anywhere.

## Hot corners

Rest the pointer in a screen corner for a moment (350 ms by default) and something happens. **They ship off**: a brush of the pointer should never start anything.

```bash
dock/hot-corners                                   # show the four corners
dock/hot-corners bottom-right quicknote            # a new note, named by the minute, in ~/Documents/Quick Notes (opened in Omawrite)
dock/hot-corners top-left missioncontrol           # Mission Control; the other actions: appexpose  apps  lock  notifications
dock/hot-corners delay 500                         # how long the pointer must rest (100 to 2000 ms)
dock/hot-corners off                               # all four off
```

Each active corner is a 3-pixel transparent surface that waits for the pointer to enter it; nothing polls the pointer, and a corner set to `none` has no surface at all (with all four off there are none). It fires once per
visit: a full-screen overlay such as Mission Control takes the pointer away from the corner surface, and when it closes with the pointer still parked there the surface would see a fresh "enter" and fire
again, so after a trigger the corner asks Hyprland where the pointer is (`hyprctl cursorpos`, a few times a second) until it has moved away. A Quick Note you never write leaves no empty file behind.

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

Cost, measured on this laptop: nothing is mapped or captured while it is closed (the Dock program was measured at 0.10 % of one core and about 255 MB at a quiet moment, counting only the program itself; **measured the same way today for both**, nothing open, over 60 s: the Dock as it was before the background dot, hot corners, Spotlight and Control Center took 0.30 % of one core (0.22 itself and 0.08 for the programs it starts) and 225 MB, and with them it takes 0.45 % (0.28 and 0.17) and 240 to 265 MB; the process-name scan is most of the difference, at about 4 ms every eight seconds); opening takes about a quarter of a
second and one second of CPU time, adds about 75 MB while it is open, and the memory goes back when it closes. Held open it uses no CPU: there is no live capture. It is one surface
on the primary screen; on several monitors it covers the one it opens on and lists the windows of all of them.

## What it does not do (yet)

- Dragging reorders only the pinned apps (an icon cannot be dragged onto the Dock to pin it, and the others do not slide aside while you drag: the icon follows the pointer and the order changes when you let go).
- No stacks, no recent-apps section.
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
- The lighter dot: a stand-in process named like a pinned app's program made the Dock show it (`dock describe` over IPC said `obsidian:b`, a screenshot showed the dim dot next to the terminal's full one) and dropped it again within seconds of the process ending.
- Control Center, on the live desktop: screenshots of the panel with the real values (Wi-Fi network, Bluetooth, brightness 13 %, keyboard backlight 49 %, volume 100 %, battery, power mode); through test hooks that run what a click or a drag runs, Focus turned Omarchy's do-not-disturb on and off, Night Shift changed the colour temperature to 4000 K and back, the Display slider moved the real backlight (13 → 30 → 13 %), the Keyboard slider the keyboard backlight (49 → 70 → 49 %), and the power mode cycled power-saver, balanced and performance; every value was put back afterwards. The panel opens with its values filled within 0.3 s.
- Spotlight, on the live desktop with real key events from `wtype` (Tab and Ctrl or Alt with a digit change view, typing filters, ↑ ↓ move, Return runs the "Mission Control" action, Esc closes), the global shortcut that the chord sends, screenshots of the Apps, Actions and Files views, a sum answered, a name found in the home folder. The tests run the sum parser, the name scoring, the file ordering and the icon rules in node.
- Hot corners, with the real pointer (moved with Hyprland's own cursor dispatcher): nothing at 0.12 s, Mission Control open at 0.62 s; a 0.1 s brush did nothing; closing it with the pointer still parked did **not** reopen it (before the latch it did, which is how that bug was found); leaving, waiting and returning fired it again;
  Quick Note opened Omawrite on a new file, and closing it unwritten removed the file. The 3 px surface appears at the corner (`hyprctl layers`) only for a corner that has an action.
- Drag to reorder: the move itself (before/after, no-op cases, one save) is run in node by the tests.
- `test/test_macdesktop.py`: the installer in a sandbox (files, `dock.json` kept, one require line, clean removal), QML and Lua syntax, and that every QML file is installed.

**Not verified, because it needs a real keyboard or pointer:** clicking a Control Center tile, dragging its sliders and clicking the bar button (the same code ran through the test hooks and the button's own IPC call), the Super+Alt+Space chord itself (the shortcut it sends was triggered through `hyprctl`), Spotlight's mouse hover and clicks, Return on Apps (it would start an app), pasting from the Clipboard view into another window, the drag gesture itself (holding an icon and moving the pointer: no button events can be injected here), a hand-made trip into a corner, pressing the actual F3, Super+Ctrl+Up, Super+Ctrl+Down and Super+Tab chords, the real four-finger swipe (the swipe handler runs the same
global shortcut as F3, which was tested; the gesture itself was not), hovering to show the close button and clicking cards (the same code runs through the tested IPC calls), Mission Control in a light theme
(it uses the same theme colours as the Dock), pressing the actual Super+Tab chord (Hyprland ignores `wtype`'s virtual keyboard for key binds, and the
release watcher uses `hl.is_key_down`, which does not see it either), mouse clicks and right-click menus (no pointer injection here), and starting at login
(`hyprland.start`). The checklist for those is on the Setup log page.

## Files

`shell.qml` (entry), `Dock.qml`, `DockIcon.qml`, `ItemMenu.qml`, `Switcher.qml`, `MissionControl.qml`, `HotCorners.qml`, `hot-corners` (the command), `Spotlight.qml`, `ControlCenter.qml`, `AppIcon.qml`, `Apps.qml` (what is running, pinned and hidden), `Config.qml`
(`dock.json`), `Theme.qml` (colours from the Omarchy theme), `IconIndex.qml` (which icons the theme has), `macdock.lua` (the Hyprland side), `install-dock`.

Undo: `dock/install-dock --remove`.

---

Related: [icons/](../icons/README.md) · [menubar/](../menubar/README.md) · [keys/](../keys/README.md) · [docs/MAC-FEEL](../docs/MAC-FEEL.md) · [docs/INDEX](../docs/INDEX.md)
