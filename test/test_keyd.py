"""Tests for the keyboard pieces in keys/: the keyd Mac command layer (keyd-config, keyd-appmap, install-keyd) and caps-lock.
Standard library only, no root, nothing touches the real system.

  python3 -B test/test_keyd.py            # or: python3 -B -m unittest test.test_keyd

What is covered, and how:
  keys/keyd-config   the generated configuration (shape, ids, caps delay, no trailing comments), device detection from a sample of
                     /proc/bus/input/devices, the overlays, and that the Super chords it sends are the ones it documents
  keys/keyd-appmap   terminal-or-app classification, the socket safety checks (owner, symlink, kind), the overlay file shape, the
                     applier against a fake `keyd`, and the whole service against fake Hyprland sockets (events in, `keyd bind` calls out)
  keys/install-keyd  argument handling, refusal without root, the dry run, and the real install, twice, and --remove run as fake
                     root in a private user+mount namespace with tmpfs over /etc and /usr/local and fake pacman, systemctl and keyd
  keys/caps-lock     real, compose, idempotence, a single backup, what is kept in kb_options, a failing reload; run on a COPY of the
                     script with fake hyprctl/systemctl so no page is rebuilt and no compositor is touched

Two groups need things that are not in this repository and are skipped without them (set the variables to run them):
  KEYD_BIN=/path/to/keyd            keyd's own `keyd check` on every configuration the generator can write
  KEYD_SRC=/path/to/keyd/source     the real keyd engine: every Mac chord, the app switcher, the overlays and the Caps Lock delay are
                                    fed to the engine through test/keyd-trace.c and the keys that come out are compared (needs gcc)
"""
import contextlib, getpass, importlib.machinery, io, importlib.util, json, os, pathlib, re, shutil, signal, socket, subprocess, sys, tempfile, threading, time, unittest
from collections import Counter

sys.dont_write_bytecode = True

HERE = pathlib.Path(__file__).resolve().parent
KIT = HERE.parent
KEYS = KIT / "keys"
sys.path.insert(0, str(HERE))
from test_sleep_power_themes import Sandbox, USERNS, calls, fake_bin, in_userns, run, tree, write_exec, SAFE_PATH  # noqa: E402


def load(path, name):
    loader = importlib.machinery.SourceFileLoader(name, str(path))
    mod = importlib.util.module_from_spec(importlib.util.spec_from_loader(name, loader))
    loader.exec_module(mod)
    return mod


CONFIG = load(KEYS / "keyd-config", "keyd_config")
APPMAP = load(KEYS / "keyd-appmap", "keyd_appmap")

KEYD_BIN = os.environ.get("KEYD_BIN") or shutil.which("keyd")
KEYD_SRC = os.environ.get("KEYD_SRC")
IDS = ["k:05ac:0262"]

PROC_DEVICES = """\
I: Bus=0019 Vendor=0000 Product=0001 Version=0000
N: Name="Power Button"
H: Handlers=kbd event1

I: Bus=0003 Vendor=05ac Product=0262 Version=0111
N: Name="Apple Inc. Apple Internal Keyboard / Trackpad"
H: Handlers=sysrq kbd leds event10

I: Bus=0003 Vendor=05ac Product=0262 Version=0001
N: Name="bcm5974"
H: Handlers=event11 mouse2

I: Bus=0003 Vendor=046d Product=4075 Version=0111
N: Name="Logitech Wireless Keyboard PID:4075"
H: Handlers=sysrq kbd leds event7

I: Bus=0005 Vendor=004c Product=0267 Version=0001
N: Name="Magic Keyboard"
H: Handlers=sysrq kbd leds event20

I: Bus=0003 Vendor=05ac Product=8600 Version=0001
N: Name="Apple Inc. Some Mouse"
H: Handlers=mouse3 event21
"""


# ======================================================================================================================
# keys/keyd-config
# ======================================================================================================================
class Generator(unittest.TestCase):
    def test_the_configuration_has_the_documented_shape(self):
        text = CONFIG.conf(IDS)
        self.assertTrue(text.startswith("# Omarchy Kit"))
        self.assertIn("[ids]\n\nk:05ac:0262\n", text)
        self.assertIn("leftmeta = layer(cmd)", text)
        for header in ("[main]", "[cmd:C]", "[cmd_switch:M]", "[cmd+shift]", "[cmd+alt]", "[control+cmd]", "[alt]", "[altgr]"):
            self.assertIn(f"\n{header}\n", text)
        order = [text.index(f"\n[{h}]") for h in ("cmd:C", "cmd+shift", "cmd+alt", "control+cmd")]
        self.assertEqual(order, sorted(order), "composite layers must come after the layers they combine")
        self.assertNotIn("rightmeta", text, "the right Command key must stay Super")
        self.assertNotIn("leftcontrol", text.replace("# ", ""), "left Ctrl must stay as it is")

    def test_the_panic_sequence_is_in_the_file_people_will_open(self):
        self.assertIn("Backspace + Escape + Enter", CONFIG.conf(IDS))

    def test_comments_are_on_their_own_lines_because_keyd_rejects_a_trailing_one(self):
        for line in CONFIG.conf(IDS).splitlines():
            if "#" in line:
                self.assertTrue(line.startswith("#"), line)

    def test_copy_and_paste_are_terminal_safe_without_the_helper(self):
        text = CONFIG.conf(IDS)
        self.assertIn("c = C-insert", text)
        self.assertIn("v = S-insert", text)
        self.assertNotIn("c = C-c", text, "plain Ctrl+C is the helper's job, only while an app has the focus")

    def test_caps_delay_is_on_by_default_and_zero_turns_it_off(self):
        self.assertIn("capslock = timeout(noop, 150, capslock)", CONFIG.conf(IDS))
        self.assertNotIn("capslock", CONFIG.conf(IDS, 0).replace("# Caps Lock", ""))
        self.assertIn("timeout(noop, 1000, capslock)", CONFIG.conf(IDS, 1000))

    def test_bad_input_is_refused(self):
        for ids in ([], ["05ac:0262"], ["k:05ac:026"], ["k:05AC:0262"], ["*"], ["k:05ac:0262\n[main]"]):
            with self.subTest(ids=ids):
                with self.assertRaises(ValueError):
                    CONFIG.conf(ids)
        for delay in (-1, 1001):
            with self.subTest(delay=delay):
                with self.assertRaises(ValueError):
                    CONFIG.conf(IDS, delay)

    def test_output_is_deterministic(self):
        self.assertEqual(CONFIG.conf(IDS), CONFIG.conf(IDS))
        self.assertEqual(CONFIG.overlays_json(), CONFIG.overlays_json())

    def test_detect_finds_apple_keyboards_only(self):
        self.assertEqual(CONFIG.detect(PROC_DEVICES), ["k:05ac:0262", "k:004c:0267"],
                         "the trackpad (same id, no kbd handler), the Logitech keyboard, the Apple mouse and the power button are not keyboards to remap")
        self.assertEqual(CONFIG.detect(""), [])

    def test_the_super_chords_it_sends_are_all_documented(self):
        norm = {"return": "enter", "escape": "escape", "grave": "grave", "print": "print"}
        documented = set()
        for _, sends, _, _ in CONFIG.SUPER_CHORDS:
            for chord in sends.split(", "):
                *mods, key = chord.split("+")
                documented.add((frozenset(mods), norm.get(key.lower(), key.lower())))
        for mods, key in CONFIG.config_super_chords():
            with self.subTest(mods=mods, key=key):
                self.assertIn((frozenset(mods), key), documented, "the layer sends a Super chord that chords_text() does not tell the Hyprland side about")

    def test_the_documented_chords_that_omarchy_already_has_are_real_omarchy_bindings(self):
        bindings = pathlib.Path("/usr/share/omarchy/default/hypr/bindings")
        if not bindings.is_dir():
            self.skipTest("Omarchy's default bindings are not installed")
        text = "".join(p.read_text() for p in bindings.glob("*.lua"))
        for needle in ('"SUPER + ALT + SPACE", "Apps menu"', '"SUPER + CTRL + L"', '"SUPER + CTRL + E"', '"SUPER + F"', '"SUPER + CTRL + C"', '"PRINT", "Screenshot"'):
            self.assertIn(needle, text, f"Omarchy no longer binds {needle}: update the table in keyd-config")

    def test_overlays_are_well_formed_and_cover_every_dangerous_terminal_chord(self):
        data = json.loads(CONFIG.overlays_json())
        self.assertEqual(sorted(data["overlays"]), ["app", "terminal"])
        for name, binds in data["overlays"].items():
            for b in binds:
                self.assertRegex(b, APPMAP.BINDING.pattern, f"{name}: {b}")
        term = data["overlays"]["terminal"]
        for k in "dzs":
            self.assertIn(f"cmd.{k} = noop", term, f"Cmd+{k} must never reach a shell as Ctrl+{k}")
        self.assertIn("cmd.c = C-insert", term)
        self.assertIn("cmd.dot = C-c", term, "Cmd+. cancels, as on a Mac")
        self.assertEqual(data["overlays"]["app"], ["cmd.c = C-c", "cmd.v = C-v"])

    def test_the_cli_prints_and_refuses_unknown_arguments(self):
        ok = run([sys.executable, "-I", str(KEYS / "keyd-config"), "conf", "--ids", "k:05ac:0262", "--caps-delay", "0"])
        self.assertEqual(ok.returncode, 0, ok.stderr)
        self.assertEqual(ok.stdout, CONFIG.conf(IDS, 0))
        for args in ([], ["bogus"], ["conf", "--nope"], ["conf", "--caps-delay", "x"], ["overlays", "x"], ["detect", "a", "b"]):
            with self.subTest(args=args):
                self.assertEqual(run([sys.executable, "-I", str(KEYS / "keyd-config"), *args]).returncode, 2)
        self.assertEqual(run([sys.executable, "-I", str(KEYS / "keyd-config"), "conf"]).returncode, 1, "no ids: refused, not guessed")
        self.assertEqual(run([sys.executable, "-I", str(KEYS / "keyd-config"), "--help"]).returncode, 0)

    def test_detect_cli_exit_codes(self):
        with tempfile.TemporaryDirectory() as d:
            f = pathlib.Path(d) / "devices"
            f.write_text(PROC_DEVICES)
            r = run([sys.executable, "-I", str(KEYS / "keyd-config"), "detect", str(f)])
            self.assertEqual((r.returncode, r.stdout.split()), (0, ["k:05ac:0262", "k:004c:0267"]))
            f.write_text("")
            self.assertEqual(run([sys.executable, "-I", str(KEYS / "keyd-config"), "detect", str(f)]).returncode, 1)
            self.assertEqual(run([sys.executable, "-I", str(KEYS / "keyd-config"), "detect", str(pathlib.Path(d) / "nope")]).returncode, 1)


