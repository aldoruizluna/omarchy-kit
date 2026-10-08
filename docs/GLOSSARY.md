# Glossary

> **TL;DR.** One definition per term used across the docs, alphabetical, each with a link to where it is explained in depth. The portal has a
> shorter, bilingual glossary on its Reference page; this one is the precise, English reference for readers and tools.

Related: [INDEX](INDEX.md) · [ARCHITECTURE](ARCHITECTURE.md) · [SLEEP](SLEEP.md) · [POWER-LAB](POWER-LAB.md) · [FIELD-NOTES](FIELD-NOTES.md)

## A to C

**ASPM** (Active State Power Management). Lets a PCIe link drop into low-power states (L0s, L1) when idle. The kernel can refuse to enable it on a link; on this Mac the Thunderbolt links refused. See [POWER-LAB](POWER-LAB.md).

**Binding description (`"k"`).** The name Omarchy gives a shortcut (for example "Terminal"). Lessons and Mac habits refer to shortcuts by it, so pages show *your current keys* and a shortcut that no longer exists shows as "not bound". See [ARCHITECTURE](ARCHITECTURE.md#the-learning-engine).

**btrfs.** The file system of this Mac's disk; snapshots (restore points) depend on it. See [backup/README](../backup/README.md).

**Check (lesson).** What the Learn page verifies after a step, through `/api/state` (a window opened, a space changed, a theme switched). *Edge-triggered*: the goal must be false at some point after the step starts. See [ARCHITECTURE](ARCHITECTURE.md#the-learning-engine).

**Check (Setup log).** A live status computed by `checks()` in `build_setup.py`: `ok`, `action`, `pending` or `info`, with English and Spanish text. See [ARCHITECTURE](ARCHITECTURE.md#the-setup-log).

**Core (RetroArch).** The emulator library RetroArch loads for a system; `games/systems.toml` names the best one per system on this machine. See [games/README](../games/README.md).

**CC BY 4.0.** The Creative Commons Attribution licence that covers the themes' palettes, files, previews, wallpapers and texts. See [themes/LICENSE](../themes/LICENSE).

## D to H

**Deep sleep (S3).** The classic suspend: almost everything is off. On this MacBook, opening the lid does not wake it from this state (the embedded controller's firmware decides, and Linux cannot change it). See [SLEEP](SLEEP.md).

**Delay inhibitor (`PrepareForSleep`).** A lock systemd-logind honours so a program can finish work (here: lock the screen) before the machine sleeps. Omarchy's lock monitor holds one. See [SLEEP](SLEEP.md#one-password-the-no-lock-shim).

**Drop-in.** A small file in `name.service.d/` that overrides part of a systemd unit without editing it. The no-lock installer uses one to set `OMARCHY_PATH` for a single service. See [sleep/README](../sleep/README.md).

**DSDT and `_PRW`.** The ACPI firmware table, and the method in it that declares which devices may wake the machine and from which sleep state. `sleep/acpi-prw-scan` lists them. See [SLEEP](SLEEP.md#what-the-firmware-says-read-from-this-macs-dsdt).

**EC** (embedded controller). A small chip that handles the lid, fans, power button and charger. Its code is not changeable from Linux. See [SLEEP](SLEEP.md).

**ES-DE.** EmulationStation Desktop Edition, the frontend `kit-games esde` configures over the library. See [games/README](../games/README.md).

**ExecStopPost.** A systemd step that runs after a service ends *however* it ends (finished, killed, crashed). `power-lab` uses it to put the display and backlight back. See [power/README](../power/README.md).

**fnmode.** The `hid_apple` kernel parameter that decides whether the top row sends media keys first (1) or function keys (2); 3 is "auto", media-first on a real Apple keyboard. See [MAC-FEEL](MAC-FEEL.md).

**fcitx5.** The input method Omarchy runs. It copies the keyboard layout only when it starts, so restart it (`systemctl --user restart omarchy-fcitx5`) after changing the layout. See [FIELD-NOTES](FIELD-NOTES.md).

**GPE** (general-purpose event). An ACPI wake line. The lid, the EC and the AC adapter share GPE 0x23; the USB controller (XHC1) uses 0x0D. Both fire on every wake, so counters cannot tell causes apart. See [SLEEP](SLEEP.md).

**Hermetic test.** A test that cannot touch the real machine or network: temporary directories, fake commands in `PATH`, no root. See [test/README](../test/README.md).

**Hibernate.** Save everything in memory to the encrypted disk and power off completely; on the next start you type the disk passphrase and the session returns. Here `HibernateMode=shutdown` makes it stay off. See [SLEEP](SLEEP.md#hibernate).

**Hyprland.** The Wayland compositor Omarchy uses. Its configuration here is Lua; `hyprctl` queries and drives it. The tests call it directly (`hyprctl eval`). See [keys/README](../keys/README.md).

## I to P

**Installer contract.** Idempotent; `--remove` undoes it; `--help` prints usage; an unknown option exits 2 without installing; fails closed. See [ARCHITECTURE](ARCHITECTURE.md#the-scripts-that-change-the-machine).

**Light sleep (s2idle).** The machine keeps running at a whisper, so opening the lid wakes it at once. Costs: fans keep spinning and the battery drains faster. See [SLEEP](SLEEP.md#light-sleep-and-its-price).

**LUKS.** Disk encryption. The disk passphrase typed at start-up is what protects the hibernate image, which is why the no-lock installer refuses without it. See [SLEEP](SLEEP.md).

**MSR** (model-specific register). CPU registers read through `/dev/cpu/N/msr`; `power/msr-probe` reads the package C-state limit (register `0xE2`) without changing anything. See [POWER-LAB](POWER-LAB.md).

**No-lock shim.** A user-level stand-in for Omarchy's sleep-lock script that skips the lock screen only before a plain hibernate. See [SLEEP](SLEEP.md#one-password-the-no-lock-shim).

**Omarchy.** The Arch Linux + Hyprland desktop this kit teaches and configures; its commands are `omarchy ...` and `omarchy-*`. See [README](../README.md).

**Package C-state (PC2 to PC7).** How deeply the whole CPU package sleeps when idle. This Mac sits in PC2 or PC3 and never reaches PC6/PC7, which costs battery; the cause was not found. See [POWER-LAB](POWER-LAB.md).

**Power lab.** `power/power-lab`: measures real battery draw and tries power-saving changes one at a time, reverting each. See [POWER-LAB](POWER-LAB.md).

## R to Z

**RAPL** (running average power limit). Intel energy counters (`package-0`, `dram`) the power lab reads to split the draw. See [POWER-LAB](POWER-LAB.md).

**Setup log.** The page `/setup`: a live health check of every change this kit can make, a record of each with its undo command, open items and ideas deliberately not done. See [ARCHITECTURE](ARCHITECTURE.md#the-setup-log).

**Signed catalog snapshot.** A versioned list of free games a publisher signs (ECDSA P-256); the store client trusts it only if the checksum and signature verify against a key you saved and the version is newer. See [GAME-STORE-ROADMAP](GAME-STORE-ROADMAP.md).

**Snapper.** The btrfs snapshot manager behind the hourly `/home` snapshots. See [backup/README](../backup/README.md).

**Super key.** The ⌘ command key on this MacBook; nearly every Omarchy shortcut starts with it. See [MAC-FEEL](MAC-FEEL.md).

**system-sleep hook.** An executable in `/usr/lib/systemd/system-sleep/` that systemd runs before and after every sleep. It is the *only* folder this systemd reads. See [FIELD-NOTES](FIELD-NOTES.md).

**Theme (Omarchy).** A folder, not a setting: `colors.toml` is its heart, and Omarchy's templates turn it into the terminal, bar, editor and lock-screen colours. See [THEMES](THEMES.md).

**tmpfiles.d.** systemd's way to write a value at boot; `install-s2idle` uses one line to set `/sys/power/mem_sleep`. See [sleep/README](../sleep/README.md).

**vga_switcheroo.** The kernel interface that switches or powers off a hybrid GPU. `gpu/nvidia-off` writes OFF to it; never ON. See [gpu/README](../gpu/README.md).

---

Related: [INDEX](INDEX.md) · [ARCHITECTURE](ARCHITECTURE.md) · [SLEEP](SLEEP.md) · [POWER-LAB](POWER-LAB.md) · [FIELD-NOTES](FIELD-NOTES.md) · [README](../README.md)
