"""Tests for the tools added around sleep, power and themes. Standard library only, no root, nothing touches the real system.

  python3 -B test/test_sleep_power_themes.py            # or: python3 -B -m unittest discover -s test -p 'test_*.py'

What is covered (and how it stays sandboxed):
  sleep/sleep-lock-policy   the lock/hibernate decision, via its SLEEP_LOCK_POLICY_LINES hook; the non --check path runs a COPY of the
                            script whose REAL_PATH points at a fake lock script, with a fake `logger` (the real lock never runs)
  sleep/sleep-check         journal parsing, suspend/hibernate pairing, lid windows, battery drain, verdicts: the module is loaded
                            from its file and journal() / Path are patched; plus one end-to-end run with a fake `journalctl`
  sleep/battery-log         its journal line must match what sleep-check parses (cross-tool contract)
  themes/install-themes     runs a copy of the script in a temp "kit" with XDG_CONFIG_HOME in a temp dir
  power/power-lab           mode registry, --check, the hunt simulation, reversible changes, the relaunch/ExecStopPost rescue
                            property: module loaded from its file, sysfs reads/writes replaced by an in-memory fake
  power/power-auto, install-power-auto   fake powerprofilesctl / systemctl in PATH, HOME and XDG_CONFIG_HOME in a temp dir
  sleep/install-*, power/install-wifi-powersave   they need root and write /etc, /usr/lib: they run inside `unshare -Urm` (a private
                            user + mount namespace, no real root) with tmpfs mounted over the target folders; skipped if unavailable

Tests marked expectedFailure document real defects found in the audit: when the tool is fixed they start to "unexpectedly succeed",
which is the cue to remove the marker.
"""
import importlib.machinery, importlib.util, io, json, os, pathlib, re, shlex, shutil, stat, subprocess, sys, tempfile, textwrap, unittest
from contextlib import redirect_stdout
from unittest import mock

sys.dont_write_bytecode = True   # loading extension-less scripts would otherwise write __pycache__ into the repo

HERE = pathlib.Path(__file__).resolve().parent
KIT = HERE.parent   # this file lives in <kit>/test/
SAFE_PATH = "/usr/bin:/bin"


def load(path, name):
    loader = importlib.machinery.SourceFileLoader(name, str(path))
    mod = importlib.util.module_from_spec(importlib.util.spec_from_loader(name, loader))
    loader.exec_module(mod)
    return mod


def write_exec(path, body):
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("#!/bin/bash\n" + textwrap.dedent(body))
    path.chmod(0o755)
    return path


def fake_bin(d, **cmds):
    """Create fake commands in directory d; each body is bash. Every fake also logs its arguments to <d>/calls.log."""
    d = pathlib.Path(d)
    for name, body in cmds.items():
        write_exec(d / name, f'echo "{name} $*" >> "{d}/calls.log"\n' + textwrap.dedent(body))
    return d


def calls(d):
    f = pathlib.Path(d) / "calls.log"
    return f.read_text().splitlines() if f.exists() else []


def run(cmd, env=None, timeout=60, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env=env, **kw)


def tree(root):
    root = pathlib.Path(root)
    return sorted(str(p.relative_to(root)) + ("/" if p.is_dir() else "") for p in root.rglob("*"))


def userns_ok():
    if os.geteuid() == 0:
        return False
    try:
        return run(["unshare", "-Urm", "true"], timeout=10).returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


USERNS = userns_ok()


def in_userns(script, *args, env=None):
    """Run a bash driver as (fake) root in a private user+mount namespace; returns {KEY: value} from its KEY=value output lines."""
    r = run(["unshare", "-Urm", "bash", "-c", script, "driver", *args], env=env)
    out = dict(l.split("=", 1) for l in r.stdout.splitlines() if re.match(r"^[A-Z_0-9]+=", l))
    out["_stderr"] = r.stderr
    return out


class Sandbox(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="kit-test-")
        self.addCleanup(self._tmp.cleanup)
        self.tmp = pathlib.Path(self._tmp.name)


# ======================================================================================================================
# sleep/sleep-lock-policy
# ======================================================================================================================
POLICY = KIT / "sleep" / "sleep-lock-policy"


class SleepLockPolicy(Sandbox):
    def decide(self, text, *, missing=False):
        f = self.tmp / "lines.txt"
        if not missing:
            f.write_text(text)
        r = run(["bash", str(POLICY), "--check"], env={"PATH": SAFE_PATH, "SLEEP_LOCK_POLICY_LINES": str(f)})
        self.assertEqual(r.returncode, 0, r.stderr)
        return r.stdout.strip()

    def test_only_the_exact_plain_hibernate_line_skips_the_lock(self):
        self.assertEqual(self.decide("The system will hibernate now!\n"), "hibernate")

    def test_everything_else_locks(self):
        for line in ["The system will suspend now!", "The system will hybrid-sleep now!", "The system will suspend and hibernate now!",
                     "The system will suspend then hibernate now!", "The system will power off now!", "The system will reboot now!",
                     "The system will hibernate now! ", "The system will hibernate now!!", "The system will hibernate soon!",
                     "the system will hibernate now!", "The system will hibernate now", "Something: The system will hibernate now!",
                     " The system will hibernate now!", "The system will hibernate now!\r", ""]:
            with self.subTest(line=line):
                self.assertEqual(self.decide(line + "\n"), "lock")

    def test_most_recent_decision_line_wins(self):
        self.assertEqual(self.decide("The system will hibernate now!\nThe system will suspend now!\n"), "lock")
        self.assertEqual(self.decide("The system will suspend now!\nnoise\nThe system will hibernate now!\nLid closed.\n"), "hibernate")

    def test_unrelated_lines_and_empty_or_missing_log_lock(self):
        self.assertEqual(self.decide("Lid closed.\nNew seat seat0.\n"), "lock")
        self.assertEqual(self.decide(""), "lock")
        self.assertEqual(self.decide("", missing=True), "lock")

    def sandboxed_copy(self):
        """A copy of the script whose REAL_PATH is a fake Omarchy folder; returns (script, fake_real_lock_log, fake_bin_dir)."""
        text = POLICY.read_text()
        self.assertIn("REAL_PATH=/usr/share/omarchy\n", text, "the script changed: update this test's sandbox")
        real = self.tmp / "omarchy"
        write_exec(real / "bin" / "omarchy-system-sleep-lock", f'echo "LOCKED args=[$*] OMARCHY_PATH=$OMARCHY_PATH" >> "{self.tmp}/lock.log"\n')
        script = self.tmp / "policy"
        script.write_text(text.replace("REAL_PATH=/usr/share/omarchy\n", f"REAL_PATH={real}\n"))
        return script, self.tmp / "lock.log", fake_bin(self.tmp / "fb", logger="exit 0"), real

    def go(self, script, fb, line, *args):
        f = self.tmp / "lines.txt"
        f.write_text(line + "\n")
        return run(["bash", str(script), *args], env={"PATH": f"{fb}:{SAFE_PATH}", "SLEEP_LOCK_POLICY_LINES": str(f)})

    def test_plain_hibernate_does_not_run_the_real_lock_and_logs_why(self):
        script, lock_log, fb, _ = self.sandboxed_copy()
        r = self.go(script, fb, "The system will hibernate now!")
        self.assertEqual(r.returncode, 0)
        self.assertFalse(lock_log.exists(), "the real lock must not run before a plain hibernate")
        self.assertTrue(any(c.startswith("logger -t sleep-lock-policy") for c in calls(fb)), calls(fb))

    def test_suspend_runs_the_real_lock_with_the_original_arguments_and_omarchy_path(self):
        script, lock_log, fb, real = self.sandboxed_copy()
        r = self.go(script, fb, "The system will suspend now!", "--some", "arg")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(lock_log.read_text().strip(), f"LOCKED args=[--some arg] OMARCHY_PATH={real}")
        self.assertEqual(calls(fb), [], "no 'not locking' log line for a suspend")

    def test_lock_decision_with_no_log_line_still_locks(self):
        script, lock_log, fb, _ = self.sandboxed_copy()
        self.assertEqual(self.go(script, fb, "").returncode, 0)
        self.assertTrue(lock_log.exists())

    def test_missing_real_lock_script_fails_loudly_not_silently(self):
        """Characterisation of a fail-open gap: with no real lock script nothing locks (audit finding). At least it must not exit 0."""
        script, lock_log, fb, real = self.sandboxed_copy()
        (real / "bin" / "omarchy-system-sleep-lock").unlink()
        r = self.go(script, fb, "The system will suspend now!")
        self.assertNotEqual(r.returncode, 0)
        self.assertFalse(lock_log.exists())


