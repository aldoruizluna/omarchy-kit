# Themes: Kawaii Bow, Mecha Unit, Solarpunk

> **TL;DR.** Six original Omarchy themes in three families (Kawaii Bow, Mecha Unit, Solarpunk), each with a light or dark partner. Palettes are re-derived and checked for contrast, wallpapers are drawn by generators when you install, and the looks are inspired in the second degree by credited open-source works. Licence: CC BY 4.0.

Related: [themes/README](../themes/README.md) · [DEVELOPING](DEVELOPING.md#add-a-theme) · [MAC-FEEL](MAC-FEEL.md) · [INDEX](INDEX.md)

Six complete Omarchy themes made for this kit, in three families. Each folder in `themes/` has a `colors.toml` palette (Omarchy's
templates turn it into terminal, bar, btop, Neovim, VS Code and lock-screen colours), a preview and a `THEME.md` with the palette
rationale, a WCAG contrast table, and the **inspiration chain**. The five original 2880x1800 wallpapers of each theme are not stored:
generator scripts in `themes/generators/` draw them when you install the theme (about 7 seconds per theme).

| Theme | Mode | Background | Text | Accent | Idea |
|---|---|---|---|---|---|
| **Kawaii Bow** (`kawaii-bow`) | light | `#fff6f8` | `#43202d` | `#c1082c` | Strawberry-milk pinks, cream, a bow-red accent, baby blue and butter yellow. |
| **Kawaii Bow Night** (`kawaii-bow-night`) | dark | `#2a1226` | `#ffe9f0` | `#fd6776` | The same sweets after dark: deep berry-plum ground with pink and mint. |
| **Mecha Unit** (`mecha-unit`) | dark | `#0b0614` | `#d7f2ff` | `#a874ff` | Black-violet command centre, industrial purple and acid green, warning orange. |
| **Mecha Unit Red** (`mecha-unit-red`) | dark | `#0d0510` | `#ffeee6` | `#ff5a36` | The same console, red/orange-led. |
| **Solarpunk** (`solarpunk`) | light | `#f6efd9` | `#1f3a2b` | `#0c7a60` | Sunlit cream paper, leaf green, sun gold and sky teal: a genuinely light theme. |
| **Solarpunk Dusk** (`solarpunk-dusk`) | dark | `#10261e` | `#ebe6c9` | `#f2c14e` | A bio-lit garden at dusk: forest green ground with gold and mint. |

## How to try them

```
themes/install-themes            # copies them to ~/.config/omarchy/themes and draws their wallpapers (no root); switches nothing
omarchy theme set "Kawaii Bow"   # also: "Kawaii Bow Night", "Mecha Unit", "Mecha Unit Red", "Solarpunk", "Solarpunk Dusk"
omarchy theme set "Retro 82"     # back to the previous one
themes/install-themes --remove   # take the kit's themes out again (never touches anyone else's)
```
The portal's theme picker and the Omarchy menu list them as soon as they are installed.

Drawing the wallpapers needs `python-pillow` and `librsvg` (`sudo pacman -S python-pillow librsvg`). Without them the theme still installs
and its colours work; install the two packages and run `themes/install-themes` again. Other commands:

```
themes/make-wallpapers                  # draw all six themes into themes/<theme>/backgrounds/ (git-ignored), for looking at them
themes/make-wallpapers --only 2 solarpunk   # just wallpaper 2 of one theme, a quick check
themes/install-themes --no-wallpapers   # install the colours only
```
Reinstalling never deletes wallpapers it cannot redraw: if drawing fails, the previous ones are kept. The drawing is deterministic
(the same art every time, apart from a little film grain on Kawaii Bow), so a reinstall gives back the same images.

## Where the looks come from (second-degree inspiration)

The aim was to be true to each muse without a direct link to the original. So every theme is inspired by **open-source works that are
themselves inspired by it**: pastel and kawaii colour systems and Neovim schemes (for Kawaii Bow), purple-and-neon HUD and terminal
themes, hexagon-field and command-centre UI kits (for Mecha Unit), and nature-inspired editor themes plus public-domain botanical
illustration as an idea source (for Solarpunk). Nothing was copied: palettes were re-derived (in OKLCH with an equal-contrast
solver) and all art was generated for the kit with Python and SVG. Each `THEME.md` lists what it drew on, with URL, licence and the
idea taken, including the weak spots of each neighbour that these themes were built to fix.

The community gallery (https://learn.omacom.io/2/the-omarchy-manual/90/extra-themes) has no Hello Kitty, Evangelion or solarpunk
theme; the nearest neighbours are credited in each THEME.md, not used.

## What was checked

* Palette: every colors.toml has the complete key set; text contrast is at least 4.5:1 everywhere (foreground 10.8:1 to 17.8:1), computed
  independently of the agents that wrote them.
* Each theme renders with `omarchy dev theme preview`.
* Each theme was **applied to the live desktop** and screenshotted (terminal, bar, window borders, wallpaper): no Hyprland config
  errors, then the previous theme was restored.
* Privacy: no personal strings in any file or image, and no image metadata.
* Wallpapers viewed one by one: generic bows, hearts, strawberries, hexagon grids, hazard stripes, rooftop gardens; no character
  likeness, logo or official mark.

## Licence and decisions

* **Licence: CC BY 4.0** for the palettes, the theme files made from them, the previews, the wallpapers and the `THEME.md` texts
  (`themes/LICENSE`). You may share and adapt them, even commercially, with credit. A suitable line: *Omarchy Kit themes by Aldo Ruiz
  Luna, https://github.com/aldoruizluna/omarchy-kit, CC BY 4.0*. The generator scripts are code and stay under the repository's MIT
  licence. The works credited in each `THEME.md` only inspired the looks; nothing of theirs was copied.
* **Franchise words in two credit rows: kept.** Mecha Unit credits two open-source works whose own names contain the franchise's words
  (a Blender theme and an Obsidian theme). They stay for honest provenance.
* **Wallpapers are generated, not stored** (decided 2026-10-07). The working tree dropped about 12 MB of JPEGs. The repository history
  still contains the original images (commit `964f30e`), so a fresh clone is not smaller unless that history is rewritten, which would
  need a force-push of the public repository and has not been done.

---

Related: [themes/README](../themes/README.md) · [DEVELOPING](DEVELOPING.md#add-a-theme) · [MAC-FEEL](MAC-FEEL.md) · [INDEX](INDEX.md)