# ======================================================================================================================
# keyd's own checker and the real engine (skipped without KEYD_BIN / KEYD_SRC)
# ======================================================================================================================
@unittest.skipUnless(KEYD_BIN, "set KEYD_BIN (or install keyd) to run keyd's own configuration check")
class KeydCheck(Sandbox):
    def check(self, text):
        f = self.tmp / "t.conf"
        f.write_text(text)
        return run([KEYD_BIN, "check", str(f)])

    def test_every_configuration_the_generator_can_write_passes_keyd_check(self):
        for delay in (0, 1, 150, 1000):
            for ids in (IDS, IDS + ["k:004c:0267"]):
                with self.subTest(delay=delay, ids=ids):
                    r = self.check(CONFIG.conf(ids, delay))
                    self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_the_checker_really_fails_on_a_bad_file(self):
        self.assertNotEqual(self.check("[ids]\n\nk:05ac:0262\n\n[main]\n\nleftmeta = layer(nothere)\n").returncode, 0)
        self.assertNotEqual(self.check(CONFIG.conf(IDS).replace("M-grave", "M-bogus")).returncode, 0)


def effective(lines):
    """The chords an app would see: the held modifiers at each key press, from keyd's emitted events."""
    mods = {"leftcontrol": "Ctrl", "rightcontrol": "Ctrl", "leftshift": "Shift", "rightshift": "Shift", "leftalt": "Alt",
            "rightalt": "AltGr", "leftmeta": "Super", "rightmeta": "Super"}
    order = ["Super", "Ctrl", "Alt", "AltGr", "Shift"]
    held, chords = Counter(), []
    for line in lines:
        if not line.strip():
            continue
        if line.startswith("BIND FAILED"):
            chords.append(line)
            continue
        key, state = line.rsplit(" ", 1)
        if key in mods:
            held[mods[key]] += 1 if state == "down" else -1
        elif state == "down":
            chords.append("+".join([m for m in order if held[m] > 0] + [key]))
    return chords, sorted(m for m in order if held[m] > 0)


def tap(*keys):
    """Keys pressed in order and released in reverse: tap('meta', 'shift', 'z') is Command+Shift+Z."""
    return [f"{k} down" for k in keys[:-1]] + [f"{keys[-1]} down", f"{keys[-1]} up"] + [f"{k} up" for k in reversed(keys[:-1])]


