# backup/: a Time Machine for your files

> **TL;DR.** Two layers. Hourly local snapshots of `/home` with snapper (needs btrfs; keeps the last 6 hours, 7 days, 2 weeks and 1 month; browse or restore any
> file without sudo), and Pika Backup (a friendly borg GUI) for the real, encrypted, scheduled backup to an external drive or a server. Snapshots live on the *same*
> disk: they undo mistakes, not a dead disk.

`sudo backup/install-backups` (preview with `--dry-run`, which needs no sudo) installs both; afterwards open Pika Backup and pick the drive, the one step that needs
you. `sudo backup/install-backups --remove` removes the `/home` snapper config and the timeline timer (snapshots already taken stay until you delete them; Pika Backup
stays installed). Setup log rows: **Hourly snapshots of /home**, **A real backup of your files to an external drive (Pika Backup)**.

---

Related: [docs/MAC-FEEL](../docs/MAC-FEEL.md) · [docs/INDEX](../docs/INDEX.md)
