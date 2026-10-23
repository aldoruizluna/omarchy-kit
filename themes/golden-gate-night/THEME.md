# Golden Gate Night (dark) - Omarchy theme

**EN.** The dark partner: a charcoal ground (`#1c1c1e`), near-white text (15.6:1), the vivid system hues, a system-blue accent, the same rounded windows and soft shadows with a hairline white edge. Five original wallpapers: the bridge under a low glowing moon, and deep colour fields.

**ES.** El compañero oscuro: fondo carbón (`#1c1c1e`), texto casi blanco (15,6:1), los tonos vivos del sistema, acento azul de sistema, las mismas ventanas redondeadas con sombras suaves y un borde blanco finísimo. Cinco fondos originales: el puente bajo una luna baja y brillante y campos de color profundos.

## Palette rationale / Razon de la paleta

**EN.** Dark surfaces use the layered charcoals macOS uses (`#0f0f11`, `#161618`, `#1c1c1e`, `#2c2c2e`): each step lifts a surface a little, so panels read as above the window without borders. On dark grounds the vivid system hues already pass 4.5:1, so they are used as they are. The menu highlight is a deeper blue (`#0a6cdc`) so its white text passes 5:1; the pure `#0a84ff` would give white text only 3.7:1.

**ES.** Las superficies oscuras usan los carbones por capas de macOS (`#0f0f11`, `#161618`, `#1c1c1e`, `#2c2c2e`): cada paso eleva un poco la superficie, así los paneles se leen por encima de la ventana sin bordes. Sobre fondos oscuros los tonos vivos del sistema ya pasan 4,5:1, así que se usan tal cual. El resaltado de los menús es un azul más profundo (`#0a6cdc`) para que su texto blanco pase 5:1; el `#0a84ff` puro daría al texto blanco solo 3,7:1.

```toml
mode = "dark"

accent = "#0a84ff"
selection = "#1a4d8f"
muted = "#98989d"

background = "#1c1c1e"
dark_background = "#161618"
darker_background = "#0f0f11"
lighter_background = "#2c2c2e"

foreground = "#f5f5f7"
dark_foreground = "#98989d"
light_foreground = "#e5e5ea"
bright_foreground = "#ffffff"

red = "#ff453a"
yellow = "#ffd60a"
orange = "#ff9f0a"
green = "#30d158"
cyan = "#64d2ff"
blue = "#5aa9ff"
magenta = "#bf5af2"
brown = "#ac8e68"

bright_red = "#ff6961"
bright_yellow = "#ffe14d"
bright_green = "#5ae07a"
bright_cyan = "#8fe0ff"
bright_blue = "#80bdff"
bright_magenta = "#d388ff"
```

## WCAG 2.x contrast table (computed in Python, `relative luminance`, sRGB)

Text pairs at or above 4.5:1. Failing pairs: none.