# ======================================================================================================================
# sleep/sleep-check
# ======================================================================================================================
SC = load(KIT / "sleep" / "sleep-check", "sleep_check")


def K_ENTRY(t, mode="s2idle"): return (t, f"kernel: PM: suspend entry ({mode})" if mode else "kernel: PM: suspend entry")
def K_EXIT(t): return (t, "kernel: PM: suspend exit")
def H_ENTRY(t): return (t, "kernel: PM: hibernation: hibernation entry")
def H_EXIT(t): return (t, "kernel: PM: hibernation: hibernation exit")
def LID_C(t): return (t, "systemd-logind[1]: Lid closed.")
def LID_O(t): return (t, "systemd-logind[1]: Lid opened.")
def BAT(t, phase, charge, ac=0, volt=12_000_000): return (t, f"sleep-battery: {phase} suspend charge_uah={charge} full_uah=6000000 volt_uv={volt} ac={ac}")


def jfake(kernel=(), logind=(), battery=()):
    def journal(*args):
        if args == ("_TRANSPORT=kernel",): return list(kernel)
        if args == ("-u", "systemd-logind"): return list(logind)
        if args == ("-t", "sleep-battery"): return list(battery)
        raise AssertionError(f"unexpected journal query {args}")
    return journal


WAKEUP = "Device\tS-state\t  Status   Sysfs node\nXHC1\t  S3\t*enabled   pci:0000:00:14.0\nLID0\t  S3\t*enabled   platform:PNP0C0D:00\nEHC1\t  S3\t*disabled  pci:0000:00:1d.0\nPEG0\t  S3\t*enabled   pci:0000:00:01.0\n"


class SleepCheckReport(Sandbox):
    def report(self, kernel=(), logind=(), battery=(), wakeup=WAKEUP):
        wk = self.tmp / "wakeup"
        if wakeup is not None:
            wk.write_text(wakeup)
        real_path = pathlib.Path
        with mock.patch.object(SC, "journal", jfake(kernel, logind, battery)), \
             mock.patch.object(SC, "Path", lambda p: real_path(wk) if str(p) == "/proc/acpi/wakeup" else real_path(p)):
            return SC.report()

    def test_no_events_is_pending(self):
        r = self.report()
        self.assertEqual((r["status"], r["count"], r["cycles"], r["hibernates"]), ("pending", 0, [], []))
        self.assertIn("Close the lid", r["verdict"])

    def test_deep_sleep_asks_for_the_s2idle_fix(self):
        r = self.report([K_ENTRY(1000, "deep"), K_EXIT(1300)])
        self.assertEqual((r["status"], r["cycles"][0]["mode"]), ("action", "deep"))
        self.assertIn("install-s2idle", r["verdict"])

    def test_mode_detection(self):
        r = self.report([K_ENTRY(1000, "s2idle"), K_EXIT(1100), K_ENTRY(2000, "deep"), K_EXIT(2100), K_ENTRY(3000, None), K_EXIT(3100)])
        self.assertEqual([c["mode"] for c in r["cycles"]], ["s2idle", "deep", "?"])

    def test_self_wake_blames_xhc1_when_it_may_wake_the_machine(self):
        r = self.report([K_ENTRY(1000), K_EXIT(1005)])
        self.assertEqual((r["status"], r["cycles"][0]["secs"]), ("action", 5.0))
        self.assertIn("XHC1", r["verdict"])
        self.assertEqual(r["wake_enabled"], ["XHC1", "LID0"], "only XHC1/LID0/EHC1/EHC2 that are *enabled* are reported")

    def test_self_wake_without_xhc1_says_wake_sources_look_normal(self):
        r = self.report([K_ENTRY(1000), K_EXIT(1005)], wakeup="Device S-state Status Sysfs\nXHC1 S3 *disabled pci:x\nLID0 S3 *enabled platform:y\n")
        self.assertIn("look normal", r["verdict"])
        self.assertEqual(r["wake_enabled"], ["LID0"])

    def test_missing_wakeup_file_is_tolerated(self):
        r = self.report([K_ENTRY(1000), K_EXIT(1800)], wakeup=None)
        self.assertEqual((r["status"], r["wake_enabled"]), ("ok", []))

    def test_long_sleep_is_ok_and_reports_minutes(self):
        r = self.report([K_ENTRY(1000), K_EXIT(2800)])
        self.assertEqual(r["status"], "ok")
        self.assertIn("30.0 min", r["verdict"])

    def test_threshold_between_self_wake_and_ok_is_20_seconds(self):
        self.assertEqual(self.report([K_ENTRY(1000), K_EXIT(1019.9)])["status"], "action")
        self.assertEqual(self.report([K_ENTRY(1000), K_EXIT(1020)])["status"], "ok")

    def test_battery_drain_math(self):
        r = self.report([K_ENTRY(1000), K_EXIT(2800)], battery=[BAT(995, "pre", 5_000_000), BAT(2805, "post", 4_970_000)])
        b = r["cycles"][0]["battery"]
        # 30 mAh over 1810 s = 59.67 mA; at 12 V that is 0.716 W
        self.assertEqual((b["mah"], b["secs"], b["ma"], b["watts"], b["reliable"]), (30.0, 1810, 60, 0.7, True))
        self.assertIn("30 mAh", r["verdict"])
        self.assertIn("0.7 W", r["verdict"])

    def test_short_battery_window_is_marked_unreliable_and_kept_out_of_the_verdict(self):
        r = self.report([K_ENTRY(1000), K_EXIT(1100)], battery=[BAT(995, "pre", 5_000_000), BAT(1105, "post", 4_999_000)])
        self.assertFalse(r["cycles"][0]["battery"]["reliable"])
        self.assertNotIn("mAh", r["verdict"])

    def test_no_battery_figure_when_on_the_charger_or_outside_the_60_second_windows(self):
        self.assertNotIn("battery", self.report([K_ENTRY(1000), K_EXIT(2800)], battery=[BAT(995, "pre", 5_000_000, ac=1), BAT(2805, "post", 4_970_000)])["cycles"][0])
        self.assertNotIn("battery", self.report([K_ENTRY(1000), K_EXIT(2800)], battery=[BAT(995, "pre", 5_000_000), BAT(2805, "post", 4_970_000, ac=1)])["cycles"][0])
        self.assertNotIn("battery", self.report([K_ENTRY(1000), K_EXIT(2800)], battery=[BAT(930, "pre", 5_000_000), BAT(2805, "post", 4_970_000)])["cycles"][0])
        self.assertNotIn("battery", self.report([K_ENTRY(1000), K_EXIT(2800)], battery=[BAT(995, "pre", 5_000_000), BAT(2870, "post", 4_970_000)])["cycles"][0])

    def test_pairing_drops_an_entry_that_never_exited_and_an_exit_without_entry(self):
        r = self.report([K_EXIT(50), K_ENTRY(1000), K_ENTRY(2000), K_EXIT(2600)])
        self.assertEqual(r["count"], 1)
        self.assertEqual((r["cycles"][0]["entry"], r["cycles"][0]["exit"]), (2000, 2600))

    def test_only_the_last_five_cycles_are_returned_but_all_are_counted(self):
        ev = []
        for i in range(7):
            ev += [K_ENTRY(1000 + i * 1000), K_EXIT(1300 + i * 1000)]
        r = self.report(ev)
        self.assertEqual((r["count"], len(r["cycles"]), r["cycles"][0]["entry"]), (7, 5, 3000))

    def test_events_are_ordered_even_if_the_journal_returns_them_shuffled(self):
        r = self.report([K_EXIT(1300), K_ENTRY(1000)])
        self.assertEqual(r["count"], 1)

    def test_lid_closed_counts_only_in_the_30_seconds_before_the_suspend(self):
        for t_lid, expect in [(995, True), (1000, True), (971, True), (960, False), (1010, False)]:
            with self.subTest(lid_closed_at=t_lid):
                r = self.report([K_ENTRY(1000), K_EXIT(1500)], logind=[LID_C(t_lid)])
                self.assertEqual(r["cycles"][0]["lid_closed"], expect)

    def test_lid_opened_counts_between_the_suspend_and_5_seconds_after_the_resume(self):
        for t_lid, expect in [(1200, True), (1500, True), (1504, True), (1506, False), (999, False)]:
            with self.subTest(lid_opened_at=t_lid):
                r = self.report([K_ENTRY(1000), K_EXIT(1500)], logind=[LID_O(t_lid)])
                self.assertEqual(r["cycles"][0]["lid_opened"], expect)

    def test_hibernate_pairs_are_separate_from_suspend_cycles(self):
        r = self.report([H_EXIT(50), H_ENTRY(100), H_EXIT(400)])
        self.assertEqual(r["count"], 0)
        self.assertEqual(r["status"], "pending")
        self.assertEqual(r["hibernates"], [{"entry": 100, "exit": 400, "secs": 300.0}])

    def test_only_the_last_three_hibernates_are_kept(self):
        ev = []
        for i in range(5):
            ev += [H_ENTRY(1000 * (i + 1)), H_EXIT(1000 * (i + 1) + 60)]
        self.assertEqual([h["entry"] for h in self.report(ev)["hibernates"]], [3000, 4000, 5000])