@unittest.skipUnless(KEYD_SRC and shutil.which("gcc"), "set KEYD_SRC to a keyd source tree (and have gcc) to run the real engine")
class Engine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory(prefix="kit-keyd-")
        cls.tmp = pathlib.Path(cls._tmp.name)
        src = pathlib.Path(KEYD_SRC)
        cls.trace = cls.tmp / "keyd-trace"
        files = [str(src / "src" / f"{n}.c") for n in ("keyboard", "string", "macro", "config", "log", "ini", "keys", "unicode")]
        r = run(["gcc", "-DDATA_DIR=\"\"", f"-DKEYD_H=\"{src}/src/keyd.h\"", "-o", str(cls.trace), str(HERE / "keyd-trace.c"), *files])
        if r.returncode:
            raise unittest.SkipTest("could not build the keyd engine driver: " + r.stderr[-400:])
        cls.conf = cls.tmp / "mac.conf"
        cls.conf.write_text(CONFIG.conf(IDS))
        cls.conf0 = cls.tmp / "mac0.conf"
        cls.conf0.write_text(CONFIG.conf(IDS, 0))
        cls.overlays = json.loads(CONFIG.overlays_json())["overlays"]

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def feed(self, batches, binds=(), conf=None):
        text = "".join(f"bind {b}\n" for b in binds) + "\n".join("\n".join(b) + "\n" for b in batches)
        r = run([str(self.trace), str(conf or self.conf)], input=text)
        self.assertEqual(r.returncode, 0, r.stderr)
        return effective(r.stdout.splitlines())

    def chord(self, *keys, binds=()):
        chords, held = self.feed([tap(*keys)], binds)
        self.assertEqual(held, [], f"{keys}: a modifier is left pressed")
        return chords

    # -- the layer on its own: what an app sees when the helper is not running (the static, terminal-safe state)
    def test_command_acts_as_ctrl_for_the_ordinary_shortcuts(self):
        for key in "xazwfrtl1":
            with self.subTest(key=key):
                self.assertEqual(self.chord("meta", key), [f"Ctrl+{key}"])
        self.assertEqual(self.chord("meta", "shift", "z"), ["Ctrl+Shift+z"])
        self.assertEqual(self.chord("meta", "shift", "t"), ["Ctrl+Shift+t"])

    def test_copy_and_paste_are_safe_for_a_terminal_when_the_helper_is_down(self):
        self.assertEqual(self.chord("meta", "c"), ["Ctrl+insert"])
        self.assertEqual(self.chord("meta", "v"), ["Shift+insert"])

    def test_text_navigation_like_a_mac(self):
        cases = {("meta", "left"): "home", ("meta", "right"): "end", ("meta", "up"): "Ctrl+home", ("meta", "down"): "Ctrl+end",
                 ("meta", "shift", "right"): "Shift+end", ("alt", "left"): "Ctrl+left", ("alt", "shift", "right"): "Ctrl+Shift+right",
                 ("alt", "backspace"): "Ctrl+backspace", ("alt", "delete"): "Ctrl+delete", ("rightalt", "left"): "Ctrl+left"}
        for keys, want in cases.items():
            with self.subTest(keys=keys):
                self.assertEqual(self.chord(*keys), [want])

    def test_history_and_tabs(self):
        self.assertEqual(self.chord("meta", "["), ["Alt+left"])
        self.assertEqual(self.chord("meta", "]"), ["Alt+right"])
        self.assertEqual(self.chord("meta", "shift", "["), ["Ctrl+Shift+tab"])
        self.assertEqual(self.chord("meta", "shift", "]"), ["Ctrl+tab"])
        self.assertEqual(self.chord("meta", "alt", "left"), ["Ctrl+pageup"])
        self.assertEqual(self.chord("meta", "alt", "right"), ["Ctrl+pagedown"])

    def test_mac_system_chords_become_the_super_chords_that_hyprland_binds(self):
        cases = {("meta", "space"): "Super+Alt+space", ("meta", "`"): "Super+`", ("meta", "q"): "Super+q", ("meta", "h"): "Super+h",
                 ("meta", "m"): "Super+m", ("meta", "shift", "3"): "Shift+print", ("meta", "shift", "4"): "print",
                 ("meta", "shift", "5"): "Super+Ctrl+c", ("control", "meta", "q"): "Super+Ctrl+l", ("control", "meta", "space"): "Super+Ctrl+e",
                 ("control", "meta", "f"): "Super+f", ("meta", "shift", "."): "Ctrl+h", ("meta", "alt", "i"): "Ctrl+Shift+i",
                 ("meta", "alt", "u"): "Ctrl+u"}
        for keys, want in cases.items():
            with self.subTest(keys=keys):
                self.assertEqual(self.chord(*keys), [want])

    def test_command_option_delete_never_becomes_omarchys_close_all_windows(self):
        self.assertEqual(self.chord("meta", "alt", "delete"), [], "Ctrl+Alt+Delete closes every window in Omarchy")

    def test_what_physical_ctrl_option_and_the_right_command_key_still_do(self):
        cases = {("control", "c"): "Ctrl+c", ("control", "d"): "Ctrl+d", ("control", "left"): "Ctrl+left", ("alt", "tab"): "Alt+tab",
                 ("rightmeta", "enter"): "Super+enter", ("rightmeta", "c"): "Super+c", ("rightmeta", "tab"): "Super+tab",
                 ("rightalt", "e"): "AltGr+e"}
        for keys, want in cases.items():
            with self.subTest(keys=keys):
                self.assertEqual(self.chord(*keys), [want])

    def test_unmodified_typing_is_untouched(self):
        self.assertEqual(self.chord("a"), ["a"])
        self.assertEqual(self.chord("shift", "a"), ["Shift+a"])
        self.assertEqual(self.chord("backspace"), ["backspace"])
        self.assertEqual(self.chord("left"), ["left"])
        self.assertEqual(self.chord("tab"), ["tab"])

    def test_command_pressed_alone_leaves_nothing_stuck(self):
        chords, held = self.feed([["meta down", "meta up"]])
        self.assertEqual((chords, held), ([], []))

    # -- the app switcher: Super must stay held for as long as Command is
    def test_command_tab_holds_super_until_command_is_released(self):
        chords, held = self.feed([["meta down", "tab down", "tab up", "tab down", "tab up"]])
        self.assertEqual(chords, ["Super+tab", "Super+tab"])
        self.assertEqual(held, ["Super"], "the switcher needs to see Super still down, and Ctrl must not be")
        chords, held = self.feed([["meta down", "tab down", "tab up", "tab down", "tab up"], ["meta up"]])
        self.assertEqual(held, [], "releasing Command releases Super")

    def test_shift_command_tab_goes_backwards_and_inside_the_switcher_the_keys_work(self):
        self.assertEqual(self.chord("meta", "shift", "tab"), ["Super+Shift+tab"])
        chords, held = self.feed([["meta down", "tab down", "tab up", "shift down", "tab down", "tab up", "shift up",
                                   "left down", "left up", "right down", "right up", "` down", "` up",
                                   "q down", "q up", "h down", "h up", "esc down", "esc up", "meta up"]])
        self.assertEqual(chords, ["Super+tab", "Super+Shift+tab", "Super+Shift+tab", "Super+tab", "Super+Shift+tab", "Super+q", "Super+h",
                                  "Super+Alt+esc"], "Esc must never be Super+Esc (Omarchy's system menu)")
        self.assertEqual(held, [])

    # -- the overlays the helper applies with `keyd bind`
    def test_app_overlay_makes_copy_and_paste_plain_ctrl_c_and_v(self):
        a = self.overlays["app"]
        self.assertEqual(self.chord("meta", "c", binds=a), ["Ctrl+c"])
        self.assertEqual(self.chord("meta", "v", binds=a), ["Ctrl+v"])
        self.assertEqual(self.chord("meta", "shift", "c", binds=a), ["Ctrl+Shift+c"])
        self.assertEqual(self.chord("meta", "shift", "v", binds=a), ["Ctrl+Shift+v"])

    def test_terminal_overlay_keeps_the_dangerous_ctrl_chords_away_from_the_shell(self):
        t = self.overlays["terminal"]
        want = {("meta", "c"): ["Ctrl+insert"], ("meta", "v"): ["Shift+insert"], ("meta", "k"): ["Ctrl+l"], ("meta", "w"): ["Super+w"],
                ("meta", "n"): ["Super+enter"], ("meta", "."): ["Ctrl+c"], ("meta", "shift", "c"): ["Ctrl+Shift+c"],
                ("meta", "shift", "v"): ["Ctrl+Shift+v"], ("alt", "backspace"): ["Alt+backspace"], ("rightalt", "backspace"): ["Alt+backspace"],
                ("meta", "q"): ["Super+q"], ("control", "c"): ["Ctrl+c"], ("control", "d"): ["Ctrl+d"], ("control", "z"): ["Ctrl+z"]}
        for key in CONFIG.TERMINAL_NOOP:
            want[("meta", key)] = []
        for keys, chords in want.items():
            with self.subTest(keys=keys):
                self.assertEqual(self.chord(*keys, binds=t), chords)

    def test_every_overlay_binding_is_accepted_by_the_engine(self):
        for name, binds in self.overlays.items():
            chords, _ = self.feed([tap("meta", "c")], binds)
            self.assertFalse([c for c in chords if c.startswith("BIND FAILED")], f"{name} overlay: {chords}")

    # -- Caps Lock
    def test_caps_lock_needs_a_deliberate_press(self):
        self.assertEqual(self.feed([["capslock down", "50ms", "capslock up"]])[0], [], "a quick brush does nothing")
        self.assertEqual(self.feed([["capslock down", "120ms", "capslock up"]])[0], [], "still below 150 ms")
        self.assertEqual(self.feed([["capslock down", "200ms", "capslock up"]])[0], ["capslock"], "a held press toggles it")

    def test_caps_lock_is_plain_with_the_delay_off(self):
        self.assertEqual(self.feed([["capslock down", "capslock up"]], conf=self.conf0)[0], ["capslock"])

    def test_typing_through_a_caps_lock_brush_is_not_swallowed(self):
        self.assertEqual(self.feed([["capslock down", "60ms", "a down", "a up", "capslock up"]])[0], ["a"])


