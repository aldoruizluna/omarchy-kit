# Solarpunk (light) - Omarchy theme

**EN.** A sunlit-paper light theme: warm cream background, deep forest-green text (10.8:1), leaf-green, sky-teal and terracotta accents and a deep amber for yellow. Five original wallpapers: solar hills with wind turbines, green terraced towers with airships, an art-nouveau garden, a sun-ray fan and a leaf-circuit pattern.

**ES.** Un tema claro de papel soleado: fondo crema calido, texto verde bosque profundo (10.8:1), acentos verde hoja, turquesa cielo y terracota, y un ambar profundo como amarillo. Cinco fondos originales: colinas solares con aerogeneradores, torres verdes con terrazas y dirigibles, un jardin art nouveau, un abanico de rayos de sol y un patron hoja-circuito.

## Palette rationale / Razon de la paleta

**EN.** Optimistic eco-futurism on paper: the background is a warm cream (`#f6efd9`) rather than white, so long reading stays soft; text is deep forest green instead of black. ANSI hues are solved per hue to the same contrast (6.0:1, bright 4.8:1), which forces yellow into a deep amber (`#825700`) and keeps green, cyan and blue clearly distinct. Terracotta anchors the warm side (red, orange, brown); turquoise-green is the accent (4.6:1, passes the 3:1 UI rule with margin). `muted` and `dark_foreground` use a warm olive hue so comments feel organic.

**ES.** Ecofuturismo optimista sobre papel: el fondo es un crema calido (`#f6efd9`) y no blanco, para lecturas largas; el texto es verde bosque profundo, no negro. Cada tono ANSI se resuelve al mismo contraste (6.0:1, brillante 4.8:1), lo que lleva el amarillo a un ambar profundo (`#825700`) y mantiene verde, cian y azul bien distintos. La terracota ancla el lado calido (rojo, naranja, marron); el acento es un verde turquesa (4.6:1, supera con holgura el 3:1 de UI). `muted` y `dark_foreground` usan un oliva calido para que los comentarios se sientan organicos.

```toml
mode = "light"

accent = "#0c7a60"
selection = "#c6dca4"
muted = "#606f4d"

background = "#f6efd9"
dark_background = "#efe7cc"
darker_background = "#e3d9b8"
lighter_background = "#e8e7c3"

foreground = "#1f3a2b"
dark_foreground = "#7e8a64"
light_foreground = "#36573f"
bright_foreground = "#0f2a1b"

red = "#a33126"
yellow = "#825700"
orange = "#964b11"
green = "#396420"
cyan = "#0a6464"
blue = "#1c5f88"
magenta = "#8f3d6a"
brown = "#6b4a2f"

bright_red = "#c62c1e"
bright_yellow = "#916000"
bright_green = "#3c761a"
bright_cyan = "#047474"
bright_blue = "#146ea5"
bright_magenta = "#b3397c"

```

## WCAG 2.x contrast table (computed in Python, `relative luminance`, sRGB)

All text pairs are at or above 4.5:1; primary text is at or above 7:1. Failing pairs: none.

| Pair | FG | BG | Ratio | Needed | Result | Use |
|---|---|---|---|---|---|---|
| foreground / background | `#1f3a2b` | `#f6efd9` | 10.76:1 | 7:1 | pass | body text (AAA) |
| bright_foreground / background | `#0f2a1b` | `#f6efd9` | 13.36:1 | 7:1 | pass | cursor, bold text |
| light_foreground / background | `#36573f` | `#f6efd9` | 7.05:1 | 4.5:1 | pass | secondary text |
| foreground / dark_background | `#1f3a2b` | `#efe7cc` | 9.99:1 | 7:1 | pass | sidebars, status bars |
| foreground / lighter_background | `#1f3a2b` | `#e8e7c3` | 9.80:1 | 7:1 | pass | cursor line, menus |
| bright_foreground / selection | `#0f2a1b` | `#c6dca4` | 10.37:1 | 7:1 | pass | selected text |
| muted / background | `#606f4d` | `#f6efd9` | 4.71:1 | 4.5:1 | pass | ANSI bright black, comments |
| dark_foreground / background | `#7e8a64` | `#f6efd9` | 3.20:1 | 3:1 | pass | disabled/dim UI (decorative) |
| accent / background | `#0c7a60` | `#f6efd9` | 4.60:1 | 3:1 | pass | active border, prompt (UI >= 3) |
| red / background | `#a33126` | `#f6efd9` | 6.04:1 | 4.5:1 | pass | ANSI |
| orange / background | `#964b11` | `#f6efd9` | 5.52:1 | 4.5:1 | pass | ANSI |
| yellow / background | `#825700` | `#f6efd9` | 5.51:1 | 4.5:1 | pass | ANSI |
| green / background | `#396420` | `#f6efd9` | 6.05:1 | 4.5:1 | pass | ANSI |
| cyan / background | `#0a6464` | `#f6efd9` | 6.05:1 | 4.5:1 | pass | ANSI |
| blue / background | `#1c5f88` | `#f6efd9` | 6.01:1 | 4.5:1 | pass | ANSI |
| magenta / background | `#8f3d6a` | `#f6efd9` | 6.00:1 | 4.5:1 | pass | ANSI |
| bright_red / background | `#c62c1e` | `#f6efd9` | 4.83:1 | 4.5:1 | pass | ANSI bright |
| bright_yellow / background | `#916000` | `#f6efd9` | 4.71:1 | 4.5:1 | pass | ANSI bright |
| bright_green / background | `#3c761a` | `#f6efd9` | 4.81:1 | 4.5:1 | pass | ANSI bright |
| bright_cyan / background | `#047474` | `#f6efd9` | 4.86:1 | 4.5:1 | pass | ANSI bright |
| bright_blue / background | `#146ea5` | `#f6efd9` | 4.80:1 | 4.5:1 | pass | ANSI bright |
| bright_magenta / background | `#b3397c` | `#f6efd9` | 4.82:1 | 4.5:1 | pass | ANSI bright |
| brown / background | `#6b4a2f` | `#f6efd9` | 6.90:1 | 3:1 | pass | decorative accent |

