# Solarpunk Dusk (dark) - Omarchy theme

**EN.** A bio-lit garden at dusk: deep forest-green background, warm cream text (12.7:1), sun-gold accent, mint, moss and sky-teal ANSI colours and soft coral and clay for warm tones. Five original wallpapers: dusk hills with glowing turbines, lit green towers and airships, a night art-nouveau garden, a sun-ray fan and a glowing leaf-circuit.

**ES.** Un jardin bioluminiscente al anochecer: fondo verde bosque profundo, texto crema calido (12.7:1), acento dorado sol, colores ANSI menta, musgo y turquesa cielo, y coral y arcilla suaves para los calidos. Cinco fondos originales: colinas al atardecer con turbinas luminosas, torres verdes iluminadas con dirigibles, un jardin art nouveau nocturno, un abanico de rayos de sol y una hoja-circuito luminosa.

## Palette rationale / Razon de la paleta

**EN.** A deep green ground (`#10261e`) instead of neutral black keeps the forest mood; warmth comes from the cream foreground and the sun-gold accent (`#f2c14e`, 9.5:1). ANSI hues are solved per hue to 6.3:1 (bright 8.8:1) so nothing glares: moss green, mint-teal, sky blue, blossom pink, soft coral and clay orange. Background tiers (`darker` / `dark` / `lighter`) give panels depth without extra hues; `selection` is a mid forest green that keeps selected text above 7:1.

**ES.** Un fondo verde profundo (`#10261e`) en lugar de negro neutro conserva el ambiente de bosque; la calidez viene del texto crema y del acento dorado sol (`#f2c14e`, 9.5:1). Cada tono ANSI se resuelve a 6.3:1 (brillante 8.8:1) para que nada deslumbre: verde musgo, turquesa menta, azul cielo, rosa flor, coral suave y naranja arcilla. Los niveles de fondo (`darker` / `dark` / `lighter`) dan profundidad sin tonos extra; `selection` es un verde bosque medio que mantiene el texto seleccionado sobre 7:1.

```toml
mode = "dark"

accent = "#f2c14e"
selection = "#215040"
muted = "#739679"

background = "#10261e"
dark_background = "#0b1c15"
darker_background = "#07130e"
lighter_background = "#183629"

foreground = "#ebe6c9"
dark_foreground = "#5c7b69"
light_foreground = "#bccaa8"
bright_foreground = "#faf5dc"

red = "#ec877d"
yellow = "#d89709"
orange = "#f28836"
green = "#64b733"
cyan = "#33b69b"
blue = "#49ace9"
magenta = "#de88b7"
brown = "#916741"

bright_red = "#f6afa8"
bright_yellow = "#ffb20a"
bright_green = "#7bd747"
bright_cyan = "#47d7ba"
bright_blue = "#81c9f5"
bright_magenta = "#edafd1"

```

## WCAG 2.x contrast table (computed in Python, `relative luminance`, sRGB)

All text pairs are at or above 4.5:1; primary text is at or above 7:1. Failing pairs: none.

