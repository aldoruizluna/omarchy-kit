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
| **Menu-bar clock with the date** (Wed 7 Oct 15:08) | `omarchy bar set omarchy.clock format …` | screenshot of the bar | `omarchy bar set omarchy.clock format "dddd HH:mm"` |
| **Auto appearance** (light by day, dark at night), installed but **off** | `appearance/` | schedule logic for every hour, one real theme round trip | `auto-appearance off` |
| **Light sleep on the lid** (s2idle): closing the lid sleeps, opening it wakes at once | `sleep/install-s2idle` (a tmpfiles rule) | three real lid tests, awake again about 1.3 s after opening | `sudo sleep/install-s2idle --remove` |
| **Hibernate that stays off**: saves the session, powers off like a shutdown | `sleep/install-hibernate-mode` (`HibernateMode=shutdown`) | a real hibernate: it stayed off until the power button | `sudo sleep/install-hibernate-mode --remove` |
| **One password after hibernate** (no lock screen before a plain hibernate; only the disk passphrase) | `sleep/install-hibernate-nolock` (no root; refuses on an unencrypted disk) | a real hibernate: one password; suspend still locks | `sleep/install-hibernate-nolock --remove` |
| **Sleep battery log** around every sleep | `sleep/install-battery-log` (hook in `/usr/lib/systemd/system-sleep/`) | entries in the journal after real sleeps | `sudo sleep/install-battery-log --remove` |
| **Sleep check** from the journal: every suspend and hibernate, its mode, duration and battery use | `sleep/sleep-check` | run against this machine's real journal and tested on fake ones | read-only, nothing to undo |
| **Wi-Fi power saving** (about 0.9 W; a packet can wait up to one beacon interval) | `power/install-wifi-powersave` (overrides Omarchy's default off) | measured with `power/power-lab`; idle link latency 2.3 to 5.8 ms | `sudo power/install-wifi-powersave --remove` |
| **Six themes of our own**: Kawaii Bow, Mecha Unit, Solarpunk, each in two variants | `themes/install-themes` (no root; never touches other themes) | each applied to the live desktop and screenshotted; text contrast at least 4.5:1 | `themes/install-themes --remove` |

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
- **Themes**: choose a licence for the original wallpapers (MIT, CC0 or CC BY 4.0) and say whether the 17 MB of images should
  stay in the repository or be replaced by their generators ([THEMES.md](THEMES.md)).
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
