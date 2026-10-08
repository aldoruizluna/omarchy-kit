# boot/: a faster, themed boot

> **TL;DR.** The Limine menu waits 1 s instead of 5 (any key still opens the full menu, snapshots included), shows a wallpaper in the current Omarchy theme, and uses the
> theme's colours. Plymouth is told to draw on the firmware framebuffer (`UseSimpledrm=1`), so the splash and the disk-passphrase prompt appear about 0.5 s
> into the kernel instead of about 3 s, and the boot image is rebuilt the way Omarchy does (`limine-mkinitcpio`).

| Script | What |
|---|---|
| `make-wallpaper` | no root: makes the boot wallpaper (`omarchy-boot.png`) and colours (`boot-colors.env`) from the *current* Omarchy theme; re-run after switching themes |
| `apply-boot-look` | root: edits only the header of `/boot/limine.conf` (the entries below belong to `limine-update`), sets Plymouth `UseSimpledrm=1`, and rebuilds the boot image; `--undo` restores the backups |

`sudo boot/apply-boot-look`, then reboot. Setup log row: **Faster, themed boot screen**.

---

Related: [themes/](../themes/README.md) · [docs/FIELD-NOTES](../docs/FIELD-NOTES.md) · [docs/INDEX](../docs/INDEX.md)
