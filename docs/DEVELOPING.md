# Developing Omarchy Kit

> **TL;DR.** `python3 build_cheatsheet.py` rebuilds every page; `./apps-helper` serves them; `test/run-all --fast` checks everything that
> does not need a browser; `test/run-all` adds the browser suites. Every user-facing string is English *and* Spanish, every change to the
> machine has an undo and a Setup log record, and installers refuse unknown options. Recipes for the common additions are below.

Related: [INDEX](INDEX.md) · [ARCHITECTURE](ARCHITECTURE.md) · [FIELD-NOTES](FIELD-NOTES.md) · [GLOSSARY](GLOSSARY.md) · [test/README](../test/README.md) · [AGENTS](../AGENTS.md)

## Set up

```bash
git clone https://github.com/aldoruizluna/omarchy-kit ~/labspace/omarchy-kit && cd ~/labspace/omarchy-kit
python3 build_cheatsheet.py            # builds every page from your live Omarchy install (needs `omarchy` on PATH)
./apps-helper                          # serves http://127.0.0.1:8787 (add --no-open to skip the browser)
```

Requirements: Omarchy 4 with a running user session; Python 3.11 or newer; Node 22 or newer for the browser tests; Chromium for the headless
runs. `python-pillow` and `librsvg` only matter for the theme wallpapers.

As a service (so the portal starts with your session): copy `omarchy-kit.service` to `~/.config/systemd/user/` and
`systemctl --user enable --now omarchy-kit`. **After editing any Python file, `systemctl --user restart omarchy-kit`**; the server keeps
`build_setup` in memory.

## The loop

| You changed | Run |
|---|---|
| `kit.js`, `kit.css`, `portal.js`, `portal-nav.js`, `portal.css`, `setup.template.html` | reload the browser (the server reads these on every request) |
| any other `*.template.html`, `portal_lessons.py`, `portal_content.py`, `build_portal.py`, `build_cheatsheet.py`, `apps.toml` | `python3 build_cheatsheet.py`, then reload |
| `apps-helper`, `kitlive.py`, `build_setup.py` | `systemctl --user restart omarchy-kit` (the server imports them once) |
| anything | `test/run-all --fast` before committing; `test/run-all` when pages changed |

## Conventions (the rules every change follows)

1. **Bilingual.** Every user-visible string has English and Spanish (neutral Latin American Spanish, tuteo). Use "reposo" for sleep,
   "hibernar" for hibernate, "sin actividad" for idle. Tests fail on a missing translation.
2. **Undoable and recorded.** A change to the machine gets an installer that takes `--remove`, and a record in `build_setup.py` (`LOG`) with the
   undo command, plus a live check in `checks()` where one is possible.
3. **Installers are safe to probe.** `--help` prints the header comment; an unknown option exits 2 and installs nothing. Root-only installers say so
   and are run by the owner with `sudo`. Never run an installer "just to see its flags".
4. **Fail closed.** A lock that cannot find its script still locks; an installer that cannot prove its precondition refuses.
5. **Honest status.** Say what was verified and how. Do not claim a hardware effect that was not measured (see [POWER-LAB](POWER-LAB.md)).
6. **Derive, don't hard-code.** Shortcuts come from Omarchy's binding descriptions; counts in prose are checked by `test/test_docs.py`.
7. **Public-repository hygiene.** No usernames, home paths, hostnames, MAC or IP addresses, network names, UUIDs or firmware dumps; no private
   product names (`KIT_PRIVATE_NAMES="a,b" node test/verify-store-page.mjs` checks a page against a list a maintainer supplies). Built pages, `data/`,
   `backups/`, `local.toml` and `*.bak*` stay git-ignored. Scan before every push, images included.
8. **Original art only.** Themes carry no official artwork, logos or character likenesses; they credit the open-source works that inspired them.
   Palettes, theme files and art are CC BY 4.0 ([themes/LICENSE](../themes/LICENSE)); code is MIT.
9. **Chain with `&&`.** An edit that fails midway must not let the commit after it proceed.

## Recipes

