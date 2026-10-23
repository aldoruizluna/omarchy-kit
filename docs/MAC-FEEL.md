# Making Omarchy feel like a Mac

> **TL;DR.** Everything the kit changes so a macOS user feels at home: right-Option accents, a real Caps Lock, ⌘ shortcuts in apps (⌘ as Ctrl everywhere was tried and removed), the macOS icons and pointer, a Dock, a ⌘Tab app switcher, Mission Control, a Mac menu bar, the Golden Gate themes, three-finger behaviour, the power profile following the charger, a menu-bar clock with the date, Auto appearance, working sleep and hibernate, Wi-Fi saving and six themes. Each row says where it lives, how it was verified and how to undo it; the decisions that still wait for a person follow.

Related: [GOLDEN-GATE](GOLDEN-GATE.md) · [look/README](../look/README.md) · [keys/README](../keys/README.md) · [icons/README](../icons/README.md) · [dock/README](../dock/README.md) · [menubar/README](../menubar/README.md) · [trackpad/README](../trackpad/README.md) · [appearance/README](../appearance/README.md) · [SLEEP](SLEEP.md) · [THEMES](THEMES.md) · [INDEX](INDEX.md)

What the kit changes so a macOS user feels at home on this MacBook, how each piece was checked, how to undo it, and
what is still waiting for a person. The live version of this (with real-time status) is the **Setup log** page.

## Done and verified