| Pair | FG | BG | Ratio | Needed | Result | Use |
|---|---|---|---|---|---|---|
| foreground / background | `#ebe6c9` | `#10261e` | 12.67:1 | 7:1 | pass | body text (AAA) |
| bright_foreground / background | `#faf5dc` | `#10261e` | 14.54:1 | 7:1 | pass | cursor, bold text |
| light_foreground / background | `#bccaa8` | `#10261e` | 9.22:1 | 4.5:1 | pass | secondary text |
| foreground / dark_background | `#ebe6c9` | `#0b1c15` | 14.02:1 | 7:1 | pass | sidebars, status bars |
| foreground / lighter_background | `#ebe6c9` | `#183629` | 10.44:1 | 7:1 | pass | cursor line, menus |
| bright_foreground / selection | `#faf5dc` | `#215040` | 8.38:1 | 7:1 | pass | selected text |
| muted / background | `#739679` | `#10261e` | 4.83:1 | 4.5:1 | pass | ANSI bright black, comments |
| dark_foreground / background | `#5c7b69` | `#10261e` | 3.41:1 | 3:1 | pass | disabled/dim UI (decorative) |
| accent / background | `#f2c14e` | `#10261e` | 9.49:1 | 3:1 | pass | active border, prompt (UI >= 3) |
| red / background | `#ec877d` | `#10261e` | 6.32:1 | 4.5:1 | pass | ANSI |
| orange / background | `#f28836` | `#10261e` | 6.34:1 | 4.5:1 | pass | ANSI |
| yellow / background | `#d89709` | `#10261e` | 6.34:1 | 4.5:1 | pass | ANSI |
| green / background | `#64b733` | `#10261e` | 6.35:1 | 4.5:1 | pass | ANSI |
| cyan / background | `#33b69b` | `#10261e` | 6.30:1 | 4.5:1 | pass | ANSI |
| blue / background | `#49ace9` | `#10261e` | 6.34:1 | 4.5:1 | pass | ANSI |
| magenta / background | `#de88b7` | `#10261e` | 6.31:1 | 4.5:1 | pass | ANSI |
| bright_red / background | `#f6afa8` | `#10261e` | 8.81:1 | 4.5:1 | pass | ANSI bright |
| bright_yellow / background | `#ffb20a` | `#10261e` | 8.82:1 | 4.5:1 | pass | ANSI bright |
| bright_green / background | `#7bd747` | `#10261e` | 8.84:1 | 4.5:1 | pass | ANSI bright |
| bright_cyan / background | `#47d7ba` | `#10261e` | 8.87:1 | 4.5:1 | pass | ANSI bright |
| bright_blue / background | `#81c9f5` | `#10261e` | 8.81:1 | 4.5:1 | pass | ANSI bright |
| bright_magenta / background | `#edafd1` | `#10261e` | 8.84:1 | 4.5:1 | pass | ANSI bright |
| brown / background | `#916741` | `#10261e` | 3.20:1 | 3:1 | pass | decorative accent |

Notes: Omarchy maps ANSI black to `background` and bright black to `muted`; the terminal search match paints `background` on `yellow`/`red`, so those pairs reuse the ratios above. `accent` is judged against the 3:1 rule for UI components.

## Files

- `THEME.md` - this file
- `backgrounds/1-sun-hills.jpg` - wallpaper 2880x1800 JPEG
- `backgrounds/2-green-towers.jpg` - wallpaper 2880x1800 JPEG
- `backgrounds/3-nouveau-garden.jpg` - wallpaper 2880x1800 JPEG
- `backgrounds/4-sunray-fan.jpg` - wallpaper 2880x1800 JPEG
- `backgrounds/5-circuit-leaf.jpg` - wallpaper 2880x1800 JPEG
- `colors.toml` - palette (same 25 keys + `mode` as the stock themes)
- `icons.theme` - Yaru icon variant
- `preview-unlock.png` - lock-screen preview
- `preview.png` - 1800x1012 composite preview
- `unlock.png` - lock-screen wordmark (800x188 RGBA)

All wallpapers are 2880x1800 JPEG (<= 700 KB each) generated procedurally (Python, rsvg-convert, PIL; the generator script is not shipped in this folder). `neovim.lua` and `vscode.json` are intentionally omitted: Omarchy then generates the Neovim and VS Code themes from `colors.toml` through its templates (`/usr/share/omarchy/default/themed/*.tpl`), so they match this palette exactly instead of borrowing another theme's plugin.

## Install

```bash
cp -r solarpunk-dusk ~/.config/omarchy/themes/
omarchy theme set solarpunk-dusk      # or pick it in the Omarchy menu: Style > Theme
```

Preview without applying: `omarchy dev theme preview ~/.config/omarchy/themes/solarpunk-dusk --no-osc`.

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

- Palette, wallpapers, preview and lock images: original work generated for this machine; no third-party artwork, screenshots or traced images are included. Suggested licence for the art and palette: CC0 1.0 (the owner of this repository decides).
- Fonts used only inside preview.png: JetBrainsMono Nerd Font (OFL-1.1), Noto Serif (OFL-1.1), Liberation Sans (OFL-1.1).
- Icon theme referenced by `icons.theme`: `Yaru-prussiangreen` (part of the Yaru icon set, CC-BY-SA-4.0 / GPL-3.0, installed system-wide, not redistributed here).