class SleepCheckJournal(unittest.TestCase):
    def cp(self, out): return subprocess.CompletedProcess([], 0, stdout=out)

    def test_parses_short_unix_lines_and_ignores_the_rest(self):
        out = "1700000000.123456 mac kernel: PM: suspend entry (s2idle)\n-- Boot abc --\n\n1700000100.5 mac systemd-logind[1]: Lid opened.\n"
        with mock.patch.object(SC.subprocess, "run", return_value=self.cp(out)):
            rows = SC.journal("-u", "systemd-logind")
        self.assertEqual(rows, [(1700000000.123456, "kernel: PM: suspend entry (s2idle)"), (1700000100.5, "systemd-logind[1]: Lid opened.")])

    def test_command_line_reads_14_days_and_never_uses_dash_k(self):
        with mock.patch.object(SC.subprocess, "run", return_value=self.cp("")) as run:
            SC.journal("_TRANSPORT=kernel")
        cmd = run.call_args[0][0]
        self.assertEqual(cmd[0], "journalctl")
        self.assertEqual(cmd[cmd.index("--since") + 1], "14 days ago")
        self.assertNotIn("-k", cmd, "-k is current-boot only: a reboot would wipe the history")
        self.assertEqual(cmd[-1], "_TRANSPORT=kernel")
        self.assertIn("timeout", run.call_args[1])

    def test_a_failing_or_missing_journalctl_gives_no_rows(self):
        for exc in (FileNotFoundError(), subprocess.TimeoutExpired("journalctl", 15), PermissionError()):
            with self.subTest(exc=type(exc).__name__), mock.patch.object(SC.subprocess, "run", side_effect=exc):
                self.assertEqual(SC.journal("-t", "x"), [])


class SleepCheckCli(Sandbox):
    def fake_journalctl(self):
        fb = self.tmp / "fb"
        write_exec(fb / "journalctl", r'''
            case "$*" in
              *_TRANSPORT=kernel*) printf '%s\n' "1760000000.100000 mac kernel: PM: suspend entry (s2idle)" "1760001800.200000 mac kernel: PM: suspend exit" \
                                      "1760005000.000000 mac kernel: PM: hibernation: hibernation entry" "1760005300.000000 mac kernel: PM: hibernation: hibernation exit" ;;
              *systemd-logind*)   printf '%s\n' "1759999995.000000 mac systemd-logind[1]: Lid closed." "1760001800.000000 mac systemd-logind[1]: Lid opened." ;;
              *sleep-battery*)    printf '%s\n' "1759999990.000000 mac sleep-battery: pre suspend charge_uah=5000000 full_uah=6000000 volt_uv=12000000 ac=0" \
                                      "1760001805.000000 mac sleep-battery: post suspend charge_uah=4970000 full_uah=6000000 volt_uv=12000000 ac=0" ;;
            esac
        ''')
        return fb

    def test_json_and_human_output_end_to_end(self):
        env = {"PATH": f"{self.fake_journalctl()}:{SAFE_PATH}", "TZ": "UTC"}
        r = run(["python3", "-I", str(KIT / "sleep" / "sleep-check"), "--json"], env=env)
        self.assertEqual(r.returncode, 0, r.stderr)
        j = json.loads(r.stdout)
        self.assertEqual((j["count"], j["cycles"][0]["mode"], j["cycles"][0]["lid_closed"], j["cycles"][0]["lid_opened"]), (1, "s2idle", True, True))
        self.assertEqual(j["hibernates"][0]["secs"], 300.0)
        self.assertIn(j["status"], ("ok", "action"))
        self.assertEqual(j["cycles"][0]["battery"]["mah"], 30.0)
        h = run(["python3", "-I", str(KIT / "sleep" / "sleep-check")], env=env)
        self.assertEqual(h.returncode, 0, h.stderr)
        self.assertIn("Suspend cycles in the last 14 days: 1", h.stdout)
        self.assertIn("hibernated and resumed after 5.0 min", h.stdout)
        self.assertRegex(h.stdout, r"\n(OK|ACTION|PENDING): ")

    def test_empty_journal_is_pending_and_still_valid_json(self):
        fb = fake_bin(self.tmp / "fb", journalctl="exit 0")
        r = run(["python3", "-I", str(KIT / "sleep" / "sleep-check"), "--json"], env={"PATH": f"{fb}:{SAFE_PATH}"})
        self.assertEqual(json.loads(r.stdout)["status"], "pending")


class BatteryLogContract(Sandbox):
    """sleep/battery-log writes what sleep-check reads: if either side changes its format this fails."""
    def hook(self, *args, env_extra=None):
        fb = fake_bin(self.tmp / "fb", logger="exit 0")
        (fb / "calls.log").unlink(missing_ok=True)      # one clean log per invocation (the dir is reused by the subtests)
        r = run(["bash", str(KIT / "sleep" / "battery-log"), *args], env={"PATH": f"{fb}:{SAFE_PATH}", **(env_extra or {})})
        return r, calls(fb)

    def test_line_matches_the_sleep_check_regex_and_exit_is_always_zero(self):
        for args in [("pre", "suspend"), ("post", "hibernate"), ("pre", "suspend-then-hibernate")]:
            with self.subTest(args=args):
                r, c = self.hook(*args)
                self.assertEqual(r.returncode, 0)
                self.assertEqual(len(c), 1)
                self.assertTrue(c[0].startswith("logger -t sleep-battery "), c)
                msg = c[0].split("sleep-battery ", 1)[1]
                m = re.search(r"(pre|post) \S+ charge_uah=(\d+) full_uah=\d+ volt_uv=(\d+) ac=(\d)", msg)   # the regex in sleep-check report()
                self.assertTrue(m, msg)
                self.assertEqual(m.group(1), args[0])

    def test_missing_second_argument_falls_back_to_systemd_sleep_action(self):
        _, c = self.hook("pre", env_extra={"SYSTEMD_SLEEP_ACTION": "hibernate"})
        self.assertIn("pre hibernate charge_uah=", c[0])


