# games/: a retro library inside a disk budget

> **TL;DR.** `kit-games` organises RetroArch, ES-DE and Dolphin over `~/Games`, benchmarked for this MacBook, within half the free disk. Free games come from their official
> sources. A store client reads a signed catalog snapshot and only ever installs free games. Commercial ROMs are never fetched, hosted or listed as files.

| File | What |
|---|---|
| `kit-games` | `init`, `scan`, `art`, `budget`, `bios`, `status`, `ingest` (identify your own dumps and compress them), `esde`, `dolphin`, `cabinet`, `export-telesia`, `store ...` |
| `systems.toml` | the plan: per system the folder, libretro database, best core here, target size and tier |
| `fetch-homebrew` | the best-ranked finished homebrew from Homebrew Hub, with cover art and author credits (`HOMEBREW-CREDITS.md`) |
| `fetch-freeware` | ScummVM freeware adventures, the MAME-permitted arcade ROMs and open-source GameCube homebrew, with credits |
| `storelib.py` | the store client: verifies a snapshot (checksum, ECDSA P-256 signature with a publisher key you saved, version newer than yours), then installs free games |
| `personallib.py` | your own backups: locations you register are scanned and matched locally against libretro databases; nothing is uploaded and the lists cannot be shared |

Run `games/kit-games` with no argument for the usage. The long-form description is in the README's [Retro gaming](../README.md#retro-gaming) section; dumping your own
games is in [docs/DUMPING-GUIDE](../docs/DUMPING-GUIDE.md); the store's design is in [docs/GAME-STORE-ROADMAP](../docs/GAME-STORE-ROADMAP.md).

Checked by: Setup log rows **RetroArch tuned for this GPU**, **GameCube (Dolphin) tuned for this GPU**, **Game library within its budget**, **Free games store (signed catalog)**, **Your own backups (recognised on this machine)**; `test/test_store.py`, `test/test_personal.py`,
`test/verify-store-page.mjs`.

---

Related: [docs/DUMPING-GUIDE](../docs/DUMPING-GUIDE.md) · [docs/GAME-STORE-ROADMAP](../docs/GAME-STORE-ROADMAP.md) · [docs/ARCHITECTURE](../docs/ARCHITECTURE.md) · [docs/INDEX](../docs/INDEX.md)