# ======================================================================================================================
# keys/keyd-appmap
# ======================================================================================================================
class Classify(unittest.TestCase):
    def test_the_terminal_tag_decides(self):
        tagged = json.dumps({"class": "anything", "tags": ["default-opacity*", "terminal*"]})
        self.assertEqual(APPMAP.classify(tagged), "terminal")
        self.assertEqual(APPMAP.classify(json.dumps({"class": "foot", "tags": ["terminal"]})), "terminal")

    def test_an_app_or_no_window_is_an_app(self):
        self.assertEqual(APPMAP.classify(json.dumps({"class": "brave-browser", "tags": ["default-opacity*"]})), "app")
        self.assertEqual(APPMAP.classify(json.dumps({"class": "x", "tags": []})), "app")
        self.assertEqual(APPMAP.classify("{}"), "app", "Hyprland answers {} when nothing has the focus (a launcher, an empty workspace)")

    def test_a_real_answer_beats_the_class_hint_but_no_answer_falls_back_to_omarchys_rule(self):
        self.assertEqual(APPMAP.classify(json.dumps({"class": "Alacritty", "tags": []}), "Alacritty"), "app", "the compositor's tags are the authority")
        for hint in ("Alacritty", "kitty", "foot", "com.mitchellh.ghostty", "org.omarchy.btop", "TUI.float", "wezterm"):
            with self.subTest(hint=hint):
                self.assertEqual(APPMAP.classify("", hint), "terminal")
        for hint in ("", "brave-browser", "footnote", "my-kitty-app", "org.gnome.Nautilus"):
            with self.subTest(hint=hint):
                self.assertEqual(APPMAP.classify("not json", hint), "app")

    def test_dynamic_tags_carry_a_trailing_star_and_nothing_else_counts(self):
        self.assertEqual(APPMAP.classify(json.dumps({"tags": ["terminal*x"]})), "app")
        self.assertEqual(APPMAP.classify(json.dumps({"tags": [1, None, "terminal*"]})), "terminal")

    def test_active_class_reads_the_event_line(self):
        self.assertEqual(APPMAP.active_class("activewindow>>foot,~/code: nvim, a,b"), "foot")
        self.assertEqual(APPMAP.active_class("activewindow>>,"), "")
        self.assertEqual(APPMAP.active_class("openwindow>>1,2,3,foot"), "")


class Instances(Sandbox):
    def make(self, name, *, uid_ok=True, kind1="socket", kind2="socket", mtime=None):
        d = self.tmp / "hypr" / name
        d.mkdir(parents=True)
        socks = []
        for n, kind in ((".socket.sock", kind1), (".socket2.sock", kind2)):
            p = d / n
            if kind == "socket":
                s = socket.socket(socket.AF_UNIX)
                s.bind(str(p))
                socks.append(s)
            elif kind == "file":
                p.write_text("")
            elif kind == "symlink":
                other = self.tmp / f"{name}-target"
                s = socket.socket(socket.AF_UNIX)
                s.bind(str(other))
                socks.append(s)
                p.symlink_to(other)
            if mtime is not None and p.exists() and not p.is_symlink():
                os.utime(p, (mtime, mtime))
        self.addCleanup(lambda: [s.close() for s in socks])
        return d

    def test_finds_the_session_of_the_right_user(self):
        d = self.make("abc")
        self.assertEqual(APPMAP.find_instance(str(self.tmp), os.getuid()), (str(d / ".socket.sock"), str(d / ".socket2.sock")))

    def test_a_session_of_another_user_is_ignored(self):
        self.make("abc")
        self.assertIsNone(APPMAP.find_instance(str(self.tmp), os.getuid() + 1))

    def test_a_symlink_or_a_plain_file_in_place_of_a_socket_is_refused(self):
        self.make("evil1", kind1="symlink")
        self.make("evil2", kind2="file")
        self.assertIsNone(APPMAP.find_instance(str(self.tmp), os.getuid()), "a root service must not be pointed at another socket")

    def test_the_newest_session_wins(self):
        self.make("old", mtime=1_000_000)
        new = self.make("new", mtime=2_000_000)
        self.assertEqual(APPMAP.find_instance(str(self.tmp), os.getuid())[1], str(new / ".socket2.sock"))

    def test_no_runtime_dir_is_no_session(self):
        self.assertIsNone(APPMAP.find_instance(str(self.tmp / "missing"), os.getuid()))
        self.assertIsNone(APPMAP.find_instance(str(self.tmp), os.getuid()))


class OverlayFile(Sandbox):
    def write(self, data):
        p = self.tmp / "o.json"
        p.write_text(data if isinstance(data, str) else json.dumps(data))
        return str(p)

    def test_the_generated_file_loads(self):
        self.assertEqual(set(APPMAP.load_overlays(self.write(CONFIG.overlays_json()))["overlays"]), {"app", "terminal"})

    def test_anything_else_is_refused(self):
        bad = ["not json", "[]", {"overlays": {}}, {"overlays": {"app": []}}, {"overlays": {"app": [], "terminal": "x"}},
               {"overlays": {"app": [], "terminal": [1]}}, {"overlays": {"app": [], "terminal": ["no equals sign"]}},
               {"overlays": {"app": ["cmd.c = C-c\n[main]"], "terminal": []}}, {"overlays": {"app": ["cmd.c =  "], "terminal": []}}]
        for b in bad:
            with self.subTest(bad=b):
                with self.assertRaises(ValueError):
                    APPMAP.load_overlays(self.write(b))
        with self.assertRaises(OSError):
            APPMAP.load_overlays(str(self.tmp / "missing.json"))


FAKE_KEYD = '''#!/bin/bash
echo "$*" >> "$KEYD_LOG"
[ -e "$KEYD_FAIL" ] && { echo "boom" >&2; exit 1; }
exit 0
'''


class Applier(Sandbox):
    def setUp(self):
        super().setUp()
        self.enterContext(contextlib.redirect_stderr(io.StringIO()))   # the applier logs a refusal once, which is what some tests provoke
        self.log = self.tmp / "keyd.log"
        self.fail = self.tmp / "fail"
        keyd = write_exec(self.tmp / "keyd", FAKE_KEYD.split("\n", 1)[1])
        keyd.write_text(FAKE_KEYD.replace('"$KEYD_LOG"', f'"{self.log}"').replace('"$KEYD_FAIL"', f'"{self.fail}"'))
        keyd.chmod(0o755)
        self.applier = APPMAP.Applier(str(keyd), json.loads(CONFIG.overlays_json()))

    def lines(self):
        return self.log.read_text().splitlines() if self.log.exists() else []

    def test_apply_resets_then_binds_and_only_when_the_state_changes(self):
        self.assertTrue(self.applier.apply("terminal"))
        self.assertTrue(self.applier.apply("terminal"))
        self.assertEqual(len(self.lines()), 1)
        self.assertTrue(self.lines()[0].startswith("bind reset cmd.c = C-insert cmd.v = S-insert"))
        self.assertTrue(self.applier.apply("app"))
        self.assertEqual(self.lines()[1], "bind reset cmd.c = C-c cmd.v = C-v")

    def test_a_refusal_is_remembered_so_the_next_event_tries_again(self):
        self.fail.write_text("")
        self.assertFalse(self.applier.apply("terminal"))
        self.assertIsNone(self.applier.current)
        self.fail.unlink()
        self.assertTrue(self.applier.apply("terminal"))
        self.assertEqual(len(self.lines()), 2)

    def test_a_missing_keyd_binary_is_not_a_crash(self):
        a = APPMAP.Applier(str(self.tmp / "no-such-keyd"), json.loads(CONFIG.overlays_json()))
        self.assertFalse(a.apply("terminal"))

    def test_reset_drops_the_overlay(self):
        self.applier.apply("terminal")
        self.applier.reset()
        self.assertEqual(self.lines()[-1], "bind reset")
        self.assertIsNone(self.applier.current)