# ======================================================================================================================
# themes/install-themes
# ======================================================================================================================
class InstallThemes(Sandbox):
    def setUp(self):
        super().setUp()
        self.kit = self.tmp / "kit"
        self.cfg = self.tmp / "cfg"
        self.dest = self.cfg / "omarchy" / "themes"
        self.fb = fake_bin(self.tmp / "fb", omarchy="echo fake-omarchy-list")
        for name in ("alpha", "beta"):
            d = self.kit / name
            (d / "backgrounds").mkdir(parents=True)
            (d / "source").mkdir()
            (d / "__pycache__").mkdir()
            (d / "colors.toml").write_text(f'accent = "#112233"\nname = "{name}"\n')
            (d / "THEME.md").write_text("docs")
            (d / "source" / "gen.py").write_text("print()")
            (d / "__pycache__" / "x.pyc").write_text("x")
            (d / "backgrounds" / "1.png").write_text("png")
            (d / "hyprland.lua").write_text("-- lua")
        shutil.copy(KIT / "themes" / "install-themes", self.kit / "install-themes")
        self.kit.joinpath("install-themes").chmod(0o755)

    def go(self, *args, kit=None):
        env = {"PATH": f"{self.fb}:{SAFE_PATH}", "HOME": str(self.tmp / "home"), "XDG_CONFIG_HOME": str(self.cfg)}
        return run(["bash", str((kit or self.kit) / "install-themes"), *args], env=env)

    def test_installs_every_theme_strips_docs_and_generators_and_marks_the_copy(self):
        r = self.go()
        self.assertEqual(r.returncode, 0, r.stderr)
        for t in ("alpha", "beta"):
            d = self.dest / t
            self.assertTrue((d / "colors.toml").is_file() and (d / "hyprland.lua").is_file() and (d / "backgrounds" / "1.png").is_file())
            self.assertTrue((d / ".omarchy-kit").is_file(), "marker")
            for gone in ("THEME.md", "source", "__pycache__"):
                self.assertFalse((d / gone).exists(), gone)
            self.assertTrue((self.kit / t / "THEME.md").exists() and (self.kit / t / "source").exists(), "the kit's own folder is untouched")
        self.assertIn("installed alpha", r.stdout)

    def test_it_never_switches_the_theme_and_only_lists(self):
        self.go()
        self.assertEqual(calls(self.fb), ["omarchy theme list"])

    def test_install_twice_gives_the_same_state(self):
        self.go()
        first = {p: (self.dest / p).read_bytes() for p in tree(self.dest) if not p.endswith("/")}
        tree1 = tree(self.dest)
        r = self.go()
        self.assertEqual(r.returncode, 0)
        self.assertEqual(tree(self.dest), tree1)
        self.assertEqual({p: (self.dest / p).read_bytes() for p in tree(self.dest) if not p.endswith("/")}, first)

    def test_reinstall_replaces_the_kits_own_copy_including_stale_files(self):
        self.go()
        (self.dest / "alpha" / "stale.txt").write_text("old")
        (self.kit / "alpha" / "colors.toml").write_text('accent = "#ffffff"\n')
        self.go()
        self.assertFalse((self.dest / "alpha" / "stale.txt").exists())
        self.assertIn("#ffffff", (self.dest / "alpha" / "colors.toml").read_text())

    def test_a_theme_that_is_not_the_kits_is_never_overwritten(self):
        (self.dest / "alpha").mkdir(parents=True)
        (self.dest / "alpha" / "mine.txt").write_text("precious")
        r = self.go()
        self.assertEqual(r.returncode, 0)
        self.assertIn("skipped alpha", r.stdout)
        self.assertEqual((self.dest / "alpha" / "mine.txt").read_text(), "precious")
        self.assertFalse((self.dest / "alpha" / ".omarchy-kit").exists())
        self.assertTrue((self.dest / "beta" / ".omarchy-kit").exists(), "the other themes still install")

    def test_install_just_the_named_theme_and_skip_unknown_names(self):
        r = self.go("beta", "nope")
        self.assertEqual(r.returncode, 0)
        self.assertTrue((self.dest / "beta").is_dir())
        self.assertFalse((self.dest / "alpha").exists())
        self.assertIn("skipped nope: no such kit theme", r.stdout)

    def test_remove_takes_out_only_marked_copies(self):
        self.go()
        (self.dest / "gamma").mkdir()                       # the user's own theme, never ours
        (self.dest / "gamma" / "colors.toml").write_text("x")
        (self.dest / "beta" / ".omarchy-kit").unlink()      # beta is no longer ours (user took it over)
        r = self.go("--remove")
        self.assertEqual(r.returncode, 0)
        self.assertFalse((self.dest / "alpha").exists())
        self.assertTrue((self.dest / "beta").is_dir(), "unmarked folder survives --remove")
        self.assertTrue((self.dest / "gamma" / "colors.toml").exists())
        self.assertIn("removed alpha", r.stdout)
        self.assertIn("left beta alone", r.stdout)

    def test_remove_named_and_remove_twice(self):
        self.go()
        self.assertIn("removed alpha", self.go("--remove", "alpha").stdout)
        self.assertTrue((self.dest / "beta").exists())
        r = self.go("--remove", "alpha")
        self.assertEqual(r.returncode, 0)
        self.assertIn("alpha was not installed", r.stdout)

    def test_remove_then_install_returns_to_the_installed_state(self):
        self.go()
        before = tree(self.dest)
        self.go("--remove")
        self.assertEqual(tree(self.dest), [])
        self.go()
        self.assertEqual(tree(self.dest), before)

    def test_list_marks_ours_missing_and_clashes(self):
        self.go("alpha")
        (self.dest / "beta").mkdir()
        out = self.go("--list").stdout
        self.assertRegex(out, r"alpha\s+yes\s+yes")
        self.assertRegex(out, r"beta\s+yes\s+CLASH")

    def test_nothing_outside_the_temp_config_is_touched(self):
        before = tree(self.tmp)
        self.go()
        new = [p for p in tree(self.tmp) if p not in before]
        self.assertTrue(all(p.startswith("cfg/") or p.startswith("fb/calls.log") for p in new), new)

    def test_a_folder_without_colors_toml_must_not_abort_the_installer(self):
        """Fixed audit bug: kit_themes() returns 1 when the last folder has no colors.toml; under `set -e` the installer exits silently."""
        (self.kit / "notes").mkdir()                        # sorts after alpha and beta
        r = self.go()
        self.assertEqual(r.returncode, 0, "exited silently: " + repr(r.stdout))
        self.assertTrue((self.dest / "beta").exists())

    def test_an_empty_kit_prints_the_friendly_message(self):
        """Fixed audit bug: same cause; the 'no themes with a colors.toml' message is unreachable."""
        empty = self.tmp / "empty"
        empty.mkdir()
        shutil.copy(self.kit / "install-themes", empty / "install-themes")
        r = self.go(kit=empty)
        self.assertIn("no themes with a colors.toml", r.stdout)

    def test_remove_refuses_names_that_climb_out_of_the_themes_folder(self):
        """Fixed audit bug (low): `--remove ../victim` runs rm -rf outside DEST when ../victim holds a .omarchy-kit file."""
        victim = self.cfg / "omarchy" / "victim"
        victim.mkdir(parents=True)
        (victim / ".omarchy-kit").write_text("")
        self.dest.mkdir(parents=True, exist_ok=True)
        self.go("--remove", "../victim")
        self.assertTrue(victim.exists())


# ======================================================================================================================
# power/power-lab
# ======================================================================================================================
PL = load(KIT / "power" / "power-lab", "power_lab")


class FakeFS:
    def __init__(self, files, refuse=()):
        self.f, self.refuse, self.writes = dict(files), set(refuse), []

    def rd(self, p): return self.f.get(p, "")

    def wr(self, p, v):
        self.writes.append((p, str(v)))
        if p not in self.refuse:
            self.f[p] = str(v)
        return True

    def __enter__(self):
        self._p = [mock.patch.object(PL, "rd", self.rd), mock.patch.object(PL, "wr", self.wr), mock.patch.object(PL.time, "sleep", lambda s: None)]
        for p in self._p: p.start()
        return self

    def __exit__(self, *a):
        for p in self._p: p.stop()


L1 = "/sys/bus/pci/devices/%s/link/l1_aspm"
PC = "/sys/bus/pci/devices/%s/power/control"
CAM, TB, OTHER, OK = "0000:02:00.0", "0000:06:00.0", "0000:07:00.0", "0000:00:01.0"


class PowerLabRegistry(unittest.TestCase):
    def test_every_mode_is_registered_everywhere(self):
        self.assertEqual(set(PL.MODES), set(PL.RUN))
        self.assertEqual(set(PL.MODES), set(PL.NEEDS))
        for m, fn in PL.RUN.items():
            self.assertEqual(fn.__name__, f"mode_{m}")
        self.assertLessEqual(PL.BATTERY_ONLY, set(PL.MODES))
        self.assertNotIn("hunt", PL.BATTERY_ONLY, "hunt reads CPU counters only and works on the charger")
        for needs in PL.NEEDS.values():
            self.assertLessEqual(set(needs), {"dpms", "rapl"})
        for m in ("hunt", "breakdown", "stack"):
            self.assertIn("dpms", PL.NEEDS[m], f"{m} switches the display off, so it needs a Hyprland signature")

    def test_the_msr_registers_are_the_haswell_package_counters(self):
        self.assertEqual(PL.PC_MSRS, {"PC2": 0x60D, "PC3": 0x3F8, "PC6": 0x3F9, "PC7": 0x3FA})

    def test_no_arguments_prints_help_and_exits_zero(self):
        r = run(["python3", "-I", str(KIT / "power" / "power-lab")], env={"PATH": SAFE_PATH})
        self.assertEqual(r.returncode, 0)
        self.assertIn("power-lab", r.stdout)
        self.assertIn("hunt", r.stdout)

    def test_an_unknown_mode_is_rejected_by_argparse(self):
        r = run(["python3", "-I", str(KIT / "power" / "power-lab"), "wipe-everything"], env={"PATH": SAFE_PATH})
        self.assertEqual(r.returncode, 2)


