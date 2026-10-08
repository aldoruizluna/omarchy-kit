# Making Omarchy feel like a Mac

What the kit changes so a macOS user feels at home on this MacBook, how each piece was checked, how to undo it, and
what is still waiting for a person. The live version of this (with real-time status) is the **Setup log** page.

## Done and verified

| Change | Where | Verified | Undo |
|---|---|---|---|
| Accents on the **right Option key** (⌥e e = é, ⌥n n = ñ, ⌥1 = ¡, ⌥⇧/ = ¿); left ⌥ stays Alt | `kb_variant = "mac"` in `input.lua` | every key checked with libxkbcommon | delete the line, `hyprctl reload`, restart fcitx5 |
| **13 ⌘ shortcuts** in apps (⌘A ⌘Z ⇧⌘Z ⌘R ⇧⌘R ⌘N ⇧⌘T ⌘D ⌘B ⌘I ⌘U ⌘[ ⌘]); terminals skipped | `keys/` | `test/verify-mackeys.mjs`: 32 checks against a real Brave window | `keys/install-mackeys --remove` |
| **Three fingers**: swipe between spaces (default) or drag, never both | `THREE_FINGERS` in `input.lua` | trackpad page test in both modes | `trackpad/three-fingers swipe` |
| **Power profile follows the charger** | `power/` (user service, no root) | simulated charger against the real power daemon | `power/install-power-auto --remove` |
| **Sleep check** from the journal | `sleep/sleep-check` | synthetic journal data | read-only, nothing to undo |
| **Menu-bar clock with the date** (Wed 7 Oct 15:08) | `omarchy bar set omarchy.clock format …` | screenshot of the bar | `omarchy bar set omarchy.clock format "dddd HH:mm"` |
| **Auto appearance** (light by day, dark at night), installed but **off** | `appearance/` | schedule logic for every hour, one real theme round trip | `auto-appearance off` |

Everything is reversible and logged, with its undo command, on the Setup log page.

## Waiting for a person

- **Make light sleep permanent**: `sudo sleep/install-s2idle` (undo with `--remove`). This MacBook's deep sleep does not
  wake when the lid opens (tested 2026-10-07: two failures, the lid only woke it when closing an open lid); light sleep
  (s2idle) wakes on the lid at once. Then, away from the charger, measure what a closed lid costs in battery.
- **Type with your own fingers** the accents, ⌘ shortcuts and trackpad gestures; the Learn lessons check them.
- **Unplug the charger once** to see the power profile flip to `balanced`.
- **Backups** (needs a password): `sudo backup/install-backups` (preview with `--dry-run`) sets up hourly `/home`
  snapshots and installs Pika Backup. Snapshots on the same disk undo mistakes, not a dead disk, so also point Pika
  Backup at an external drive.
- **A decision about ⌘W ⌘T ⌘F ⌘S ⌘L ⌘G ⌘P**, below.
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

## Looked at and left alone

- **System font.** GTK apps and `system-ui` pages already use Adwaita Sans (GNOME's UI font, derived from Inter, the
  closest free relative of San Francisco). The stack most sites use (`-apple-system, BlinkMacSystemFont`) falls to
  Liberation Sans, and fontconfig cannot change that in Chromium, which ignores substitutes that are not
  metric-compatible. Omarchy's generic `sans-serif` is a deliberate choice, so it was not overridden.
- **Optimized Battery Charging (80% limit).** The battery exposes no charge-limit control to Linux.
- **Press-and-hold accent picker.** No general equivalent on Linux; the right Option key does the same job.
- **A Dock.** Not installed: it fights the tiling idea. `nwg-dock-hyprland` is in the extra repo if wanted, and should be
  built and tested rather than added on a guess.

## Tests

```bash
node test/verify-portal.mjs      # needs the kit service running; every page, lessons, language switch
node test/verify-trackpad.mjs
node test/verify-keyboard.mjs
node test/verify-mackeys.mjs     # needs a Hyprland session; launches its own scratch Brave and cleans up
CDP_ATTACH=9334 node test/verify-trackpad.mjs   # same, in a real GPU Brave (use a full-size window)
```