class FakeHyprland:
    """The two sockets of a Hyprland session: a command socket that answers `j/activewindow` with the JSON in .window, and an event
    socket that sends whatever send() is given to every connected client."""
    def __init__(self, runtime):
        d = pathlib.Path(runtime) / "hypr" / "sig"
        d.mkdir(parents=True)
        self.window = {"class": "brave-browser", "title": "x", "tags": []}
        self.s1, self.s2 = socket.socket(socket.AF_UNIX), socket.socket(socket.AF_UNIX)
        self.s1.bind(str(d / ".socket.sock"))
        self.s2.bind(str(d / ".socket2.sock"))
        self.s1.listen(5)
        self.s2.listen(5)
        self.clients, self.stop = [], False
        threading.Thread(target=self._serve1, daemon=True).start()
        threading.Thread(target=self._accept2, daemon=True).start()

    def _serve1(self):
        while not self.stop:
            try:
                c, _ = self.s1.accept()
            except OSError:
                return
            with c:
                c.recv(1024)
                c.sendall(json.dumps(self.window).encode())

    def _accept2(self):
        while not self.stop:
            try:
                c, _ = self.s2.accept()
            except OSError:
                return
            self.clients.append(c)

    def send(self, line):
        for c in list(self.clients):
            c.sendall((line + "\n").encode())

    def close_events(self):
        for c in self.clients:
            c.close()
        self.clients.clear()

    def close(self):
        self.stop = True
        self.close_events()
        self.s1.close()
        self.s2.close()


class Service(Sandbox):
    """keyd-appmap as a real process against fake Hyprland sockets and a fake keyd: events in, `keyd bind` calls out."""
    def setUp(self):
        super().setUp()
        self.runtime = self.tmp / "run"
        self.runtime.mkdir()
        self.log = self.tmp / "keyd.log"
        keyd = self.tmp / "keyd"
        keyd.write_text(f'#!/bin/bash\necho "$*" >> "{self.log}"\nexit 0\n')
        keyd.chmod(0o755)
        self.keyd = str(keyd)
        self.overlays = self.tmp / "overlays.json"
        self.overlays.write_text(CONFIG.overlays_json())

    def start(self, *extra):
        err = open(self.tmp / "service.err", "w")
        self.addCleanup(err.close)
        p = subprocess.Popen([sys.executable, "-I", str(KEYS / "keyd-appmap"), "--uid", str(os.getuid()), "--runtime-dir", str(self.runtime),
                              "--keyd", self.keyd, "--overlays", str(self.overlays), "--poll", "0.2", *extra],
                             stdout=subprocess.DEVNULL, stderr=err)
        self.addCleanup(lambda: (p.poll() is None) and (p.kill(), p.wait()))
        return p

    def binds(self):
        return [l for l in (self.log.read_text().splitlines() if self.log.exists() else [])]

    def wait_for(self, n, timeout=8):
        end = time.time() + timeout
        while time.time() < end:
            if len(self.binds()) >= n:
                return True
            time.sleep(0.05)
        return False

    def test_it_follows_the_focus_and_resets_when_stopped(self):
        hypr = FakeHyprland(self.runtime)
        self.addCleanup(hypr.close)
        p = self.start()
        self.assertTrue(self.wait_for(1), "the first overlay (an app has the focus) is applied at start")
        self.assertEqual(self.binds()[0], "bind reset cmd.c = C-c cmd.v = C-v")
        time.sleep(0.3)   # let the service connect to the event socket
        hypr.window = {"class": "foot", "title": "zsh", "tags": ["terminal*"]}
        hypr.send("activewindow>>foot,zsh")
        self.assertTrue(self.wait_for(2))
        self.assertTrue(self.binds()[1].startswith("bind reset cmd.c = C-insert"))
        hypr.send("activewindow>>foot,zsh")   # the same state again: nothing to do
        hypr.send("workspace>>2")
        time.sleep(0.4)
        self.assertEqual(len(self.binds()), 2)
        hypr.window = {}
        hypr.send("activewindow>>,")
        self.assertTrue(self.wait_for(3))
        self.assertEqual(self.binds()[2], "bind reset cmd.c = C-c cmd.v = C-v", "no window: treated as an app")
        p.send_signal(signal.SIGTERM)
        self.assertEqual(p.wait(timeout=8), 0)
        self.assertEqual(self.binds()[-1], "bind reset", "stopping always drops the overlay")

    def test_many_events_in_one_burst_cost_one_query_and_one_apply(self):
        hypr = FakeHyprland(self.runtime)
        self.addCleanup(hypr.close)
        self.start()
        self.assertTrue(self.wait_for(1))
        time.sleep(0.3)
        hypr.window = {"class": "foot", "title": "", "tags": ["terminal*"]}
        hypr.send("\n".join(["activewindow>>brave,a", "activewindowv2>>0x1", "activewindow>>foot,b"]))
        self.assertTrue(self.wait_for(2))
        time.sleep(0.4)
        self.assertEqual(len(self.binds()), 2)

    def test_when_hyprland_goes_away_the_overlay_is_reset_and_it_waits_for_the_next_session(self):
        hypr = FakeHyprland(self.runtime)
        p = self.start()
        self.assertTrue(self.wait_for(1))
        time.sleep(0.3)
        hypr.close()
        shutil.rmtree(self.runtime / "hypr")
        self.assertTrue(self.wait_for(2))
        self.assertEqual(self.binds()[1], "bind reset", "the session ended: back to the static, terminal-safe keys")
        self.assertIsNone(p.poll(), "it keeps running and waits")
        hypr2 = FakeHyprland(self.runtime)
        self.addCleanup(hypr2.close)
        self.assertTrue(self.wait_for(3), "a new session gets its overlay")
        self.assertEqual(self.binds()[2], "bind reset cmd.c = C-c cmd.v = C-v")

    def test_it_waits_quietly_when_there_is_no_session_and_still_stops_on_sigterm(self):
        p = self.start()
        time.sleep(0.6)
        self.assertEqual(self.binds(), [])
        p.send_signal(signal.SIGTERM)
        self.assertEqual(p.wait(timeout=8), 0)
        self.assertEqual(self.binds(), ["bind reset"])

    def test_a_bad_overlay_file_stops_it_before_it_binds_anything(self):
        self.overlays.write_text("{}")
        p = self.start()
        self.assertEqual(p.wait(timeout=8), 1)
        self.assertEqual(self.binds(), [])

    def test_print_state_and_once(self):
        hypr = FakeHyprland(self.runtime)
        self.addCleanup(hypr.close)
        base = [sys.executable, "-I", str(KEYS / "keyd-appmap"), "--uid", str(os.getuid()), "--runtime-dir", str(self.runtime)]
        self.assertEqual(run(base + ["--print-state"]).stdout.strip(), "app")
        hypr.window = {"class": "foot", "tags": ["terminal*"]}
        self.assertEqual(run(base + ["--print-state"]).stdout.strip(), "terminal")
        self.assertEqual(self.binds(), [], "--print-state never touches keyd")
        r = run(base + ["--once", "--keyd", self.keyd, "--overlays", str(self.overlays)])
        self.assertEqual((r.returncode, r.stdout.strip()), (0, "terminal"))
        self.assertTrue(self.binds()[0].startswith("bind reset cmd.c = C-insert"))
        self.assertEqual(run(base[:-2] + ["--runtime-dir", str(self.tmp / "none"), "--print-state"]).stdout.strip(), "app")

    def test_argument_guard(self):
        script = str(KEYS / "keyd-appmap")
        for args in ([], ["--bogus"], ["--uid"], ["--uid", "1", "extra"]):
            with self.subTest(args=args):
                self.assertEqual(run([sys.executable, "-I", script, *args]).returncode, 2)
        self.assertEqual(run([sys.executable, "-I", script, "--uid", "x"]).returncode, 1, "a bad value is an error, not a default")
        self.assertEqual(run([sys.executable, "-I", script, "--help"]).returncode, 0)