Notes: Omarchy maps ANSI black to `background` and bright black to `muted`; the terminal search match paints `background` on `yellow`/`red`, so those pairs reuse the ratios above. `accent` is judged against the 3:1 rule for UI components.

## Files

- `THEME.md` - this file
- `backgrounds/1-sun-hills.jpg` - wallpaper 2880x1800 JPEG, drawn at install time
- `backgrounds/2-green-towers.jpg` - wallpaper 2880x1800 JPEG, drawn at install time
- `backgrounds/3-nouveau-garden.jpg` - wallpaper 2880x1800 JPEG, drawn at install time
- `backgrounds/4-sunray-fan.jpg` - wallpaper 2880x1800 JPEG, drawn at install time
- `backgrounds/5-circuit-leaf.jpg` - wallpaper 2880x1800 JPEG, drawn at install time
- `colors.toml` - palette (same 25 keys + `mode` as the stock themes)
- `icons.theme` - Yaru icon variant
- `preview-unlock.png` - lock-screen preview
- `preview.png` - 1800x1012 composite preview
- `unlock.png` - lock-screen wordmark (800x188 RGBA)

All wallpapers are 2880x1800 JPEG (<= 700 KB each) generated procedurally (Python, rsvg-convert, PIL; the generator is `themes/generators/solarpunk.py`, run by `themes/make-wallpapers`; the images are not stored in git). `neovim.lua` and `vscode.json` are intentionally omitted: Omarchy then generates the Neovim and VS Code themes from `colors.toml` through its templates (`/usr/share/omarchy/default/themed/*.tpl`), so they match this palette exactly instead of borrowing another theme's plugin.

## Install

```bash
cp -r solarpunk ~/.config/omarchy/themes/
omarchy theme set solarpunk      # or pick it in the Omarchy menu: Style > Theme
```

Preview without applying: `omarchy dev theme preview ~/.config/omarchy/themes/solarpunk --no-osc`.

## Inspiration chain (second degree)

This theme is inspired by open-source works that are themselves inspired by nature and by the solarpunk idea of a warm, hopeful, readable future. Nothing below was copied: no file, code, palette value or pixel. Palette values were re-derived with an equal-contrast solver and every composition was drawn from scratch. Licences are noted so that anyone who wants to build on these works can; "no licence found" means the repository had no LICENSE file or the GitHub API reported none (default copyright applies), which is one more reason we only took ideas.

### Editor and terminal palettes (palette ideas)

| Work | URL | Licence | Idea taken |
|---|---|---|---|
| Everforest (sainnhe) | https://github.com/sainnhe/everforest | MIT | Green-based scheme where warmth comes from a cream foreground and warm accents on a cool green ground; stepped background tiers (dark / darker / lighter); soft, narrow ANSI contrast band. Read via Omarchy's bundled `/usr/share/omarchy/themes/everforest/colors.toml`. Applied to: dusk foreground tint (`#ebe6c9`), background tiers. |
| Gruvbox Material (sainnhe) | https://github.com/sainnhe/gruvbox-material | MIT | "Softer contrast to protect the eyes" with warm earthy neutrals; cream-paper light background and an amber/gold accent. Applied to: warm olive `muted` / `dark_foreground` in the light variant, gold as the dusk accent, ANSI ratios held at 6-9:1 rather than maximal. |
| Open Color (yeun) | https://github.com/yeun/open-color | MIT | Hues tuned to the same perceived brightness per step. Applied to: a per-hue lightness solver so every ANSI hue lands on the same contrast ratio (6.0:1 normal / 4.8:1 bright in light; 6.3:1 / 8.8:1 in dusk). |
| Miasma (bundled with Omarchy) | `/usr/share/omarchy/themes/miasma` | ships with Omarchy; upstream licence not checked | Muted olive accent (`#78824b`) paired with a clay-orange warm colour (`#b36d43`) as a grounding pair. Applied to: terracotta/clay as the warm anchor next to leaf green. |

### Nearest Omarchy community themes (read their palettes, learned from strengths and gaps)

