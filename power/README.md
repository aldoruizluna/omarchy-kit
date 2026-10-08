# power/: where the battery goes, and what to do about it

> **TL;DR.** The profile follows the charger, Wi-Fi can nap between packets (about 0.9 W), and `power-lab` measures where the roughly 20 W of an idle
> MacBook goes, trying power-saving changes one at a time and undoing each. The findings (including what was ruled out and what is still open) are in
> [docs/POWER-LAB.md](../docs/POWER-LAB.md).

| Script | Root? | What it does | Undo |
|---|---|---|---|
| `power-auto` (+ `power-auto.service`) | no | switches the power profile when the charger changes: performance on AC, balanced on battery (override in `~/.config/omarchy-kit/power-auto.conf`); `--once`, `--status` | `install-power-auto --remove` |
| `install-power-auto` | no | installs the user service | `--remove` |
| `install-wifi-powersave` | sudo | `/etc/NetworkManager/conf.d/wifi-powersave.conf` with `wifi.powersave = 3`; overrides Omarchy's deliberate "off"; a packet can wait up to one beacon interval (about 100 ms) | `--remove` |
| `power-lab` | asks for sudo once | modes `quiet`, `breakdown`, `singles`, `stack`, `hunt`, plus `results` and `<mode> --check`. Runs as a transient systemd service so the terminal stays idle (a busy terminal adds about 4 W); every change is reverted right after its measurement and on any exit, by a cleanup step that systemd runs after the test (`power-lab rescue`, never typed by hand) | nothing permanent |
| `msr-probe` | root, read-only | prints the CPU's package C-state limit and related switches | read-only |

## Use

```bash
power/install-power-auto                 # profile follows the charger
sudo power/install-wifi-powersave        # about -0.9 W, see the trade-off above
power/power-lab quiet --check            # look only: what it detected on this machine
power/power-lab breakdown                # about 3 minutes, charger unplugged, hands off the keyboard
power/power-lab results                  # the last results (data/power-lab/, not committed)
```

## Rules learned here

Keep the charger unplugged during a test (the draw is read from the battery); measure with the terminal idle; never remove or rescan PCI devices
(a rescan crashed the kernel); never unload the `thunderbolt` driver. See [docs/FIELD-NOTES.md](../docs/FIELD-NOTES.md).

## Checked by

Setup log rows **Power profile follows the charger**, **Wi-Fi power saving (about 0.9 W less)**; tests in `test/test_sleep_power_themes.py`.

---

Related: [docs/POWER-LAB](../docs/POWER-LAB.md) · [docs/FIELD-NOTES](../docs/FIELD-NOTES.md) · [sleep/](../sleep/README.md) · [docs/ARCHITECTURE](../docs/ARCHITECTURE.md) · [docs/INDEX](../docs/INDEX.md)
