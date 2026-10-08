# Kawaii Bow

**EN.** A light Omarchy theme inspired by a kawaii red-bow pastel look: strawberry-milk pinks and cream, a bow-red accent, with baby blue and butter yellow as secondary pops. It is cute but built to be read: body text is at least 7:1 on the background, every ANSI colour is at least 4.5:1 on every surface, and the accent clears 4.5:1 too. Five original wallpapers (2880x1800), a preview, btop, border and lock-screen assets are included. Neovim and VS Code colours are generated from the palette by Omarchy itself.

**ES.** Un tema de Omarchy claro inspirado en un estilo kawaii pastel con moño rojo: rosas "leche de fresa" y crema, acento rojo moño, con azul cielo y amarillo mantequilla como toques secundarios. Es tierno pero legible: el texto tiene al menos 7:1 de contraste con el fondo, cada color ANSI tiene al menos 4.5:1 sobre todas las superficies y el acento tambien supera 4.5:1. Incluye cinco fondos originales (2880x1800), vista previa y recursos de btop, bordes y pantalla de bloqueo. Los colores de Neovim y VS Code los genera Omarchy a partir de la paleta.

## Palette rationale

- **Base**: `#fff6f8` is a pink-tinted cream rather than pure white, with `dark_background`, `darker_background`, `lighter_background` and `selection` as a small ramp of the same hue so panels stay distinguishable without harsh edges.
- **Text**: berry-brown `#43202d` (never plain black); `muted` and `dark_foreground` form the quiet tier and still clear 4.5:1.
- **Accent**: `#c1082c` is the bow red (deep), also used for window borders (gradient to pink) and btop highlights.
- **ANSI**: red, orange, yellow (butter), green (mint), cyan, blue (baby blue), magenta (strawberry pink) each keep their own hue family. They are solved in OKLCH at equal contrast, then brights use a small hue shift and higher chroma so the two tiers stay distinct.
- **Secondary pops**: baby blue (`blue`) and butter yellow (`yellow`) are darkened to goldenrod/azure in this light variant, because pastel yellow cannot reach 4.5:1 on cream.

## Palette (`colors.toml`)

| key | value |
|---|---|
| `mode` | `light` |
| `accent` | `#c1082c` |
| `selection` | `#f8d3e1` |
| `muted` | `#815366` |
| `background` | `#fff6f8` |
| `dark_background` | `#fdecf2` |
| `darker_background` | `#fbe0ea` |
| `lighter_background` | `#f1c3d4` |
| `foreground` | `#43202d` |
| `dark_foreground` | `#744659` |
| `light_foreground` | `#5a3041` |
| `bright_foreground` | `#2a0e19` |
| `red` | `#be0e43` |
| `yellow` | `#7e5905` |
| `orange` | `#994a08` |
| `green` | `#006e43` |
| `cyan` | `#076b6f` |
| `blue` | `#0561af` |
| `magenta` | `#af2276` |
| `brown` | `#714a39` |
| `bright_red` | `#c10042` |
| `bright_yellow` | `#715e05` |
| `bright_green` | `#076d4e` |
| `bright_cyan` | `#006a7a` |
| `bright_blue` | `#076596` |
| `bright_magenta` | `#b40090` |

## WCAG 2.x contrast (computed in Python, relative luminance)

Targets: body text >= 7:1 (AAA), text colours >= 4.5:1 (AA), accent vs background >= 3:1 (UI). `lighter_bg` is a border/inactive-surface colour, shown for completeness. Failing pairs found during tuning were fixed, not documented.

**Foreground roles**

| role | hex | background | dark_bg | darker_bg | lighter_bg | selection | level (min of bg/dark/darker/selection) |
|---|---|---|---|---|---|---|---|
| `foreground` | `#43202d` | 13.34 | 12.44 | 11.43 | 9.10 | 10.38 | AAA |
| `bright_foreground` | `#2a0e19` | 16.84 | 15.70 | 14.42 | 11.48 | 13.10 | AAA |
| `light_foreground` | `#5a3041` | 10.23 | 9.54 | 8.77 | 6.98 | 7.96 | AAA |
| `dark_foreground` | `#744659` | 7.16 | 6.68 | 6.14 | 4.89 | 5.57 | AA |
| `muted` | `#815366` | 5.89 | 5.49 | 5.04 | 4.01 | 4.58 | AA |

**Accent**

| role | hex | background | dark_bg | darker_bg | lighter_bg | selection | level |
|---|---|---|---|---|---|---|---|
| `accent` | `#c1082c` | 5.93 | 5.53 | 5.08 | 4.04 | 4.61 | AA |

**ANSI colours (text on surfaces)**

