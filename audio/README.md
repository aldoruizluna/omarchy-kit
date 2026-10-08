# audio/: speaker EQ that bypasses itself for headphones

> **TL;DR.** The 2014 MacBook speakers get a voicing EQ (a high-pass, a warmth boost, a de-boxing cut, a presence cut, some air) installed in Omarchy's
> speaker-tuning layout. A watcher sends only the speakers through it. It is unmeasured voicing for small laptop drivers, not a measured correction.

| File | What |
|---|---|
| `design_eq.py` | computes the exact response of the biquad chain and the pre-gain that keeps it at or below -0.5 dB (no limiter needed); writes `eq_design.json` and `macbookpro11-speakers.conf` |
| `macbookpro11-speakers.conf` | the PipeWire filter-chain settings that `design_eq.py` generates |
| `install-speaker-eq` | no root: installs the tuning in `~/.config/pipewire/` and the user services; re-run after editing `design_eq.py`; `--remove` undoes it (`omarchy-audio-tuning off`) |
| `speaker-eq-follow` (+ `.service`) | speakers and headphones are two ports of one hardware sink, so this points the default output at the EQ for speakers and straight at the hardware for headphones; it leaves Bluetooth and HDMI choices alone |

The tuning talks to RTKit directly (`rtportal.enabled = false`): the desktop portal reported a 0 us realtime budget here and the kernel killed the audio thread.

Checked by: Setup log rows **Speaker EQ, bypassed for headphones**, **Realtime audio priority (rtkit)**.

---

Related: [docs/FIELD-NOTES](../docs/FIELD-NOTES.md) · [docs/ARCHITECTURE](../docs/ARCHITECTURE.md) · [docs/INDEX](../docs/INDEX.md)