class PowerLabResults(Sandbox):
    def results(self, *args):
        buf = io.StringIO()
        with mock.patch.object(sys, "argv", ["power-lab", "results", *args, "--out", str(self.tmp)]), redirect_stdout(buf):
            self.assertEqual(PL.main(), 0)
        return buf.getvalue()

    def test_results_shows_saved_files_or_says_none_yet(self):
        self.assertIn("no results yet", self.results())
        (self.tmp / "hunt.txt").write_text("VERDICT x\n")
        (self.tmp / "quiet.txt").write_text("RESULT y\n")
        out = self.results()
        self.assertIn("===== hunt =====", out)
        self.assertIn("===== quiet =====", out)
        only = self.results("quiet")
        self.assertIn("RESULT y", only)
        self.assertNotIn("VERDICT", only)


def make_lab(out, **kw):
    lab = PL.Lab.__new__(PL.Lab)
    lab.user, lab.sig, lab.out = "tester", "sig123", str(out)
    lab.lines, lab.undo, lab.saved, lab.name = [], [], {}, "hunt"
    lab.bat, lab.ac, lab.backlight, lab.wifi, lab.rapl, lab.msr = "/fake/BAT0", [], "intel_backlight", "", {}, None
    lab.camera, lab.thunderbolt, lab.orig_brightness = [], [], "400"
    for k, v in kw.items(): setattr(lab, k, v)
    return lab


class PowerLabCheck(Sandbox):
    def test_check_output_changes_nothing_and_runs_no_commands(self):
        lab = make_lab(self.tmp, ac=["/fake/AC/online"], camera=[CAM], thunderbolt=[TB], rapl={"package-0": "/x"})
        with FakeFS({"/fake/AC/online": "1"}) as fs, mock.patch.object(PL, "sh", side_effect=AssertionError("--check must not run commands")):
            buf = io.StringIO()
            with redirect_stdout(buf):
                PL.show_check(lab, "quiet")
        self.assertEqual(fs.writes, [])
        out = buf.getvalue()
        self.assertIn("looks only, changes nothing", out)
        self.assertIn("YES: unplug it first", out)
        self.assertIn(CAM, out)
        self.assertIn("about 2 minutes", out)

    def test_hunt_does_not_care_about_the_charger(self):
        lab = make_lab(self.tmp, ac=["/fake/AC/online"])
        with FakeFS({"/fake/AC/online": "1"}):
            buf = io.StringIO()
            with redirect_stdout(buf):
                PL.show_check(lab, "hunt")
        self.assertIn("either way is fine", buf.getvalue())

    def test_missing_hyprland_signature_and_battery_are_called_out(self):
        lab = make_lab(self.tmp, sig="", bat="")
        with FakeFS({}):
            buf = io.StringIO()
            with redirect_stdout(buf):
                PL.show_check(lab, "stack")
        out = buf.getvalue()
        self.assertIn("MISSING", out)
        self.assertIn("NOT FOUND", out)

    def test_check_through_the_cli_only_runs_read_only_commands(self):
        fb = fake_bin(self.tmp / "fb", lspci="exit 0", brightnessctl='[ "$3" = get ] && echo 300; exit 0', lsmod="exit 0")
        r = run(["python3", "-I", str(KIT / "power" / "power-lab"), "quiet", "--check", "--out", str(self.tmp / "out")],
                env={"PATH": f"{fb}:{SAFE_PATH}", "HYPRLAND_INSTANCE_SIGNATURE": "x"})
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("changes nothing", r.stdout)
        for c in calls(fb):
            self.assertTrue(c.startswith("lspci -D") or c.startswith("brightnessctl -d") and c.endswith(" get"), f"non read-only call: {c}")
        self.assertFalse((self.tmp / "out" / "quiet.txt").exists(), "--check writes no results file")


class PowerLabHunt(Sandbox):
    def flags(self):
        return {OK: ("1", "1"), CAM: ("1", "0"), TB: ("1", "0"), OTHER: ("1", "0")}

    def files(self):
        return {L1 % a: v[1] for a, v in self.flags().items()} | {PC % TB: "auto"}

    def hunt(self, fs, measures, dpms_state="0"):
        lab = make_lab(self.tmp, camera=[CAM], thunderbolt=[TB])
        patches = [mock.patch.object(PL.Lab, "set_backlight"), mock.patch.object(PL.Lab, "dpms"),
                   mock.patch.object(PL.Lab, "dpms_state", return_value=dpms_state),
                   mock.patch.object(PL.Lab, "link_flags", return_value=self.flags()),
                   mock.patch.object(PL.Lab, "lnkctl", return_value="ASPM Disabled"), mock.patch.object(PL.Lab, "pci_name", return_value="dev"),
                   mock.patch.object(PL.Lab, "measure", side_effect=measures)]
        mocks = [p.start() for p in patches]
        self.addCleanup(lambda: [p.stop() for p in patches])
        PL.mode_hunt(lab)
        return lab, mocks

    @staticmethod
    def pcs(pc6=0, pc7=0): return {"W": 9.0, "pkg": 3.0, "dram": 0.5, "PC2": 40, "PC3": 20, "PC6": pc6, "PC7": pc7}

    def test_hunt_flips_only_l1_flags_reports_the_first_step_that_unlocks_deep_sleep_and_reverts_everything(self):
        with FakeFS(self.files()) as fs:
            lab, (backlight, dpms, *_rest) = self.hunt(fs, [self.pcs(), self.pcs(), self.pcs(3, 3), self.pcs(3, 3)])
            flipped = {p for p, v in fs.writes if v == "1"}
            self.assertEqual(flipped, {L1 % CAM, L1 % TB, L1 % OTHER})
            for p, _ in fs.writes:
                self.assertRegex(p, r"^/sys/bus/pci/devices/[0-9a-f:.]+/(link/l1_aspm|power/control)$", "hunt must only touch these two sysfs files")
            self.assertEqual(fs.f[PC % TB], "on", "Thunderbolt is kept awake while testing, never unloaded")
            self.assertEqual(len(lab.undo), 4)
            text = "\n".join(lab.lines)
            self.assertIn("VERDICT", text)
            self.assertIn("first appeared at: 2. + L1 forced on the Thunderbolt links", text)
            self.assertTrue((self.tmp / "hunt.txt").read_text().startswith("backlight 0."), "results are saved incrementally")
            lab.restore_all()
            self.assertEqual(lab.undo, [])
            self.assertEqual({k: v for k, v in fs.f.items()}, self.files(), "every sysfs value is back to what it was")
            self.assertEqual(dpms.call_args_list[-1], mock.call("enable"))
            self.assertEqual(backlight.call_args_list[-1], mock.call("400"))

    def test_hunt_reports_when_no_step_unlocks_deep_sleep(self):
        with FakeFS(self.files()) as fs:
            lab, _ = self.hunt(fs, [self.pcs()] * 4)
        self.assertIn("never appeared", "\n".join(lab.lines))

    def test_hunt_names_links_the_kernel_refuses_and_does_not_undo_them(self):
        with FakeFS(self.files(), refuse=[L1 % CAM]) as fs:
            lab, _ = self.hunt(fs, [self.pcs()] * 4)
        self.assertIn("REFUSED by the kernel on: " + CAM, "\n".join(lab.lines))
        self.assertNotIn("camera link L1", [t for t, _ in lab.undo])

    def test_hunt_aborts_without_touching_sysfs_if_the_display_will_not_switch_off(self):
        with FakeFS(self.files()) as fs:
            lab, (_, dpms, *_rest) = self.hunt(fs, [], dpms_state="1")
        self.assertEqual(fs.writes, [])
        self.assertIn("aborting", "\n".join(lab.lines))
        self.assertEqual(lab.undo, [])


