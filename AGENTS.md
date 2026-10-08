# AGENTS.md: working on Omarchy Kit

Omarchy Kit is a bilingual (English / Spanish) learning portal and a set of reversible setup scripts for running Omarchy on a 15" MacBook Pro, mid-2014
(MacBookPro11,3). It is a **public** repository. Python standard library only; no build tools. Read [docs/INDEX.md](docs/INDEX.md) for the documentation map and
[llms.txt](llms.txt) for the machine-readable index (`llms-full.txt` is the whole documentation in one file).

## Map

| Path | What |
|---|---|
| `build_cheatsheet.py` | entry point: builds every page from the live Omarchy install (calls `build_setup.py` and `build_portal.py`) |
| `apps-helper`, `kitlive.py` | the local server on `127.0.0.1:8787` and its live data (theme CSS, hardware sampler, wallpaper) |
| `*.template.html`, `kit.js`, `kit.css`, `portal*.js`, `portal.css` | the pages and shared browser code |
| `portal_lessons.py`, `portal_content.py` | the learning path (6 levels), Mac habits, glossary, hardware cards |
| `build_setup.py` | the Setup log: live `checks()`, and the records of every change with its undo |
| `sleep/`, `power/`, `themes/`, `gpu/`, `audio/`, `keys/`, `trackpad/`, `appearance/`, `backup/`, `boot/`, `games/` | scripts that change the machine; each folder has a README |
| `test/` | `run-all`, hermetic Python tests, browser suites; see [test/README.md](test/README.md) |
| `docs/` | the documentation; [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) explains how it fits together |

Built `*.html`, `data/`, `backups/`, `local.toml` and `*.bak*` are git-ignored on purpose (they hold this machine's details).

## Commands

```bash
python3 build_cheatsheet.py            # rebuild every page
./apps-helper --no-open                # serve http://127.0.0.1:8787 (or: systemctl --user restart omarchy-kit)
test/run-all --fast                    # lint + every hermetic test (about 30 s, no browser, no root)
test/run-all                           # the same + the browser suites (needs the portal running and Chromium)
python3 scripts/build-llms             # regenerate llms-full.txt after any documentation change
```

After editing Python, **restart the service**: it keeps `build_setup` in memory and a rebuilt page would show old checks.

## Hard rules

1. **Never run a script you have not read the argument handling of, and never probe one with `--help`** to see its flags. Kit installers now refuse unknown options, but
   other scripts may treat any argument as "install".
2. **You cannot run `sudo`.** Give the owner the exact command (`! sudo path/to/script`) and verify the result afterwards. Never install something that lowers a security
   control (for example `sleep/install-hibernate-nolock`); the owner does that.
3. **Every change to the machine is undoable and recorded.** An installer with `--remove`, a record in `build_setup.py` (`LOG`) with the undo command, and a live check
   in `checks()` where possible. Installers are idempotent, print usage on `--help`, exit 2 on an unknown option, and fail closed.
4. **Everything user-visible is English and Spanish** (neutral Latin American Spanish; "reposo" for sleep, "hibernar", "sin actividad" for idle). Tests fail otherwise.
5. **Honest status.** State what was verified and how; do not claim a hardware effect that was not measured. Measure power with the terminal idle, on battery, and quote
   `charge_now / charge_full`, never the raw `capacity` ([docs/FIELD-NOTES.md](docs/FIELD-NOTES.md)).
6. **Public-repository hygiene.** No usernames, home paths, hostnames, MAC or IP addresses, network names, UUIDs, firmware dumps or private product names in code, docs,
   tests or **images**. Original art only: no official artwork, logos or character likenesses. Scan before every push.
7. **Do not push, merge or publish without the owner's explicit word.** Commit locally in small steps chained with `&&`.
8. **Verify for real.** Run the tests; for anything visual also use a real GPU Brave (`CDP_ATTACH=9334`), which catches rendering bugs headless Chromium misses. Run browser
   suites one at a time, kill only processes you started (check the working directory), and never `pkill -f` a pattern that also appears in your own command.
9. **Never rescan or remove PCI devices, or unload the `thunderbolt` driver,** on this machine; both broke it. `systemd` here reads sleep hooks only from
   `/usr/lib/systemd/system-sleep/`.

## Recipes and conventions

How to add a lesson, a Mac habit, a Setup row, an installer, a theme or a document: [docs/DEVELOPING.md](docs/DEVELOPING.md). Terms: [docs/GLOSSARY.md](docs/GLOSSARY.md).
Documents start with a TL;DR and end with a **Related** line; a new one must be listed in `docs/INDEX.md` and `llms.txt`. `test/test_docs.py` enforces this.

## Where to look for X

| Question | Document |
|---|---|
| How does the lid, sleep or hibernate work here? | [docs/SLEEP.md](docs/SLEEP.md) |
| Where does the battery go? | [docs/POWER-LAB.md](docs/POWER-LAB.md) |
| What did we change to feel like a Mac? | [docs/MAC-FEEL.md](docs/MAC-FEEL.md) |
| What are the themes and their licence? | [docs/THEMES.md](docs/THEMES.md) |
| What must I not do on this machine? | [docs/FIELD-NOTES.md](docs/FIELD-NOTES.md) |
| How is it built and served? | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) |
