# test/: what checks what

> **TL;DR.** `test/run-all --fast` runs a syntax lint and every hermetic test in about 30 s with no browser, no running service and no root. `test/run-all` adds the
> browser suites against the running portal. Hermetic means: temporary directories, fake commands in `PATH`, no network.

| File | Kind | Covers |
|---|---|---|
| `run-all` | runner | lint (`bash -n`, Python syntax), then the unit tests, then each `verify-*.mjs` if the portal answers; `--fast` skips the browser suites |
| `test_sleep_power_themes.py` | unit | every installer in `sleep/`, `power/`, `themes/` (install, twice, `--remove`, others' files untouched, refusal paths), `sleep-check`, `sleep-lock-policy`, `power-lab`, `make-wallpapers` (one real wallpaper per generator family) |
| `test_lessons.py` | unit | the learning path: both languages, known check types, answer patterns, menu routes, no privileged commands handed out |
| `test_docs.py` | unit | the documentation: links resolve, every doc is indexed, `llms.txt` and `llms-full.txt` are complete and current, README counts are true; with `KIT_PRIVATE_NAMES=a,b` also that no document names a private project |
| `test_store.py`, `test_personal.py` | unit | the store client and your-own-backups library (signed snapshots, rollback, checksums; local matching with sockets blocked) |
| `test_keyd.py` | unit | the keyboard pieces in `keys/`: the keyd configuration generator, the Hyprland-aware app helper (against fake sockets), `install-keyd` (as fake root in a namespace), `caps-lock`; with `KEYD_BIN` and `KEYD_SRC` also keyd's own checker and the real keyd engine (`keyd-trace.c`) |
| `test_macdesktop.py` | unit | the Mac look: `icons/install-icons` (wrong checksum installs nothing, idempotent, `--remove` never deletes a folder it did not create), the theme-set hook, `dock/install-dock`, `menubar/install-menubar` (layout moved and restored exactly, bad JSON untouched), and the contracts between the pieces (every QML file installed, every menu item id has a Lua action, `luac` and `qmllint` parse) |
| `test_macsweep.py` | unit | the Golden Gate themes (every colour key, text contrast of 4.5:1 or better, valid shell-section overrides, the window style), `look/install-look` (font rule, button layout saved and restored exactly, glass module), `look/mac-glass`, and that the font rule changes quickshell's monospace request and nothing else |
| `test_coadmin.py` | unit | `coadmin/`: the installer as fake root against a fixture home (refusals, dry run, groups, mode 700, the allowlist and the denylist both ways, path rewriting, enablement links, `--remove` only for accounts it created) and the first-login helper against fakes |
| `verify-portal.mjs` | browser | all 12 pages, nav, lessons engine, palette, Setup log (including Spanish), skip links, EN/ES, phone width |
| `verify-keyboard.mjs`, `verify-trackpad.mjs` | browser | the 3D keyboard and trackpad pages |
| `verify-mackeys.mjs` | real compositor | each ⌘ shortcut through `hyprctl eval`, reported by a scratch Brave window (needs Hyprland) |
| `verify-store-page.mjs` | browser | the Games page's store section, served from a throw-away static server; `KIT_PRIVATE_NAMES` guard |
| `cdp.mjs` | helper | a dependency-free Chrome DevTools driver; each headless run takes its own free port; `CDP_ATTACH=<port>` drives a real GPU Brave instead |
| `frames.mjs`, `idle.mjs`, `realshot.mjs`, `sweep.mjs` | tools | frame-rate probes, a real-browser screenshot, a camera-angle sweep (need `CDP_ATTACH`) |

Run one piece: `python3 -B -m unittest test.test_lessons`, `node test/verify-portal.mjs`, `CDP_ATTACH=9334 node test/verify-portal.mjs`. Every browser script prints usage with `--help`.

Rules from experience: run browser suites one at a time (a leftover browser used to leak into the next run, fixed by giving each its own port); never `pkill -f` a pattern that
also appears in your own command line. More in [docs/FIELD-NOTES](../docs/FIELD-NOTES.md).

---

Related: [docs/DEVELOPING](../docs/DEVELOPING.md) · [docs/FIELD-NOTES](../docs/FIELD-NOTES.md) · [docs/ARCHITECTURE](../docs/ARCHITECTURE.md) · [docs/INDEX](../docs/INDEX.md)