| Change | Where | Verified | Undo |
|---|---|---|---|
| Accents on the **right Option key** (⌥e e = é, ⌥n n = ñ, ⌥1 = ¡, ⌥⇧/ = ¿); left ⌥ stays Alt | `kb_variant = "mac"` in `input.lua` | every key checked with libxkbcommon | delete the line, `hyprctl reload`, restart fcitx5 |
| **13 ⌘ shortcuts** in apps (⌘A ⌘Z ⇧⌘Z ⌘R ⇧⌘R ⌘N ⇧⌘T ⌘D ⌘B ⌘I ⌘U ⌘[ ⌘]); terminals skipped | `keys/` | `test/verify-mackeys.mjs`: 32 checks against a real Brave window | `keys/install-mackeys --remove` |
| **Caps Lock is a real Caps Lock**: it capitalises, the light follows it, Shift does not cancel it. Removed: Omarchy's Compose key on Caps Lock, and Caps Lock on both Shifts (right Option still types every accent) | a marked block in `input.lua` (`keys/caps-lock`; the file as it was is kept as `input.lua.bak-caps`) | `hyprctl` shows `kb_options` empty on every keyboard; libxkbcommon compiles `<CAPS>` as `Caps_Lock` with plain Shift keys (before: `Multi_key` and Shift+Shift); `test/test_keyd.py`; not with a physical press | `keys/caps-lock compose` |
| **Mac icons and pointer**: the WhiteSur icon theme (a free re-drawing of the macOS icon style, not Apple's art) and an open-source macOS cursor set; the icon variant follows each Omarchy theme's light or dark mode | `icons/` (no root; downloads two pinned releases, checksums verified) | install on the real desktop, a real theme round trip (`mecha-unit`, `flexoki-light`, back), screenshots; `test/test_macdesktop.py` | `icons/install-icons --remove` |
| **A Dock** at the bottom: magnification, running dots, bounce on launch, right-click menu, Downloads and Trash, autohide (⌥⌘D), tinted glass that follows the Omarchy theme | `dock/` (a small Quickshell program, no root) | screenshots of the real compositor, pointer hover, autohide, a light and a dark theme, a real web app; idle cost 0.1 % of one core; `test/test_macdesktop.py`. Not verified: mouse clicks, start at login | `dock/install-dock --remove` (your `dock.json` stays) |
| **⌘Tab app switcher**: running apps, most recently used first; Tab to step, let go of ⌘ to switch; Q quits and H hides the selected app. Replaces *Next / Previous workspace* on Super+Tab (moved to Super+Ctrl+Shift+Right / Left) | `dock/` | real switcher over three apps; Tab, Return, and Ctrl or Super release driven with `wtype` while it had the keyboard; the Lua routing of ⌘Q with the switcher open or closed. Not verified: the real Super+Tab key chord | `dock/install-dock --remove` |
| **Mac menu bar**: Apple-style menu, the focused app's name in bold, File / Edit / View / Window / Help; workspaces in the middle, clock last on the right. The menus send the matching ⌘ shortcut to the focused app (almost no Wayland app publishes a real menu) | `menubar/` (a bar widget plugin and a Hyprland module, no root) | screenshots in both themes, a menu opened and an item run (File > New Window opened a window); layout moved and restored exactly in tests | `menubar/install-menubar --remove` (puts your layout back) |
| **Mission Control and App Exposé**: F3 (the Mac keyboard's Mission Control key, which did nothing), Super+Ctrl+Up or four fingers up open a Spaces bar and real pictures of the windows; Super+Ctrl+Down shows the focused app's windows. F4 (the Launchpad key, also dead before) opens the Apps menu | `dock/` | real windows on three spaces: previews of visible and non-visible spaces, Esc, arrows, Return into another space, closing a window, the + card, App Exposé; idle cost unchanged. Not verified: the real F3/F4 presses and the swipe | `dock/install-dock --remove` |
| **UI font, window buttons on the left, glass switch**: the bar, menus and Dock in Adwaita Sans (a free relative of San Francisco), the close button of GTK apps at the top left, and a switch for blur behind the glass (off) | `look/` (no root; one shell restart) | the whole bar redrawn with every icon intact (screenshot); the font rule tested to change quickshell's monospace and nothing else; `test/test_macsweep.py`. Not verified: the button layout in a real Files window | `look/install-look --remove` |
| **Golden Gate and Golden Gate Night themes**: macOS system-colour palettes (contrast-checked), rounded windows with soft shadows and a hairline edge, translucent rounded menus, launcher and notifications with the accent-blue selection, sliding spaces, original bridge wallpapers. Installed, **not applied** | `themes/` (no root) | applied on the real desktop in both variants (no Hyprland errors; terminal, notification, menus, launcher, Mission Control and the Dock screenshotted), then your theme was put back | `omarchy theme set "Mecha Unit"`; `themes/install-themes --remove golden-gate golden-gate-night` |
| **Three fingers**: swipe between spaces (default) or drag, never both | `THREE_FINGERS` in `input.lua` | trackpad page test in both modes | `trackpad/three-fingers swipe` |
| **Power profile follows the charger** | `power/` (user service, no root) | simulated charger against the real power daemon | `power/install-power-auto --remove` |
| **Menu-bar clock with the date** (Wed 7 Oct 15:08) | `omarchy bar set omarchy.clock format …` | screenshot of the bar | `omarchy bar set omarchy.clock format "dddd HH:mm"` |
| **Auto appearance** (light by day, dark at night), installed but **off** | `appearance/` | schedule logic for every hour, one real theme round trip | `auto-appearance off` |
| **Light sleep on the lid** (s2idle): closing the lid sleeps, opening it wakes at once | `sleep/install-s2idle` (a tmpfiles rule) | three real lid tests, awake again about 1.3 s after opening | `sudo sleep/install-s2idle --remove` |
| **Hibernate that stays off**: saves the session, powers off like a shutdown | `sleep/install-hibernate-mode` (`HibernateMode=shutdown`) | a real hibernate: it stayed off until the power button | `sudo sleep/install-hibernate-mode --remove` |
| **One password after hibernate** (no lock screen before a plain hibernate; only the disk passphrase) | `sleep/install-hibernate-nolock` (no root; refuses on an unencrypted disk) | a real hibernate: one password; suspend still locks | `sleep/install-hibernate-nolock --remove` |
| **Sleep battery log** around every sleep | `sleep/install-battery-log` (hook in `/usr/lib/systemd/system-sleep/`) | entries in the journal after real sleeps | `sudo sleep/install-battery-log --remove` |
| **Sleep check** from the journal: every suspend and hibernate, its mode, duration and battery use | `sleep/sleep-check` | run against this machine's real journal and tested on fake ones | read-only, nothing to undo |
| **Wi-Fi power saving** (about 0.9 W; a packet can wait up to one beacon interval) | `power/install-wifi-powersave` (overrides Omarchy's default off) | measured with `power/power-lab`; idle link latency 2.3 to 5.8 ms | `sudo power/install-wifi-powersave --remove` |
| **Six themes of our own**: Kawaii Bow, Mecha Unit, Solarpunk, each in two variants (CC BY 4.0; wallpapers drawn at install time) | `themes/install-themes` (no root; never touches other themes) | each applied to the live desktop and screenshotted; text contrast at least 4.5:1 | `themes/install-themes --remove` |

Everything is reversible and logged, with its undo command, on the Setup log page.

## Waiting for a person

- **Decide the lid plan.** Today closing the lid uses light sleep, which wakes instantly but keeps the fans spinning and drains the
  battery faster. The alternative, light sleep first and hibernate after about 15 minutes (`suspend-then-hibernate`), costs a
  second password on that automatic path. Not installed; see [SLEEP.md](SLEEP.md).
- **Measure a closed lid on battery**: unplug, close the lid for 10 minutes or more, open it, run `sleep/sleep-check`. The first
  8 W reading was too short to trust.
- **Retest the fan floor** at 1,200 rpm (one run saved about 0.7 W; it needs repeating before it is worth applying).
- **Type with your own fingers** the accents, ⌘ shortcuts and trackpad gestures; the Learn lessons check them.
- **Unplug the charger once** to see the power profile flip to `balanced`.
- **Backups** (needs a password): `sudo backup/install-backups` (preview with `--dry-run`) sets up hourly `/home`
  snapshots and installs Pika Backup. Snapshots on the same disk undo mistakes, not a dead disk, so also point Pika
  Backup at an external drive.
- **Try the real keys** for the Dock and switcher (a real keyboard is needed; the tests could only send virtual keys): hold ⌘ and press Tab a few times, then let go; Super+Q with the switcher open; F3, F4, Super+Ctrl+Up and Down and a four-finger swipe up; log out and in to see the Dock start by itself; click, right-click and drag over the Dock and the menu bar titles. What to expect is in [dock/README](../dock/README.md) and [menubar/README](../menubar/README.md).
- **Decide whether you still want ⌘ as Ctrl everywhere** (tried and removed on 2026-10-23; see the section below). Today both ⌘ keys are Super.
- **A decision about ⌘W ⌘T ⌘F ⌘S ⌘L ⌘G ⌘P**, below (not needed if you install the keyd layer: they are plain Ctrl in apps then).
- Optional: turn on Auto appearance (`auto-appearance on`).

## The decision: Mac keys that Omarchy already uses

Omarchy uses Super+W/T/F/S/L/G/P for window management, so those ⌘ shortcuts still need Ctrl inside apps. Each can be
switched on separately (`keys/mac-key-extras W T F S`). A key that is on sends Ctrl+key **in apps**; **in terminals** it
keeps its Omarchy meaning; and the Omarchy action stays reachable in every window at a new chord:

| Key | Mac meaning (in apps) | Omarchy meaning (kept in terminals) | Omarchy action in apps |
|---|---|---|---|
| W | close tab / window | close window | Super+Alt+W |
| T | new tab | toggle floating / tiling | Super+Alt+T |
| F | find | full screen | Super+Ctrl+Alt+F |
| S | save | toggle scratchpad | Super+Ctrl+Alt+S |
| L | address bar | toggle workspace layout | Super+Alt+L |
| G | find next | toggle window grouping | Super+Ctrl+Alt+G |
| P | print | pseudo window | Super+Ctrl+Alt+P |

**Recommendation:** W, T, F and S. They are the four a Mac user reaches for most, and what they displace is used far
less (a four-finger swipe down still toggles the scratchpad). L, G and P are rarer on both sides, so leave them until
they are missed.

## Tried and removed: the ⌘ key as Ctrl everywhere (keyd)

**Outcome (2026-10-23).** `keys/install-keyd` was installed and removed the same day. The left ⌘ became Ctrl while the right ⌘ stayed Super, and the owner wanted both ⌘ keys to behave alike, as the two Ctrl keys do. And keyd's own log showed that it
had **matched and grabbed the Apple trackpad** (`bcm5974`) although the config used the keyboard-only `k:` id; keyd warned that mouse movement was likely to break, and pointer behaviour was not tested before the removal. Both ⌘ keys are Super again and nothing of the layer remains
(the `keyd` package is still installed, disabled, with no configuration). Lesson: the daemon's device matching could only be tested with fakes before the install; any redo must exclude the trackpad by its full id, make both ⌘ keys identical and be checked in `journalctl -u keyd`.
What follows describes the design as it was prepared.

`keys/install-keyd` (one sudo command; `--dry-run` previews it) makes the **left ⌘ key act as Ctrl for every key in every app**, so every shortcut, ⌘-click and ⌘-scroll work, which the Hyprland
binds above cannot do. Mac system chords (⌘Space, ⌘Tab, ⌘`, ⌘Q, ⌘H, ⌘M, ⇧⌘3/4/5, ⌃⌘Q, ⌃⌘Space, ⌃⌘F) reach Hyprland as Super chords; ⌘←/→ are Home/End and ⌥←/→ move by words; Caps Lock needs a
deliberate 150 ms press. A terminal never receives ⌘ as Ctrl+letter: a small root service, `keyd-appmap`, reads Hyprland's terminal tag and switches the overlay (⌘C copies, ⌘D and ⌘Z do nothing).
Ctrl, Option, the **right ⌘ key** (still Super: all of Omarchy's shortcuts keep working on it), other keyboards and the trackpad are untouched.

- **The price.** The left ⌘ key no longer starts Omarchy's Super+Return or Super+1…9; use the right ⌘ key, or the trackpad gestures for spaces.
- **Safety.** If the keyboard ever misbehaves, Backspace + Escape + Enter together make keyd quit. The installer runs keyd's own checker before activating anything, refuses if another keyd configuration exists,
  and is undone by `sudo keys/install-keyd --remove`. If the service is down, ⌘C and ⌘V fall back to Ctrl+Insert and Shift+Insert, which terminals accept.
- **Why not the keyd group.** It would make every process in your session root-equivalent; the service runs as root instead, sandboxed.
- **Verified:** keyd 2.6.0's own checker on every configuration the generator writes; 17 tests drive keyd's real engine (compiled from its source) with key events and compare the keys that come out; the service against fake
  Hyprland sockets and its focus query against the live compositor; the installer as fake root in a namespace; the unit with `systemd-analyze verify`. **Not verified:** the daemon on the physical keyboard (needs root), how
  the keys feel, and whether 150 ms matches a real Mac's Caps Lock delay (Apple does not publish it).
- Details, the full chord table and the limits: [keys/README](../keys/README.md).

## Looked at and left alone

- **System font.** GTK apps and `system-ui` pages already use Adwaita Sans (GNOME's UI font, derived from Inter, the
  closest free relative of San Francisco). The stack most sites use (`-apple-system, BlinkMacSystemFont`) falls to
  Liberation Sans, and fontconfig cannot change that in Chromium, which ignores substitutes that are not
  metric-compatible. Omarchy's generic `sans-serif` is a deliberate choice, so it was not overridden.
- **Optimized Battery Charging (80% limit).** The battery exposes no charge-limit control to Linux.
- **Press-and-hold accent picker.** No general equivalent on Linux; the right Option key does the same job.
- **A Dock** was left alone in the first pass (it fights the tiling idea) and has since been built, because it is the most recognisable part of the Mac desktop: [dock/](../dock/README.md). It
  is a Quickshell program rather than `nwg-dock-hyprland`, because the Mac Dock's magnification and the shared switcher need one program that knows what is running. It can be hidden (⌥⌘D, or `autohide` in its settings).
- **Blur behind the glass** (what "Liquid Glass" is) is built but **off**, on evidence: see [the measurement below](#blur-behind-the-glass).
- **Window corners and shadows** are in the Golden Gate themes and the UI font in `look/`. **Left alone:** the glossy traffic-light buttons (the apps draw their own), Apple's fonts, system sounds and layered icons (Apple's own work). [GOLDEN-GATE](GOLDEN-GATE.md) has the whole comparison.

## Blur behind the glass

Liquid Glass is translucency plus blur. `look/mac-glass on` turns on Hyprland's blur for the shell's own surfaces (Dock, switcher, Mission Control, menus, notifications, launcher, the bar's drop-downs; never the bar itself or the windows). It was measured, not guessed:
the same scripted workload ran with blur off and on, sampling the Intel GPU's actual clock ten times a second and the CPU time of Hyprland and Quickshell (two runs each, on the charger, the other
work on the machine unchanged).

| Workload | Blur | GPU busy | GPU mean clock | Hyprland CPU | Quickshell CPU |
|---|---|---|---|---|---|
| idle, 20 s | off | 10 % | 225 MHz | 14.6 % of a core | 0.5 % |
| idle, 20 s | on | 40 % | 320 MHz | 15.7 % | 0.5 % |
| app switcher x25 | off | 43 % | 370 MHz | 13.8 % | 8.6 % |
| app switcher x25 | on | 62 % | 725 MHz | 16.9 % | 9.7 % |
| Dock hover x6 | off | 27 % | 266 MHz | 7.7 % | 1.8 % |
| Dock hover x6 | on | 65 % | 353 MHz | 8.1 % | 2.0 % |
| notifications x8 | off | 27 % | 257 MHz | 13.3 % | 2.8 % |
| notifications x8 | on | 47 % | 669 MHz | 17.6 % | 2.5 % |

"GPU busy" is the share of samples above the idle clock. **Reading:** blur quadruples the idle GPU activity and roughly doubles the GPU clock whenever a glass surface moves, with Hyprland spending 5 to 30 % more CPU. The package's energy counter needs root, so
**battery draw was not measured**: the honest conclusion is "it costs, and on this laptop that has meant heat", not a number of watts. It is off by default. Turn it on, look at the fans and the battery for a day, and decide: `look/mac-glass on`, `look/mac-glass off`.
The surfaces are translucent and tinted without it (and the switcher and menus nearly opaque so text behind them cannot be read through them).

## Tests

```bash
node test/verify-portal.mjs      # needs the kit service running; every page, lessons, language switch
node test/verify-trackpad.mjs
node test/verify-keyboard.mjs
node test/verify-mackeys.mjs     # needs a Hyprland session; launches its own scratch Brave and cleans up
CDP_ATTACH=9334 node test/verify-trackpad.mjs   # same, in a real GPU Brave (use a full-size window)
```

---

Related: [GOLDEN-GATE](GOLDEN-GATE.md) · [look/README](../look/README.md) · [keys/README](../keys/README.md) · [icons/README](../icons/README.md) · [dock/README](../dock/README.md) · [menubar/README](../menubar/README.md) · [trackpad/README](../trackpad/README.md) · [appearance/README](../appearance/README.md) · [SLEEP](SLEEP.md) · [THEMES](THEMES.md) · [INDEX](INDEX.md)
