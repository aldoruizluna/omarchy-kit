# Omarchy Kit

A bilingual (English / Español) learning portal and setup toolkit for running
[Omarchy](https://omarchy.org) on a **15" MacBook Pro, mid-2014 (MacBookPro11,3)**: Intel Haswell + NVIDIA GT 750M.

It is a small local web app (Python standard library only, no build tools) that teaches Omarchy using your own
machine's real shortcuts, gestures, menus and hardware, and checks live that you actually did each step.

![Start page](docs/start.png)

## What's inside

| Page | What it does |
|---|---|
| **Start** | Your progress (XP, levels, streak, 15 badges), a live machine panel, and a gallery to switch the Omarchy theme |
| **Learn** | 24 hands-on lessons, verified live against Hyprland (opening windows, switching spaces, the scratchpad…) |
| **From macOS** | "How do I…?" for 41 Mac habits, translated to the shortcuts on *this* system |
| **Your MacBook** | What works on 2014 MacBook hardware, with live readings and fixes |
| **System** | Live graphs (2 s samples, 30 min history) of CPU temperature, fans, load, memory, network and battery, plus the busiest apps |
| **Games** | Retro library status per console, disk budget, BIOS checklist, PS4 controller battery and hotkeys |
| **Keyboard / Trackpad** | Interactive 3D models of the MacBook keyboard and trackpad, showing every binding and gesture |
| **Reference / Cheat sheet** | All Omarchy commands, the full menu tree, and a glossary, read from the installed Omarchy |
| **Apps** | One-click installer for the apps in `apps.toml` |
| **Setup log** | Every change made to the machine, how to undo it, and its live status |

Across every page:

- **Follows your Omarchy theme.** Colors and font come from the current theme and update the moment you switch themes.
- **Ctrl+K command palette.** Search pages, lessons, shortcuts, Mac translations, apps, menu items, commands and themes from anywhere.
- **Gamified progress.** XP, ranks, a daily streak, badges with toasts, and confetti when you finish a lesson (skipped when reduced motion is on).

![System page](docs/system.png)
![Command palette](docs/palette.png)

## MacBook Pro 2014 fixes included

- `gpu/`: keep the hot NVIDIA GT 750M **off** (`nvidia-off.service`) and the panel on Intel. Fans dropped from about 5,900 to about 2,200 RPM.
- `audio/`: a measured speaker EQ in Omarchy's speaker-tuning layout, automatically bypassed for headphones.
- The Setup log documents each change with its undo command.

These scripts are written for MacBookPro11,3. `gpu/nvidia-off` and `gpu/switch-to-intel` refuse to run on any other model; read the rest before running them on another machine.

## Retro gaming

RetroArch (installed with Omarchy's own installer), tuned from benchmarks on this machine at 2880×1800:

- **OpenGL instead of Vulkan:** Mesa reports Haswell Vulkan as incomplete.
- **CRT filters chosen by measured fps:** Omarchy's default crt-royale ran at 45 fps (games need 60). The global
  filter is zfast-crt (558 fps), 2D consoles use crt-hyllian-fast (272 fps), and handhelds get LCD filters.
- **Low latency:** 2D consoles use one frame of run-ahead plus rewind. Cave Story (Mega Drive) still runs at
  202 fps with everything on.
- **3D consoles:** PlayStation at 2× with PGXP, N64 with GLideN64 at 960×720, Dreamcast at 1280×960.
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
  Queen, Broken Sword 2.5 and more) and the 20 arcade ROMs MAME distributes with their owners' permission.

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
```

## Run it

```bash
git clone https://github.com/aldoruizluna/omarchy-kit ~/labspace/omarchy-kit
cd ~/labspace/omarchy-kit
python3 build_cheatsheet.py        # builds every page from your live Omarchy install
./apps-helper                      # serves http://127.0.0.1:8787 and opens it
```

To start it with your session, install the user service:

```bash
mkdir -p ~/.config/systemd/user && cp omarchy-kit.service ~/.config/systemd/user/
systemctl --user enable --now omarchy-kit
```

The service only listens on `127.0.0.1`. The endpoints that act on your desktop (open a menu, switch theme,
install apps) require a per-run token embedded in the served pages, and the `Host` header is checked to block DNS
rebinding.

Optional personal details, such as a co-admin's name on the Setup log, go in a git-ignored `local.toml`:

```toml
[coadmin]
name = "Full Name"
user = "username"
```

## Tests

```bash
node test/verify-portal.mjs      # all pages, lessons engine, palette, System page
node test/verify-keyboard.mjs
node test/verify-trackpad.mjs
CDP_ATTACH=9334 node test/verify-portal.mjs   # drive a real, GPU-accelerated Brave instead of headless Chromium
```

The tests drive Chromium over the DevTools protocol with no npm dependencies (Node 22+). They never apply themes
or open the real Omarchy menu.

---

**Español:** Omarchy Kit es un portal de aprendizaje bilingüe y un kit de configuración para usar Omarchy en una
MacBook Pro de 15" de mediados de 2014. Enseña con tus atajos, gestos y hardware reales, verifica cada paso en vivo,
sigue tu tema de Omarchy, y trae gráficas del sistema, búsqueda con Ctrl+K e insignias. Licencia MIT.