class PowerLabChanges(Sandbox):
    def test_single_applies_measures_and_reverts_in_order(self):
        order = []
        lab = make_lab(self.tmp, name="singles")
        builder = lambda: (lambda: order.append("on") or True, lambda: order.append("off"))
        with FakeFS({}), mock.patch.object(PL.Lab, "measure", side_effect=[{"W": 10.0}, {"W": 9.0}, {"W": 10.0}]) as m:
            delta = lab.single("test change", builder)
        self.assertEqual(order, ["on", "off"])
        self.assertEqual(lab.undo, [], "the undo entry is removed once reverted")
        self.assertAlmostEqual(delta, -1.0)
        self.assertEqual([c.args[0] for c in m.call_args_list], [10, 20, 10])

    def test_single_skips_and_reverts_when_not_applicable(self):
        order = []
        lab = make_lab(self.tmp, name="singles")
        with FakeFS({}), mock.patch.object(PL.Lab, "measure", return_value={"W": 10.0}):
            self.assertIsNone(lab.single("x", lambda: (lambda: False, lambda: order.append("off"))))
        self.assertEqual(order, ["off"])

    def test_restore_all_runs_every_undo_even_if_one_fails_then_restores_the_screen(self):
        done = []
        lab = make_lab(self.tmp)
        lab.undo = [("a", lambda: done.append("a")), ("boom", lambda: 1 / 0), ("c", lambda: done.append("c"))]
        with mock.patch.object(PL.Lab, "dpms") as dpms, mock.patch.object(PL.Lab, "set_backlight") as bl, FakeFS({}):
            lab.restore_all()
            lab.restore_all()    # atexit + signal handler + finally may all call it: it must be safe to repeat
        self.assertEqual(done, ["c", "a"])   # undone in reverse order
        self.assertTrue(any("undo error in boom" in l for l in lab.lines))
        dpms.assert_called_with("enable")
        bl.assert_called_with("400")

    def test_alpm_and_aspm_builders_restore_the_previous_values(self):
        files = {"/sys/class/scsi_host/host0/link_power_management_policy": "max_performance",
                 "/sys/module/pcie_aspm/parameters/policy": "default [performance] powersave powersupersave"}
        lab = make_lab(self.tmp)
        with FakeFS(files) as fs, mock.patch.object(PL.glob, "glob", return_value=["/sys/class/scsi_host/host0/link_power_management_policy"]):
            on, off = lab.b_alpm()
            on(); self.assertEqual(fs.f["/sys/class/scsi_host/host0/link_power_management_policy"], "med_power_with_dipm")
            off(); self.assertEqual(fs.f["/sys/class/scsi_host/host0/link_power_management_policy"], "max_performance")
            on, off = lab.b_aspm()
            on(); self.assertEqual(fs.f["/sys/module/pcie_aspm/parameters/policy"], "powersupersave")
            off(); self.assertEqual(fs.f["/sys/module/pcie_aspm/parameters/policy"], "performance")

    def test_pci_runtime_pm_builder_skips_host_bridge_lpc_and_the_switched_off_dgpu(self):
        paths = [PC % a for a in ("0000:00:00.0", "0000:00:1f.0", "0000:01:00.0", "0000:05:00.0", "0000:00:16.0")]
        lab = make_lab(self.tmp)
        with FakeFS({p: "on" for p in paths}) as fs, mock.patch.object(PL.glob, "glob", return_value=paths):
            on, off = lab.b_pci()
            on()
            self.assertEqual({p for p, v in fs.writes if v == "auto"}, {PC % "0000:05:00.0", PC % "0000:00:16.0"})

    def test_there_is_deliberately_no_thunderbolt_or_pci_rescan_code(self):
        src = (KIT / "power" / "power-lab").read_text()
        code = "\n".join(l for l in src.splitlines() if not l.lstrip().startswith("#"))
        self.assertNotIn("modprobe\", \"-r\", \"thunderbolt", code)
        self.assertNotIn("/rescan", code, "a PCI rescan crashed the kernel on 2026-10-07: never again")
        self.assertNotIn("/remove", code)


class PowerLabRelaunch(Sandbox):
    class FakeLab:
        instances = []
        def __init__(self, user, sig, out):
            self.user, self.sig, self.out, self.orig_brightness, self.backlight, self.calls = user, sig, out, "450", "intel_backlight", []
            PowerLabRelaunch.FakeLab.instances.append(self)
        def dpms(self, a): self.calls.append(("dpms", a))
        def set_backlight(self, v): self.calls.append(("backlight", str(v)))

    def relaunch(self, sig="abc123", mode="hunt"):
        args = mock.Mock(out=str(self.tmp / "out"))
        with mock.patch.dict(os.environ, {"HYPRLAND_INSTANCE_SIGNATURE": sig}), mock.patch.object(PL, "Lab", self.FakeLab), \
             mock.patch.object(PL.subprocess, "call", return_value=0) as call, redirect_stdout(io.StringIO()):
            rc = PL.relaunch(mode, args, "tester")
        self.assertEqual(rc, 0)
        return call.call_args[0][0]

    def rescue_of(self, cmd):
        props = [c for c in cmd if c.startswith("--property=ExecStopPost=")]
        self.assertEqual(len(props), 1)
        return props[0].split("=", 2)[2]

    def test_the_test_runs_as_a_transient_system_service_that_sudo_starts(self):
        cmd = self.relaunch()
        self.assertEqual(cmd[:2], ["sudo", "systemd-run"])
        self.assertIn("--collect", cmd)
        self.assertIn("--unit=power-lab-hunt", cmd)
        tail = cmd[cmd.index("python3"):]
        self.assertEqual(tail, ["python3", "-I", str(KIT / "power" / "power-lab"), "hunt", "--user", "tester", "--sig", "abc123", "--out", str(self.tmp / "out")])

    def test_rescue_command_runs_after_the_service_however_it_ends_and_restores_display_and_brightness(self):
        cmd = self.relaunch()
        rescue = self.rescue_of(cmd)
        self.assertEqual(shlex.split(rescue), ["/usr/bin/python3", "-I", str(KIT / "power" / "power-lab"), "rescue", "--user=tester",
                                               "--sig=abc123", "--brightness=450"])
        # feed the rescue command line to the real argument parser, as root: it must switch the display on and put the brightness back
        FL = self.FakeLab
        FL.instances.clear()
        with mock.patch.object(sys, "argv", ["power-lab", *shlex.split(rescue)[3:]]), mock.patch.object(PL.os, "geteuid", return_value=0), \
             mock.patch.object(PL, "Lab", FL):
            self.assertEqual(PL.main(), 0)
        self.assertEqual(FL.instances[-1].calls, [("dpms", "enable"), ("backlight", "450")])

    def test_rescue_refuses_to_run_unprivileged_and_is_silent_about_zero_brightness(self):
        FL = self.FakeLab
        with mock.patch.object(sys, "argv", ["power-lab", "rescue", "--user", "u", "--sig", "s", "--brightness", "0"]):
            with mock.patch.object(PL.os, "geteuid", return_value=1000), redirect_stdout(io.StringIO()):
                self.assertEqual(PL.main(), 2)
            FL.instances.clear()
            with mock.patch.object(PL.os, "geteuid", return_value=0), mock.patch.object(PL, "Lab", FL):
                PL.main()
        self.assertEqual(FL.instances[-1].calls, [("dpms", "enable")], "brightness 0 would black the screen out: never set it")

    def test_rescue_command_survives_a_missing_hyprland_signature(self):
        """Fixed audit bug: quiet/singles may run without Hyprland; then the rescue line reads `--sig  --brightness 450`, argparse rejects it
        (exit 2) and the backlight is NOT restored if the test is killed."""
        rescue = self.rescue_of(self.relaunch(sig=""))
        FL = self.FakeLab
        FL.instances.clear()
        with mock.patch.object(sys, "argv", ["power-lab", *shlex.split(rescue)[3:]]), mock.patch.object(PL.os, "geteuid", return_value=0), \
             mock.patch.object(PL, "Lab", FL), mock.patch.object(sys, "stderr", io.StringIO()):
            self.assertEqual(PL.main(), 0)