# ======================================================================================================================
# keys/install-keyd
# ======================================================================================================================
INSTALLER = KEYS / "install-keyd"


class InstallerArguments(Sandbox):
    def env(self, **extra):
        return {"PATH": SAFE_PATH, "HOME": str(self.tmp), **extra}

    def devices(self, text=PROC_DEVICES):
        f = self.tmp / "devices"
        f.write_text(text)
        return str(f)

    def test_unknown_options_exit_2_and_say_usage(self):
        for args in (["--bogus"], ["--remove", "--bogus"], ["install"], ["--caps-delay"], ["--caps-delay", "x"], ["--caps-delay", "1001"], ["--caps-delay", "-1"]):
            with self.subTest(args=args):
                r = run(["bash", str(INSTALLER), *args], env=self.env())
                self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
                self.assertIn("usage", r.stderr + r.stdout)

    def test_help_prints_the_header_and_does_nothing(self):
        before = tree(self.tmp)
        r = run(["bash", str(INSTALLER), "--help"], env=self.env())
        self.assertEqual(r.returncode, 0)
        self.assertIn("Backspace + Escape + Enter", r.stdout)
        self.assertIn("--dry-run", r.stdout)
        self.assertEqual(tree(self.tmp), before)

    @unittest.skipIf(os.geteuid() == 0, "would touch the real system when run as root")
    def test_it_refuses_without_root_and_says_to_use_sudo(self):
        for args in ([], ["--remove"], ["--caps-delay", "0"]):
            with self.subTest(args=args):
                r = run(["bash", str(INSTALLER), *args], env=self.env())
                self.assertEqual(r.returncode, 1)
                self.assertIn("sudo", r.stderr)
                self.assertIn("--dry-run", r.stderr)

    @unittest.skipIf(os.geteuid() == 0, "would touch the real system when run as root")
    def test_dry_run_needs_no_root_prints_every_step_and_the_configuration(self):
        fb = fake_bin(self.tmp / "fb", pacman="exit 0", systemctl="exit 0", keyd="exit 0")
        devices = self.devices()
        before = tree(self.tmp)
        r = run(["bash", str(INSTALLER), "--dry-run"], env={"PATH": f"{fb}:{SAFE_PATH}", "HOME": str(self.tmp), "KEYD_KIT_DEVICES": devices})
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("keyboards to remap: k:05ac:0262 k:004c:0267", r.stdout)
        for step in ("+ install -Dm644", "/etc/keyd/omarchy-kit-mac.conf", "keyd-appmap", "+ systemctl daemon-reload", "+ systemctl enable keyd.service",
                     "+ systemctl restart omarchy-kit-keyd-appmap.service", "dry run: nothing was changed"):
            self.assertIn(step, r.stdout)
        self.assertIn("leftmeta = layer(cmd)", r.stdout)
        self.assertIn(f"--uid {os.getuid()}", r.stdout)
        self.assertEqual([c for c in calls(fb) if not c.startswith("keyd check")], [], "a dry run must not run pacman or systemctl")
        self.assertEqual([l for l in tree(self.tmp) if not l.startswith("fb")], [l for l in before if not l.startswith("fb")])

    @unittest.skipIf(os.geteuid() == 0, "would touch the real system when run as root")
    def test_dry_run_honours_the_caps_delay_and_remove_prints_its_steps(self):
        fb = fake_bin(self.tmp / "fb", keyd="exit 0")
        env = {"PATH": f"{fb}:{SAFE_PATH}", "HOME": str(self.tmp), "KEYD_KIT_DEVICES": self.devices()}
        r = run(["bash", str(INSTALLER), "--dry-run", "--caps-delay", "0"], env=env)
        self.assertEqual(r.returncode, 0)
        self.assertNotIn("capslock = timeout", r.stdout)
        r = run(["bash", str(INSTALLER), "--dry-run", "--remove"], env=env)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("+ rm -f", r.stdout)
        self.assertIn("+ systemctl disable --now omarchy-kit-keyd-appmap.service", r.stdout)

    @unittest.skipIf(os.geteuid() == 0, "would touch the real system when run as root")
    def test_no_apple_keyboard_means_nothing_to_do(self):
        r = run(["bash", str(INSTALLER), "--dry-run"], env=self.env(KEYD_KIT_DEVICES=self.devices("I: Bus=0003 Vendor=046d Product=4075 Version=0111\nN: Name=\"Logitech Keyboard\"\nH: Handlers=kbd event7\n")))
        self.assertEqual(r.returncode, 1)
        self.assertIn("no Apple keyboard", r.stderr)