| Pair | FG | BG | Ratio | Needed | Result | Use |
|---|---|---|---|---|---|---|
| foreground / background | `#f5f5f7` | `#1c1c1e` | 15.63:1 | 7:1 | pass | body text (AAA) |
| bright_foreground / background | `#ffffff` | `#1c1c1e` | 17.01:1 | 7:1 | pass | cursor, bold text |
| light_foreground / background | `#e5e5ea` | `#1c1c1e` | 13.55:1 | 4.5:1 | pass | secondary text |
| foreground / dark_background | `#f5f5f7` | `#161618` | 16.60:1 | 7:1 | pass | sidebars, status bars |
| foreground / lighter_background | `#f5f5f7` | `#2c2c2e` | 12.80:1 | 7:1 | pass | cursor line, menus |
| foreground / selection | `#f5f5f7` | `#1a4d8f` | 7.71:1 | 4.5:1 | pass | selected text |
| muted / background | `#98989d` | `#1c1c1e` | 5.93:1 | 4.5:1 | pass | ANSI bright black, comments |
| accent / background | `#0a84ff` | `#1c1c1e` | 4.66:1 | 4.5:1 | pass | links, focus, highlights |
| red / background | `#ff453a` | `#1c1c1e` | 4.99:1 | 4.5:1 | pass | ANSI red |
| orange / background | `#ff9f0a` | `#1c1c1e` | 8.28:1 | 4.5:1 | pass | ANSI orange |
| yellow / background | `#ffd60a` | `#1c1c1e` | 12.05:1 | 4.5:1 | pass | ANSI yellow |
| green / background | `#30d158` | `#1c1c1e` | 8.42:1 | 4.5:1 | pass | ANSI green |
| cyan / background | `#64d2ff` | `#1c1c1e` | 9.89:1 | 4.5:1 | pass | ANSI cyan |
| blue / background | `#5aa9ff` | `#1c1c1e` | 6.93:1 | 4.5:1 | pass | ANSI blue |
| magenta / background | `#bf5af2` | `#1c1c1e` | 4.83:1 | 4.5:1 | pass | ANSI magenta |
| brown / background | `#ac8e68` | `#1c1c1e` | 5.53:1 | 4.5:1 | pass | ANSI brown |
| bright_red / background | `#ff6961` | `#1c1c1e` | 6.03:1 | 4.5:1 | pass | ANSI bright red |
| bright_yellow / background | `#ffe14d` | `#1c1c1e` | 13.07:1 | 4.5:1 | pass | ANSI bright yellow |
| bright_green / background | `#5ae07a` | `#1c1c1e` | 10.03:1 | 4.5:1 | pass | ANSI bright green |
| bright_cyan / background | `#8fe0ff` | `#1c1c1e` | 11.57:1 | 4.5:1 | pass | ANSI bright cyan |
| bright_blue / background | `#80bdff` | `#1c1c1e` | 8.62:1 | 4.5:1 | pass | ANSI bright blue |
| bright_magenta / background | `#d388ff` | `#1c1c1e` | 7.08:1 | 4.5:1 | pass | ANSI bright magenta |
| menu highlight text / highlight | `#ffffff` | `#0a6cdc` | 5.01:1 | 4.5:1 | pass | selected row of menus and the launcher |

## What the theme changes besides colours

- **Window style** (`hyprland.lua`): spaces slide when you switch (Omarchy turns that off), corner radius 16 with `rounding_power = 4` (smooth, squircle-like corners; macOS 26 used about 26 pt for windows with a toolbar and macOS 27 reportedly one shared radius of about 20 pt, from a forum report Apple has not confirmed, against 10 pt before: 16 sits between), a soft deep shadow, a 1 px hairline edge, the focused window edged in a faint accent instead of Omarchy's glowing gradient, and unfocused windows dimmed 6 %. The Omarchy shell mirrors the corner radius, so its popups, menus, notifications and the launcher are rounded too.
- **Shell surfaces** (`shell.*.toml`, one file per section): popups, notifications, the launcher and menus are 88-90 % opaque with a hairline border, and the selected row is the accent with white text, as in a Mac menu. They become real glass when `look/mac-glass on` is run.
- **Icons** (`icons.theme`): the fallback is Yaru; `icons/install-icons` replaces it with WhiteSur (the light or dark variant follows this theme's mode).

## Inspiration and what is original

- The palettes follow the *shape* of Apple's published human-interface colour guidance (a neutral grey/charcoal ground, blue as the system accent, an accessible colour set for text on light surfaces). Colour values are numbers, not artwork; every colour here was re-checked against the contrast table above. Dark partner: `golden-gate`.
- Wallpapers: original SVG scenes drawn by `themes/generators/golden_gate.py` (a suspension bridge built from simple shapes, fog banks, soft colour fields). They do not copy a photograph or any Apple wallpaper, and they are not stored: install-themes draws them.
- Nothing here includes Apple artwork, logos, fonts or icons.

## Credits and licences

- Palette, wallpapers, window style and texts: original work generated for this machine. Licence for the art and palette: CC BY 4.0 (see `../LICENSE`).
- Icon theme referenced by `icons.theme`: Yaru (installed system-wide, not redistributed here). With `icons/install-icons`, WhiteSur (GPL-3.0) is downloaded at install time and never stored in this repository.
