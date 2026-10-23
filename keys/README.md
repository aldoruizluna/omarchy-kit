# keys/: Mac ⌘ shortcuts, the keyd command layer and Caps Lock

> **TL;DR.** Two ways to get your ⌘ shortcuts. `mackeys.lua` (no root) turns a list of Super+key chords into the Ctrl chord the focused app expects, and both ⌘ keys stay Super.
> `install-keyd` (needs sudo) goes all the way: **both ⌘ keys act as Ctrl for every key in every app** (⌘-click and ⌘-scroll included), ⌘Tab, ⌘Space and ⌘Q reach Hyprland as Super chords,
> the Mac's Control chords switch Spaces, and a terminal never receives ⌘ as Ctrl+letter. No key is Super any more: Omarchy's own Super shortcuts are reached through those Mac chords
> and Option+⌘+Space (its menu). `caps-lock` makes Caps Lock a real Caps Lock. If the keyboard ever misbehaves under keyd, press **Backspace + Escape + Enter** together and keyd quits.

> **Status (2026-10-23): the first `install-keyd` was tried and removed; this is its redesign, installed the same day.** The first version made the left ⌘ act as Ctrl while the right ⌘ stayed Super,
> which the owner rejected (both ⌘ keys must behave alike, as the two Ctrl keys do), and keyd's log showed it had matched and **grabbed the Apple trackpad** (`bcm5974`) despite the keyboard-only `k:` id.
> The redesign: both ⌘ keys are the same layer; the keyboard is listed by its **full id** (`vendor:product:hash`, computed the way keyd computes it and checked against the ids keyd logged on this laptop),
> which the trackpad cannot match; and after starting keyd the installer **reads keyd's journal and takes everything back** if keyd grabbed anything but that keyboard. `caps-lock` and `mackeys.lua` are unaffected and in use.

