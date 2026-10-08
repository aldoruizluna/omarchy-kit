# Kawaii Bow Night

**EN.** A dark Omarchy theme inspired by a kawaii red-bow pastel look: strawberry-milk pinks and cream, a bow-red accent, with baby blue and butter yellow as secondary pops. It is cute but built to be read: body text is at least 7:1 on the background, every ANSI colour is at least 4.5:1 on every surface, and the accent clears 4.5:1 too. Five original wallpapers (2880x1800), a preview, btop, border and lock-screen assets are included. Neovim and VS Code colours are generated from the palette by Omarchy itself.

**ES.** Un tema de Omarchy oscuro inspirado en un estilo kawaii pastel con moño rojo: rosas "leche de fresa" y crema, acento rojo moño, con azul cielo y amarillo mantequilla como toques secundarios. Es tierno pero legible: el texto tiene al menos 7:1 de contraste con el fondo, cada color ANSI tiene al menos 4.5:1 sobre todas las superficies y el acento tambien supera 4.5:1. Incluye cinco fondos originales (2880x1800), vista previa y recursos de btop, bordes y pantalla de bloqueo. Los colores de Neovim y VS Code los genera Omarchy a partir de la paleta.

## Palette rationale

- **Base**: `#2a1226` is a pink-tinted deep berry-plum rather than pure black, with `dark_background`, `darker_background`, `lighter_background` and `selection` as a small ramp of the same hue so panels stay distinguishable without harsh edges.
- **Text**: pale strawberry-milk `#ffe9f0` (never plain white); `muted` and `dark_foreground` form the quiet tier and still clear 4.5:1.
- **Accent**: `#fd6776` is the bow red (lit coral), also used for window borders (gradient to pink) and btop highlights.
- **ANSI**: red, orange, yellow (butter), green (mint), cyan, blue (baby blue), magenta (strawberry pink) each keep their own hue family. They are solved in OKLCH at equal contrast, then brights use a small hue shift and higher lightness, lower chroma so the two tiers stay distinct.
- **Secondary pops**: baby blue (`blue`) and butter yellow (`yellow`) stay close to their pastel originals because the dark background lets them.

## Palette (`colors.toml`)

| key | value |
|---|---|
| `mode` | `dark` |
| `accent` | `#fd6776` |
| `selection` | `#4a2145` |
| `muted` | `#b98ba1` |
| `background` | `#2a1226` |
| `dark_background` | `#220e1f` |
| `darker_background` | `#190a17` |
| `lighter_background` | `#401d3b` |
| `foreground` | `#ffe9f0` |
| `dark_foreground` | `#c996ad` |
| `light_foreground` | `#f6cfdd` |
| `bright_foreground` | `#fff8fb` |
| `red` | `#fe9fa7` |
| `yellow` | `#fed48c` |
| `orange` | `#fda670` |
| `green` | `#7be0a8` |
| `cyan` | `#4be3eb` |
| `blue` | `#8ec2fd` |
| `magenta` | `#fa9bc9` |
| `brown` | `#d19e87` |
| `bright_red` | `#ffc0c4` |
| `bright_yellow` | `#fff0bb` |
| `bright_green` | `#a6efce` |
| `bright_cyan` | `#a0eeff` |
| `bright_blue` | `#a7dafe` |
| `bright_magenta` | `#f9bde4` |

## WCAG 2.x contrast (computed in Python, relative luminance)

Targets: body text >= 7:1 (AAA), text colours >= 4.5:1 (AA), accent vs background >= 3:1 (UI). `lighter_bg` is a border/inactive-surface colour, shown for completeness. Failing pairs found during tuning were fixed, not documented.

**Foreground roles**

| role | hex | background | dark_bg | darker_bg | lighter_bg | selection | level (min of bg/dark/darker/selection) |
|---|---|---|---|---|---|---|---|
| `foreground` | `#ffe9f0` | 14.98 | 15.79 | 16.56 | 12.47 | 11.39 | AAA |
| `bright_foreground` | `#fff8fb` | 16.55 | 17.44 | 18.30 | 13.78 | 12.59 | AAA |
| `light_foreground` | `#f6cfdd` | 12.27 | 12.94 | 13.57 | 10.22 | 9.34 | AAA |
| `dark_foreground` | `#c996ad` | 6.97 | 7.34 | 7.70 | 5.80 | 5.30 | AA |
| `muted` | `#b98ba1` | 5.99 | 6.32 | 6.63 | 4.99 | 4.56 | AA |

**Accent**

| role | hex | background | dark_bg | darker_bg | lighter_bg | selection | level |
|---|---|---|---|---|---|---|---|
| `accent` | `#fd6776` | 6.08 | 6.41 | 6.73 | 5.06 | 4.63 | AA |

**ANSI colours (text on surfaces)**

