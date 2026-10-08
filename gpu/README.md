# gpu/: keep the hot NVIDIA GPU off

> **TL;DR.** The MacBookPro11,3 has an Intel GPU and a hot NVIDIA GT 750M that `nouveau` never lets sleep (about 70 °C, fans near 5,900 rpm).
> `nvidia-off` powers it down through `vga_switcheroo` at boot and after every sleep; fans settle near 2,100 to 2,200 rpm.
> All scripts refuse to run on any other model.

| Script | Root? | What it does |
|---|---|---|
| `nvidia-off` (+ `nvidia-off.service`) | root (runs as a service) | writes OFF to `vga_switcheroo` for the NVIDIA card; skipped when an external display is connected or the card is in use; never writes ON; copies the real state to `/run/nvidia-off.status` |
| `gpu-status` | no | which GPU drives the screen, the real vga_switcheroo state, and what the firmware boots with |
| `switch-to-intel` | sudo | sets Apple's `gpu-power-prefs` firmware variable so the panel is on Intel from power-on (takes effect next boot; recovery steps are in the script header) |
| `switch-to-nvidia` | sudo | removes that variable (the firmware default) |

## Install and undo

```bash
sudo install -m755 gpu/nvidia-off /usr/local/bin/ && sudo install -m644 gpu/nvidia-off.service /etc/systemd/system/ && sudo systemctl enable nvidia-off.service
sudo systemctl disable --now nvidia-off.service        # undo for good
echo ON | sudo tee /sys/kernel/debug/vgaswitcheroo/switch   # undo right now
```

Pitfall: sysfs `power_state` for the card can read D0 after a sleep even when it is off; trust `gpu-status`, not sysfs ([FIELD-NOTES](../docs/FIELD-NOTES.md)).

## Checked by

Setup log rows **Screen on the efficient Intel GPU**, **Idle NVIDIA GPU powered off**.

---

Related: [docs/FIELD-NOTES](../docs/FIELD-NOTES.md) · [docs/POWER-LAB](../docs/POWER-LAB.md) · [docs/ARCHITECTURE](../docs/ARCHITECTURE.md) · [docs/INDEX](../docs/INDEX.md)