| Script | What | Undo |
|---|---|---|
| `install-mackeys` | no root: installs `mackeys.lua` into the Hyprland config | `--remove` |
| `mackeys.lua` | the shortcut definitions | n/a |
| `mac-key-extras` | choose which of ⌘W ⌘T ⌘F ⌘S ⌘L ⌘G ⌘P also work in apps (`W T F S`, `all`, `none`); in terminals they keep their Omarchy meaning, and the Omarchy action stays reachable at a new chord in every window | `mac-key-extras none` |
| `install-keyd` | **root.** Installs keyd and the Mac command layer below, plus the `keyd-appmap` service; `--dry-run` previews every step and prints the configuration without sudo; `--caps-delay MS` | `sudo install-keyd --remove` |
| `keyd-config` | prints the keyd configuration, the app overlays, the Super-chord table and the Apple keyboards it finds (by full id); changes nothing | n/a |
| `keyd-appmap` | the service that tells terminals from apps (see below) | removed by `install-keyd --remove` |
| `caps-lock` | no root: `real` (a Mac-style Caps Lock) or `compose` (Omarchy's default) | `caps-lock compose` |

## Which one do I want?

| | `mackeys.lua` | the keyd layer |
|---|---|---|
| Root | no | once (a service and a package) |
| Which ⌘ shortcuts | the 13 listed, plus the opt-in extras | every key: ⌘C ⌘T ⌘W ⌘F ⌘L ⌘1…9 and the rest are plain Ctrl |
| ⌘-click, ⌘-scroll, ⌘-drag | no (a bind sees keys, not the pointer) | yes: Ctrl is really held |
| Terminals | skipped | ⌘C copies, ⌘V pastes, ⌘K clears, ⌘W closes; the dangerous Ctrl chords are blocked |
| What it costs | nothing | **no key is Super**: Omarchy's ~150 own Super shortcuts are reachable only through the Mac chords below (see "What you lose") |

They do not clash. With the keyd layer installed nothing sends Super for the letters `mackeys.lua` binds, so it sits idle; it is the fallback if keyd is removed. With the keyd layer the opt-in extras
(`mac-key-extras`) are not needed: ⌘W, ⌘T, ⌘F, ⌘S, ⌘L, ⌘G and ⌘P are already plain Ctrl in apps.

## The keyd layer

Only the Apple keyboard is remapped, and it is listed by its **full keyd id** (`vendor:product:hash`, for example `05ac:0262:f2d1f5c2`), which `keyd-config detect` works out from `/proc/bus/input/devices`: the
hash is keyd's own (djb2 over the number of keys, the first byte of the ABS and REL axis masks, and the device name), recomputed in Python and checked against the ids keyd logged for seven devices on this laptop.
The Apple keyboard and the `bcm5974` trackpad share one vendor and product, differ in the hash, and keyd matches an id as a prefix: the full id cannot match the trackpad, while the `k:vendor:product` form of
the first attempt did. An external PC keyboard keeps its keys. Both ⌘ keys are one layer, so they are identical in every case below.

| You press | Apps receive | Note |
|---|---|---|
| ⌘ + any key not listed below | Ctrl + that key | ⌘T ⌘W ⌘F ⌘L ⌘R ⌘A ⌘Z ⇧⌘Z ⇧⌘T ⌘1…9 … |
| ⌘C / ⌘V | Ctrl+C / Ctrl+V (Ctrl+Insert / Shift+Insert until the helper runs) | the helper switches them, see Terminals |
| ⌘← / ⌘→ | Home / End | ⇧ extends the selection |
| ⌘↑ / ⌘↓ | Ctrl+Home / Ctrl+End | top and bottom of the document |
| ⌥← / ⌥→ | Ctrl+← / Ctrl+→ | move by words (also on the right ⌥) |
| ⌥⌫ / ⌥⌦ | Ctrl+Backspace / Ctrl+Delete | delete a word (a terminal keeps Alt+Backspace) |
| ⌘[ / ⌘] | Alt+← / Alt+→ | back and forward |
| ⇧⌘[ / ⇧⌘] | Ctrl+Shift+Tab / Ctrl+Tab | previous and next tab |
| ⌥⌘I / ⌥⌘J / ⌥⌘C / ⌥⌘U | Ctrl+Shift+I / J / C, Ctrl+U | developer tools, console, inspect, view source |
| ⌥⌘← / ⌥⌘→ | Ctrl+PageUp / PageDown | previous and next tab |
| ⇧⌘. | Ctrl+H | show hidden files in Files |

These ⌘ chords are Mac *system* chords, so they go to Hyprland as **Super chords**; `keyd-config chords` prints the table, and the Hyprland side has to bind the ones marked "to bind":

| You press | Hyprland receives | Today in Omarchy |
|---|---|---|
| ⌘Space | Super+Alt+Space | Spotlight: Apps, Files, Actions and Clipboard (`dock/macdock.lua`; the Apps menu it replaced on this chord is on F4) |
| ⌥⌘Space | Super+Space | Omarchy's menu: the way to everything with no Mac chord |
| ⌘Tab / ⇧⌘Tab | Super+Tab / Super+Shift+Tab, with Super held until ⌘ is released | the app switcher (`dock/macdock.lua`) |
| ⌘` and, while the switcher is up, ← → | Super+grave; Super+Shift+Tab, Super+Tab | the app switcher |
| ⌘Q / ⌘H / ⌘M | Super+Q / Super+H / Super+M | `dock/macdock.lua`: quit, hide, minimise |
| ⌥⌘W | Super+W | close the window, for an app with no Ctrl+W |
| ⇧⌘Q | Super+Escape | Omarchy's system menu (lock, log out, restart, shut down) |
| Esc while the switcher is up | Super+Alt+Escape (never Super+Esc, which is Omarchy's system menu) | cancels the switcher |
| ⇧⌘3 / ⇧⌘4 / ⇧⌘5 | Shift+Print / Print / Super+Ctrl+C | `dock/macdock.lua` binds Shift+Print; Print is the screenshot; the capture menu |
| ⌃⌘Q / ⌃⌘Space / ⌃⌘F | Super+Ctrl+L / Super+Ctrl+E / Super+F | lock, emoji picker, full screen |
| ⌘Enter | Super+Return | open a terminal, in any app (physical Ctrl+Enter still reaches the app) |
| ⌘W / ⌘N / ⌘T in a terminal | Super+W / Super+Return / Super+Return | close window / new terminal / new terminal (a terminal has no tabs). In any other app ⌘W and ⌘T are plain Ctrl+W and Ctrl+T: close tab, new tab |

And the Mac's **Control** chords, which Spaces and Mission Control use (they replace Ctrl+arrow and Ctrl+digit for everything, as on a Mac; ⌃⇧ with the arrows is untouched, so selecting by word with Ctrl still works):

| You press | Hyprland receives | What it does |
|---|---|---|
| ⌃↑ / ⌃↓ | Super+Ctrl+Up / Super+Ctrl+Down | Mission Control / App Exposé (`dock/macdock.lua`) |
| ⌃← / ⌃→ | Super+Ctrl+Shift+Left / Right | previous / next workspace (`dock/macdock.lua`) |
| ⌃1 … ⌃0 | Super+1 … Super+0 | switch to workspace 1 … 10 |
| ⌃⌥← ↑ → ↓ | Super+arrow | focus the window in that direction (Omarchy's tiling) |

Text editing: ⌘⌫ deletes to the start of the line (Shift+Home, Backspace; a terminal gets Ctrl+U).

### What you lose

With no key as Super, Omarchy's own Super shortcuts that have no Mac chord above cannot be pressed: the app launchers (Super+Shift+letter), window toggles (float, pseudo, split, layout, grouping,
scratchpad), resizing and moving windows by keyboard and by Super+mouse, moving a window to another workspace, the notification, toggle and keybindings shortcuts, and workspace scrolling with Super+wheel. Most of
them are reachable from **Omarchy's menu (⌥⌘Space)**, the Apps menu (⌘Space), the Dock and Mission Control. Omarchy's bindings are untouched, so any of them can be given a Mac-style chord later:
add the row to `keyd-config` (one line in a layer table, one in `SUPER_CHORDS`) and the test fails until both agree.

**Super stays held for the app switcher.** After the first ⌘Tab, keyd keeps Super pressed (and not Ctrl) until ⌘ is released, so a switcher bound to Super+Tab can see ⌘ being released and
commit, exactly like a Mac. Verified against keyd's engine (see below).

### Terminals

A terminal reads Ctrl+C as "interrupt", Ctrl+D as "end of input", Ctrl+Z as "stop", Ctrl+S as "freeze". On a Mac none of those is ⌘'s business, so a terminal must never receive ⌘ as
Ctrl+letter. keyd's own `keyd-application-mapper` speaks X, Sway and GNOME but not Hyprland, so `keyd-appmap` does the same job here: it listens on Hyprland's event socket, asks the
compositor whether the focused window carries Omarchy's `terminal` tag (so a terminal added to Omarchy's rule works here too), and applies one of two overlays with `keyd bind`:

- **app:** ⌘C = Ctrl+C, ⌘V = Ctrl+V (a file manager does not take Ctrl+Insert). A launcher, a menu or no window at all counts as an app.
- **terminal:** ⌘C = Ctrl+Insert, ⌘V = Shift+Insert, ⇧⌘C / ⇧⌘V = Ctrl+Shift+C / V, ⌘K clears, ⌘W closes the window, ⌘N and ⌘T open a terminal, ⌘. = Ctrl+C (as in Terminal and iTerm),
  ⌥⌫ = Alt+Backspace, and ⌘A ⌘B ⌘D ⌘E ⌘F ⌘G ⌘I ⌘J ⌘O ⌘P ⌘R ⌘S ⌘U ⌘X ⌘Y ⌘Z do nothing. Physical Ctrl still sends every one of them, the way a Mac's Control does.

**It fails closed.** If the service is down, keyd falls back to its static configuration, which is the terminal-safe one: ⌘C and ⌘V are Ctrl+Insert and Shift+Insert, which GTK, Chromium and
every Omarchy terminal accept (a file manager may ignore them: copy then does nothing, which is a nuisance and not a danger). The remaining Ctrl+letter chords (⌘D, ⌘Z) would reach a shell
until the service is back; systemd restarts it after 2 seconds.

**Why a root service and not the `keyd` group.** `keyd bind` needs the keyd socket. A user in the `keyd` group can make keyd run commands as root, so the group is root-equivalent for everything
in the session (a browser tab included). The service runs as root instead, with only the two capabilities it needs to read the session's sockets, no network, no /home or /root (but it can see the session's runtime directory, which `ProtectHome=yes` would also hide and which it needs) and a
read-only file system; it takes its bindings from a root-owned file, and from the focused window it uses a single bit: terminal or not. It refuses sockets that are symlinks or not
owned by the session's user.

### Caps Lock

With the keyd layer Caps Lock needs a deliberate press of 150 ms, as on a Mac (a quick brush does nothing; `--caps-delay 0` turns that off). Apple does not publish the delay, so 150 ms is an
estimate: tune it with `sudo install-keyd --caps-delay MS`. The light on the key should follow Caps Lock (keyd passes the light's state on, which was read in its source and not tried on this keyboard).

### Install, preview, undo

```bash
~/labspace/omarchy-kit/keys/install-keyd --dry-run     # no sudo: every step, and the configuration it would write
sudo ~/labspace/omarchy-kit/keys/install-keyd          # install (keyd package, /etc/keyd/omarchy-kit-mac.conf, the service)
sudo ~/labspace/omarchy-kit/keys/install-keyd --remove # undo; the keyd package stays (sudo pacman -Rns keyd removes it)
```

It refuses (and changes nothing) if keyd's own `keyd check` rejects the configuration, if another keyd configuration exists (a keyboard can be in only one file), if there is no Apple keyboard,
or if it was not started with sudo from your own account. If keyd, once started, grabbed anything but the keyboard, everything is taken back (see below). Running it twice changes nothing.

After installing: press Caps Lock briefly (nothing), then hold it a moment (the light comes on); try ⌘C and ⌘V in Brave, in Files and in a terminal (in the terminal ⌘C must copy, not
interrupt a running program); try ⌘←, ⌥← and ⌘[ in a text field. Neither ⌘ key starts Omarchy's Super shortcuts any more: use the Mac chords above, ⌥⌘Space for Omarchy's menu, or the trackpad gestures for spaces.

The installer starts keyd, reads its journal and prints `keyd grabbed exactly: <the keyboard>`; if keyd took anything else (the trackpad, last time) or nothing, it removes everything it wrote and exits with an error. To look yourself:
`journalctl -u keyd -b | grep DEVICE` must show one `match` line, for the keyboard, and the trackpad (`bcm5974`) as `ignoring`.

### Limits

- Written for an ANSI keyboard: the `` ` `` key is the one left of the 1 key. An ISO keyboard needs `102nd` bound as well.
- ⌘← and ⌘→ are Home and End, which on a web page scroll to the top and the bottom; a Mac's browsers use them for back and forward (use ⌘[ and ⌘]).
- Do not run `sudo keyd reload`: keyd 2.6.0 frees its keyboards on reload but keeps a pointer to one, and the daemon crashes (SIGSEGV) a second or two later (it happened on 2026-10-23, after the first install over a running keyd). The installer restarts keyd instead; restart it by hand with `sudo systemctl restart keyd`. While keyd is down the keyboard is stock (⌘ is Super).
- Only the physical Apple keyboards are remapped. Typing through fcitx5 or a virtual keyboard (wtype) is not.
- The id's hash depends on the device name and its key count. If a kernel update changes either, keyd stops matching the keyboard (⌘ is Super again, which is safe) and the Setup log row says the id no longer fits; run `install-keyd` again.
- Hyprland sees ⌘ as Ctrl, so a Hyprland bind on plain Ctrl+key also fires on ⌘+key. Omarchy's own Ctrl-only binds are few (the capture selection's Ctrl+Return and Ctrl+Tab, Ctrl+Alt+Tab for monitors).