| ANSI role | hex | OKLCH L / C / h | background | dark_bg | darker_bg | lighter_bg | selection | level |
|---|---|---|---|---|---|---|---|---|
| `red` | `#fe9fa7` | 0.80 / 0.113 / 14 | 8.85 | 9.33 | 9.78 | 7.37 | 6.73 | AA |
| `orange` | `#fda670` | 0.80 / 0.124 / 52 | 8.96 | 9.44 | 9.90 | 7.46 | 6.81 | AA |
| `yellow` | `#fed48c` | 0.89 / 0.101 / 80 | 12.37 | 13.05 | 13.68 | 10.30 | 9.41 | AAA |
| `green` | `#7be0a8` | 0.83 / 0.125 / 158 | 10.78 | 11.36 | 11.91 | 8.97 | 8.20 | AAA |
| `cyan` | `#4be3eb` | 0.84 / 0.125 / 200 | 11.12 | 11.72 | 12.29 | 9.26 | 8.46 | AAA |
| `blue` | `#8ec2fd` | 0.80 / 0.101 / 252 | 9.30 | 9.81 | 10.29 | 7.75 | 7.08 | AAA |
| `magenta` | `#fa9bc9` | 0.80 / 0.126 / 350 | 8.74 | 9.21 | 9.66 | 7.27 | 6.65 | AA |
| `brown` | `#d19e87` | 0.74 / 0.069 / 45 | 7.38 | 7.78 | 8.16 | 6.14 | 5.61 | AA |
| `bright_red` | `#ffc0c4` | 0.87 / 0.073 / 14 | 11.20 | 11.81 | 12.39 | 9.33 | 8.52 | AAA |
| `bright_yellow` | `#fff0bb` | 0.95 / 0.070 / 94 | 15.20 | 16.02 | 16.80 | 12.65 | 11.56 | AAA |
| `bright_green` | `#a6efce` | 0.90 / 0.086 / 165 | 13.07 | 13.78 | 14.46 | 10.89 | 9.95 | AAA |
| `bright_cyan` | `#a0eeff` | 0.90 / 0.080 / 213 | 13.33 | 14.05 | 14.74 | 11.10 | 10.14 | AAA |
| `bright_blue` | `#a7dafe` | 0.87 / 0.073 / 239 | 11.63 | 12.26 | 12.85 | 9.68 | 8.84 | AAA |
| `bright_magenta` | `#f9bde4` | 0.86 / 0.085 / 340 | 11.07 | 11.67 | 12.24 | 9.22 | 8.42 | AAA |

**Selection and extra pairs**

| pair | ratio | level |
|---|---|---|
| foreground on selection | 11.39 | AAA |
| bright_foreground on selection | 12.59 | AAA |
| foreground on lighter_bg | 12.47 | AAA |
| accent border on background (UI) | 6.08 | AA |
| accent on selection (btop selected_fg) | 4.63 | AA |

Result: no failing pair.

## Files

| file | size | what it is |
|---|---|---|
| `backgrounds/1-bow-garden.jpg` | 419 KB | original wallpaper 2880x1800 (JPEG) |
| `backgrounds/2-gingham-picnic.jpg` | 360 KB | original wallpaper 2880x1800 (JPEG) |
| `backgrounds/3-polka-clouds.jpg` | 344 KB | original wallpaper 2880x1800 (JPEG) |
| `backgrounds/4-ribbon-waves.jpg` | 386 KB | original wallpaper 2880x1800 (JPEG) |
| `backgrounds/5-strawberry-patch.jpg` | 433 KB | original wallpaper 2880x1800 (JPEG) |
| `btop.theme` | 3 KB | btop colours (box outlines: bow red / baby blue / butter / pink) |
| `chromium.theme` | 0 KB | browser chrome colour (background RGB) |
| `colors.toml` | 1 KB | palette (same key set as the bundled themes); every other generated config derives from it |
| `hyprland.lua` | 0 KB | active window border: bow red to pink gradient |
| `icons.theme` | 0 KB | icon theme name (installed Yaru variant) |
| `preview.png` | 605 KB | 1800x1012 composite: wallpaper, bar, terminal, btop, swatches, launcher (PIL) |
| `unlock.png` | 2 KB | lock-screen wordmark recoloured with the accent |
| `THEME.md` | - | this file |

Total: 2.5 MB. `neovim.lua` and `vscode.json` are intentionally absent: without them Omarchy generates a palette-matched Neovim config (aether.nvim) and a local VS Code theme from `colors.toml`, which is better than pointing at an extension that does not exist for this palette.

## How to install

```bash
cp -r kawaii-bow-night ~/.config/omarchy/themes/
omarchy theme set kawaii-bow-night
```

Preview without applying anything: `omarchy dev theme preview ./kawaii-bow-night --no-osc`. Remove with `rm -r ~/.config/omarchy/themes/kawaii-bow-night`.

## Credits and licences

