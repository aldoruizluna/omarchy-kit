# Mecha Unit Red (Omarchy theme)

## Summary (EN)

**Mecha Unit Red** is a dark Omarchy theme in the style of a purple and acid-green tactical command centre: a near-black crimson-violet background, red/orange-led (alert red-orange main accent, purple and acid green as secondary accents), warning orange and alert red for status, and warm white text. It ships a full `colors.toml`, matching btop, Hyprland border and glow, lock-screen colours, a lock-screen logo, a preview, and 5 original 2880x1800 wallpapers generated procedurally (hex force-field, radar rings, data panels, armour plates with hazard stripe, circuit core). Foreground/background contrast is above 7:1 and every ANSI colour is above 4.5:1. A sibling variant is `mecha-unit`.

## Resumen (ES)

**Mecha Unit Red** es un tema oscuro de Omarchy con aspecto de centro de mando tactico morado y verde acido: fondo casi negro carmesi-violeta, rojo-naranja de alerta como acento principal; morado y verde acido como acentos secundarios, naranja de aviso y rojo de alerta para estados, y texto blanco calido. Incluye `colors.toml` completo, btop, borde y brillo de Hyprland, colores y logo de la pantalla de bloqueo, una vista previa y 5 fondos originales de 2880x1800 generados por codigo (campo de fuerza hexagonal, anillos de radar, paneles de datos, placas con franja de peligro, nucleo de circuitos). El contraste texto/fondo supera 7:1 y cada color ANSI supera 4.5:1. La variante hermana es `mecha-unit`.

## Palette rationale

The palette is built for long terminal sessions first and for looks second.

- **Base**: `#0d0510` (near-black crimson), with three steps (`darker_background`, `dark_background`, `lighter_background`) so panels read as layers without borders.
- **Roles, not decoration**: green means nominal, orange or yellow means caution, red means critical. Red is also the bar's "active" colour (recording, alerts), so it is kept out of ordinary syntax highlighting where possible.
- **One lightness band**: the six ANSI hues sit in a narrow lightness range (about 6.4:1 to 13.6:1 against the background) so no colour shouts over another; the `bright_*` row is lighter by roughly one step (all above 7:1).
- **Glow stays on the wallpapers**: the neon glow exists only in the wallpaper art. UI text, borders and the terminal never glow; the only UI glow is a 6 px Hyprland window shadow at 60% accent alpha.
- **Dim text is still readable**: `muted` and `dark_foreground` (comments, placeholders, disabled items) are kept above 4.5:1 instead of the usual 3:1.
- **Neovim and VS Code**: no third-party plugin is required. Omarchy generates editor colours from `colors.toml`, so there is no `neovim.lua` or `vscode.json` here.

| Role | Hex | Used for |
|---|---|---|
| `background` | `#0d0510` | terminal and bar background (black-crimson) |
| `dark_background / darker_background` | `#080309` `#050207` | recessed panels, gaps |
| `lighter_background` | `#1f0e1c` | raised panels, popups, title strips |
| `foreground / bright_foreground / light_foreground` | `#ffeee6` `#fff8f4` `#e8cfc6` | warm white text, emphasised text, secondary text |
| `accent` | `#ff5a36` | borders, bar highlight, cursor, keyboard LEDs |
| `selection` | `#4a1620` | selected rows and text selection |
| `muted / dark_foreground` | `#b08a9a` `#8f6f80` | comments, placeholders, disabled text (both >= 4.5:1) |
| `red` | `#ff4f68` | critical / alert (reserved for errors and recording) |
| `orange / yellow` | `#ff8c2e` `#f5c83d` | warning / caution |
| `green` | `#7aef3e` | nominal / ok, second accent |
| `cyan / blue / magenta` | `#47d3e8` `#7b92ff` `#c27dff` | info, links, keywords and purple tones |
| `bright_*` | see `colors.toml` | bold / high-emphasis variants, all >= 7:1 |

## WCAG contrast table

Computed in Python with the WCAG 2.x relative-luminance formula. Target: 7:1 for main text, 4.5:1 for all other text and ANSI colours, 3:1 for accent on its own selection background. All pairs below pass; none had to be waived.

