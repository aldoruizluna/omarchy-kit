# menubar/: the Mac menu bar

> **TL;DR.** Omarchy's top bar rearranged the way macOS lays out its menu bar: a system menu (Apple menu) and the **name of the focused app in bold** at the left, then File, Edit,
> View, Window and Help menus; the workspaces in the middle; the status icons and the clock at the right. Almost no Wayland app publishes a real menu, so for Brave and its web apps,
> Files, terminals and Obsidian the bar shows **that app's own menus** (its real item names and shortcuts, from `plugin/apps.json`), and every other app gets the standard Mac menus; each
> item sends the matching shortcut to the focused app. No root; your original bar layout is saved and `--remove` restores it exactly.

| Command | What |
|---|---|
| `install-menubar` | adds the "Mac menu bar" widget to the bar, installs `macmenu.lua`, saves your layout, then rearranges the bar |
| `install-menubar --remove` | restores the saved layout, removes the widget and the module |
| `omarchy-shell omarchykit.macmenu open edit` | open a menu without the pointer (`apple`, `app`, `file`, `edit`, `view`, `window`, `help`); `close`, `current`, `activate <id>` also exist |

## What you get

| Menu | Items (each does what its ⌘ shortcut does in the focused app) |
|---|---|
| Omarchy logo (Apple menu) | About This Mac (the kit's MacBook page), System Settings, Software, Omarchy Menu, Force Quit, Sleep, Restart, Shut Down, Lock Screen, Log Out |
| App name (bold) | Settings (⌘,), Hide (⌘H), Quit (⌘Q) |
| File | New Window ⌘N, New Tab ⌘T, Open ⌘O, Close ⌘W, Save ⌘S, Print ⌘P |
| Edit | Undo ⌘Z, Redo ⇧⌘Z, Cut ⌘X, Copy ⌘C, Paste ⌘V, Select All ⌘A, Find ⌘F, Find Next ⌘G |
| View | Reload ⌘R, Zoom In, Zoom Out, Actual Size, Enter Full Screen |
| Window | Float or Tile, Center, Move to Workspace 1 to 5, Next Window of This App, the app's open windows |
| Help | Omarchy Kit, Keyboard Shortcuts |

Moving across the titles while a menu is open switches menus, as on a Mac. The bar keeps its transparency; the clock keeps its format (`Fri 23 Oct 00:36`).

## Per-app menus

The first profile in `plugin/apps.json` whose `match` fits the focused window's app id decides the titles and items; an app with no profile gets the generic menus above.

| App | Menus |
|---|---|
| Brave (and Chromium, Chrome) | File, Edit, View, History, Bookmarks, Tab, Window, Help: New Tab and Window, Private Window, Reopen Closed Tab, Open Location, Hard Reload, Developer Tools, View Source, Console, Back and Forward, Bookmark This Tab, Select Next Tab, Tab 1 to 3 and Last Tab, and more |
| Web apps (WhatsApp, Omarchy Kit, ...: Brave windows with an address in the class) | File, Edit, View, History, Window, Help: no tabs and no bookmarks, because those windows have none |
| Files (Nautilus) | File, Edit, View, Go, Window, Help: New Folder, Rename, Move to Trash, Properties, Invert Selection, Show Hidden Files, Enclosing Folder, Go to Location |
| Terminals (foot, Alacritty, kitty, Ghostty, WezTerm) | Shell, Edit, View, Window, Help: New Window, Clear Screen, Interrupt (⌃C), End of Input (⌃D), Suspend (⌃Z), Copy and Paste in the terminal's own keys, Bigger and Smaller, scrollback |
| Obsidian | File, Edit, View, Go, Window, Help: New Note, Quick Switcher, Command Palette, Search in All Files, Graph View, Reading View, Back and Forward |
| Telegram, Signal and everything else | the generic File, Edit, View, Window and Help (a profile is a few lines of JSON; none was written for these because their shortcuts could not be checked here) |

An item is a **chord** sent to the focused window (`"send": "ctrl+shift+n"`, through `o.mac_chord` in `macmenu.lua`, which accepts only Ctrl, Shift and Alt and a key name) or one of the actions in `macmenu.lua`; a menu file can never name a command.
The shortcut shown beside an item is the one you press **on this keyboard once the keyd layer of [keys/](../keys/README.md) is installed**, and a test derives it from keyd's own tables for every item, so a hint cannot say something the keyboard does not do
(a few items have no hint because no Mac key sends their chord: Ctrl+Alt+arrows is the window-focus chord here, for example). What these menus cannot do is what a real menu does: **ask the app**. An item that does not apply right now is not greyed out, and an item the app
does not have is not here because nobody wrote it down.

## Why not the app's real menus

A real global menu needs a menu service on the desktop and every app to publish its menu to it. A feasibility study (static analysis plus what Hyprland advertises on this machine; nothing was published by a running app) found: Hyprland offers none of the
protocols that tie a menu to a window (`org_kde_kwin_appmenu`, `gtk_shell1`), none of the Dock's pinned apps publishes a menu today, Nautilus has no menu bar at all and foot has no menus, Brave's global-menu code only runs when the compositor offers that
protocol, Electron's is X11-only, and Quickshell cannot act as the menu registrar. Reaching three to five of the eight apps would mean a separate registrar service **and** a third-party Hyprland plugin that runs inside the compositor (one repository, one star, no release, no licence),
which can end the session on a Hyprland update. That is why the per-app menus above are the shipped answer and the real thing is a later, opt-in experiment, not a default.

A real global menu needs a menu service on the desktop and every app to publish its menu to it. No such service runs on this desktop, and as far as I could find Brave, Chromium
and Electron apps have no way to publish one on Wayland, so there is nothing real to show for most of the apps in the Dock. What this does instead is the same job at its most useful: the
menus teach and run the shortcuts. The shortcuts are the common ones, so an app that uses different keys for something (a terminal, a game) can ignore an item. In terminals Copy and
Paste are translated to the terminal's own keys and Close closes the window.

## What the installer changes in the bar

| Before (Omarchy's default arrangement) | After |
|---|---|
| left: Omarchy menu button, workspaces | left: the Mac menu bar widget |
| centre: indicators, clock, keyboard layout, weather, updates | centre: workspaces |
| right: tray, network, audio, power, ... | right: the same, plus indicators, updates, weather and keyboard layout, ending with the clock |

Anything else you had in the bar (extra widgets, spacers, custom command modules) keeps its place on the right, before the clock, with its settings. The Omarchy menu button is gone from the
bar (the Apple menu has an *Omarchy Menu* item and Super+Space still opens it). Your layout before the change is saved in `~/.config/omarchy-kit/menubar-layout-before.json`
and `shell.json.bak-menubar` is a plain copy of the file; `--remove` puts the layout back exactly.

## Notes

- After the **plugin code** changes (not the layout), restart the shell once: `omarchy restart shell`. Omarchy reloads a placed widget's files but does not rebuild the widget that is already on screen.
- Adding an app: add a profile to `plugin/apps.json` (copy a small one such as `obsidian`), run `install-menubar` (it copies the file) and restart the shell once; the tests check every chord, every action name and every shown shortcut.
- `⌘Q` and `⌘H` in these menus use the Dock module (`dock/install-dock`); without it those two items do nothing.

## How it was checked

On the real desktop: a screenshot of the new bar, the Edit menu and the Apple menu open (dark and light themes); `File > New Window` opened a second Files window
and the menu closed (menu to `hyprctl eval` to the app); the window actions (Ctrl+N, Ctrl+W, quit) on real Files windows. `test/test_macdesktop.py`: the layout moves to the Mac order and back
to the exact original, nothing the user had is lost or duplicated, invalid `shell.json` is never touched, and every item id in the widget has a Lua action.
Per-app menus, on the real desktop: the bar showed Foot's Shell menu and Files' Go menu with the right items and hints (screenshots); `o.mac_chord("ctrl+n")` opened a second Files window and `ctrl+w` closed it, and malformed chords were refused. `test/test_macdesktop.py`: the file's shape, every action name exists in Lua,
every displayed shortcut equals what pressing it sends through keyd's tables, the widget's matching and filtering functions run in node, and the chord parser runs in real Lua. **Not verified:** Brave, Obsidian and the web apps' menus were not opened live (only their data and the shared code path were tested), and the shortcuts are the apps' documented ones: they were not each tried in the app.
**Not verified:** pointer clicks and hover-to-switch (no pointer injection here); they use the same code paths as the tested `open` and `activate` calls.

Undo: `menubar/install-menubar --remove`.

---

Related: [dock/](../dock/README.md) · [icons/](../icons/README.md) · [keys/](../keys/README.md) · [docs/MAC-FEEL](../docs/MAC-FEEL.md) · [docs/INDEX](../docs/INDEX.md)