- Palette, config files, `THEME.md`: original work for this machine. Licence to be chosen by the owner (suggested: MIT for config, CC BY 4.0 for wallpapers).
- Wallpapers and `preview.png`: original, generated by script (Python/PIL and `rsvg-convert` SVG). The bows, hearts, sparkles, clouds and strawberries are generic vector shapes. No third-party artwork, logo, screenshot or character image was downloaded, copied, traced or embedded.
- `unlock.png`: the stock Omarchy lock-screen wordmark (Omarchy is MIT-licensed) recoloured with this theme's accent.
- `preview.png` text is rendered with JetBrains Mono Nerd Font and Noto Sans (SIL OFL).
- Not affiliated with or endorsed by any brand; "inspired by" a general kawaii aesthetic only.

## Inspiration chain (second degree)

This theme is only a second-degree inspiration: the look is described in general terms ("kawaii red-bow pastel", "strawberry-milk pinks") and every colour, composition and wallpaper was re-derived and drawn from scratch. Open-source works below were read for *ideas only*; no file, code or artwork was copied. Licences are as shown on each project's page when it was read.

| Work | URL | Licence | Idea taken (and re-derived here) |
|---|---|---|---|
| lawvs/pastel (kawaii-inspired OKLCH colour system) | https://github.com/lawvs/pastel | MIT | Work in OKLCH with tiers: a "kawaii" tier (high lightness 0.82-0.9, low chroma 0.08-0.14) for dark UIs and a "high-contrast" tier (lightness 0.4-0.6, higher chroma) for light UIs. Night uses the pastel tier, light uses the high-contrast tier, so each hue lands at equal contrast instead of equal RGB lightness. |
| meowsoot.nvim (pink/lavender/cyan Neovim scheme) | https://github.com/marekh19/meowsoot.nvim | MIT | Aim for AAA contrast on the main background, three lightness tiers per accent (standard / bright / quiet), author colours in a perceptual space, and fixed roles per hue. Night ANSI colours are >= 7:1 on the main surfaces, brights >= 9.5:1, muted/quiet tier >= 4.5:1. |
| Catppuccin (Latte flavour, bundled with Omarchy) | https://github.com/catppuccin/catppuccin | MIT | "Colorfulness, balance, harmony": a tinted (not pure white/black) base and tinted text. The light variant uses a berry-brown text colour on a strawberry-milk base instead of black on white. Its weakness (7 of its 12 hue/muted colours under 4.5:1 on the base) is what the equal-contrast solver here avoids. |
| Rose Pine (Dawn flavour, bundled with Omarchy) | https://github.com/rose-pine/rose-pine-theme | MIT | Warm cream base and low-chroma rose as the "red" role. Its light palette is a good mood reference but fails readability for yellow/cyan/muted (about 1.5-2.6:1), so those roles are darkened here until they pass. |
| Inky Pinky (Omarchy theme) | https://github.com/HANCORE-linux/omarchy-inkypinky-theme | MIT | Soft pink-violet on near-black reads as "cute but calm". Weak point: red, yellow, magenta and brown all collapse into similar pinks, so ANSI roles become hard to tell apart. Here every ANSI hue keeps its own family (red, orange, yellow, green, cyan, blue, magenta). |
| Sakura (Omarchy theme) | https://github.com/bjarneo/omarchy-sakura-theme | no licence file found (nothing copied) | Warm blossom palette on near-black. Weak points: muted text is about 3.4:1, "green" is a pink and "blue" equals the accent. Lesson: keep `muted` >= 4.5:1 and never alias roles. |
| Sakura Mochi (Omarchy theme) | https://github.com/OldJobobo/omarchy-sakura-mochi-theme | MIT (its wallpapers mix original and third-party art; none used) | A soft-pink foreground with a saturated pink accent on near-black. Here: a pale pink foreground and a coral bow-red accent that keeps >= 4.5:1 on every surface. |
| Ghost Pastel (Omarchy theme) | https://github.com/row-huh/omarchy-ghost-pastel-theme | no licence shown (nothing copied) | Pastel ANSI colours with an inverted selection pair. Here the selection pair is explicit and checked (see the table above). |
| Ethereal (bundled with Omarchy) | /usr/share/omarchy/themes/ethereal | Omarchy, MIT | Good reference for a dark scheme where every text colour clears 4.5:1; used as the bar to beat. |

Also reviewed only for licence terms (no files used): Hero Patterns (CC BY 4.0) and Kenney Pattern Pack (CC0). The gingham, polka-dot, bow, heart, sparkle, cloud and strawberry shapes here are plain vector primitives drawn in `rsvg-convert` SVG; they are generic motifs, not traced from any artwork.

What changed because of this research: the six ANSI hues, their bright tiers and the accent were re-derived in OKLCH with a contrast solver (previous hand-picked set kept in the scratch folder), `muted` and `dark_foreground` were raised to >= 4.5:1 on every surface, bright tiers got a small hue shift so they stay distinct from the normal tier, and the dark ANSI set moved to the pastel tier at AAA contrast.