| Foreground | Background | Ratio | Target | Result |
|---|---|---:|---:|---|
| `foreground` #ffeee6 | `background` #0d0510 | 17.80 | 7 | PASS AAA |
| `bright_foreground` #fff8f4 | `background` #0d0510 | 19.10 | 7 | PASS AAA |
| `light_foreground` #e8cfc6 | `background` #0d0510 | 13.54 | 4.5 | PASS AAA |
| `muted` #b08a9a | `background` #0d0510 | 6.64 | 4.5 | PASS AA |
| `dark_foreground` #8f6f80 | `background` #0d0510 | 4.54 | 4.5 | PASS AA |
| `accent` #ff5a36 | `background` #0d0510 | 6.47 | 4.5 | PASS AA |
| `orange` #ff8c2e | `background` #0d0510 | 8.64 | 4.5 | PASS AAA |
| `brown` #b27b45 | `background` #0d0510 | 5.55 | 4.5 | PASS AA |
| `red` #ff4f68 | `background` #0d0510 | 6.28 | 4.5 | PASS AA |
| `green` #7aef3e | `background` #0d0510 | 13.61 | 4.5 | PASS AAA |
| `yellow` #f5c83d | `background` #0d0510 | 12.63 | 4.5 | PASS AAA |
| `blue` #7b92ff | `background` #0d0510 | 7.07 | 4.5 | PASS AAA |
| `magenta` #c27dff | `background` #0d0510 | 7.33 | 4.5 | PASS AAA |
| `cyan` #47d3e8 | `background` #0d0510 | 11.23 | 4.5 | PASS AAA |
| `bright_red` #ff7a80 | `background` #0d0510 | 7.98 | 4.5 | PASS AAA |
| `bright_green` #b4ff7a | `background` #0d0510 | 16.75 | 4.5 | PASS AAA |
| `bright_yellow` #ffe375 | `background` #0d0510 | 15.77 | 4.5 | PASS AAA |
| `bright_blue` #a0b2ff | `background` #0d0510 | 9.85 | 4.5 | PASS AAA |
| `bright_magenta` #d9a6ff | `background` #0d0510 | 10.37 | 4.5 | PASS AAA |
| `bright_cyan` #85ebf8 | `background` #0d0510 | 14.56 | 4.5 | PASS AAA |
| `foreground` #ffeee6 | `selection` #4a1620 | 13.05 | 4.5 | PASS AAA |
| `bright_foreground` #fff8f4 | `selection` #4a1620 | 14.01 | 4.5 | PASS AAA |
| `foreground` #ffeee6 | `lighter_background` #1f0e1c | 16.37 | 4.5 | PASS AAA |
| `muted` #b08a9a | `lighter_background` #1f0e1c | 6.11 | 4.5 | PASS AA |
| `accent` #ff5a36 | `lighter_background` #1f0e1c | 5.95 | 3 | PASS AA |
| `accent` #ff5a36 | `selection` #4a1620 | 4.74 | 3 | PASS AA |
| `background` #0d0510 | `accent (button text)`  | 6.47 | 4.5 | PASS AA |
| `red` #ff4f68 | `lighter_background` #1f0e1c | 5.77 | 4.5 | PASS AA |
| `green` #7aef3e | `lighter_background` #1f0e1c | 12.52 | 4.5 | PASS AAA |

## Files

- `colors.toml`: palette (EXACT key set of the stock themes, `mode = "dark"`)
- `btop.theme`: btop colours
- `chromium.theme`: browser toolbar colour (r,g,b)
- `hyprland.lua`: window border and 6 px accent shadow
- `icons.theme`: installed icon theme: `Yaru-red` (from /usr/share/icons)
- `keyboard.rgb`: keyboard backlight colour (accent)
- `shell.lock.toml`: lock-screen text and border colours
- `unlock.png`: lock-screen logo (800x188, transparent)
- `preview.png`: 1800x1012 theme preview composite
- `preview-unlock.png`: 1920x1080 lock-screen preview
- `backgrounds/`: 5 original wallpapers, 2880x1800 JPEG, each under 700 KB
- `THEME.md`: this file

## Install

This folder is self-contained. Nothing here has been applied to any desktop.

```sh
# from this repository
cp -r omarchy-kit/themes/mecha-unit-red ~/.config/omarchy/themes/mecha-unit-red
omarchy theme set mecha-unit-red        # run this yourself when you want it
# preview first, without applying anything:
omarchy dev theme preview ~/.config/omarchy/themes/mecha-unit-red --no-osc
```

Wallpapers are cycled with the Omarchy background-next key. Wallpaper files are numbered `1-` to `5-` so the order is stable.

## Credits and licences

