# Field notes: hard-won rules for this machine

Short, checkable rules learned the hard way while setting up a MacBookPro11,3 with Omarchy 4. Each says what, why, and where it is
recorded. If you are a person or an assistant about to change something on this machine, read this first.

## Measuring

* **Measure power with the terminal idle.** A working terminal (animated spinner, streaming text) repaints the screen and adds about
  4 W by itself. Run tests as a background service that wakes you when it ends; `power/power-lab` does this.
* **A background job must BE the process.** `nohup cmd &` inside a "background command" returns at once, so it signals completion
  immediately. Make the long process itself the background command.
* **Read the battery, not a guess**: draw = `current_now x voltage_now`, averaged over 20 to 35 s (single samples swing by 3 W), on
  battery. Noise is about 1 W; repeat anything smaller.
* **Never quote `/sys/class/power_supply/BAT0/capacity`.** It is relative to the battery when new (69 %) while the menu shows charge
  against what it holds today (93 %). Use `charge_now / charge_full`.

## Things that must not be done

* **Do not remove or rescan PCI devices** (`/sys/bus/pci/.../remove`, `/sys/bus/pci/rescan`): the rescan crashed the kernel. Docs: SLEEP.md.
* **Do not unload the `thunderbolt` driver while its idle controller may runtime-sleep.** It could not be woken again and vanished from
  the PCI bus until reboot.
* **Do not trust timestamps that span a sleep** (kernel, monotonic and journald clocks disagree).
* **Do not use `journalctl -k` for history**: it implies the current boot. Match `_TRANSPORT=kernel`.

## How this system behaves

* **systemd 261 reads sleep hooks only from `/usr/lib/systemd/system-sleep/`.** A hook in `/etc/systemd/system-sleep/` never runs.
* **Omarchy's lock has no unlock command** (only lock, status, preview). One password after hibernate needed a user-level shim.
* **Hyprland (Lua config) accepts `hl.dsp.dpms({ action = "enable" | "disable" | "toggle" })` only.** Any other word acts as a toggle: it
  switched the screen off once by accident. Verify with `hyprctl monitors | grep dpms`.
* **Omarchy ships its own config for some things** (e.g. `/etc/NetworkManager/conf.d/omarchy-wifi-powersave.conf`). Check with `ls` and
  `pacman -Qo` before adding a file; a file that sorts later wins.
* **fcitx5 is owned by its user unit.** Restart it with `systemctl --user restart omarchy-fcitx5`; a hand-started copy made the unit
  restart itself every two seconds.
* **sysfs `power_state` for the NVIDIA card reads D0 after a sleep even when it is off.** Use `gpu/gpu-status`, which keeps the real
  vga_switcheroo state.

## Writing and testing scripts here

* **A script that changes the machine must refuse unknown arguments.** Every kit installer once treated anything but `--remove` as
  "install", so an audit probe with `--help` really installed two of them (harmless, because they are idempotent, but only by luck).
  All of them now print their usage on `--help` and exit 2 on anything unknown. Read a script's argument handling before running
  it with a flag you are only guessing at.
* **Test installers in a sandbox.** `test/test_sleep_power_themes.py` runs them in temporary directories with fake commands in the
  PATH, so a test can never install anything for real.
* **Restart the portal after editing Python.** `omarchy-kit.service` imports `build_setup` once and keeps it; a rebuilt page still
  shows the old checks until `systemctl --user restart omarchy-kit`.
* **Check text colours on every surface**, not just the card. Muted text and links were readable on the card but fell to 3.2:1 on
  the page background and on `kbd` chips in 28 of Omarchy's themes; `kitlive.theme_css` now checks all four surfaces. Leave a small
  margin: the CSS rounds colours to 8 bits.
* **Fail closed.** A lock policy that cannot find the real lock script must still lock (it falls back to `omarchy-system-lock`, then
  `loginctl lock-session`), and the no-lock installer refuses when the hibernate image is not on an encrypted volume.
* **Quote what goes into a service command.** The `power-lab` rescue line is parsed by systemd; an empty value without `=` broke it.

## Working in the `!` prompt

* **Only the first `sudo` in a `&&` chain runs.** Use one `sudo bash -c '...'` per step batch, or a script run with `sudo`.
* **Installers are run by the owner.** An assistant's attempt to install something that lowers a security control (the no-lock shim) is
  blocked by the harness's auto-mode classifier, and that is correct: the owner runs those himself.
* **Chain edit, build and commit with `&&`.** An edit that failed mid-script once let the following commit go ahead with a message that
  overclaimed; it was caught and amended before pushing.

## Public repository hygiene

* Built pages, `data/`, `backups/`, `local.toml`, `*.bak*` are git-ignored on purpose: they hold the co-admin's name, network names and
  firmware dumps. Never commit personal details, Wi-Fi names, efivar or boot-entry dumps.
* Scan before every push: usernames, home paths, hostnames, MAC/IP addresses, UUIDs, private product names, and **inside images**
  (preview screenshots once showed the real username).
* Themes carry only original art. No official artwork, logos or character likenesses; credit the open-source works that inspired a theme,
  not the original brand.