@unittest.skipUnless(USERNS, "needs `unshare -Urm` (unprivileged user namespaces) and a non-root caller")
class InstallerInNamespace(Sandbox):
    """Fake root in a private user+mount namespace with tmpfs over /etc and /usr/local, so nothing real is written; pacman, systemctl and
    keyd are fakes (keyd runs the real `keyd check` when KEYD_BIN is set, so the configuration is validated for real)."""
    DRIVER = r'''
        S=$1; mount -t tmpfs none /etc && mount -t tmpfs none /usr/local || { echo MOUNT_FAIL=1; exit 0; }
        mkdir -p /etc/systemd/system
        C=/etc/keyd/omarchy-kit-mac.conf; O=/etc/omarchy-kit/keyd-overlays.json; H=/usr/local/libexec/omarchy-kit/keyd-appmap; U=/etc/systemd/system/omarchy-kit-keyd-appmap.service
        sum() { sha256sum "$@" 2>/dev/null | cut -d' ' -f1 | paste -sd, -; }
        have() { for f in "$@"; do [ -e "$f" ] && printf 1 || printf 0; done; }
        bash "$S" --caps-delay 200 >/tmp/out1 2>&1; echo RC1=$?
        echo FILES1=$(have $C $O $H $U); echo MODES=$(stat -c %a $C $O $H $U | paste -sd, -); echo OWNERS=$(stat -c %u $C $H | paste -sd, -)
        echo CONF=$(grep -c '^k:' $C); echo DELAY=$(grep -c 'timeout(noop, 200, capslock)' $C)
        cp $U "$UNIT_COPY"; echo UNIT_UID=$(grep -o -- '--uid [0-9]*' $U); echo UNIT_EXEC=$(grep '^ExecStart' $U | cut -d= -f2- | cut -d' ' -f1-3)
        echo HELPER_SAME=$(cmp -s "$(dirname "$S")/keyd-appmap" $H && echo 1 || echo 0)
        echo OVERLAYS_VALID=$(python3 -c 'import json; d=json.load(open("'$O'")); print(sorted(d["overlays"]))' | tr -d " ")
        H1=$(sum $C $O $H $U)
        bash "$S" --caps-delay 200 >/tmp/out2 2>&1; echo RC2=$?; echo SAME=$([ "$H1" = "$(sum $C $O $H $U)" ] && echo 1 || echo 0)
        bash "$S" --remove >/tmp/out3 2>&1; echo RCR=$?; echo FILES3=$(have $C $O $H $U)
        bash "$S" --remove >/tmp/out4 2>&1; echo RCR2=$?
        echo DIRS=$(have /usr/local/libexec/omarchy-kit /etc/omarchy-kit)
        '''

    def fakes(self, keyd_ok=True):
        """pacman, systemctl and keyd as fakes. keyd is NOT on the PATH at first: the fake pacman puts it there, like the real one would."""
        state = self.tmp / "state"
        state.mkdir(exist_ok=True)
        fb = self.tmp / "fb"
        real = f'[ "$1" = check ] && [ -x "{KEYD_BIN}" ] && exec "{KEYD_BIN}" "$@"; ' if KEYD_BIN and keyd_ok else ""
        keyd_body = real + ("exit 0" if keyd_ok else '[ "$1" = check ] && { echo "line 3: nope" >&2; exit 1; }; exit 0')
        src = self.tmp / "keyd.src"
        src.write_text(f'#!/bin/bash\necho "keyd $*" >> "{fb}/calls.log"\n{keyd_body}\n')
        fake_bin(
            fb,
            pacman=f'case "$*" in *keyd*) cp "{src}" "{fb}/keyd"; chmod +x "{fb}/keyd";; esac; exit 0',
            systemctl=f'''case "$1" in is-active) n=$(cat {state}/n 2>/dev/null || echo 0); echo $((n+1)) > {state}/n; [ "$n" -ge 1 ] && exit 0 || exit 3;; esac; exit 0''',
        )
        return fb

    def env(self, fb, **extra):
        return {"PATH": f"{fb}:{SAFE_PATH}", "HOME": str(self.tmp), "SUDO_UID": "1234", "KEYD_KIT_DEVICES": self.write_devices(),
                "UNIT_COPY": str(self.tmp / "unit.service"), **extra}

    def write_devices(self):
        f = self.tmp / "devices"
        f.write_text(PROC_DEVICES)
        return str(f)

    def test_install_twice_then_remove_twice(self):
        fb = self.fakes()
        o = in_userns(self.DRIVER, str(INSTALLER), env=self.env(fb))
        if "MOUNT_FAIL" in o:
            self.skipTest("cannot mount tmpfs in the namespace")
        self.assertEqual((o["RC1"], o["FILES1"], o["MODES"], o["OWNERS"]), ("0", "1111", "644,644,755,644", "0,0"), o)
        self.assertEqual((o["CONF"], o["DELAY"]), ("2", "1"), "both Apple keyboards, and the caps delay that was asked for")
        self.assertEqual(o["UNIT_UID"], "--uid 1234", "the service reads the session of the user who ran sudo")
        self.check_unit(self.tmp / "unit.service")
        self.assertEqual(o["UNIT_EXEC"], "/usr/bin/python3 -I /usr/local/libexec/omarchy-kit/keyd-appmap")
        self.assertEqual((o["HELPER_SAME"], o["OVERLAYS_VALID"]), ("1", "['app','terminal']"), "the root-owned copy is the kit's file")
        self.assertEqual((o["RC2"], o["SAME"]), ("0", "1"), "installing again changes nothing")
        self.assertEqual((o["RCR"], o["FILES3"], o["RCR2"], o["DIRS"]), ("0", "0000", "0", "00"), "remove deletes everything it made, twice is fine")
        log = calls(fb)
        self.assertEqual(log.count("pacman -S --needed --noconfirm keyd"), 1, "keyd is installed when it is missing, and not again once it is there")
        for expect in ("systemctl daemon-reload", "systemctl enable keyd.service omarchy-kit-keyd-appmap.service", "systemctl start keyd.service",
                       "keyd reload", "systemctl restart omarchy-kit-keyd-appmap.service", "systemctl disable --now omarchy-kit-keyd-appmap.service",
                       "systemctl disable --now keyd.service"):
            self.assertIn(expect, log, "start on the first install, reload on the second")
        self.assertLess(log.index("pacman -S --needed --noconfirm keyd"), min(i for i, c in enumerate(log) if c.startswith("keyd check")), "keyd is installed before its check runs")

    def check_unit(self, unit):
        """systemd's own verifier on the unit that was written (it also needs keyd.service to exist, so a stand-in sits next to it)."""
        analyze = shutil.which("systemd-analyze")
        if not analyze:
            return
        d = self.tmp / "units"
        d.mkdir()
        shutil.copy(unit, d / "omarchy-kit-keyd-appmap.service")
        (d / "keyd.service").write_text("[Unit]\nDescription=stand-in\n[Service]\nExecStart=/bin/true\n")
        r = run([analyze, "verify", "--man=no", str(d / "omarchy-kit-keyd-appmap.service")])
        text = r.stdout + r.stderr
        self.assertNotRegex(text, r"(?i)unknown (key|section|lvalue)|invalid|failed to parse|bad (value|unit)", text)
        text = unit.read_text()
        for must in ("CapabilityBoundingSet=CAP_DAC_OVERRIDE CAP_DAC_READ_SEARCH", "NoNewPrivileges=yes", "ProtectSystem=strict", "RestrictAddressFamilies=AF_UNIX",
                     "PartOf=keyd.service", "Requires=keyd.service", "Restart=always", "ExecStopPost=-/usr/bin/keyd bind reset"):
            self.assertIn(must, text)

    def test_it_checks_the_configuration_before_activating_anything(self):
        fb = self.fakes()
        o = in_userns(self.DRIVER, str(INSTALLER), env=self.env(fb))
        if "MOUNT_FAIL" in o:
            self.skipTest("cannot mount tmpfs in the namespace")
        checks = [c for c in calls(fb) if c.startswith("keyd check")]
        self.assertTrue(checks, "keyd check ran")
        self.assertLess(calls(fb).index(checks[0]), calls(fb).index("systemctl enable keyd.service omarchy-kit-keyd-appmap.service"))

    def test_a_configuration_keyd_rejects_installs_nothing(self):
        fb = self.fakes(keyd_ok=False)
        drv = r'''
            S=$1; mount -t tmpfs none /etc && mount -t tmpfs none /usr/local || { echo MOUNT_FAIL=1; exit 0; }
            mkdir -p /etc/systemd/system
            bash "$S" >/tmp/out 2>&1; echo RC=$?; echo MSG=$(grep -c 'rejected the configuration' /tmp/out)
            echo LEFT=$(find /etc /usr/local -type f | wc -l)'''
        o = in_userns(drv, str(INSTALLER), env=self.env(fb))
        if "MOUNT_FAIL" in o:
            self.skipTest("cannot mount tmpfs in the namespace")
        self.assertEqual((o["RC"], o["MSG"], o["LEFT"]), ("1", "1", "0"))
        self.assertNotIn("systemctl enable keyd.service omarchy-kit-keyd-appmap.service", calls(fb))

    def test_another_keyd_configuration_is_never_overwritten_or_joined(self):
        fb = self.fakes()
        shutil.copy(self.tmp / "keyd.src", fb / "keyd")   # keyd is already installed here (someone else's configuration uses it)
        (fb / "keyd").chmod(0o755)
        drv = r'''
            S=$1; mount -t tmpfs none /etc && mount -t tmpfs none /usr/local || { echo MOUNT_FAIL=1; exit 0; }
            mkdir -p /etc/systemd/system /etc/keyd; printf '[ids]\n*\n[main]\ncapslock = esc\n' > /etc/keyd/default.conf
            bash "$S" >/tmp/out 2>&1; echo RC=$?; echo MSG=$(grep -c 'another keyd configuration' /tmp/out)
            echo MINE=$([ -e /etc/keyd/omarchy-kit-mac.conf ] && echo 1 || echo 0); echo THEIRS=$(grep -c capslock /etc/keyd/default.conf)
            bash "$S" --remove >/tmp/out 2>&1; echo RCR=$?; echo THEIRS2=$(grep -c capslock /etc/keyd/default.conf)'''
        o = in_userns(drv, str(INSTALLER), env=self.env(fb))
        if "MOUNT_FAIL" in o:
            self.skipTest("cannot mount tmpfs in the namespace")
        self.assertEqual((o["RC"], o["MSG"], o["MINE"], o["THEIRS"], o["RCR"], o["THEIRS2"]), ("1", "1", "0", "1", "0", "1"))
        self.assertNotIn("systemctl disable --now keyd.service", calls(fb), "remove must not switch keyd off while someone else's configuration needs it")
        self.assertIn("keyd reload", calls(fb))

    def test_without_sudo_uid_it_refuses_instead_of_guessing_whose_session(self):
        fb = self.fakes()
        env = self.env(fb)
        del env["SUDO_UID"]
        drv = r'''S=$1; mount -t tmpfs none /etc && mount -t tmpfs none /usr/local || { echo MOUNT_FAIL=1; exit 0; }
                  bash "$S" >/tmp/out 2>&1; echo RC=$?; echo MSG=$(grep -c 'SUDO_UID' /tmp/out); echo LEFT=$(find /etc /usr/local -type f | wc -l)'''
        o = in_userns(drv, str(INSTALLER), env=env)
        if "MOUNT_FAIL" in o:
            self.skipTest("cannot mount tmpfs in the namespace")
        self.assertEqual((o["RC"], o["MSG"], o["LEFT"]), ("1", "1", "0"))


