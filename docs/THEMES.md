# Themes: Kawaii Bow, Mecha Unit, Solarpunk

Six complete Omarchy themes made for this kit, in three families. Each folder in `themes/` has a `colors.toml` palette (Omarchy's
templates turn it into terminal, bar, btop, Neovim, VS Code and lock-screen colours), five original 2880x1800 wallpapers, a preview
and a `THEME.md` with the palette rationale, a WCAG contrast table, and the **inspiration chain**.

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
themes/install-themes            # copies them to ~/.config/omarchy/themes (no root); switches nothing
omarchy theme set "Kawaii Bow"   # also: "Kawaii Bow Night", "Mecha Unit", "Mecha Unit Red", "Solarpunk", "Solarpunk Dusk"
omarchy theme set "Retro 82"     # back to the previous one
themes/install-themes --remove   # take the kit's themes out again (never touches anyone else's)
```
The portal's theme picker and the Omarchy menu list them as soon as they are installed.

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

## Open points

* **Licence for the original art and files.** The kit is MIT; the agents suggested CC0 or CC BY 4.0 for the wallpapers. Decide before
  publishing (see the Setup log open items).
* **Franchise words in two credit rows.** Mecha Unit credits two open-source works whose own names contain the franchise's words;
  strip those rows if you want zero textual link.
* **Weight.** The six themes add about 17 MB of JPEG wallpapers to the repository.
