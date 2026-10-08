# sleep/: lid, sleep and hibernate on the MacBookPro11,3

> **TL;DR.** On this Mac, deep sleep (S3) never wakes when the lid opens. These scripts switch to **light sleep** (s2idle), which wakes at
> once, make **hibernate** stay off, let a plain hibernate ask for **one** password, and **record** what every sleep did and cost.
> Every installer takes `--remove`; `--help` only prints usage. The full story with measurements: [docs/SLEEP.md](../docs/SLEEP.md).

| Script | Root? | What it does | Undo |
|---|---|---|---|
| `install-s2idle` | sudo | a tmpfiles rule `w /sys/power/mem_sleep - - - - s2idle`, applied early at every boot | `--remove` (sets `deep` again) |
| `install-hibernate-mode` | sudo | `HibernateMode=shutdown` in `/etc/systemd/sleep.conf.d/10-hibernate-shutdown.conf`: save the image, then power off instead of restarting | `--remove` |
| `install-hibernate-nolock` | no | points the user service `omarchy-sleep-lock` at a shim (`~/.local/share/omarchy-kit/sleep-lock-shim`) so a plain hibernate skips the lock screen. Refuses if Omarchy's sleep monitor is missing or changed, or if the resume device is not on an encrypted volume | `--remove` |
| `sleep-lock-policy` | n/a | what the shim runs: skips the lock **only** when logind's newest line is exactly `The system will hibernate now!`; anything else, or any error, runs Omarchy's real lock (falling back to `omarchy-system-lock`, then `loginctl lock-session`). `--check` prints `hibernate` or `lock` | n/a |
| `install-battery-log` + `battery-log` | sudo | a hook in `/usr/lib/systemd/system-sleep/` (the only folder this systemd reads) that logs the battery charge before and after every sleep (journal tag `sleep-battery`) | `--remove` |
| `sleep-check` | no | reads the journal: every suspend and hibernate, its mode, how long, how much battery; `--json` for the Setup log | read-only |
| `acpi-prw-scan` | no | research tool: reads raw DSDT/SSDT tables and prints every `_PRW` wake definition with its device path | read-only |

## Use

```bash
sudo sleep/install-s2idle                # lid wakes the Mac again
sudo sleep/install-hibernate-mode        # hibernate stays off
sleep/install-hibernate-nolock           # one password after hibernate (no root; read the trade-off in docs/SLEEP.md first)
sudo sleep/install-battery-log           # then: sleep/sleep-check shows what each sleep cost
sleep/sleep-check                        # the report
```

## Trade-offs you should know

Light sleep keeps the fans spinning and drains the battery faster than deep sleep. Skipping the lock before hibernate leaves the screen unlocked
for the ~30 s the image takes to save, and unlocked if a hibernate ever fails. Both are explained, with the open decision about the lid, in
[docs/SLEEP.md](../docs/SLEEP.md).

## Checked by

Setup log rows **Sleep and wake with the lid**, **Hibernate powers off and stays off**, **One password after hibernate**, **Battery log around sleep**; tests in
`test/test_sleep_power_themes.py` (every installer in a sandbox with fake commands).

---

Related: [docs/SLEEP](../docs/SLEEP.md) · [docs/FIELD-NOTES](../docs/FIELD-NOTES.md) · [power/](../power/README.md) · [docs/ARCHITECTURE](../docs/ARCHITECTURE.md) · [docs/INDEX](../docs/INDEX.md)
