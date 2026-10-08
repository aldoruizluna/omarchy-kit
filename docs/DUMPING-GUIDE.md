# Dumping your own games

> **TL;DR.** Games you own enter the library by dumping the cartridge or disc yourself: copy the file into `~/Games/inbox`, run `games/kit-games ingest`, and it identifies, names, compresses and files it. This page lists the dumping tool for each console. The kit never downloads commercial ROMs or BIOS files.

Related: [games/README](../games/README.md) · [GAME-STORE-ROADMAP](GAME-STORE-ROADMAP.md) · [README: Retro gaming](../README.md#retro-gaming) · [INDEX](INDEX.md)

How games you own get into the library: copy (dump) the cartridge or disc yourself, drop the file in
`~/Games/inbox`, and run `games/kit-games ingest`. Ingest checks each file against libretro's No-Intro
(cartridges) and Redump (discs) databases, names it the canonical way, compresses discs (CHD, or RVZ for
GameCube), files it under `~/Games/roms/<console>`, and refreshes playlists, box art and ES-DE.

**Resumen (ES):** Así entran a la biblioteca los juegos que ya tienes: copias (vuelcas) tú mismo el cartucho o
disco, pones el archivo en `~/Games/inbox` y ejecutas `games/kit-games ingest`. Ingest lo compara con las bases
No-Intro/Redump, le pone el nombre correcto, comprime discos (CHD, o RVZ para GameCube), lo archiva y actualiza
listas, carátulas y ES-DE. Abajo: qué equipo sirve para cada consola y los pasos.

A dump that matches the database is byte-identical to the original, so it's also a check that your cartridge is
healthy. A dump that doesn't match stays in the inbox with a note. Clean the contacts (isopropyl alcohol) and
dump again.

## What to use, per console

| Console | Tool | Notes |
|---|---|---|
| Game Boy / Color / Advance | **Epilogue GB Operator** + Playback (AppImage on Linux) | Easiest. "Backup ROM" and "Backup Save". Also plays the cart directly. |
| SNES / Super Famicom | **Epilogue SN Operator** or **OSCR** | SN Operator has Linux support. |
| NES, SNES, N64, Mega Drive, Master System, GB/GBC/GBA | **OSCR** (sanni's Open Source Cartridge Reader) | Standalone, USB-powered, writes ROMs and saves to its SD card. Extra adapters: Game Gear, PC Engine, Virtual Boy, Neo Geo Pocket, WonderSwan. Also reads N64 Controller Pak saves. |
| PlayStation, Sega CD, Saturn, PC Engine CD | **redumper** + a supported USB optical drive | This MacBook has no optical drive. Get one from redumper's supported list (Plextor, some LG/ASUS/LITE-ON; the ASUS BW-16D1HT is a common in-production pick). Byte-perfect CD dumps that match Redump. |
| GameCube | **CleanRip** on a Wii with the Homebrew Channel (USB or SD), or on a GameCube with an SD2SP2 adapter via Swiss | GameCube discs are 1.36 GiB, so FAT32 is fine. CleanRip verifies its hash against Redump. |
| Dreamcast | **DreamShell** on the Dreamcast with an SD adapter, or redumper with a drive that can read GD-ROMs | PC drives read only the CD half of a GD-ROM unless redumper's drive notes say otherwise. |

BIOS files (PS1, Sega CD, Saturn, PC Engine CD) also have to come from your own consoles. `kit-games bios`
lists which file each system needs and where it goes (`~/Games/bios`). The dumping guides linked below cover
BIOS dumping per console.

## Steps

### Cartridges with a GB/SN Operator
1. Download Playback from epilogue.co (Linux AppImage), make it executable, run it.
2. Insert the cartridge, plug in the Operator, click **Backup ROM**, then **Backup Save** if the game has one.
3. Move the `.gb/.gbc/.gba/.sfc` file to `~/Games/inbox`. Put the save next to the game in RetroArch's save
   folder (`~/Games/saves/<core>/<game name>.srm`) to continue your progress.

### Cartridges with an OSCR
1. Format its SD card FAT32 and load the firmware per the OSCR wiki.
2. Insert the cartridge, choose the console in the menu, **Read ROM** (and **Read Save**).
3. Copy the files from the SD card's `ROM/` folder to `~/Games/inbox`.

### CDs with redumper (PS1, Sega CD, Saturn, PC Engine CD)
1. Plug in a supported drive; check it shows up (`lsblk`).
2. Run `redumper disc --drive=/dev/sr0 --image-name="<Title>"`. It writes `.cue/.bin` (plus logs) and reports
   whether the dump matched.
3. Move the `.cue` and all its `.bin` files to `~/Games/inbox`. Ingest keeps them together and makes a `.chd`.

### GameCube with CleanRip (Wii)
1. Put CleanRip in `apps/` on the SD card or USB drive, launch it from the Homebrew Channel.
2. Choose the device, insert the disc, accept the defaults (download the Redump DAT when offered, for
   verification), dump.
3. Copy the `.iso` to `~/Games/inbox`. Ingest converts it to `.rvz` when `dolphin-tool` is installed
   (`sudo pacman -S dolphin-emu-tool`): lossless, and usually much smaller because GameCube discs carry padding.

## After ingest

```bash
games/kit-games ingest     # identify, name, compress, file, refresh playlists/art/ES-DE
games/kit-games budget     # space used per console vs the 231 GB budget
games/kit-games export-telesia   # update ~/Games/telesia/library.json for Telesia
```

## Further reading

- dumping.guide: per-console disc and cartridge methods (Redump community).
- consolemods.org wiki: "Creating Game Backups" pages per console.
- Dolphin's "Ripping Games" guide: dolphin-emu.org/docs/guides/ripping-games.
- redumper: github.com/superg/redumper (supported drive list in its README).

---

Related: [games/README](../games/README.md) · [GAME-STORE-ROADMAP](GAME-STORE-ROADMAP.md) · [README: Retro gaming](../README.md#retro-gaming) · [INDEX](INDEX.md)
