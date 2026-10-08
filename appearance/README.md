# appearance/: light by day, dark at night

> **TL;DR.** Like macOS "Appearance: Auto". A user timer runs `auto-appearance` every 10 minutes; it switches the Omarchy theme only when the day/night
> *period* changes, so a theme you pick by hand stays until the next boundary. Installed but **off** until you run `auto-appearance on`.

| Command | What |
|---|---|
| `install-auto-appearance` | no root: installs the script, a service and a timer; `--remove` removes everything |
| `auto-appearance` | apply the theme for the current period if the period changed |
| `auto-appearance status`, `light`, `dark`, `on`, `off`, `--dry-run` | show the schedule; switch now; turn the timer on or off; say what would happen |

Settings: `~/.config/omarchy-kit/appearance.conf` (`LIGHT_THEME=`, `DARK_THEME=`, `LIGHT_FROM=07:00`, `DARK_FROM=19:00`). Test a time without waiting:
`KIT_FAKE_NOW=21:30 auto-appearance --dry-run`. Setup log row: **Auto appearance: light by day, dark at night (optional)**.

---

Related: [themes/](../themes/README.md) · [docs/MAC-FEEL](../docs/MAC-FEEL.md) · [docs/INDEX](../docs/INDEX.md)