- **Palette, `colors.toml`, `btop.theme`, `hyprland.lua`, `shell.lock.toml`, `unlock.png`, `preview*.png`, wallpapers**: original work, generated for this machine; the wallpapers are drawn procedurally with Python and Pillow (the generator is in `mecha-unit/source/`, run `python3 walls.py {base|red} OUTDIR`). No third-party artwork, logos, characters or screenshots are embedded. The repository owner chooses the final licence for these original files (CC0 1.0 is suggested).
- **Fonts**: the wallpapers and the lock-screen logo use JetBrains Mono Nerd Font as already installed on the system (SIL OFL 1.1); it is not bundled in this folder.
- Names such as "unit", "sync" and "plate" in the art are generic sci-fi interface vocabulary.

## Inspiration chain (second degree)

Only open-source works were consulted. Their files, code and artwork were not copied; the palette and compositions here were re-derived and re-checked.

| Work | URL | Licence | Idea taken |
|---|---|---|---|
| cyberdream.nvim | https://github.com/scottmckendry/cyberdream.nvim | MIT | Neon ANSI hues held in one tight lightness band, a calmer desaturated option, and a grey for dim text. We narrowed our six ANSI colours into a 6.4 to 13.6:1 band. |
| Dracula theme | https://github.com/dracula/dracula-theme | MIT | Fixed colour roles on a dark base (purple, green, orange, red) and a 4.5:1 AA floor for foreground/background. We raised ours to 7:1 for the main text and kept dim text above 4.5:1. |
| SynthWave '84 | https://github.com/robb0wen/synthwave-vscode | MIT | Its own warning that glow is not meant for long sessions and should stay at low brightness. We confined glow to wallpapers and halved the glow gain after a first draft looked washed out. |
| augmented-ui | https://github.com/propjockey/augmented-ui | BSD-2-Clause | Chamfered, clipped-corner frames and hex shapes. Used for the panel frames and hex lattice in the wallpapers (drawn from scratch, no CSS reused). |
| Arwes | https://github.com/arwes/arwes | MIT | The overall sci-fi HUD grammar: framed panels, small caption tabs, readout text. Project is no longer maintained. |
| NASA Open MCT | https://github.com/nasa/openmct | Apache-2.0 | The idea of a telemetry dashboard built from labelled panels with nominal, caution and critical states. Its README gives no palette; only the layout concept was used. |
| eva-unit-01 (Blender theme) | https://extensions.blender.org/themes/eva-unit-01/ | GPL-2.0-or-later | The pairing itself: a deep-purple surface with a neon-green active accent, dark mode. Only its one-line description was read (no palette is published on the page); nothing was copied. |
| obsidian-nerv (Obsidian theme) | https://github.com/ethanthatonekid/obsidian-nerv | not stated on the page consulted | Squared-off HUD framing and corner "viewport brackets" as a composition idea. Its CRT scanlines trade legibility for atmosphere, so this theme keeps scanlines and glow out of the UI. Nothing was copied. |
| Omarchy Purplewave | https://github.com/dotsilva/omarchy-purplewave-theme | MIT | Reference for the optional-file set an Omarchy purple theme ships, and a readability measurement (see below). |
| Omarchy Pulsar | https://github.com/bjarneo/omarchy-pulsar-theme | no licence visible on the page | Measured only: confirms a near-black violet background around `#0a0314` works with a cold white-blue foreground at about 16:1. No values reused. |
| Shippori Mincho / Zen Old Mincho (Google Fonts) | https://fonts.google.com/specimen/Shippori+Mincho | SIL OFL 1.1 | Candidate open-licence Japanese Mincho faces for optional title-card typography. **Not installed and not embedded**; install one yourself only if you want title cards in that style. |

### Where neon-on-dark themes lose readability, and what this theme does instead

The raw `colors.toml` of two community purple themes was measured with the same WCAG formula (values were not copied).

- **Neon purple and magenta slip under 4.5:1.** Purplewave has an ANSI slot at `#ca2edc` that reaches only 4.4:1 on its `#121212` background. Here `magenta` is 7.3:1 and `bright_magenta` is 10.4:1.
- **No distinct accent.** Purplewave's `accent` equals its foreground (`#d7accd`), so highlights cannot stand out. Here `accent` is a separate hue at 6.5:1.
- **Decorative slots left unreadable.** Pulsar's `brown` is `#731f31` at 1.9:1. Here `brown` is 5.6:1, so any tool that prints with it stays legible.
- **Glow and scanlines on text.** Some neon themes apply glow or CRT scanlines to interface text. Here they exist only inside the wallpaper art.
