# Sleep, the lid and hibernate on a MacBookPro11,3

> **TL;DR.** On this MacBook deep sleep never wakes when the lid opens, so closing the lid uses light sleep (s2idle), which wakes at once but keeps the fans spinning and costs battery. Hibernate works, stays off, and can ask for one password. This page has the measurements, what is installed, how to check and undo each piece, and the open decision about the lid.

Related: [sleep/README](../sleep/README.md) · [POWER-LAB](POWER-LAB.md) · [FIELD-NOTES](FIELD-NOTES.md) · [GLOSSARY](GLOSSARY.md) · [INDEX](INDEX.md)

What was found, what is set up, how to check it, and how to undo each piece. Everything here was measured on this machine
(MacBook Pro 15" mid-2014, Intel Iris Pro + a switched-off NVIDIA, Omarchy 4, kernel 7.2) on 2026-10-07.

## In one minute

| Piece | What it does | Installer (all take `--remove`) |
|---|---|---|
| Light sleep | Closing the lid suspends to light sleep (s2idle); the lid wakes it at once | `sudo sleep/install-s2idle` |
| Hibernate that stays off | Hibernate saves the session and powers off like a normal shutdown | `sudo sleep/install-hibernate-mode` |
| One password after hibernate | A plain hibernate skips the lock screen: disk passphrase only | `sleep/install-hibernate-nolock` (no root) |
| Sleep battery log | Records the battery around every sleep; `sleep-check` turns it into mAh and watts | `sudo sleep/install-battery-log` |

Check everything at any time with `sleep/sleep-check` (every suspend and hibernate, its mode, how long, how much battery) and the
**Sleep** rows of the Setup log page.

## The symptom

The first real lid test: closed for about 4.5 minutes, opened, nothing. The screen stayed black until a key or the power button was
pressed. The kernel had suspended correctly and resumed in about a second once it was woken; the problem was that opening the lid
did not wake it. It failed the same way in a second test, even with the embedded controller (EC) allowed to wake the machine.

## What the firmware says (read from this Mac's DSDT)

* The lid (`LID0`), the EC and the AC adapter all wake the machine through the same line, **GPE 0x23** (lowest state S4 on a "Darwin"
  boot, S3 otherwise); the USB controller (`XHC1`) uses GPE 0x0D. Both fire on every wake, so the GPE counters cannot tell causes apart.
* `LID0._PSW(1)` sets an EC flag (`EWLO`, EC byte 0x68 bit 0) to wake on the lid, but only if the EC reports itself ready; `_PTS` clears it
  for S4 on non-Darwin boots. The flag reads 0 while the machine is awake, which is expected.
* The lid-close event woke the machine in one test (lid open when the suspend began, then closed), so the hardware does see the lid.
  Opening a lid that was closed before the suspend does not wake deep sleep (S3). The decision is made inside the EC's own firmware,
  which Linux cannot change. The exact cause was not found.
* **Light sleep (s2idle) wakes on the lid immediately** (three tests: the machine was running again about 1.3 s after opening). In
  s2idle the OS is alive, so the EC's lid event is handled like any other.

## Light sleep and its price

`install-s2idle` writes one systemd-tmpfiles rule that sets `/sys/power/mem_sleep` to `s2idle` early in every boot (no kernel parameter,
no bootloader change). The price:

* **The fans never stop.** The Mac counts as running in s2idle, and Apple's fan controller only powers the fans off in deep sleep
  (their floor is about 2,100 rpm). A closed lid also traps heat, so they spin faster for the first minute.
* **More battery.** The first reading was about 8 W with the lid closed (3.7 minutes, flagged too short to trust). A 10-minute closed-lid
  test on battery gives the real figure: unplug, close the lid for 10 minutes or more, open, run `sleep/sleep-check`.

## Hibernate

Omarchy had already set it up: a 15.5 GB swapfile on btrfs, `resume=` and `resume_offset=` on the kernel command line, the initramfs
`resume` hook. It works, with two things to know:

1. **Default mode restarts the Mac.** systemd's default (`platform`, the firmware's S4) saved the image, then the Mac switched itself
   back on within seconds. `install-hibernate-mode` sets `HibernateMode=shutdown`: the same image, then an ordinary power-off. Verified:
   it stays off until the power button.