None of them is a light theme and none is named solarpunk; the official gallery has no solarpunk entry. All were read through their public repositories; contrast ratios below are computed by us from the values in their terminal configs.

| Community theme | URL | Licence | fg/bg | worst ANSI/bg | Good idea (kept as an idea) | Weak spot (what we avoid) |
|---|---|---|---|---|---|---|
| Green Garden | https://github.com/kalk-ak/omarchy-green-garden-theme | no licence file found | 10.8:1 | 3.7:1 | warm cream text on a deep green ground (our dusk direction) | dark only; the magenta slot is an orange, so the role is lost |
| Forest Green | https://github.com/abhijeet-swami/omarchy-forest-green-theme | MIT | 12.3:1 | 5.6:1 | keeps every ANSI hue true to its role inside a green world | default text is itself green (`#a8e6a1`), so green output barely stands out; dark only |
| Temerald | https://github.com/Ahmad-Mtr/omarchy-temerald-theme | MIT | 17.2:1 | 5.0:1 | mint as the cool companion to green; roles intact | neutral near-black ground, no sun or warmth; dark only |
| Stillwood | https://github.com/shresth-dwivedi/omarchy-stillwood-theme | MIT | 18.2:1 | 5.9:1 | warm cream text and sunlit yellow | the blue slot is an orange (`#f85a04`), red and blue nearly collide; dark only |
| Green City | https://github.com/zillamtt/omarchy-green-city | no licence found via GitHub API | 15.4:1 | 4.7:1 | a fully committed green mood | all six ANSI hues are greens (red is `#44B13E`), so error/ok/warn colours are indistinguishable; dark only |
| Evergarden | https://github.com/celsobenedetti/omarchy-evergarden | GPL-3.0 | 8.2:1 (selection text 1.6:1) | - | pale mint accent (`#B3E6DB`) and soft pastel contrast | soft pastel text on grey-green; dark only |
| Gold Rush | https://github.com/tahayvr/omarchy-gold-rush-theme | no licence found via GitHub API | 13.3:1 (selection text 3.4:1) | - | gold as a single confident accent (`#C9A227`) | gold-brown selection (`#926C15`) under light-grey text; neutral grey ground; dark only |

Sunset Drive (https://github.com/tahayvr/omarchy-sunset-drive-theme, no licence found via GitHub API) was read but not drawn on: its purple/blue night palette is off-topic.

What we took from them:

- Keep every ANSI hue recognisable (Forest Green does this well; Green City and Stillwood show the cost of not doing so): red stays terracotta/coral, green stays leaf/moss, yellow stays gold/amber, blue stays sky, magenta stays blossom, cyan stays teal (mint-teal in dusk, after Temerald and Evergarden's mint accents).
- Warmth through the foreground, not the background (Green Garden, Stillwood, Everforest): the dusk text is cream, not green-tinted, so green output keeps its own identity (Forest Green's weak spot).
- Never put light text on a gold or tan selection (Gold Rush, Evergarden): our selections are pale leaf green with near-black text (10.4:1) in light and mid forest green with cream text (8.4:1) in dusk.
- A single confident gold accent (Gold Rush) is right for dark grounds, but gold fails 3:1 on cream; the light variant therefore uses a turquoise-green accent and spends gold on wallpapers and the deep-amber yellow.
- The gap we fill: the first genuinely sunlit light theme, plus a matching dusk theme sharing hues, wallpapers' compositions and role mapping.

### Art references

| Work | URL | Licence | Idea taken |
|---|---|---|---|
| Ernst Haeckel, *Kunstformen der Natur* (1899-1904), scans on Wikimedia Commons | https://commons.wikimedia.org/wiki/Category:Kunstformen_der_Natur | Public domain (author d. 1919) | Radial symmetry and ornament-as-organism, reinterpreted in the sun-ray fan and the flower rosettes. No plate was traced or embedded. |
| Biodiversity Heritage Library botanical illustrations | https://www.biodiversitylibrary.org/ , https://www.flickr.com/photos/biodivlibrary/ | Public domain / "no known copyright restrictions" (per image; verify before reuse) | Pinnate leaf venation (midrib plus angled side veins) as the structural reference for the circuit-leaf wallpaper. No image was used. |

Art Nouveau (whiplash curves, framed borders) is an art-historical vocabulary, not a specific work. A search for an open-source solarpunk-branded terminal or editor theme found none; generic palette articles for "gold + green + terracotta + teal" are web content under unknown licences and were used only as a sanity check on hue families.

## Credits and licences

- Palette, wallpapers, preview and lock images: original work generated for this machine; no third-party artwork, screenshots or traced images are included. Licence for the art and palette: CC BY 4.0 (see `themes/LICENSE`).
- Fonts used only inside preview.png: JetBrainsMono Nerd Font (OFL-1.1), Noto Serif (OFL-1.1), Liberation Sans (OFL-1.1).
- Icon theme referenced by `icons.theme`: `Yaru-sage` (part of the Yaru icon set, CC-BY-SA-4.0 / GPL-3.0, installed system-wide, not redistributed here).