# ======================================================================================================================
# keys/caps-lock
# ======================================================================================================================
class CapsLockTool(Sandbox):
    SEED = "-- my input\nhl.config({ input = { kb_variant = \"mac\" } })\n"

    def setUp(self):
        super().setUp()
        kit = self.tmp / "kit"
        (kit / "keys").mkdir(parents=True)
        shutil.copy(KEYS / "caps-lock", kit / "keys" / "caps-lock")
        (kit / "build_cheatsheet.py").write_text(f'open("{self.tmp}/rebuilt", "w").write("x")\n')
        self.script = kit / "keys" / "caps-lock"
        self.cfg = self.tmp / "cfg"
        (self.cfg / "hypr").mkdir(parents=True)
        self.lua = self.cfg / "hypr" / "input.lua"
        self.lua.write_text(self.SEED)
        self.opts = self.tmp / "opts"
        self.opts.write_text("compose:caps,shift:both_capslock_cancel")
        self.errfile = self.tmp / "configerrors"
        self.fb = fake_bin(
            self.tmp / "fb",
            hyprctl=f'''case "$*" in
              "-j getoption input:kb_options") printf '{{"option":"input:kb_options","str":"%s","set":true}}' "$(cat {self.opts})";;
              configerrors) cat {self.errfile} 2>/dev/null;;
            esac; exit 0''',
            systemctl="exit 0",
        )

    def tool(self, *args):
        return run(["bash", str(self.script), *args],
                   env={"PATH": f"{self.fb}:{SAFE_PATH}", "HOME": str(self.tmp), "XDG_CONFIG_HOME": str(self.cfg), "CAPS_LOCK_SETTLE": "0"})

    def test_real_adds_one_marked_block_that_empties_the_two_caps_options(self):
        r = self.tool("real")
        self.assertEqual(r.returncode, 0, r.stderr)
        text = self.lua.read_text()
        self.assertTrue(text.startswith(self.SEED), "the user's own lines are untouched")
        self.assertEqual(text.count(">>> caps-lock"), 1)
        self.assertIn('hl.config({ input = { kb_options = "" } })', text)
        self.assertIn("reload", " ".join(calls(self.fb)))
        self.assertIn("systemctl --user is-active --quiet omarchy-fcitx5.service", calls(self.fb))
        self.assertIn("systemctl --user restart omarchy-fcitx5.service", calls(self.fb), "fcitx5 copies the keymap when it starts")
        self.assertTrue((self.tmp / "rebuilt").exists(), "the kit pages are rebuilt")
        self.assertEqual(self.tool().stdout.strip(), "caps lock: real")

    def test_other_options_omarchy_had_are_kept(self):
        self.opts.write_text("compose:caps,shift:both_capslock_cancel,grp:alts_toggle")
        self.assertEqual(self.tool("real").returncode, 0)
        self.assertIn('kb_options = "grp:alts_toggle"', self.lua.read_text())

    def test_real_twice_is_the_same_as_once(self):
        self.tool("real")
        first = self.lua.read_text()
        self.opts.write_text("")
        self.tool("real")
        self.assertEqual(self.lua.read_text(), first)

    def test_compose_removes_the_block_and_restores_the_file_exactly(self):
        self.tool("real")
        r = self.tool("compose")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.lua.read_text(), self.SEED)
        self.assertEqual(self.tool().stdout.strip(), "caps lock: compose")
        self.assertEqual(self.tool("compose").returncode, 0, "compose when already compose is fine")
        self.assertEqual(self.lua.read_text(), self.SEED)

    def test_the_backup_is_made_once_and_never_overwritten(self):
        self.tool("real")
        bak = self.lua.with_name("input.lua.bak-caps")
        self.assertEqual(bak.read_text(), self.SEED)
        self.lua.write_text(self.lua.read_text() + "-- added later\n")
        self.tool("compose")
        self.tool("real")
        self.assertEqual(bak.read_text(), self.SEED)

    def test_a_hyprland_error_after_the_change_is_reported_and_fails(self):
        self.errfile.write_text("input.lua:99: syntax error\n")
        r = self.tool("real")
        self.assertEqual(r.returncode, 1)
        self.assertIn("syntax error", r.stdout)

    def test_unknown_arguments_and_a_missing_file(self):
        before = self.lua.read_text()
        for args in (["bogus"], ["--bogus"], ["REAL"], ["real", "extra"]):
            with self.subTest(args=args):
                self.assertEqual(self.tool(*args).returncode, 2)
        self.assertEqual(self.lua.read_text(), before)
        self.assertFalse(self.lua.with_name("input.lua.bak-caps").exists(), "a refused call changes nothing, not even a backup")
        self.lua.unlink()
        self.assertEqual(self.tool("real").returncode, 1)
        self.assertEqual(self.tool("--help").returncode, 0)

    def test_the_file_keeps_its_mode(self):
        self.lua.chmod(0o640)
        self.tool("real")
        self.assertEqual(oct(self.lua.stat().st_mode & 0o777), "0o640")


# ======================================================================================================================
# the public repository: nothing personal in what was added
# ======================================================================================================================
class Hygiene(unittest.TestCase):
    FILES = [KEYS / n for n in ("keyd-config", "keyd-appmap", "install-keyd", "caps-lock")] + [HERE / "keyd-trace.c", pathlib.Path(__file__)]

    def test_no_home_paths_user_names_or_addresses(self):
        user = getpass.getuser()
        for f in self.FILES:
            text = f.read_text()
            with self.subTest(file=f.name):
                self.assertNotRegex(text, r"/home/[a-z]", "a home path")
                self.assertNotRegex(text, r"\b(?:\d{1,3}\.){3}\d{1,3}\b", "an IP address")
                if len(user) >= 3 and user not in ("root", "nobody"):
                    self.assertNotIn(user, text, "the name of the account that wrote it")

    def test_the_scripts_are_executable_and_the_python_ones_compile(self):
        for n in ("keyd-config", "keyd-appmap", "install-keyd", "caps-lock"):
            self.assertTrue(os.access(KEYS / n, os.X_OK), n)
        for n in ("keyd-config", "keyd-appmap"):
            compile((KEYS / n).read_text(), n, "exec")


if __name__ == "__main__":
    unittest.main()