### How it was checked

`test/test_keyd.py` (about 8 seconds). Always: the generator, the id hash against the ids keyd logged on this laptop, the helper against fake Hyprland sockets and a fake keyd, the installer run as fake root in a private namespace (install, again, remove twice,
refusals, the unit through `systemd-analyze verify`, and the rollback when a fake journal says keyd took the trackpad, took nothing, or took only part), `caps-lock`. With `KEYD_BIN=/path/to/keyd`: keyd's own `keyd check` on every configuration the generator can write. With `KEYD_SRC=/path/to/keyd/source`
(and gcc): `test/keyd-trace.c` links keyd's real engine, and about 26 tests feed it key events and compare the keys that come out (every chord above on both ⌘ keys, the Control chords, the switcher hold, both overlays, the Caps Lock delay).
Not checked without root and a physical keyboard: the daemon grabbing the device, how the keys feel, and the real length of a Caps Lock press.

## Caps Lock

Omarchy's default (`compose:caps,shift:both_capslock_cancel`) makes Caps Lock the **Compose key** (press, release, then `'` and `e` gives é) and moves Caps Lock to both Shift keys. `caps-lock real` empties
those options in a marked block at the end of `~/.config/hypr/input.lua` (the file as it was is kept once as `input.lua.bak-caps`): Caps Lock capitalises, the light on the key follows it, Shift does not cancel it.
What it removes: the Compose key and Caps Lock on both Shifts. The right Option key still types every accent (⌥e e = é). It keeps any other option Omarchy had (for example the Alt+Alt layout switch of
a non-Latin install), reloads Hyprland, restarts fcitx5 (it copies the keymap when it starts) and rebuilds the kit pages. `caps-lock compose` brings Omarchy's default back exactly.

## mackeys.lua

Verified against a real compositor: `node test/verify-mackeys.mjs` calls each handler through `hyprctl eval` and a scratch Brave window reports the exact chord it
receives (32 checks). Needs a running Hyprland session. Setup log rows: **⌘ shortcuts inside apps**, **⌘W ⌘T ⌘F ⌘S ⌘L ⌘G ⌘P in apps (optional)**, **Command works like on a Mac (keyd)**,
**Caps Lock is a real Caps Lock**.

---

Related: [trackpad/](../trackpad/README.md) · [docs/MAC-FEEL](../docs/MAC-FEEL.md) · [test/](../test/README.md) · [docs/INDEX](../docs/INDEX.md)