# ======================================================================================================================
# power/power-auto, power/install-power-auto
# ======================================================================================================================
class PowerAuto(Sandbox):
    def setUp(self):
        super().setUp()
        self.state = self.tmp / "profile"
        self.state.write_text("balanced")
        self.fb = fake_bin(self.tmp / "fb", powerprofilesctl=f'''
            if [ "$1" = get ]; then cat "{self.state}"; elif [ "$1" = set ]; then printf '%s' "$2" > "{self.state}"; fi''')
        self.home = self.tmp / "home"
        self.cfg = self.tmp / "cfg"

    def auto(self, *args, ac=None, conf=None):
        env = {"PATH": f"{self.fb}:{SAFE_PATH}", "HOME": str(self.home), "XDG_CONFIG_HOME": str(self.cfg)}
        if ac is not None: env["KIT_FAKE_AC"] = ac
        if conf:
            (self.cfg / "omarchy-kit").mkdir(parents=True, exist_ok=True)
            (self.cfg / "omarchy-kit" / "power-auto.conf").write_text(conf)
        return run(["bash", str(KIT / "power" / "power-auto"), *args], env=env)

    def test_plugged_in_selects_performance_and_battery_selects_balanced(self):
        self.assertIn("-> performance", self.auto("--once", ac="1").stdout)
        self.assertEqual(self.state.read_text(), "performance")
        self.assertIn("-> balanced", self.auto("--once", ac="0").stdout)
        self.assertEqual(self.state.read_text(), "balanced")

    def test_no_change_when_the_profile_is_already_right(self):
        out = self.auto("--once", ac="0").stdout
        self.assertIn("already balanced", out)
        self.assertEqual([c for c in calls(self.fb) if c.startswith("powerprofilesctl set")], [])

    def test_profiles_can_be_overridden_in_the_user_config(self):
        self.auto("--once", ac="1", conf="AC_PROFILE=balanced\nBATTERY_PROFILE=power-saver\n")
        self.assertEqual(self.state.read_text(), "balanced")
        self.auto("--once", ac="0")
        self.assertEqual(self.state.read_text(), "power-saver")

    def test_status_reports_charger_and_profile(self):
        out = self.auto("--status", ac="1").stdout
        self.assertIn("charger: plugged in", out)
        self.assertIn("profile: balanced", out)
        self.assertIn("charger: on battery", self.auto("--status", ac="0").stdout)


class InstallPowerAuto(Sandbox):
    def setUp(self):
        super().setUp()
        self.home, self.cfg = self.tmp / "home", self.tmp / "cfg"
        self.home.mkdir()
        self.fb = fake_bin(self.tmp / "fb", systemctl="exit 0", journalctl="exit 0", sleep="exit 0",
                           powerprofilesctl='[ "$1" = get ] && echo balanced; exit 0')

    def go(self, *args):
        env = {"PATH": f"{self.fb}:{self.home}/.local/bin:{SAFE_PATH}", "HOME": str(self.home), "XDG_CONFIG_HOME": str(self.cfg), "KIT_FAKE_AC": "1"}
        return run(["bash", str(KIT / "power" / "install-power-auto"), *args], env=env)

    def test_install_puts_exactly_two_files_in_the_user_dirs_and_enables_the_service(self):
        r = self.go()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual([p for p in tree(self.tmp) if p.endswith(("power-auto", "power-auto.service"))],
                         ["cfg/systemd/user/power-auto.service", "home/.local/bin/power-auto"])
        svc, exe = self.cfg / "systemd/user/power-auto.service", self.home / ".local/bin/power-auto"
        self.assertEqual(svc.read_bytes(), (KIT / "power" / "power-auto.service").read_bytes())
        self.assertEqual(exe.read_bytes(), (KIT / "power" / "power-auto").read_bytes())
        self.assertEqual((stat.S_IMODE(svc.stat().st_mode), stat.S_IMODE(exe.stat().st_mode)), (0o644, 0o755))
        c = calls(self.fb)
        for want in ("systemctl --user daemon-reload", "systemctl --user enable power-auto.service", "systemctl --user restart power-auto.service"):
            self.assertIn(want, c)

    def test_install_twice_is_the_same_state(self):
        self.go()
        before = (tree(self.tmp), (self.home / ".local/bin/power-auto").read_bytes())
        self.assertEqual(self.go().returncode, 0)
        self.assertEqual((tree(self.tmp), (self.home / ".local/bin/power-auto").read_bytes()), before)

    def test_remove_is_the_inverse_and_safe_to_repeat(self):
        before = tree(self.tmp)
        self.go()
        for _ in range(2):
            r = self.go("--remove")
            self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual([p for p in tree(self.tmp) if "power-auto" in p], [])
        self.assertIn("systemctl --user disable --now power-auto.service", calls(self.fb))
        leftovers = [p for p in tree(self.tmp) if p not in before and not p.startswith("fb/")]
        self.assertTrue(all(p.rstrip("/").split("/")[0] in ("home", "cfg") for p in leftovers), leftovers)


