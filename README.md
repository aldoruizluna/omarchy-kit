# Omarchy Kit

**A bilingual (English / Español) learning portal and setup toolkit for running [Omarchy](https://omarchy.org) on one specific
laptop: the 15" MacBook Pro, mid-2014 (MacBookPro11,3, Intel Haswell + NVIDIA GT 750M).**

It teaches Omarchy with your own machine's real shortcuts, gestures, menus and hardware, checks live that you did each step,
and carries the fixes that make this old Mac quiet, cool and usable: the NVIDIA GPU switched off, a speaker EQ, Mac-style
accents and shortcuts, working sleep and hibernate, a battery power lab and six original themes. Python standard library
only (Pillow, if present, shrinks the home wallpaper and, with librsvg, draws the theme wallpapers), no build tools; it listens on
127.0.0.1 only.

![Start page](docs/start.png)

## Quick start

```bash
git clone https://github.com/aldoruizluna/omarchy-kit ~/labspace/omarchy-kit
cd ~/labspace/omarchy-kit
python3 build_cheatsheet.py     # builds every page from your live Omarchy install
./apps-helper                   # serves http://127.0.0.1:8787 and opens it
```

Start it with your session:

```bash
mkdir -p ~/.config/systemd/user && cp omarchy-kit.service ~/.config/systemd/user/
systemctl --user enable --now omarchy-kit
```

Open the **Setup log** page (`/setup`) first: it lists every change this kit can make, whether it is applied on your machine
right now, and the exact command to undo it. After editing any Python file, restart the service
(`systemctl --user restart omarchy-kit`): it keeps the page builder in memory.

## Requirements

- Omarchy 4 (Arch Linux + Hyprland) with a user session running; Python 3.11 or newer (the scripts read TOML with `tomllib`);
  Node 22 or newer, only for the browser tests. `python-pillow` and `librsvg` are needed only to draw the theme wallpapers
  (`sudo pacman -S python-pillow librsvg`); the themes install without them, minus the wallpapers.
- The portal and learning pages work on any Omarchy machine. The hardware scripts (`gpu/`, `audio/`, `sleep/`, `power/`) are
  written for the **MacBookPro11,3**; `gpu/nvidia-off` and `gpu/switch-to-intel` refuse to run on any other model. Read a script
  before running it anywhere else.

## Safety and how to undo

- Nothing system-wide changes unless you run an installer yourself; the ones that need root say so and you run them with sudo.
- Every installer takes `--remove`, and `--help` (or any unknown option) only prints its usage: it never installs by accident.
  Every change is logged with its undo command on the Setup log page.
- Two trade-offs to know before installing: `power/install-wifi-powersave` overrides Omarchy's deliberate "Wi-Fi power saving
  off" (about 0.9 W saved; undo it if you see lag), and `sleep/install-hibernate-nolock` skips the lock screen before a plain
  hibernate (the screen is unlocked for the ~30 s the image takes to save, and stays unlocked if a hibernate ever fails). That
  installer refuses if the hibernate image is not on an encrypted disk.
- Never rescan or remove PCI devices, or unload the `thunderbolt` driver, on this Mac (it crashed the kernel and lost the
  controller until reboot). `power/power-lab` no longer does either; see [docs/POWER-LAB.md](docs/POWER-LAB.md).

## Documentation

| Read | For |
|---|---|
| [docs/SLEEP.md](docs/SLEEP.md) | Lid, sleep, hibernate and the battery log: what works, what does not, and why |
| [docs/POWER-LAB.md](docs/POWER-LAB.md) | Where the battery goes (about 20 W idle), what was tried and what was ruled out |
| [docs/MAC-FEEL.md](docs/MAC-FEEL.md) | Everything done to feel like a Mac, how it was verified, what still waits for you |
| [docs/THEMES.md](docs/THEMES.md) | The six original themes, where their looks come from, and their CC BY 4.0 licence |
| [docs/FIELD-NOTES.md](docs/FIELD-NOTES.md) | Short, checkable rules learned the hard way (read before changing this machine) |
| [docs/DUMPING-GUIDE.md](docs/DUMPING-GUIDE.md), [docs/GAME-STORE-ROADMAP.md](docs/GAME-STORE-ROADMAP.md) | Retro library: your own dumps, the signed catalog |

## What's inside

| Page | What it does |
|---|---|
| **Start** | Your progress (XP, levels, streak, 16 badges), a live machine panel, and a gallery to switch the Omarchy theme |
| **Learn** | 34 hands-on lessons in six levels, verified live against Hyprland (opening windows, switching spaces, the scratchpad…) |
| **From macOS** | "How do I…?" for 55 Mac habits, translated to the shortcuts on *this* system |
| **Your MacBook** | What works on 2014 MacBook hardware, with live readings and fixes |
| **System** | Live graphs (2 s samples, 30 min history) of CPU temperature, fans, load, memory, network and battery, plus the busiest apps |
| **Games** | Retro library status per console, disk budget, BIOS checklist, PS4 controller battery and hotkeys |
| **Keyboard / Trackpad** | Interactive 3D models of the MacBook keyboard and trackpad, showing every binding and gesture |
| **Reference / Cheat sheet** | All Omarchy commands, the full menu tree, and a glossary, read from the installed Omarchy |
| **Apps** | One-click installer for the apps in `apps.toml` |
| **Setup log** | Every change made to the machine, how to undo it, and its live status (with a guide to its colours) |

Across every page:

- **Follows your Omarchy theme.** Colors and font come from the current theme and update the moment you switch themes.
- **Ctrl+K command palette.** Search pages, lessons, shortcuts, Mac translations, apps, menu items, commands and themes from anywhere.
- **Gamified progress.** XP, ranks, a daily streak, badges with toasts, and confetti when you finish a lesson (skipped when reduced motion is on).

![System page](docs/system.png)
![Command palette](docs/palette.png)

## MacBook Pro 2014 fixes included

- `gpu/`: keep the hot NVIDIA GT 750M **off** (`nvidia-off.service`) and the panel on Intel. Fans dropped from about 5,900 to about 2,100 to 2,200 RPM.
- `audio/`: a measured speaker EQ in Omarchy's speaker-tuning layout, automatically bypassed for headphones.
- `sleep/` and `power/`: sleep, hibernate and battery work (below, and in [docs/SLEEP.md](docs/SLEEP.md) and [docs/POWER-LAB.md](docs/POWER-LAB.md)).
- `themes/`: six original themes of our own ([docs/THEMES.md](docs/THEMES.md)).
- The Setup log documents each change with its undo command, and [docs/FIELD-NOTES.md](docs/FIELD-NOTES.md) holds the rules learned the hard way.

## Making it feel like a Mac

For someone coming from macOS, on top of the gestures and top row the kit sets up:

- **Accents like macOS.** `kb_variant = "mac"` (in `~/.config/hypr/input.lua`) makes the right Option key a dead-key
  accent key: ⌥e then a gives á, ⌥n then n gives ñ, ⌥1 gives ¡, ⌥⇧/ gives ¿. The left Option stays Alt, so Hyprland's Alt
  shortcuts are untouched. fcitx5 copies the layout only when it starts: after changing it run
  `systemctl --user restart omarchy-fcitx5`.
- **⌘ shortcuts inside apps** (`keys/`): `mackeys.lua` turns Super+A, Z, ⇧Z, R, ⇧R, N, ⇧T, D, B, I, U, [ and ] into the
  Ctrl chord the app expects, skipping terminals. It only uses keys Omarchy leaves free (Super+W/T/F/S/L/P/G keep their
  Omarchy meaning). `keys/install-mackeys` installs it and `--remove` undoes it; `test/verify-mackeys.mjs` checks every
  shortcut against a real Brave window.
- **Three fingers: your choice.** They switch spaces by default; `trackpad/three-fingers drag` turns them into a
  three-finger drag (select and drag without clicking) with spaces on four fingers, as on a Mac that uses it.
  libinput cannot do both, and macOS makes the same trade-off.
- **Power profile follows the charger** (`power/`): Performance when plugged in, Balanced on battery, no root needed.
- **Menu-bar clock with the date, and Auto appearance** (`appearance/`, off until you turn it on): light theme by day,
  dark at night, switching only when the period changes so a hand-picked theme sticks.
- **Opt-in ⌘W ⌘T ⌘F ⌘S ⌘L ⌘G ⌘P** (`keys/mac-key-extras`): Omarchy already uses those Super keys, so you choose key by key;
  terminals always keep the Omarchy meaning.
- **A Time Machine for your files** (`backup/install-backups`, needs sudo): hourly `/home` snapshots with snapper plus
  Pika Backup for the real backup. Preview with `--dry-run`.
- **Six themes of our own** (`themes/`, `docs/THEMES.md`): Kawaii Bow (light and night), Mecha Unit (purple and red) and Solarpunk
  (light and dusk), with original wallpapers, contrast-checked palettes and credits for the open-source works they were inspired by.
  The wallpapers are drawn by generator scripts (`themes/generators/`) and not stored. `themes/install-themes` puts the themes in
  Omarchy, drawing the wallpapers as it goes, without switching yours (`--remove` takes them out).
- **Where your battery goes** (`power/power-lab`, `docs/POWER-LAB.md`): measures the real draw, the CPU package and its sleep states
  with the display on and off, and tries power-saving changes one at a time or cumulatively, reverting each straight after. It runs
  as a background service so the terminal stays idle (a busy terminal adds about 4 W). The first tuning it produced is
  `power/install-wifi-powersave` (about 0.9 W, `--remove` undoes it). `power/msr-probe` is a read-only check of the CPU's package
  C-state limit.
- **Sleep that you can trust** (`sleep/`): this MacBook's deep sleep does not wake when the lid opens, so light sleep
  (s2idle) is set at every boot (`install-s2idle`); hibernate works and stays off (`install-hibernate-mode`), asks one
  password instead of two (`install-hibernate-nolock`, no root; it refuses unless the hibernate image sits on an encrypted
  disk, because the disk passphrase is what protects it) and `install-battery-log` records what each sleep costs.
  Every installer takes `--remove`. `sleep-check` reads the journal and tells you whether closing the lid really
  suspended and resumed, in which mode, how much battery it used, and lists hibernates. The whole story, including the
  open decision about the lid, is in [docs/SLEEP.md](docs/SLEEP.md).

The full list, with how each piece was verified, the open decision and what is still waiting for a person, is in
[docs/MAC-FEEL.md](docs/MAC-FEEL.md).

These scripts are written for MacBookPro11,3. `gpu/nvidia-off` and `gpu/switch-to-intel` refuse to run on any other model; read the rest before running them on another machine.

## Retro gaming

RetroArch (installed with Omarchy's own installer), tuned from benchmarks on this machine at 2880×1800:

- **OpenGL instead of Vulkan:** Mesa reports Haswell Vulkan as incomplete.
- **CRT filters chosen by measured fps:** Omarchy's default crt-royale ran at 45 fps (games need 60). The global
  filter is zfast-crt (558 fps), 2D consoles use crt-hyllian-fast (272 fps), and handhelds get LCD filters.
- **Low latency:** 2D consoles use one frame of run-ahead plus rewind. Cave Story (Mega Drive) still runs at
  202 fps with everything on.
- **3D consoles:** PlayStation at 2× with PGXP, N64 with GLideN64 at 960×720, Dreamcast at 1280×960.
- **GameCube:** standalone Dolphin (`kit-games dolphin`): OpenGL, 2× (1280×1056), hybrid ubershaders. It holds
  60 fps with 0.1% late frames in fullscreen (Retro League GX homebrew). The RetroArch core can't compile shaders
  in the background here, so ES-DE launches GameCube games with standalone Dolphin.
- **PS4 controller:** PS opens the menu; hold Share with R1/L1 to save/load a state, R2 to fast-forward,
  L2 to rewind, and Options to quit.

`games/kit-games` manages the library in `~/Games/roms/<console>`. Your own dumps go there, named the
No-Intro/Redump way. It builds one playlist per console pinned to the right core, downloads box art from
libretro's thumbnail server, fetches Dolphin's open-source `Sys` folder for GameCube, checks BIOS files, and
keeps the library within a budget of half the free disk. Consoles, cores and the space plan are in
`games/systems.toml`.

Free games to start with, all from their official sources:

- `games/fetch-homebrew` installs the best-ranked finished homebrew from [Homebrew Hub](https://hh.gbdev.io):
  100 Game Boy, 100 Game Boy Color, 100 GBA and 18 NES games, with cover art and author credits.
- `games/fetch-freeware` installs 12 ScummVM freeware adventures (Beneath a Steel Sky, Flight of the Amazon
  Queen, Broken Sword 2.5 and more), the 20 arcade ROMs MAME distributes with their owners' permission, and
  open-source GameCube homebrew (Retro League GX, Super Methane Brothers) with credits.

Games you own: dump them yourself and run `kit-games ingest`. [docs/DUMPING-GUIDE.md](docs/DUMPING-GUIDE.md) lists the
right tool per console (GB Operator, OSCR, redumper, CleanRip, DreamShell) with steps.

A store client reads a **signed catalog snapshot** that a publisher hosts: `kit-games store refresh --from <folder or
https address>` fetches it and trusts it only if the checksum matches, the ECDSA P-256 signature verifies with a publisher
public key you saved in `~/.config/omarchy-kit/store-publisher.pem` (never trust-on-first-use), and the version is newer than
yours. `list`, `search` and `info` browse it, `get` installs free games (checked against the library budget and the catalog's
checksums, with license and credit shown), `remove` and `sync` take them out again (saves are kept), and commercial games
appear only as guides, never as files. Nothing is uploaded. Built and tested; not yet run on this machine's real library
(no publisher key here). **Your own backups:** `store locations add <folder>` registers a folder that holds backups of games you
own, `store scan` recognises its files on this machine against the libretro databases RetroArch already uses (nothing is
sent anywhere), and a commercial catalog entry you hold a recognised copy of shows *In your backups* and installs from your
folder with `store get`. Locations and the results are local files that cannot be exported or shared. Built and tested; not
yet run on a real backup folder. Still planned: a `/store` page. See [docs/GAME-STORE-ROADMAP.md](docs/GAME-STORE-ROADMAP.md).

```bash
games/kit-games init     # folders, budget, Dolphin Sys data
games/kit-games scan     # playlists
games/kit-games art      # box art, screenshots, title screens
games/kit-games budget   # space per console vs. the plan
games/kit-games bios     # which BIOS files are present
games/kit-games ingest   # identify your own dumps in ~/Games/inbox, rename, compress (CHD/RVZ), file them
games/kit-games esde     # ES-DE frontend over the library (official AppImage in ~/.local/opt/es-de)
games/kit-games cabinet  # RetroFE config (RetroFE 0.10.31 renders black on Hyprland/Mesa 26; ES-DE is the frontend)
games/kit-games export-telesia [--upload]   # library + playtime for Telesia's RetroArch import
games/kit-games store refresh --from SOURCE # fetch, verify (pinned publisher key) and install a signed catalog snapshot
games/kit-games store list|search|info|get|remove|sync|health   # browse it, install free games, withdraw tombstoned ones
games/kit-games store locations add|list|remove, store scan|backups   # your own backups: recognised locally, installed from your folder
```

## Configuration and security

The service only listens on `127.0.0.1`. The endpoints that act on your desktop (open a menu, switch theme, install apps) require
a per-run token embedded in the served pages, compared in constant time, and the `Host` header is checked to block DNS rebinding.
Long jobs (library scan, ingest) run one at a time.

Optional personal details, such as a co-admin's name on the Setup log, go in a git-ignored `local.toml`:

```toml
[coadmin]
name = "Full Name"
user = "username"
```

## Tests

```bash
test/run-all --fast      # syntax lint, then every hermetic test (about 30 s; no browser, no running service, no root)
test/run-all             # the same, then the browser suites against the running portal
```

What runs, if you want one piece:

```bash
python3 -B -m unittest discover -s test -p 'test_*.py'   # store client, your-backups library, sleep/power/themes scripts, lesson data
node test/verify-portal.mjs      # all 12 pages, lessons engine, palette, Setup log, skip links, EN/ES
node test/verify-keyboard.mjs    # 3D keyboard page
node test/verify-trackpad.mjs    # 3D trackpad page
node test/verify-mackeys.mjs     # every ⌘ shortcut against a real Brave window
node test/verify-store-page.mjs  # the Games page's store section in EN and ES
CDP_ATTACH=9334 node test/verify-portal.mjs   # drive a real, GPU-accelerated Brave instead of headless Chromium
```

The Python tests run every installer inside a temporary directory with fake commands, so they cannot change your machine. The
browser tests drive Chromium over the DevTools protocol with no npm dependencies; they never apply themes or open the real Omarchy
menu. Each script prints usage with `--help`.

## Licence

Code: MIT (see `LICENSE`). Themes (palettes, theme files, previews, wallpapers and their texts): CC BY 4.0, see `themes/LICENSE`.

---

**Español:** Omarchy Kit es un portal de aprendizaje bilingüe y un kit de configuración para usar Omarchy en una MacBook Pro de
15" de mediados de 2014. Enseña con tus atajos, gestos y hardware reales, verifica cada paso en vivo, sigue tu tema de Omarchy y
trae gráficas del sistema, búsqueda con Ctrl+K e insignias. Incluye lo necesario para que esta Mac sea silenciosa y fresca:
reposo e hibernación que funcionan, un laboratorio de batería, atajos y acentos como en Mac, y seis temas originales. Todo cambio
queda registrado en la Bitácora con el comando exacto para deshacerlo. Licencia MIT.
