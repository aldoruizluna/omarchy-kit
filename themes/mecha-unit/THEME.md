# Mecha Unit (Omarchy theme)

## Summary (EN)

**Mecha Unit** is a dark Omarchy theme in the style of a purple and acid-green tactical command centre: a near-black violet background, purple-led (industrial purple main accent, acid green second accent), warning orange and alert red for status, and cold cyan-white text. It ships a full `colors.toml`, matching btop, Hyprland border and glow, lock-screen colours, a lock-screen logo, a preview, and 5 original 2880x1800 wallpapers generated procedurally (hex force-field, radar rings, data panels, armour plates with hazard stripe, circuit core). Foreground/background contrast is above 7:1 and every ANSI colour is above 4.5:1. A sibling variant is `mecha-unit-red`.

## Resumen (ES)

**Mecha Unit** es un tema oscuro de Omarchy con aspecto de centro de mando tactico morado y verde acido: fondo casi negro violeta, morado industrial como acento principal y verde acido como segundo acento, naranja de aviso y rojo de alerta para estados, y texto blanco-cian frio. Incluye `colors.toml` completo, btop, borde y brillo de Hyprland, colores y logo de la pantalla de bloqueo, una vista previa y 5 fondos originales de 2880x1800 generados por codigo (campo de fuerza hexagonal, anillos de radar, paneles de datos, placas con franja de peligro, nucleo de circuitos). El contraste texto/fondo supera 7:1 y cada color ANSI supera 4.5:1. La variante hermana es `mecha-unit-red`.

## Palette rationale

The palette is built for long terminal sessions first and for looks second.

- **Base**: `#0b0614` (near-black violet), with three steps (`darker_background`, `dark_background`, `lighter_background`) so panels read as layers without borders.
- **Roles, not decoration**: green means nominal, orange or yellow means caution, red means critical. Red is also the bar's "active" colour (recording, alerts), so it is kept out of ordinary syntax highlighting where possible.
- **One lightness band**: the six ANSI hues sit in a narrow lightness range (about 6.4:1 to 13.6:1 against the background) so no colour shouts over another; the `bright_*` row is lighter by roughly one step (all above 7:1).
- **Glow stays on the wallpapers**: the neon glow exists only in the wallpaper art. UI text, borders and the terminal never glow; the only UI glow is a 6 px Hyprland window shadow at 60% accent alpha.
- **Dim text is still readable**: `muted` and `dark_foreground` (comments, placeholders, disabled items) are kept above 4.5:1 instead of the usual 3:1.
- **Neovim and VS Code**: no third-party plugin is required. Omarchy generates editor colours from `colors.toml`, so there is no `neovim.lua` or `vscode.json` here.

| Role | Hex | Used for |
|---|---|---|
| `background` | `#0b0614` | terminal and bar background (black-violet) |
| `dark_background / darker_background` | `#070310` `#04020a` | recessed panels, gaps |
| `lighter_background` | `#1a1030` | raised panels, popups, title strips |
| `foreground / bright_foreground / light_foreground` | `#d7f2ff` `#f2fcff` `#b3d4e6` | cold cyan-white text, emphasised text, secondary text |
| `accent` | `#a874ff` | borders, bar highlight, cursor, keyboard LEDs |
| `selection` | `#2f1b57` | selected rows and text selection |
| `muted / dark_foreground` | `#9686bf` `#8174aa` | comments, placeholders, disabled text (both >= 4.5:1) |
| `red` | `#ff5468` | critical / alert (reserved for errors and recording) |
| `orange / yellow` | `#ff9330` `#f5c83d` | warning / caution |
| `green` | `#7aef3e` | nominal / ok, second accent |
| `cyan / blue / magenta` | `#3fd0e6` `#6b8fff` `#c07cff` | info, links, keywords and purple tones |
| `bright_*` | see `colors.toml` | bold / high-emphasis variants, all >= 7:1 |

## WCAG contrast table

Computed in Python with the WCAG 2.x relative-luminance formula. Target: 7:1 for main text, 4.5:1 for all other text and ANSI colours, 3:1 for accent on its own selection background. All pairs below pass; none had to be waived.