# ======================================================================================================================
# Root installers, run as fake root in a private user + mount namespace with tmpfs over the target folders
# ======================================================================================================================
@unittest.skipUnless(USERNS, "needs `unshare -Urm` (unprivileged user namespaces) and a non-root caller")
class RootInstallersInNamespace(Sandbox):
    """Inside the namespace `id -u` is 0, so the scripts' root check passes, but nothing is real: the folders they write to are tmpfs
    mounts that vanish with the namespace, and the commands that would act on the system (nmcli, iw, systemd-tmpfiles) are fakes."""
    def env(self, fb):
        return {"PATH": f"{fb}:{SAFE_PATH}", "HOME": str(self.tmp)}

    def test_install_hibernate_mode_install_idempotent_remove(self):
        drv = r'''
            S=$1; mount -t tmpfs none /etc/systemd || { echo MOUNT_FAIL=1; exit 0; }
            F=/etc/systemd/sleep.conf.d/10-hibernate-shutdown.conf
            mkdir -p /etc/systemd/sleep.conf.d; echo "# user file" > /etc/systemd/sleep.conf.d/20-mine.conf
            bash "$S" >/dev/null 2>&1; echo RC1=$?
            echo EXISTS1=$([ -f $F ] && echo 1 || echo 0); H1=$(sha256sum $F | cut -d' ' -f1)
            bash "$S" >/dev/null 2>&1; echo RC2=$?; H2=$(sha256sum $F | cut -d' ' -f1); echo SAME=$([ "$H1" = "$H2" ] && echo 1 || echo 0)
            echo CONTENT=$(tr '\n' '|' < $F)
            bash "$S" --remove >/dev/null 2>&1; echo RCR=$?; echo EXISTS3=$([ -f $F ] && echo 1 || echo 0)
            bash "$S" --remove >/dev/null 2>&1; echo RCR2=$?
            echo MINE=$([ -f /etc/systemd/sleep.conf.d/20-mine.conf ] && echo kept || echo deleted)'''
        o = in_userns(drv, str(KIT / "sleep" / "install-hibernate-mode"), env=self.env(self.tmp))
        if "MOUNT_FAIL" in o: self.skipTest("cannot mount tmpfs in the namespace")
        self.assertEqual((o["RC1"], o["EXISTS1"], o["RC2"], o["SAME"], o["RCR"], o["EXISTS3"], o["RCR2"], o["MINE"]),
                         ("0", "1", "0", "1", "0", "0", "0", "kept"))
        self.assertIn("HibernateMode=shutdown", o["CONTENT"])
        self.assertIn("[Sleep]", o["CONTENT"])

    def test_install_battery_log_replaces_the_old_misplaced_copy_and_remove_cleans_up(self):
        drv = r'''
            S=$1; mount -t tmpfs none /usr/lib/systemd/system-sleep && mount -t tmpfs none /etc/systemd || { echo MOUNT_FAIL=1; exit 0; }
            F=/usr/lib/systemd/system-sleep/battery-log; OLD=/etc/systemd/system-sleep/battery-log
            mkdir -p /etc/systemd/system-sleep; echo old > $OLD; echo other > /etc/systemd/system-sleep/someone-elses-hook
            bash "$S" >/dev/null 2>&1; echo RC1=$?
            echo MODE=$(stat -c %a $F); echo OLDGONE=$([ -e $OLD ] && echo 0 || echo 1)
            echo SRC=$(cmp -s "$(dirname "$S")/battery-log" $F && echo same || echo different)
            H1=$(sha256sum $F | cut -d' ' -f1); bash "$S" >/dev/null 2>&1; echo RC2=$?; echo SAME=$([ "$H1" = "$(sha256sum $F | cut -d' ' -f1)" ] && echo 1 || echo 0)
            bash "$S" --remove >/dev/null 2>&1; echo RCR=$?; echo GONE=$([ -e $F ] && echo 0 || echo 1)
            bash "$S" --remove >/dev/null 2>&1; echo RCR2=$?
            echo OTHER=$([ -f /etc/systemd/system-sleep/someone-elses-hook ] && echo kept || echo deleted)'''
        o = in_userns(drv, str(KIT / "sleep" / "install-battery-log"), env=self.env(self.tmp))
        if "MOUNT_FAIL" in o: self.skipTest("cannot mount tmpfs in the namespace")
        self.assertEqual((o["RC1"], o["MODE"], o["OLDGONE"], o["SRC"], o["RC2"], o["SAME"], o["RCR"], o["GONE"], o["RCR2"], o["OTHER"]),
                         ("0", "755", "1", "same", "0", "1", "0", "1", "0", "kept"))

    def test_install_wifi_powersave_writes_one_file_and_remove_leaves_omarchys_own(self):
        fb = fake_bin(self.tmp / "fb", nmcli="exit 0", iw='[ "$3" = get ] && echo "Power save: on"; exit 0')
        drv = r'''
            S=$1; mount -t tmpfs none /etc/NetworkManager/conf.d || { echo MOUNT_FAIL=1; exit 0; }
            F=/etc/NetworkManager/conf.d/wifi-powersave.conf; echo "wifi.powersave = 2" > /etc/NetworkManager/conf.d/omarchy-wifi-powersave.conf
            bash "$S" >/dev/null 2>&1; echo RC1=$?; H1=$(sha256sum $F | cut -d' ' -f1)
            bash "$S" >/dev/null 2>&1; echo RC2=$?; echo SAME=$([ "$H1" = "$(sha256sum $F | cut -d' ' -f1)" ] && echo 1 || echo 0)
            echo CONTENT=$(tr '\n' '|' < $F)
            bash "$S" --remove >/dev/null 2>&1; echo RCR=$?; echo GONE=$([ -e $F ] && echo 0 || echo 1)
            bash "$S" --remove >/dev/null 2>&1; echo RCR2=$?
            echo OMARCHY=$(cat /etc/NetworkManager/conf.d/omarchy-wifi-powersave.conf)'''
        o = in_userns(drv, str(KIT / "power" / "install-wifi-powersave"), env=self.env(fb))
        if "MOUNT_FAIL" in o: self.skipTest("cannot mount tmpfs in the namespace")
        self.assertEqual((o["RC1"], o["RC2"], o["SAME"], o["RCR"], o["GONE"], o["RCR2"], o["OMARCHY"]), ("0", "0", "1", "0", "1", "0", "wifi.powersave = 2"))
        self.assertIn("wifi.powersave = 3", o["CONTENT"])
        self.assertIn("nmcli general reload conf", calls(fb))
        for c in calls(fb):
            self.assertRegex(c, r"^(nmcli general reload conf|iw dev \S+ (set power_save (on|off)|get power_save))$", "only the intended commands")

    def test_install_s2idle_writes_a_tmpfiles_rule_and_remove_goes_back_to_deep(self):
        memsleep = self.tmp / "mem_sleep"
        memsleep.write_text("s2idle [deep]\n")
        fb = fake_bin(self.tmp / "fb", **{"systemd-tmpfiles": 'echo "[s2idle] deep" > /sys/power/mem_sleep'})
        drv = r'''
            S=$1; mount -t tmpfs none /etc/tmpfiles.d && mount --bind "$2" /sys/power/mem_sleep || { echo MOUNT_FAIL=1; exit 0; }
            F=/etc/tmpfiles.d/mem-sleep-s2idle.conf; echo "w /x - - - - y" > /etc/tmpfiles.d/other.conf
            bash "$S" >/dev/null 2>&1; echo RC1=$?; echo CONTENT=$(tail -1 $F); echo MODE1=$(cat /sys/power/mem_sleep); H1=$(sha256sum $F | cut -d' ' -f1)
            bash "$S" >/dev/null 2>&1; echo RC2=$?; echo SAME=$([ "$H1" = "$(sha256sum $F | cut -d' ' -f1)" ] && echo 1 || echo 0)
            bash "$S" --remove >/dev/null 2>&1; echo RCR=$?; echo GONE=$([ -e $F ] && echo 0 || echo 1); echo MODE2=$(cat /sys/power/mem_sleep)
            echo OTHER=$([ -f /etc/tmpfiles.d/other.conf ] && echo kept || echo deleted)'''
        o = in_userns(drv, str(KIT / "sleep" / "install-s2idle"), str(memsleep), env=self.env(fb))
        if "MOUNT_FAIL" in o: self.skipTest("cannot mount tmpfs/bind in the namespace")
        self.assertEqual((o["RC1"], o["CONTENT"], o["RC2"], o["SAME"], o["RCR"], o["GONE"], o["OTHER"]),
                         ("0", "w /sys/power/mem_sleep - - - - s2idle", "0", "1", "0", "1", "kept"))
        self.assertIn("[s2idle]", o["MODE1"])
        self.assertEqual(o["MODE2"], "deep", "the bind-mounted stand-in file was written, not the real sysfs file")
        self.assertEqual(memsleep.read_text().strip(), "deep")


class RootInstallersRefuseWithoutRoot(Sandbox):
    @unittest.skipIf(os.geteuid() == 0, "would touch the real system when run as root")
    def test_each_root_installer_exits_1_with_a_hint_before_doing_anything(self):
        before = tree(self.tmp)
        for rel in ("sleep/install-s2idle", "sleep/install-hibernate-mode", "sleep/install-battery-log", "power/install-wifi-powersave"):
            for extra in ([], ["--remove"]):
                with self.subTest(script=rel, args=extra):
                    r = run(["bash", str(KIT / rel), *extra], env={"PATH": SAFE_PATH, "HOME": str(self.tmp)})
                    self.assertEqual(r.returncode, 1)
                    self.assertIn("sudo", r.stdout)
        self.assertEqual(tree(self.tmp), before)

    def test_install_hibernate_nolock_refuses_when_omarchys_monitor_needs_other_files(self):
        """The shim only carries two files; if Omarchy's monitor uses a third, the installer must stop before touching anything."""
        text = (KIT / "sleep" / "install-hibernate-nolock").read_text()
        self.assertIn("REAL=/usr/share/omarchy/bin/omarchy-system-sleep-monitor\n", text)
        fake_real = self.tmp / "monitor"
        fake_real.write_text('#!/bin/bash\n"$OMARCHY_PATH/bin/omarchy-system-sleep-lock"\n"$OMARCHY_PATH/bin/omarchy-brand-new-helper"\n')
        script = self.tmp / "sleep" / "install-hibernate-nolock"
        script.parent.mkdir()
        script.write_text(text.replace("REAL=/usr/share/omarchy/bin/omarchy-system-sleep-monitor\n", f"REAL={fake_real}\n"))
        fb = fake_bin(self.tmp / "fb", systemctl="exit 0")
        home = self.tmp / "home"
        home.mkdir()
        r = run(["bash", str(script)], env={"PATH": f"{fb}:{SAFE_PATH}", "HOME": str(home)})
        self.assertEqual(r.returncode, 1)
        self.assertIn("omarchy-brand-new-helper", r.stdout)
        self.assertEqual(tree(home), [], "nothing installed")
        self.assertEqual(calls(fb), [], "no service restarted")

    def test_install_hibernate_nolock_refuses_when_omarchys_monitor_is_missing(self):
        """Fixed audit bug: grep on a missing file is swallowed by `|| true`, so the shim symlinks a dangling monitor and the lock service breaks."""
        text = (KIT / "sleep" / "install-hibernate-nolock").read_text()
        script = self.tmp / "sleep" / "install-hibernate-nolock"
        script.parent.mkdir()
        script.write_text(text.replace("REAL=/usr/share/omarchy/bin/omarchy-system-sleep-monitor\n", f"REAL={self.tmp}/does-not-exist\n"))
        shutil.copy(KIT / "sleep" / "sleep-lock-policy", script.parent / "sleep-lock-policy")
        fb = fake_bin(self.tmp / "fb", systemctl='[ "$2" = show ] && echo "OMARCHY_PATH=fake"; exit 0')
        home = self.tmp / "home"
        home.mkdir()
        r = run(["bash", str(script)], env={"PATH": f"{fb}:{SAFE_PATH}", "HOME": str(home)})
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual(tree(home), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
