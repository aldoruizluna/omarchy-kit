# Game Store — roadmap

> **Status: planned, not implemented.** Nothing in this document exists as code yet. It describes how a
> "store" for the retro library would be built on top of what `games/kit-games` already does, so the work can
> start (or be handed off) without re-doing the research. Written 2026-10-05; facts marked *verified* were
> checked on that date.

> **Update 2026-10-07:** a first slice is built and tested: `kit-games store` (refresh, list, search, info, get, remove,
> sync, health) in `games/storelib.py`. Its shape differs from §5.1–5.2: the catalog is built by a **publisher**
> and shipped as a signed snapshot (`version.json` + a zstd SQLite file, ECDSA P-256); the kit verifies it with a
> public key the user pinned and installs from it, instead of running adapters itself. `~/Games/.kit-store.json`
> is therefore the manifest of what the store installed, not the catalog. Built: browsing, `get` for plain ROMs,
> MAME zips and ScummVM archives (budget-checked, checksum-verified), `remove`, tombstone `sync`, `health`.
> Not built: RVZ/CHD conversion on `get`, the `/store` portal page and API (phase 4), art fetching on `get`,
> and a run against this machine's real library (no publisher key is installed here).
>
> **Update 2026-10-07 (later): personal backup locations are built and tested** in `games/personallib.py`:
> `store locations add|list|remove`, `store scan`, `store backups`, `store list --backups`, and `store get --which --link`.
> Locations are local folders (or shares already mounted as paths) kept in `~/.config/omarchy-kit/store-locations.json`; a
> scan hashes files on this machine and recognises them against the libretro `.rdb` databases already on disk (read
> in-process, no network), writing `~/Games/.cache/store/personal.sqlite`. A commercial (guide) entry with a recognised copy
> shows *In your backups* and installs from the user's folder; nothing is uploaded, and exporting or sharing locations is
> intentionally absent. Not built: remote locations with credentials (WebDAV/S3), disc serial reads, recognition of
> CHD/RVZ/7z containers and multi-file arcade sets, filesystem watching (scans run on demand only), and a run on a real
> backup folder.

**Resumen (ES):** Plan para una "tienda" de juegos dentro de Omarchy Kit: un catálogo con carátulas por consola,
un botón "Obtener" que descarga, archiva y agrega el juego a ES-DE, siempre dentro del presupuesto de disco.
Solo usa fuentes con derecho claro a distribuir (homebrew, freeware, contenido libre de libretro, itch.io
gratuito) o contenido que ya es tuyo (compras, tus propios volcados). Cada juego guarda su procedencia y
licencia. caprado/romgi se evaluó y se descartó (ver abajo). **Todavía no está implementado.**

---

## 1. Goal

Grow the local library toward "top titles up to GameCube" with a store-like experience: browse by console with
box art, see what a game is and where it comes from, press **Get**, and find it in ES-DE a minute later, already
named, compressed, with art, inside the 231 GB budget, and ready for Telesia.

## 2. Decision record: romgi (declined)

