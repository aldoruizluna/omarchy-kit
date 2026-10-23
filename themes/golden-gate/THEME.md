# Golden Gate (light) - Omarchy theme

**EN.** A bright, calm, system-UI light theme in the spirit of the current macOS look: soft grey-white surfaces, near-black text (15.5:1), an accessible system blue, rounded windows with deep soft shadows and a faint blue edge on the focused one. Five original wallpapers: a stylised suspension bridge in morning fog, and soft colour fields.

**ES.** Un tema claro, luminoso y sereno, de interfaz de sistema, en el espíritu del aspecto actual de macOS: superficies gris-blanco suaves, texto casi negro (15,5:1), un azul de sistema accesible, ventanas redondeadas con sombras suaves y profundas y un borde azul tenue en la enfocada. Cinco fondos originales: un puente colgante estilizado en la niebla de la mañana y campos de color suaves.

## Palette rationale / Razon de la paleta

**EN.** The background is the light system grey (`#f5f5f7`) rather than white, so long reading stays soft; text is near-black (`#1d1d1f`). Apple publishes two sets of system colours: the vivid ones for controls and an *accessible* set for text on light surfaces. This theme takes the accessible set for every ANSI hue and for the accent (`#0066d6`, white on it 5.4:1), because a vivid blue (`#007aff`) is only 3.7:1 on the grey. The menu highlight is the accent with white text, like a Mac menu.

**ES.** El fondo es el gris claro del sistema (`#f5f5f7`) y no blanco, para lecturas largas; el texto es casi negro (`#1d1d1f`). Apple publica dos juegos de colores de sistema: los vivos para controles y uno *accesible* para texto sobre superficies claras. Este tema usa el accesible para cada tono ANSI y para el acento (`#0066d6`, blanco encima 5,4:1), porque un azul vivo (`#007aff`) solo da 3,7:1 sobre el gris. El resaltado de los menús es el acento con texto blanco, como un menú de Mac.

```toml
mode = "light"

accent = "#0066d6"
selection = "#cce4ff"
muted = "#6e6e73"

background = "#f5f5f7"
dark_background = "#ebebf0"
darker_background = "#dcdce2"
lighter_background = "#ffffff"

foreground = "#1d1d1f"
dark_foreground = "#6e6e73"
light_foreground = "#3a3a3c"
bright_foreground = "#000000"

red = "#d70015"
yellow = "#8a5a00"
orange = "#c93400"
green = "#1f7a36"
cyan = "#0071a4"
blue = "#0040dd"
magenta = "#8944ab"
brown = "#7f6545"

bright_red = "#c4001a"
bright_yellow = "#7a5000"
bright_green = "#1e7a35"
bright_cyan = "#00658f"
bright_blue = "#0033cc"
bright_magenta = "#7a3a9c"
```

## WCAG 2.x contrast table (computed in Python, `relative luminance`, sRGB)

Text pairs at or above 4.5:1. Failing pairs: none.