2. **Two passwords by default.** The disk passphrase is needed before anything can be read, and Omarchy locks the screen before every
   sleep. Saving about 6.7 GB took about 30 seconds; restoring reads the same image back (not timed separately; a full
round trip including a two-minute wait and typing the passphrase took 5.5 minutes).

### One password: the no-lock shim

Omarchy's lock has no unlock command, so the only way to avoid the second password is not to lock before a *plain hibernate*. The disk
passphrase already protects the saved image, and on a cold boot Omarchy logs you straight in after it.
`install-hibernate-nolock` points the user service `omarchy-sleep-lock` (through a drop-in that sets `OMARCHY_PATH` for that one service)
at `~/.local/share/omarchy-kit/sleep-lock-shim`, which holds a symlink to the real monitor and `sleep/sleep-lock-policy`. The policy skips
the lock only when logind's newest "The system will ... now!" line (last 15 s) is exactly `hibernate now!`. Suspend, hybrid,
suspend-then-hibernate, any doubt or error run Omarchy's real lock script. No Omarchy file is edited; the Setup row turns red if a
future Omarchy changes the monitor. The installer also refuses unless the resume device sits on an encrypted volume (the whole idea
is that the disk passphrase protects the image), and if the real lock script ever goes missing the policy falls back to a plain
session lock instead of running nothing.

Risks accepted: for the roughly 30 s the image takes to save the screen is unlocked; if a hibernate ever fails and the machine stays on,
it stays unlocked. After the restore, do not type your password out of habit: it would land in the focused window.

## The battery log

`install-battery-log` installs a hook that writes the battery charge before and after every sleep (journal tag `sleep-battery`).
**The hook must live in `/usr/lib/systemd/system-sleep/`**: this systemd reads no other folder, and a copy in `/etc/systemd/system-sleep/`
silently never runs (that was the first attempt). Drain is only trusted for sleeps of 10 minutes or more on battery; the awake seconds
around a short sleep dominate the figure.

## Open decision: the lid and hibernate together

"Light sleep first, then hibernate after about 15 minutes" (`suspend-then-hibernate`) gives an instant wake for short breaks and silent,
fanless, near-zero drain for long ones. The price: that automatic path still asks two passwords (the lock is already on from the first
phase and cannot be opened by a script). Not installed; waiting for the closed-lid battery measurement and a yes or no.

## Pitfalls that cost time (so you do not repeat them)

* **Clocks disagree across sleep.** The kernel print clock, `CLOCK_MONOTONIC`, journald's receive time and the wake-source timestamps
  differ by seconds after an S3 resume. A fake "22 second stall" came from mixing them. Use journald's realtime only for events on one
  side of the sleep.
* **`journalctl -k` implies the current boot only.** `sleep-check` once reported "never suspended" after a reboot for that reason; it now
  matches `_TRANSPORT=kernel`.
* **Never remove or rescan PCI devices on this machine.** A PCI rescan crashed the kernel (an oops in `intel_rapl_msr`), killed the test
  that was about to restore the screen, and the next suspend hung. See `docs/POWER-LAB.md`.
* **Check for a package-owned config before adding one** (`ls` the folder, `pacman -Qo`): the Wi-Fi power-saving file overrides an
  Omarchy default and needed an honest trade-off note.

## Files

`sleep/sleep-check`, `sleep/install-s2idle`, `sleep/install-hibernate-mode`, `sleep/install-hibernate-nolock`, `sleep/sleep-lock-policy`,
`sleep/install-battery-log`, `sleep/battery-log`, `sleep/acpi-prw-scan` (reads a DSDT for `_PRW` wake definitions). Every change has an
EN/ES record with its undo on the Setup log page.

---

Related: [sleep/README](../sleep/README.md) · [POWER-LAB](POWER-LAB.md) · [FIELD-NOTES](FIELD-NOTES.md) · [GLOSSARY](GLOSSARY.md) · [INDEX](INDEX.md)