[caprado/romgi](https://github.com/caprado/romgi) (MIT, Android) was proposed as the store. Its catalog
(`db/CATALOG.md`, *verified*) is a SQLite database of **~241,000 entries / ~400,000 links** across 50 platforms,
pointing at full commercial ROM sets on HTTP mirrors, Internet Archive and BitTorrent, and it ships
**PS3 license files (`.rap`) and PS Vita keys (`zRIF`)**. Using it would mean downloading copyrighted games
without a license and using DRM circumvention keys, so it is out, as were CoinOPS builds before it. The
library's standing rule applies: **no commercial ROM downloads, even for games you physically own**. Owned
games enter through dumping (§4.3).

What romgi gets right and this plan borrows: a single searchable catalog, per-platform filters, box art,
a download queue, archive extraction, per-platform destinations and per-source health status.

## 3. Principles

1. **Provenance or nothing.** Every catalog entry records its source URL, author, and license or distribution
   permission. Entries whose right to redistribute is unclear are excluded, not "probably fine".
2. **Reuse the pipeline.** Downloads land in a staging folder and go through the same steps as today: identify,
   canonical name, CHD/RVZ, file into `~/Games/roms/<folder>`, `scan`, `art`, `esde`.
3. **Budget first.** `Get` refuses anything that would exceed `~/Games/.kit-budget.json` (same check as `ingest`).
4. **Verifiable.** Checksums are stored and checked; source health is shown, like romgi's status panel.
5. **Telesia-ready.** Entries carry the IDs Telesia needs (IGDB id when known, RetroAchievements game id when
   known), and `export-telesia` includes provenance.
6. **Bilingual UI**, verified in a real GPU Brave (`CDP_ATTACH=9334`), like the rest of the kit.

## 4. Sources

### 4.1 Free to redistribute

| Source | Consoles | Access | Notes |
|---|---|---|---|
| **Homebrew Hub** (hh3.gbdev.io) | GB, GBC, GBA, NES | Public API; already used by `games/fetch-homebrew` | 300 + 18 installed today; per-game license in the hub's entries. Adapter = refactor of the existing script. |
| **libretro content assets** (buildbot.libretro.com/assets/cores/) | ~50 folders incl. GameCube/Wii, N64, PS1, Mega Drive, SNES, Dreamcast, Saturn | Plain HTTP index (h5ai) | *Verified listing:* GameCube: Super Methane Brothers, 240p Test Suite; N64: Flappy Bird; Mega Drive: Cave Story, Break An Egg, Gravibots…; SNES: Super Boss Gaiden, N-Warp Daisakusen, KeepingSNESalive; Dreamcast: Volgarr the Viking. This is RetroArch's own "Content Downloader" set. **Check each item's license.** Some names look like commercial demos (e.g. "Downforce (USA) (Demo)"); include only items with a documented free license or publisher permission. Skip test suites in the store view; keep them as tools. |
| **MAME free ROMs** (mamedev.org/roms) | Arcade | Already used by `games/fetch-freeware` | 20 installed. |
| **ScummVM freeware** (scummvm.org/games) | ScummVM | Already used by `games/fetch-freeware` | 12 installed. |
| **Open-source homebrew on GitHub** | Any, incl. GameCube | Curated list file (repo + release asset + license) | Example: Retro League GX (MIT, prebuilt `.dol`), already the GameCube benchmark. GitHub's API gives the license and release checksums. |
| **itch.io** | NES, GB/GBC/GBA, Mega Drive, SNES, N64, GameCube… (tags) | API key (bearer) required; `GET /games/{id}/uploads`, then the upload's download URL, which works for free games | Many retro homebrew games are free downloads; some are pay-what-you-want or paid (those belong in §4.2). Key lives in `local.toml` (git-ignored). Respect each game's license page. |
| **Open Shop Channel** (oscwii.org) | Wii homebrew | Public API v2 was **discontinued 2024-07-01**; replaced by the "Repository Manager API" (exact endpoint to confirm at implementation time) | Mostly apps, some games. Needs a Wii system in `systems.toml` first (Dolphin already supports it). Lowest priority. |

### 4.2 Bought by you

| Source | Notes |
|---|---|
| **Steam: SEGA Mega Drive & Genesis Classics** | Delisted **2024-12-06** (*verified*); owned copies still download and play. The ROM files in the install folder are what RetroArch runs. Importer = point `ingest` at the Steam install folder; it identifies them against No-Intro. **Confirm the folder layout on a real install first.** |
| **Other digital re-releases (GOG, Steam)** | Per title: some ship plain ROMs, most don't. Only titles confirmed to contain plain ROM files get a guided importer. |
| **New homebrew cartridges** (small publishers) | Dump with a GB Operator or OSCR, then `ingest`. Many also sell the ROM digitally (then it's §4.1 or §4.2 by license). |

### 4.3 Owned physical games (already supported)

Dump your own cartridges and discs, then `kit-games ingest` identifies them against libretro's
No-Intro/Redump databases, renames, compresses and files them:

- **Cartridges:** OSCR or GB Operator.
- **CD-based consoles:** redumper.
- **GameCube:** CleanRip.
- **Dreamcast:** DreamShell.

The store page can show **"Your shelf"**: dumps found in `~/Games/inbox`, with what `ingest` will do with them.

### 4.4 Excluded

romgi's catalog, Myrient and Internet Archive mirrors of No-Intro/Redump sets, ROM torrents, ROM bundles
(CoinOPS and similar), BIOS downloads, and any DRM keys or licenses. BIOS files must come from your own consoles.

## 5. Design

### 5.1 Catalog

One file, `~/Games/.kit-store.json` (or SQLite once it passes a few thousand rows), rebuilt by `store refresh`
from every adapter:

```jsonc
{
  "id": "libretro:gc/super-methane-brothers",
  "title": "Super Methane Brothers",
  "folder": "gc",                         // systems.toml folder
  "source": "libretro-assets",
  "source_url": "https://buildbot.libretro.com/assets/cores/Nintendo - GameCube - Wii/Super Methane Brothers.zip",
  "author": "…", "license": "GPL-2.0", "license_url": "…",
  "size": 1234567, "sha1": "…",
  "art": {"boxart": "…", "snap": "…"},
  "description": "…",
  "igdb_id": null, "ra_game_id": null,    // filled when known (Telesia / RetroAchievements)
  "installed": "~/Games/roms/gc/Super Methane Brothers.rvz" // or null
}
```

### 5.2 Adapters

One small Python module per source in `games/store/`, each with `list() -> entries` and
`fetch(entry, staging_dir) -> files`. The existing `fetch-homebrew` and `fetch-freeware` become the first two
adapters, which proves the shape without adding sources. Each adapter reports health (online / down / unknown,
entry count, last checked), shown in the UI.

### 5.3 CLI

```
kit-games store refresh            rebuild the catalog from all adapters (cached)
kit-games store list [--folder gc] [--source itch] [--installed|--available]
kit-games store search "<text>"
kit-games store get <id>…          download → staging → existing ingest/file/art/esde steps; budget-checked
kit-games store remove <id>        delete the files, keep saves
kit-games store health             per-source status
```

`get` reuses `ingest`'s steps. Homebrew isn't in No-Intro, so identification falls back to the catalog's own
metadata (title, folder, checksum) rather than "unknown".

### 5.4 Portal page `/store` (EN/ES)

Grid of box art per console with filters (console, source, installed / available, has achievements), a details
panel (description, author, license, size, source), a **Get** button and a download queue, served by
`omarchy-kit.service`, which gains `GET /api/store` and `POST /api/store/get`. The budget meter from the Games
page sits at the top. The Setup log gets a `store` status row.

### 5.5 ES-DE and RetroArch

No new integration: `get` ends with the same `scan` → `art` → `esde` calls. GameCube entries open in standalone
Dolphin (`kit-games dolphin`).

### 5.6 Telesia

`export-telesia` adds `source`, `license` and `source_url` per item. IGDB matching stays blocked until Telesia's
IGDB credentials exist (gate U8), and RetroAchievements ids until gate U14. Until then the store keeps the ids it
can get from the sources themselves (Homebrew Hub and libretro entries sometimes carry them).

## 6. Phases

| # | Deliverable | Done when | Depends on |
|---|---|---|---|
| 0 | This document | Reviewed | — |
| 1 | Catalog + adapters for the **existing** sources (Homebrew Hub, MAME, ScummVM) | `store list` shows every game installed by those sources today, with provenance; reinstalling one through `store get` is byte-identical | — |
| 2 | libretro-assets adapter + curated GitHub list | New entries for GameCube, N64, PS1, Mega Drive, SNES, Dreamcast, each with a recorded license; questionable items excluded with a reason | 1 |
| 3 | `store get/remove/health` on the ingest pipeline | `get` of a GameCube entry yields an `.rvz`, art and an ES-DE entry, and launches in Dolphin | 1; **`dolphin-tool`** (Arch package `dolphin-emu-tool`) |
| 4 | `/store` portal page (EN/ES) + API | Headless tests pass; real-GPU Brave check passes; Get works from the page | 3 |
| 5 | itch.io adapter | Free retro-tagged games list and install; paid ones are shown as "buy on itch.io" links only | 3; itch.io API key in `local.toml` |
| 6 | Purchased-content importers (Steam SEGA Classics first) | Owned install folder → identified, filed games | Confirm folder layout on a real install |
| 7 | Telesia linkage | Export carries provenance; IGDB/RA ids where available | Telesia gates U8, U14; PR #36 merged |
| 8 | Wii homebrew (Open Shop Channel) | Wii system in `systems.toml`, a few games installed | Confirm the Repository Manager API endpoint |

## 7. Risks and open questions

- **License clarity on libretro assets.** Hosting there doesn't by itself prove a free license; phase 2 must
  record a license per item or drop it.
- **"Top titles" are mostly commercial.** Free sources grow the library with good homebrew but won't cover
  Zelda or Metroid. Those come only from your own dumps or legitimate purchases (§4.2–4.3); the store should
  make that path easy, not imply otherwise.
- **itch.io terms.** Bulk downloading through the API should stay per-game and user-initiated. Don't mirror.
- **Disk budget.** GameCube entries average ~0.9 GB (systems.toml). The queue must check the budget per item,
  not per batch.
- **Source drift.** Endpoints change (Open Shop Channel's v2 shutdown is an example), hence the health panel
  and cached catalogs.

## 8. Out of scope

Any commercial ROM or BIOS download, DRM keys, torrent transport, account scraping, and mobile/Ayn Thor sync
(on hold until the local library is rich).
