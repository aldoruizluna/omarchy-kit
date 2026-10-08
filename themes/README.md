# themes/: six original Omarchy themes

> **TL;DR.** Kawaii Bow (light and night), Mecha Unit (purple and red) and Solarpunk (light and dusk). Each folder is a complete Omarchy theme
> (`colors.toml` plus the theme files). The wallpapers are **not stored**: generators in `generators/` draw them when you install.
> Palettes, theme files, previews, wallpapers and texts are **CC BY 4.0** ([LICENSE](LICENSE)); the scripts are MIT.

| Path | What |
|---|---|
| `kawaii-bow/`, `kawaii-bow-night/`, `mecha-unit/`, `mecha-unit-red/`, `solarpunk/`, `solarpunk-dusk/` | one theme each: `colors.toml`, `btop.theme`, `hyprland.lua`, `chromium.theme`, `icons.theme`, previews, and a `THEME.md` with the palette rationale, a contrast table and the credits |
| `generators/` | `kawaii.py`, `solarpunk.py`, `mecha/`: seeded generators (Pillow, plus `rsvg-convert` for the first two) with one interface: `variant OUTDIR [number]` |
| `make-wallpapers` | draws any or all themes; `--out`, `--only`, `--jobs`, `--list`; about 43 s for all 30 images |
| `install-themes` | copies the themes to `~/.config/omarchy/themes`, draws each one's wallpapers, copies the licence; never touches themes it did not install; switches nothing. `--list`, `--remove`, `--no-wallpapers` |
| `LICENSE` | the CC BY 4.0 notice and a suitable credit line |

## Use

```bash
sudo pacman -S python-pillow librsvg     # only needed for the wallpapers
themes/install-themes                    # no root; about 8 s per theme
omarchy theme set "Solarpunk"            # also "Kawaii Bow", "Kawaii Bow Night", "Mecha Unit", "Mecha Unit Red", "Solarpunk Dusk"
themes/install-themes --remove           # take the kit's themes out again
```

If drawing fails, a theme still installs (its colours work) and any wallpapers from an earlier install are kept.

## Checked by

Setup log row **The kit's own themes (Kawaii Bow, Mecha Unit, Solarpunk)** (also flags a theme installed without wallpapers); `test/test_sleep_power_themes.py` (installer with a stand-in
generator, the `make-wallpapers` command line, one real wallpaper per generator family, no images tracked in git).

---

Related: [docs/THEMES](../docs/THEMES.md) · [docs/DEVELOPING](../docs/DEVELOPING.md#add-a-theme) · [docs/ARCHITECTURE](../docs/ARCHITECTURE.md) · [docs/INDEX](../docs/INDEX.md)
