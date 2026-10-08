# Power lab: where a 2014 MacBook Pro's battery goes

Findings from measuring a MacBookPro11,3 (15", mid-2014, Core i7-4870HQ, Intel Iris Pro + a switched-off NVIDIA GT 750M) running
Omarchy / Hyprland on kernel 7.2. Everything below was measured with `power/power-lab`, on battery, with the terminal idle.
The numbers are for this machine and this battery (about 75 % of its original capacity, 71 Wh when full); the method is general.

## Why the method matters

* **A busy terminal costs about 4 W by itself.** A working Claude window (animated spinner, streaming text) keeps the graphics chip
  and display engine awake: the Intel GPU idled only 48 % of the time and raised 128 display interrupts a second, against 100 % idle
  and 0 interrupts when the terminal was quiet. So every measurement is taken by a background service while the terminal is idle.
  `power-lab` re-launches itself that way after one sudo prompt.
* **Read the battery, not an estimate.** Draw = `current_now x voltage_now` from `/sys/class/power_supply/BAT0`, averaged over 20-35 s
  (single samples swing by +-3 W). Run on battery: the charger hides the draw.
* **Noise is about +-1 W.** Baselines taken minutes apart wandered between 14.9 and 16.2 W. A change below about 1 W needs repeating
  before it is believed.
* **Deep sleep is all-or-nothing.** The CPU package only enters its deep states when *every* blocker is cleared, so single changes can
  look like nothing even when they matter. That is why `power-lab stack` applies fixes cumulatively.

## Where the 20 W goes

| Piece | Watts | How it was isolated |
|---|---|---|
| Backlight at 73 % | about 5.0 | 20.0 W normal vs 15.0 W with the backlight at 0 |
| Display pipeline and panel electronics | about 4.4 | 15.1 W vs 10.7 W with the display switched off (`dpms disable`) |
| CPU package (cores, graphics, uncore) | about 4.8 | RAPL `package-0` counter, display on |
| Memory (DRAM) | about 1.7 | RAPL `dram` counter |
| The rest: fans at their floor, SSD, Wi-Fi, conversion losses | about 4 | what is left |

The CPU itself is 97 % idle and 99 % of that idle time is in core C7. The expensive part is the **package**: with the display on it
sits in the shallow state PC2 for about 90 % of the time, with the display off in PC3 (about 88 %), and **PC6/PC7 stayed at 0 % in
every test**. Deep package sleep would cut the package to roughly a quarter of its power.

## What was tried

Single changes, each reverted straight after (`power-lab singles`, noise about +-1 W):

| Change | Effect |
|---|---|
| Wi-Fi power saving on | **-0.94 W** (also -0.9 W in the cumulative run) |
| Fan floor lowered from about 2,100 to 1,200 rpm | -0.73 W (one run; needs repeating) |
| PCIe ASPM `powersave` | -0.21 W (ASPM was already on for most links) |
| Camera driver unloaded | +0.13 W (nothing) |
| SATA link power saving | 0.00 W |
| NMI watchdog off | +0.07 W |
| Sleep allowed for the SSD controller and the Intel ME | +0.46 W (noise) |

**Wi-Fi power saving is a trade-off, not free.** Omarchy ships `wifi.powersave = 2` (off) on purpose: power saving can add
20-300 ms latency spikes on idle links, and some Intel firmware drops the link when it naps. `power/install-wifi-powersave`
overrides that with a file that sorts later. On this machine (Broadcom wl, this router) replies on an idle link took 2.3-5.8 ms with
power saving on, with no spikes. The case that test cannot show is an unsolicited packet arriving while the card dozes (it can wait
up to about a beacon interval, roughly 100 ms): fine for chat and browsing, possibly noticeable in real-time games or calls.

Cumulative (`power-lab stack`, display on): baseline 15.3 W, all fixes 13.8 W, i.e. about 1.5 W, nearly all of it Wi-Fi power saving.
With the display off, every fix applied: 9.0 W against 9.4 W unfixed.

## What was ruled out

* **The CPU is not capped by the firmware.** `power/msr-probe`: package C-state limit C7s, register unlocked, no auto-demotion.
* **The discrete GPU is off.** The link is down; the kit keeps the real vga_switcheroo state in `/run/nvidia-off.status` because
  sysfs `power_state` reads D0 after a sleep even when the card is off.
* **PCIe link power saving is largely on already** (L0s/L1 enabled on most links). Off only for the camera and the Thunderbolt parts.

## What is still open

* **What blocks deep package sleep.** Not a setting we could find. A systematic search (taking PCIe devices out one at a time while
  watching the package) is possible but slow; worth up to about 3 W.
* **The display.** The graphics driver reports `FBC disabled: stolen memory not initialised`: Apple's firmware reserved no graphics
  memory, so the screen cannot be compressed and is read in full from RAM 60 times a second. There is no panel self-refresh either.
  That is a firmware limit, not a setting.
* **Fan floor** at 1,200 rpm: promising (-0.73 W, and quieter) but measured once.

## A warning from this work

**Do not unload the `thunderbolt` driver while its idle controller is allowed to runtime-sleep.** On this machine the reload failed
(`device inaccessible`, `timeout resetting host router`, probe error -22) and the Falcon Ridge controller vanished from the PCI bus
until the next reboot. The saving it offered (at most about 0.7 W) is below the noise, so `power-lab` no longer tests it.

## Using the tool

```
power/power-lab quiet --check     # look only: what it detected on this machine
power/power-lab quiet             # about 2 min
power/power-lab breakdown         # about 3 min, adds CPU-package power and package sleep states
power/power-lab singles           # about 9 min
power/power-lab stack             # about 9 min
power/power-lab results [mode]    # show the last results (data/power-lab/, not committed)
```

Keep the charger unplugged and your hands off the keyboard and trackpad while a test runs (input wakes the display). The screen goes
dark for a few minutes and comes back by itself. Nothing is permanent: each change is reverted right after its measurement and on any
exit; the backlight and display are restored at the end.