| ANSI role | hex | OKLCH L / C / h | background | dark_bg | darker_bg | lighter_bg | selection | level |
|---|---|---|---|---|---|---|---|---|
| `red` | `#be0e43` | 0.51 / 0.200 / 14 | 5.94 | 5.54 | 5.09 | 4.05 | 4.62 | AA |
| `orange` | `#994a08` | 0.50 / 0.125 / 52 | 5.93 | 5.53 | 5.08 | 4.04 | 4.61 | AA |
| `yellow` | `#7e5905` | 0.49 / 0.100 / 80 | 5.96 | 5.56 | 5.11 | 4.07 | 4.64 | AA |
| `green` | `#006e43` | 0.47 / 0.111 / 158 | 5.98 | 5.57 | 5.12 | 4.08 | 4.65 | AA |
| `cyan` | `#076b6f` | 0.48 / 0.080 / 199 | 5.92 | 5.52 | 5.07 | 4.04 | 4.61 | AA |
| `blue` | `#0561af` | 0.49 / 0.145 / 252 | 5.93 | 5.53 | 5.08 | 4.05 | 4.62 | AA |
| `magenta` | `#af2276` | 0.51 / 0.190 / 350 | 5.97 | 5.57 | 5.12 | 4.07 | 4.65 | AA |
| `brown` | `#714a39` | 0.45 / 0.060 / 44 | 7.22 | 6.73 | 6.19 | 4.92 | 5.62 | AA |
| `bright_red` | `#c10042` | 0.52 / 0.206 / 14 | 5.91 | 5.52 | 5.07 | 4.03 | 4.60 | AA |
| `bright_yellow` | `#715e05` | 0.49 / 0.098 / 95 | 5.99 | 5.58 | 5.13 | 4.08 | 4.66 | AA |
| `bright_green` | `#076d4e` | 0.47 / 0.098 / 165 | 5.99 | 5.58 | 5.13 | 4.08 | 4.66 | AA |
| `bright_cyan` | `#006a7a` | 0.48 / 0.084 / 213 | 5.92 | 5.52 | 5.07 | 4.04 | 4.61 | AA |
| `bright_blue` | `#076596` | 0.48 / 0.109 / 241 | 5.98 | 5.57 | 5.12 | 4.08 | 4.65 | AA |
| `bright_magenta` | `#b40090` | 0.52 / 0.226 / 340 | 5.92 | 5.52 | 5.07 | 4.04 | 4.60 | AA |

**Selection and extra pairs**

| pair | ratio | level |
|---|---|---|
| foreground on selection | 10.38 | AAA |
| bright_foreground on selection | 13.10 | AAA |
| foreground on lighter_bg | 9.10 | AAA |
| accent border on background (UI) | 5.93 | AA |
| accent on selection (btop selected_fg) | 4.61 | AA |

Result: no failing pair.

## Files

| file | size | what it is |
|---|---|---|
| `backgrounds/1-bow-garden.jpg` | 391 KB | original wallpaper 2880x1800 (JPEG) |
| `backgrounds/2-gingham-picnic.jpg` | 323 KB | original wallpaper 2880x1800 (JPEG) |
| `backgrounds/3-polka-clouds.jpg` | 285 KB | original wallpaper 2880x1800 (JPEG) |
| `backgrounds/4-ribbon-waves.jpg` | 309 KB | original wallpaper 2880x1800 (JPEG) |
| `backgrounds/5-strawberry-patch.jpg` | 406 KB | original wallpaper 2880x1800 (JPEG) |
| `btop.theme` | 3 KB | btop colours (box outlines: bow red / baby blue / butter / pink) |
| `chromium.theme` | 0 KB | browser chrome colour (background RGB) |
| `colors.toml` | 1 KB | palette (same key set as the bundled themes); every other generated config derives from it |
| `hyprland.lua` | 0 KB | active window border: bow red to pink gradient |
| `icons.theme` | 0 KB | icon theme name (installed Yaru variant) |
| `preview.png` | 568 KB | 1800x1012 composite: wallpaper, bar, terminal, btop, swatches, launcher (PIL) |
| `unlock.png` | 2 KB | lock-screen wordmark recoloured with the accent |
| `THEME.md` | - | this file |

Total: 2.2 MB. `neovim.lua` and `vscode.json` are intentionally absent: without them Omarchy generates a palette-matched Neovim config (aether.nvim) and a local VS Code theme from `colors.toml`, which is better than pointing at an extension that does not exist for this palette.

## How to install

```bash
cp -r kawaii-bow ~/.config/omarchy/themes/
omarchy theme set kawaii-bow
```

Preview without applying anything: `omarchy dev theme preview ./kawaii-bow --no-osc`. Remove with `rm -r ~/.config/omarchy/themes/kawaii-bow`.

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