| Pair | FG | BG | Ratio | Needed | Result | Use |
|---|---|---|---|---|---|---|
| foreground / background | `#1d1d1f` | `#f5f5f7` | 15.46:1 | 7:1 | pass | body text (AAA) |
| bright_foreground / background | `#000000` | `#f5f5f7` | 19.29:1 | 7:1 | pass | cursor, bold text |
| light_foreground / background | `#3a3a3c` | `#f5f5f7` | 10.42:1 | 4.5:1 | pass | secondary text |
| foreground / dark_background | `#1d1d1f` | `#ebebf0` | 14.16:1 | 7:1 | pass | sidebars, status bars |
| foreground / lighter_background | `#1d1d1f` | `#ffffff` | 16.83:1 | 7:1 | pass | cursor line, menus |
| foreground / selection | `#1d1d1f` | `#cce4ff` | 12.91:1 | 4.5:1 | pass | selected text |
| muted / background | `#6e6e73` | `#f5f5f7` | 4.66:1 | 4.5:1 | pass | ANSI bright black, comments |
| accent / background | `#0066d6` | `#f5f5f7` | 4.98:1 | 4.5:1 | pass | links, focus, highlights |
| red / background | `#d70015` | `#f5f5f7` | 4.94:1 | 4.5:1 | pass | ANSI red |
| orange / background | `#c93400` | `#f5f5f7` | 4.85:1 | 4.5:1 | pass | ANSI orange |
| yellow / background | `#8a5a00` | `#f5f5f7` | 5.44:1 | 4.5:1 | pass | ANSI yellow |
| green / background | `#1f7a36` | `#f5f5f7` | 4.95:1 | 4.5:1 | pass | ANSI green |
| cyan / background | `#0071a4` | `#f5f5f7` | 4.95:1 | 4.5:1 | pass | ANSI cyan |
| blue / background | `#0040dd` | `#f5f5f7` | 6.94:1 | 4.5:1 | pass | ANSI blue |
| magenta / background | `#8944ab` | `#f5f5f7` | 5.54:1 | 4.5:1 | pass | ANSI magenta |
| brown / background | `#7f6545` | `#f5f5f7` | 5.01:1 | 4.5:1 | pass | ANSI brown |
| bright_red / background | `#c4001a` | `#f5f5f7` | 5.74:1 | 4.5:1 | pass | ANSI bright red |
| bright_yellow / background | `#7a5000` | `#f5f5f7` | 6.48:1 | 4.5:1 | pass | ANSI bright yellow |
| bright_green / background | `#1e7a35` | `#f5f5f7` | 4.96:1 | 4.5:1 | pass | ANSI bright green |
| bright_cyan / background | `#00658f` | `#f5f5f7` | 5.92:1 | 4.5:1 | pass | ANSI bright cyan |
| bright_blue / background | `#0033cc` | `#f5f5f7` | 8.22:1 | 4.5:1 | pass | ANSI bright blue |
| bright_magenta / background | `#7a3a9c` | `#f5f5f7` | 6.62:1 | 4.5:1 | pass | ANSI bright magenta |
| menu highlight text / highlight | `#ffffff` | `#0066d6` | 5.42:1 | 4.5:1 | pass | selected row of menus and the launcher |

## What the theme changes besides colours

- **Window style** (`hyprland.lua`): spaces slide when you switch (Omarchy turns that off), corner radius 16 with `rounding_power = 4` (smooth, squircle-like corners; macOS 26 used about 26 pt for windows with a toolbar and macOS 27 reportedly one shared radius of about 20 pt, from a forum report Apple has not confirmed, against 10 pt before: 16 sits between), a soft deep shadow, a 1 px hairline edge, the focused window edged in a faint accent instead of Omarchy's glowing gradient, and unfocused windows dimmed 6 %. The Omarchy shell mirrors the corner radius, so its popups, menus, notifications and the launcher are rounded too.
- **Shell surfaces** (`shell.*.toml`, one file per section): popups, notifications, the launcher and menus are 88-90 % opaque with a hairline border, and the selected row is the accent with white text, as in a Mac menu. They become real glass when `look/mac-glass on` is run.
- **Icons** (`icons.theme`): the fallback is Yaru; `icons/install-icons` replaces it with WhiteSur (the light or dark variant follows this theme's mode).

## Inspiration and what is original

- The palettes follow the *shape* of Apple's published human-interface colour guidance (a neutral grey/charcoal ground, blue as the system accent, an accessible colour set for text on light surfaces). Colour values are numbers, not artwork; every colour here was re-checked against the contrast table above. Light partner: `golden-gate-night`.
- Wallpapers: original SVG scenes drawn by `themes/generators/golden_gate.py` (a suspension bridge built from simple shapes, fog banks, soft colour fields). They do not copy a photograph or any Apple wallpaper, and they are not stored: install-themes draws them.
- Nothing here includes Apple artwork, logos, fonts or icons.

## Credits and licences

- Palette, wallpapers, window style and texts: original work generated for this machine. Licence for the art and palette: CC BY 4.0 (see `../LICENSE`).
- Icon theme referenced by `icons.theme`: Yaru (installed system-wide, not redistributed here). With `icons/install-icons`, WhiteSur (GPL-3.0) is downloaded at install time and never stored in this repository.
