# Golden Gate on this MacBook Pro: what matches, what does not

> **TL;DR.** A row-by-row comparison of macOS 27 "Golden Gate" with this desktop, and of how a MacBook Pro behaves with how this one (a 15" Mid 2014, MacBookPro11,3) now does. Each row says **done**, **partial**, **not done** or
> **impossible** and why, so nothing is claimed that was not measured. The look is a matter of two themes (Golden Gate and Golden Gate Night), the Dock, the menu bar and Mission Control; the keyboard layer that makes ⌘ act as Ctrl everywhere was tried and removed once and has been redesigned (see below). Be clear
> about one thing first: Apple's own list ends at macOS Big Sur for this model, so this is an imitation of Golden Gate, never the real thing.

Related: [MAC-FEEL](MAC-FEEL.md) · [THEMES](THEMES.md) · [dock/README](../dock/README.md) · [menubar/README](../menubar/README.md) · [look/README](../look/README.md) · [keys/README](../keys/README.md) · [INDEX](INDEX.md)

## What "Golden Gate" is, and the caveat

macOS 27 "Golden Gate" was announced at WWDC on 2026-06-08 and released on 2026-09-14 ([Wikipedia](https://en.wikipedia.org/wiki/MacOS_Golden_Gate), [MacRumors](https://www.macrumors.com/2026/06/08/apple-announces-macos-golden-gate/)). It refines
the Liquid Glass design of macOS 26 Tahoe: a single Liquid Glass slider, one consistent window corner radius, deeper shadows, glossy traffic lights, a menu bar without icons in its menus, a Dock that shows background apps, and the rest listed below.
It runs only on Apple silicon. **This Mac's official ceiling is Big Sur 11** ([Apple](https://support.apple.com/en-us/103111)), so Golden Gate is a target to resemble, and Apple's own behaviour for this model is what Big Sur did.

The page is built from two sourced research passes (low-confidence items were flagged and are marked here as reported or unconfirmed); the raw notes are not stored in this repository, the sources that matter are linked at the end. Numbers Apple does not publish (blur radius,
shadow values, animation durations, the menu bar and traffic light sizes) were **not found**, and none is invented here.

Legend: **done** = built and checked on this desktop (how is in [MAC-FEEL](MAC-FEEL.md)); **partial** = the idea is there, the detail is not; **not done** = possible, not built; **impossible** = needs something Apple only ships on a Mac, or hardware this laptop lacks;
**n/a** = this Mac never had it under macOS either.

## The look

| Golden Gate | Here | Status |
|---|---|---|
| Liquid Glass: translucent, blurred surfaces | Dock, menus, popups, notifications and the launcher are tinted, translucent surfaces; real blur is one command (`look/mac-glass on`) and is **off**: measured on the real desktop it raised the GPU's busy time from 10 % to 40 % at idle and doubled the GPU clock while switching apps, which is heat on this laptop | partial |
| One Liquid Glass slider (clear, medium, opaque) | one switch (glass on or off) and the translucency fixed in the theme | partial |
| One consistent window corner radius, rounder than before (about 20 pt reported, 26 pt in Tahoe, 10 pt in Sequoia) | corner radius 16 with smooth, squircle-like curvature in both themes; the shell's popups, menus and notifications follow it. The 20 pt figure is from a forum report Apple has not confirmed | done |
| Deeper window shadows, a clearer active window | a soft deep shadow, a hairline edge, the focused window edged in a faint accent and the others dimmed 6 % | done |
| Glossy Aqua-like traffic lights | not drawable from outside the app (the apps draw their own buttons); GTK apps get the close button on the left | partial |
| Light, Dark and Auto appearance | **Golden Gate** (light) and **Golden Gate Night** (dark), contrast-checked; Auto is `appearance/` (installed, off until you turn it on) | done |
| Accent colours, Multicolor by default | a system blue; the Multicolor default and the other accents are not offered | partial |
| Squircle app icons; non-conforming icons shrunk onto a grey tile | the WhiteSur icon theme (a free re-drawing in the macOS style); icons it lacks are set on a neutral rounded tile by the Dock and the switcher | done |
| The new layered Liquid Glass icons | Apple's own artwork; no free theme has it | impossible |
| Golden Gate wallpapers (Golden Gate, Sunset, Night; animate on unlock) | original wallpapers drawn at install time (a suspension bridge in morning fog and by night, soft colour fields); no Apple artwork, no animation | partial |
| Redesigned pointer, the pointing hand returns | an open-source macOS-style cursor set; not the new design | partial |
| San Francisco font | Adwaita Sans (derived from Inter) for the bar, menus, panels and the Dock; GTK apps already used it. SF is not redistributable | partial |
| Menu bar with no background, text white or black to suit the wallpaper | transparent bar (Omarchy's own setting); the text follows the theme | done |
| Menu bar: Apple menu, the app name in bold, the app's menus | the Omarchy glyph as the system menu, the focused app's name in bold, File, Edit, View, Window, Help; the menus send the ⌘ shortcut because almost no Wayland app publishes a real menu | partial |
| Menus lost most of their icons in 27 | the menus have none | done |
| Status items, the clock on the right | network, sound, battery, display, tray and the clock, in the Mac order | done |
| Overflow arrow at the notch, the bar as one window | not needed (no notch) | n/a |
| Control Center (multi-page, resizable, Controls Gallery) | separate popups for Wi-Fi, Bluetooth, sound, display and power instead of one panel | not done |
| Battery icon redesigned, no percentage by default | Omarchy's battery icon, percentage on right-click | not done |
| Dock: dot under running apps, magnification, Downloads, Trash, auto-hide, right-click menu | all of it | done |
| Dock: lighter dot for apps running only in the background | built: an app with no window but a live process of its launcher's name gets a dimmer dot (the process list is read every 4 s) | done |
| Dock: stacks, recent apps, left and right positions | not built | not done |
| Dock: drag to reorder, drag out to remove | built: sideways reorders the pinned apps, pulled well above the Dock takes the icon off; the logic is tested, the gesture itself needs a real pointer (see dock/README) | partial |
| Cmd+Tab switcher, Cmd+\` between windows of an app | built, with Q to quit and H to hide the selected app | done |
| Mission Control with a Spaces bar and window previews, App Exposé | built (real window pictures taken when it opens, never live); F3, Super+Ctrl+Up, four fingers up; Super+Ctrl+Down for App Exposé | done |
| Spotlight on Cmd+Space: apps, files, actions, clipboard history (Cmd+1 to 4) | built: ⌘Space opens one search with Apps (⌘1), Files (⌘2), Actions (⌘3) and Clipboard (⌘4), a calculator in Apps, and no power action that fires without a menu; no web, contacts, events or Siri suggestions, no file previews. Tested with real key events; the chord itself needs a real press | partial |
| Launchpad is gone, Apps replaces it | F4 and a four-finger pinch open the Apps menu | done |
| Hot corners (bottom right: Quick Note) | built, **off until you choose** (`dock/hot-corners bottom-right quicknote`): Mission Control, App Exposé, Apps, Quick Note, lock or notifications after a 350 ms rest; fires once per visit; tested with the real pointer | done |
| Stage Manager, Fill & Arrange tiling menus | the desktop already tiles; Stage Manager is not built | not done |
| Notification banners top right, Notification Center from the clock | rounded banners top right, the calendar from the clock, notification history on a shortcut; no widget panel | partial |
| Lock screen with a large clock and an avatar | the lock card is styled by the theme (rounded, translucent); no large clock or avatar | partial |
| Login window | the login screen belongs to SDDM and needs root to change | not done |
| Screenshot toolbar (Shift-Cmd-5), Shift-Cmd-3 and 4, a floating thumbnail | all three chords work through the keyboard layer and Omarchy's capture; the thumbnail is a notification | partial |
| Finder with Quick Look | Files (Nautilus) with Quick Look on Space | done |
| System sounds (screenshot, Trash, alert) | none; Apple's are copyrighted and no original set was made | not done |
| Reduce transparency and the accessibility display options | the glass switch and the opaque theme tokens approximate it; there is no panel | partial |
| Apple Account, iCloud, Handoff, AirDrop, Siri, Apple Intelligence, Continuity, Touch ID | none of them can exist on Linux (LocalSend and Tailscale cover file sharing) | impossible |

## The keyboard, trackpad and the rest of this MacBook Pro

| This MacBook Pro under macOS | Here | Status |
|---|---|---|
| The top row is hardware keys first, Fn gives F1 to F12 | the same (`hid_apple` `fnmode=3`) | done |
| F1 and F2 brightness, F5 and F6 keyboard backlight, F7 to F9 media, F10 to F12 mute and volume | bound by Omarchy; brightness and backlight move in 5 % and 10 % steps, not the 16 steps of a Mac | done |
| F3 Mission Control, F4 Launchpad | F3 opens Mission Control, F4 the Apps menu (both did nothing before; checked as bound, not with a real press) | done |
| Eject key | this model most likely has none (Apple's spec lists 78 keys and names no Eject); Omarchy binds `XF86Eject` anyway | n/a |
| Command is the shortcut key; Option and Control as on a Mac | ⌘ shortcuts through Hyprland binds, the same on both ⌘ keys. A keyd layer that makes ⌘ act as Ctrl in every app (⌘-click, ⌘-scroll, every shortcut) was **tried on 2026-10-23 and removed** (it made the left and right ⌘ differ and grabbed the trackpad) and has been **redesigned: both ⌘ keys identical, the keyboard matched by its full id, no key left as Super, the installer undoing itself if keyd grabs anything else. Prepared, not installed** | partial |
| Command and Option arrows move to line start, word | in the redesigned keyd layer (⌘←/→ Home/End, ⌥←/→ words, ⌘⌫ to line start); not installed | not done |
| Control-A, E, K, F, B, P, N as text-editing keys in every field | not built | not done |
| Caps Lock needs a deliberate press and lights up after | a real Caps Lock now (Compose removed); the press delay (150 ms) is in the redesigned keyd layer, not installed | partial |
| Fn+Return is Enter, Fn+Delete forward delete, Fn+arrows Home, End, Page Up and Down | the kernel table maps Fn+Return to Insert; the others are expected from `hid_apple` and not checked | not done |
| Holding a letter opens the accent picker | no general equivalent; right Option types accents instead | impossible |
| Key repeat | Omarchy's fast repeat (40 per second after 250 ms) is kept; a Mac's slower default is a taste, not a fix | not done |
| Trackpad: natural scrolling, two-finger secondary click, tap to click, pinch to zoom | all on (Apple's quick-start guide implies a Mac ships with tap to click off) | done |
| Three fingers up is Mission Control, spread shows the desktop, thumb and three fingers pinch is Launchpad | four fingers up is Mission Control (three fingers switch spaces), four down shows the desktop, a four-finger pinch opens Apps | partial |
| Notification Center from a two-finger swipe from the right edge | the trackpad driver has no edge swipes | impossible |
| Force Touch, haptics, Look Up by three-finger tap | this trackpad never had them | n/a |
| Closing the lid sleeps, opening wakes | light sleep (`s2idle`), wake in about 1.3 s; a lid test on battery is still waiting for you | partial |
| Power button: Control-Power opens a Restart, Sleep, Shut Down dialog | the power key opens Omarchy's power menu (logind ignores it) | done |
| Default display scaling "looks like 1440x900" | the panel runs at 2880x1800 with scale 2 | done |
| Brightness keys, Night Shift | both work (Night Shift is Omarchy's night light) | done |
| Automatic brightness and keyboard backlight from the light sensor | the sensor reads `(0,0)` constantly on this unit, so there is nothing to follow | impossible |
| True Tone, Low Power Mode, Optimized Battery Charging, the camera and microphone dots in the menu bar | this Mac never had them under macOS | n/a |
| MagSafe light, no charging chime on MagSafe 2 | hardware; nothing to do | n/a |
| Speakers, headphone jack, SD card slot, Thunderbolt and HDMI | speaker EQ and automatic headphone switching are done; the SD slot and external displays are detected and untested (the Setup log lists it) | partial |
| FaceTime camera | the `facetimehd` driver works; its green light is hardware | done |

## Do next, in the order that matters

1. **Install the redone Ctrl-like ⌘** (⌘-click, ⌘-scroll, every shortcut): `sudo keys/install-keyd` (`--dry-run` first). Both ⌘ keys are identical and the keyboard is matched by its full id; no key stays Super (Omarchy's menu is ⌥⌘Space).
2. **Press the real keys once** (⌘Tab, F3, F4, Super+Q in the switcher, a log out and in): the tests could send neither the chords nor mouse clicks.
3. **Decide on blur** (`look/mac-glass on`): the real Liquid Glass look costs the GPU time measured above.
4. Pick a theme: `omarchy theme set "Golden Gate"` or `"Golden Gate Night"`; `omarchy theme set "Mecha Unit"` returns.
5. Not built and possible: a Control Center panel, Spotlight file previews and web results, system sounds, Control-A/E/K text keys, Dock stacks.
6. Turn a hot corner on if you want one: `dock/hot-corners bottom-right quicknote` (they ship off).

## How this was checked, and by whom

Two researchers read Apple's pages (the macOS 27 Mac User Guide, apple.com/os/macos, Apple Support's keyboard and Mac specification pages), MacRumors, 9to5Mac, MacStories, Wikipedia and others and wrote sourced checklists; the desktop was audited by hand
(function keys through the compiled keymap, `hyprctl`, `gsettings`, `libinput` options, `fc-match`, screenshots of every surface) and every row marked done was exercised on the real compositor. The blur cost was measured with the same scripted workload (the app switcher, Dock hover, notifications, idle) with
blur off and on, sampling the GPU's actual clock and the CPU time of Hyprland and Quickshell; the energy counters need root, so battery draw was not measured. Details and limits of each piece are in its own README.

## Sources

- macOS 27 overview and Liquid Glass: [Apple](https://www.apple.com/os/macos/), [MacRumors on the Liquid Glass changes](https://www.macrumors.com/2026/06/09/macos-golden-gate-liquid-glass/), [9to5Mac on the slider](https://9to5mac.com/2026/09/22/macos-27-gives-you-more-control-over-liquid-glass/), [MacStories review](https://www.macstories.net/stories/macos-27-the-macstories-review/2/)
- Menu bar: [publicspace.net](https://www.publicspace.net/blog/macos-27-menu-bar/), [MacRumors on menu icons](https://www.macrumors.com/2026/06/11/macos-27-golden-gate-menu-items/), [Apple, what is in the menu bar](https://support.apple.com/guide/mac-help/whats-in-the-menu-bar-mchlp1446/27/mac/27)
- Traffic lights: [512 Pixels](https://512pixels.net/2026/08/golden-gate-beta-6-stoplights-liquid-glass/); window corners: [TidBITS forum](https://talk.tidbits.com/t/adjust-tahoe-window-corner-radius/33791), [Michael Tsai](https://mjtsai.com/blog/2025/10/16/tahoe-window-corners)
- Dock, Spaces and Mission Control: [Apple, open apps from the Dock](https://support.apple.com/guide/mac-help/open-apps-from-the-dock-mh35859/27/mac/27), [Apple, Mission Control](https://support.apple.com/guide/mac-help/mh35798/27/mac/27)
- Spotlight: [Apple](https://support.apple.com/guide/mac-help/mchlp1008/27/mac/27); keyboard shortcuts: [Apple](https://support.apple.com/en-us/102650)
- This Mac under macOS: [Apple, compatible Macs for Big Sur](https://support.apple.com/en-us/103111), [Apple, the function keys](https://support.apple.com/en-us/102439), [Apple, the MacBook Pro specifications](https://support.apple.com/en-us/111935)

---

Related: [MAC-FEEL](MAC-FEEL.md) · [THEMES](THEMES.md) · [dock/README](../dock/README.md) · [menubar/README](../menubar/README.md) · [look/README](../look/README.md) · [keys/README](../keys/README.md) · [INDEX](INDEX.md)