### Add a lesson or a step
1. Edit `portal_lessons.py`: add `{"id", "en", "es", "why": {"en","es"}, "steps": [S(en, es, ...)]}` to a level's `lessons`.
   `S(en, es, k=<binding description>, check=<type>, menu=<route>, cmd=<command chip>, cls=<window class regex>, re=<pattern>, box=True)`.
2. Check types are listed in [ARCHITECTURE](ARCHITECTURE.md#the-learning-engine). `typed` needs `re` and `box=True`; `cmd` is copy-only; never
   put a `sudo` command in `cmd`.
3. `python3 build_cheatsheet.py`, then `python3 -B -m unittest test.test_lessons` (both languages, known check types, menu routes, patterns) and
   `node test/verify-portal.mjs`.
4. Update the size assertion in `test/test_lessons.py` and the counts in the README; `test/test_docs.py` tells you if the README is stale.

### Add a Mac habit or a hardware card
`portal_content.py`: a row in `MAC` (`{"mac": {en, es}, "mk": "", "how": same|similar|different|none, "k": [binding descriptions], "note": {en, es}}`)
or a card in `HW` (`id`, `status`, titles, bilingual `body`, optional `live` and `cmd`).

### Add a Setup row (a live check)
1. A tuple in the right `STATUS` group of `build_setup.py`: `(key, title_en, title_es, todo_en, todo_es, command)`.
2. In `checks()`: `c["key"] = (status, "english detail", "detalle en español")` for every branch. Status is `ok`, `action`, `pending` or `info`.
3. A `LOG` record `(title_en, title_es, text_en, text_es, undo_command)` with what was done, how it was verified and how to undo it.
4. Restart the service and run `node test/verify-portal.mjs` (it fails if a row has no check or a log entry lacks a language).

### Add an installer
Copy the shape of `sleep/install-s2idle` or `power/install-wifi-powersave`: header comment (usage, why, undo), `set -eu`, the argument guard
(`case "${1:-}" in "" | --remove) ;; -h | --help) ...; *) ... exit 2`), a root check if needed, `--remove`, idempotent writes. Then: a Setup row and
record, a test in `test/test_sleep_power_themes.py` (the `Sandbox` helpers run it in a temporary directory with fake commands), and a line in the
folder README.

### Add a theme
A folder in `themes/<slug>/` with a complete `colors.toml` (copy the key set of an existing theme), the theme files, `preview.png`, and a `THEME.md`
with the palette rationale, a contrast table and credits. Add a generator to `themes/generators/` and an entry to `THEMES` in
`themes/make-wallpapers` if it has wallpapers; check text contrast is at least 4.5:1; `themes/install-themes <slug>`; apply it on the real desktop
and screenshot it; update [THEMES](THEMES.md).

### Add a document
Put it in `docs/`, start it with a one-paragraph **TL;DR** and a **Related** line, end it with a **Related** footer, list it in
[INDEX](INDEX.md) and `llms.txt`, then run `python3 scripts/build-llms` (regenerates `llms-full.txt`). `test/test_docs.py` fails if any of that is
missing or a link is broken.

## Tests

| Command | What |
|---|---|
| `test/run-all --fast` | lint, then every hermetic test (about 30 s) |
| `test/run-all` | the same, then the browser suites against the running portal |
| `python3 -B -m unittest discover -s test -p 'test_*.py'` | the hermetic tests alone |
| `node test/verify-portal.mjs [out-dir]` | all pages, lessons engine, palette, Setup log, accessibility, EN/ES |
| `CDP_ATTACH=9334 node test/verify-portal.mjs` | the same in a real GPU Brave started with `--remote-debugging-port=9334` |

Details of every suite: [test/README.md](../test/README.md). Pitfalls that cost time: [FIELD-NOTES](FIELD-NOTES.md).

## Commits

Small, chained with `&&`, messages that say what changed and what was verified. Do not push without the owner's word. Never commit built pages,
`data/`, or anything from the hygiene list above.

---

Related: [INDEX](INDEX.md) · [ARCHITECTURE](ARCHITECTURE.md) · [FIELD-NOTES](FIELD-NOTES.md) · [GLOSSARY](GLOSSARY.md) · [AGENTS](../AGENTS.md)