| Foreground | Background | Ratio | Target | Result |
|---|---|---:|---:|---|
| `foreground` #d7f2ff | `background` #0b0614 | 17.17 | 7 | PASS AAA |
| `bright_foreground` #f2fcff | `background` #0b0614 | 19.18 | 7 | PASS AAA |
| `light_foreground` #b3d4e6 | `background` #0b0614 | 12.83 | 4.5 | PASS AAA |
| `muted` #9686bf | `background` #0b0614 | 6.15 | 4.5 | PASS AA |
| `dark_foreground` #8174aa | `background` #0b0614 | 4.77 | 4.5 | PASS AA |
| `accent` #a874ff | `background` #0b0614 | 6.29 | 4.5 | PASS AA |
| `orange` #ff9330 | `background` #0b0614 | 9.01 | 4.5 | PASS AAA |
| `brown` #a8703a | `background` #0b0614 | 4.80 | 4.5 | PASS AA |
| `red` #ff5468 | `background` #0b0614 | 6.40 | 4.5 | PASS AA |
| `green` #7aef3e | `background` #0b0614 | 13.56 | 4.5 | PASS AAA |
| `yellow` #f5c83d | `background` #0b0614 | 12.58 | 4.5 | PASS AAA |
| `blue` #6b8fff | `background` #0b0614 | 6.66 | 4.5 | PASS AA |
| `magenta` #c07cff | `background` #0b0614 | 7.21 | 4.5 | PASS AAA |
| `cyan` #3fd0e6 | `background` #0b0614 | 10.83 | 4.5 | PASS AAA |
| `bright_red` #ff7384 | `background` #0b0614 | 7.65 | 4.5 | PASS AAA |
| `bright_green` #b4ff7a | `background` #0b0614 | 16.69 | 4.5 | PASS AAA |
| `bright_yellow` #ffe375 | `background` #0b0614 | 15.71 | 4.5 | PASS AAA |
| `bright_blue` #97b0ff | `background` #0b0614 | 9.49 | 4.5 | PASS AAA |
| `bright_magenta` #d6a3ff | `background` #0b0614 | 10.04 | 4.5 | PASS AAA |
| `bright_cyan` #7cecfa | `background` #0b0614 | 14.50 | 4.5 | PASS AAA |
| `foreground` #d7f2ff | `selection` #2f1b57 | 12.74 | 4.5 | PASS AAA |
| `bright_foreground` #f2fcff | `selection` #2f1b57 | 14.23 | 4.5 | PASS AAA |
| `foreground` #d7f2ff | `lighter_background` #1a1030 | 15.54 | 4.5 | PASS AAA |
| `muted` #9686bf | `lighter_background` #1a1030 | 5.56 | 4.5 | PASS AA |
| `accent` #a874ff | `lighter_background` #1a1030 | 5.69 | 3 | PASS AA |
| `accent` #a874ff | `selection` #2f1b57 | 4.67 | 3 | PASS AA |
| `background` #0b0614 | `accent (button text)`  | 6.29 | 4.5 | PASS AA |
| `red` #ff5468 | `lighter_background` #1a1030 | 5.79 | 4.5 | PASS AA |
| `green` #7aef3e | `lighter_background` #1a1030 | 12.27 | 4.5 | PASS AAA |

## Files

- `colors.toml`: palette (EXACT key set of the stock themes, `mode = "dark"`)
- `btop.theme`: btop colours
- `chromium.theme`: browser toolbar colour (r,g,b)
- `hyprland.lua`: window border and 6 px accent shadow
- `icons.theme`: installed icon theme: `Yaru-purple` (from /usr/share/icons)
- `keyboard.rgb`: keyboard backlight colour (accent)
- `shell.lock.toml`: lock-screen text and border colours
- `unlock.png`: lock-screen logo (800x188, transparent)
- `preview.png`: 1800x1012 theme preview composite
- `preview-unlock.png`: 1920x1080 lock-screen preview
- `backgrounds/`: 5 original wallpapers, 2880x1800 JPEG, each under 700 KB
- `THEME.md`: this file
- `source/`: generator scripts for the wallpapers (`palette.py`, `art.py`, `walls.py`)

## Install

This folder is self-contained. Nothing here has been applied to any desktop.

```sh
# from this repository
cp -r omarchy-kit/themes/mecha-unit ~/.config/omarchy/themes/mecha-unit
omarchy theme set mecha-unit        # run this yourself when you want it
# preview first, without applying anything:
omarchy dev theme preview ~/.config/omarchy/themes/mecha-unit --no-osc
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

- **Neon purple and magenta slip under 4.5:1.** Purplewave has an ANSI slot at `#ca2edc` that reaches only 4.4:1 on its `#121212` background. Here `magenta` is 7.2:1 and `bright_magenta` is 10.0:1.
- **No distinct accent.** Purplewave's `accent` equals its foreground (`#d7accd`), so highlights cannot stand out. Here `accent` is a separate hue at 6.3:1.
- **Decorative slots left unreadable.** Pulsar's `brown` is `#731f31` at 1.9:1. Here `brown` is 4.8:1, so any tool that prints with it stays legible.
- **Glow and scanlines on text.** Some neon themes apply glow or CRT scanlines to interface text. Here they exist only inside the wallpaper art.
