# menubar/: the Mac menu bar

> **TL;DR.** Omarchy's top bar rearranged the way macOS lays out its menu bar: a system menu (Apple menu) and the **name of the focused app in bold** at the left, then File, Edit,
> View, Window and Help menus; the workspaces in the middle; the status icons and the clock at the right. Almost no Wayland app publishes a real menu, so these are the
> standard Mac menus and each item sends the matching ⌘ shortcut to the focused app. No root; your original bar layout is saved and `--remove` restores it exactly.

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

## The honest part: these are not the app's own menus

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
- `⌘Q` and `⌘H` in these menus use the Dock module (`dock/install-dock`); without it those two items do nothing.

## How it was checked

On the real desktop: a screenshot of the new bar, the Edit menu and the Apple menu open (dark and light themes); `File > New Window` opened a second Files window
and the menu closed (menu to `hyprctl eval` to the app); the window actions (Ctrl+N, Ctrl+W, quit) on real Files windows. `test/test_macdesktop.py`: the layout moves to the Mac order and back
to the exact original, nothing the user had is lost or duplicated, invalid `shell.json` is never touched, and every item id in the widget has a Lua action.
**Not verified:** pointer clicks and hover-to-switch (no pointer injection here); they use the same code paths as the tested `open` and `activate` calls.

Undo: `menubar/install-menubar --remove`.

---

Related: [dock/](../dock/README.md) · [icons/](../icons/README.md) · [keys/](../keys/README.md) · [docs/MAC-FEEL](../docs/MAC-FEEL.md) · [docs/INDEX](../docs/INDEX.md)
