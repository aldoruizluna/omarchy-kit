"""Tests for the second round of the Mac look: the Golden Gate themes, look/install-look and look/mac-glass, and the hardware key map.
Standard library only, no root, no network; installers run with HOME and the XDG folders in a temporary directory and fakes for the commands.

  python3 -B test/test_macsweep.py            # or: test/run-all --fast

What is covered:
  themes/golden-gate*     every colour key the other themes have, text contrast of 4.5:1 or better on the background, valid TOML in every shell
                          section override, the Hyprland module parses, the wallpaper generator is registered, light and dark are really light and dark
  look/install-look       the font rule, the window-button layout (saved once, restored exactly), the glass module and its require line, --remove
  look/mac-glass          argument handling, the state file, status
  look/60-kit-mac-ui-font.conf   well-formed XML that matches only quickshell's monospace requests
"""
import json, os, pathlib, re, shutil, subprocess, sys, tempfile, textwrap, tomllib, unittest
import xml.etree.ElementTree as ET

sys.dont_write_bytecode = True

KIT = pathlib.Path(__file__).resolve().parent.parent
SAFE_PATH = "/usr/bin:/bin"
THEMES = ("golden-gate", "golden-gate-night")


def write_exec(path, body):
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("#!/bin/bash\n" + textwrap.dedent(body))
    path.chmod(0o755)
    return path


def fake_bin(d, **cmds):
    d = pathlib.Path(d)
    for name, body in cmds.items():
        write_exec(d / name, f'echo "{name} $*" >> "{d}/calls.log"\n' + textwrap.dedent(body))
    return d


def calls(d):
    f = pathlib.Path(d) / "calls.log"
    return f.read_text().splitlines() if f.exists() else []


def run(cmd, env=None, timeout=60):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env=env)


def luminance(hex_colour):
    h = hex_colour.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    f = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def contrast(a, b):
    la, lb = luminance(a), luminance(b)
    if la < lb:
        la, lb = lb, la
    return (la + 0.05) / (lb + 0.05)


# ======================================================================================================================
# the themes
# ======================================================================================================================
class GoldenGateThemes(unittest.TestCase):
    def colors(self, slug):
        return tomllib.loads((KIT / "themes" / slug / "colors.toml").read_text())

    def test_every_key_the_other_themes_define_is_defined(self):
        reference = set(self.colors("solarpunk"))
        for slug in THEMES:
            self.assertEqual(sorted(reference - set(self.colors(slug))), [], slug)

    def test_light_is_light_and_night_is_dark(self):
        self.assertEqual(self.colors("golden-gate")["mode"], "light")
        self.assertEqual(self.colors("golden-gate-night")["mode"], "dark")
        self.assertGreater(luminance(self.colors("golden-gate")["background"]), 0.8)
        self.assertLess(luminance(self.colors("golden-gate-night")["background"]), 0.05)

    def test_text_colours_read_on_the_background(self):
        # the kit's rule (docs/DEVELOPING.md): at least 4.5:1 for anything that is drawn as text
        low = []
        for slug in THEMES:
            c = self.colors(slug)
            for key, value in c.items():
                if key in ("mode", "selection", "background", "dark_background", "darker_background", "lighter_background"):
                    continue
                if isinstance(value, str) and value.startswith("#") and contrast(value, c["background"]) < 4.5:
                    low.append(f"{slug}.{key} {value} on {c['background']} = {contrast(value, c['background']):.2f}")
        self.assertEqual(low, [])

    def test_text_on_the_selection_colour_and_the_menu_highlight_reads(self):
        for slug in THEMES:
            c = self.colors(slug)
            self.assertGreaterEqual(contrast(c["foreground"], c["selection"]), 4.5, slug)
            menu = tomllib.loads((KIT / "themes" / slug / "shell.menu.toml").read_text())
            self.assertGreaterEqual(contrast(menu["selected-text"], menu["selected-background"]), 4.5, f"{slug} menu highlight")

    def test_every_shell_section_override_is_valid_toml_and_names_a_real_section(self):
        template = pathlib.Path("/usr/share/omarchy/default/themed/shell.toml.tpl")
        sections = set(re.findall(r"^\[(\w[\w-]*)\]", template.read_text(), re.M)) if template.exists() else None
        for slug in THEMES:
            files = sorted((KIT / "themes" / slug).glob("shell.*.toml"))
            self.assertTrue(files, slug)
            for f in files:
                data = tomllib.loads(f.read_text())
                self.assertTrue(data, f"{f.name} is empty")
                if sections is not None:
                    self.assertIn(f.name.split(".")[1], sections, f"{f.name} is not a section of Omarchy's shell.toml")

    def test_the_hyprland_module_parses_and_rounds_the_corners(self):
        luac = shutil.which("luac")
        for slug in THEMES:
            f = KIT / "themes" / slug / "hyprland.lua"
            text = f.read_text()
            self.assertIn("rounding = 16", text)
            self.assertIn("rounding_power", text)
            if luac:
                r = run([luac, "-p", str(f)])
                self.assertEqual(r.returncode, 0, r.stderr)

    def test_the_focused_window_stays_distinguishable(self):
        # no glow, but not invisible either: a different edge colour for the focused window and a dimmed unfocused one
        for slug in THEMES:
            text = (KIT / "themes" / slug / "hyprland.lua").read_text()
            active = re.search(r'local active_border_color = "([^"]+)"', text).group(1)
            inactive = re.search(r'local inactive_border_color = "([^"]+)"', text).group(1)
            self.assertNotEqual(active, inactive, slug)
            self.assertIn("dim_inactive = true", text)

    def test_the_wallpaper_generator_is_registered_and_importable(self):
        text = (KIT / "themes" / "make-wallpapers").read_text()
        for slug, variant in (("golden-gate", "day"), ("golden-gate-night", "night")):
            self.assertRegex(text, rf'"{slug}": \("golden_gate\.py", "{variant}"\)')
        self.assertIn("golden_gate.py", re.search(r"NEEDS_SVG = \{[^}]*\}", text).group(0))
        r = run([sys.executable, "-I", "-c", "import ast,sys; ast.parse(open(sys.argv[1]).read())", str(KIT / "themes" / "generators" / "golden_gate.py")])
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_the_themes_name_no_apple_artwork(self):
        for slug in THEMES:
            for f in (KIT / "themes" / slug).glob("*"):
                self.assertNotIn(f.suffix.lower(), (".icns", ".heic"), f.name)


# ======================================================================================================================
# look/
# ======================================================================================================================
class FontRule(unittest.TestCase):
    def test_the_rule_is_well_formed_and_narrow(self):
        root = ET.parse(KIT / "look" / "60-kit-mac-ui-font.conf").getroot()
        match = root.find("match")
        tests = {t.get("name"): t for t in match.findall("test")}
        self.assertEqual(set(tests), {"prgname", "genericfamily"})
        self.assertEqual(tests["prgname"].find("string").text, "quickshell")
        self.assertEqual(tests["genericfamily"].find("const").text, "monospace")
        edit = match.find("edit")
        self.assertEqual((edit.get("name"), edit.get("mode")), ("family", "prepend"))
        self.assertEqual(edit.find("string").text, "Adwaita Sans")

    @unittest.skipUnless(shutil.which("fc-match"), "fontconfig is not installed")
    def test_it_changes_quickshell_and_nothing_else(self):
        with tempfile.TemporaryDirectory() as d:
            conf = pathlib.Path(d) / "fonts.conf"
            rule = (KIT / "look" / "60-kit-mac-ui-font.conf").read_text().replace("<string>quickshell</string>", "<string>fc-match</string>", 1)
            body = re.search(r"<match.*</match>", rule, re.S).group(0)
            conf.write_text(f'<?xml version="1.0"?><!DOCTYPE fontconfig SYSTEM "urn:fontconfig:fonts.dtd"><fontconfig>'
                            f'<include ignore_missing="yes">/etc/fonts/fonts.conf</include>{body}</fontconfig>')
            env = dict(os.environ, FONTCONFIG_FILE=str(conf))
            plain = run(["fc-match", "monospace"], env=dict(os.environ)).stdout
            ruled = run(["fc-match", "monospace"], env=env).stdout
            if "Adwaita Sans" not in run(["fc-list"]).stdout:
                self.skipTest("Adwaita Sans is not installed")
            self.assertIn("Adwaita Sans", ruled)          # with the rule (the test stands in for quickshell), monospace becomes the UI font
            self.assertNotEqual(plain, ruled)
            self.assertEqual(run(["fc-match", "sans-serif"], env=env).stdout, run(["fc-match", "sans-serif"], env=dict(os.environ)).stdout)
            self.assertEqual(run(["fc-match", "omarchy"], env=env).stdout, run(["fc-match", "omarchy"], env=dict(os.environ)).stdout)


class Sandbox(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="kit-test-")
        self.addCleanup(self._tmp.cleanup)
        self.tmp = pathlib.Path(self._tmp.name)
        self.home = self.tmp / "home"
        self.cfg = self.home / ".config"
        self.hypr = self.cfg / "hypr"
        self.hypr.mkdir(parents=True)
        (self.hypr / "hyprland.lua").write_text('require("hypr.monitors")\nrequire("hypr.gpu")\nrequire("hypr.mackeys")\n-- end\n')

    def env(self, **extra):
        e = {"PATH": f"{self.fb}:{SAFE_PATH}", "HOME": str(self.home), "XDG_CONFIG_HOME": str(self.cfg), "XDG_DATA_HOME": str(self.home / ".local/share")}
        e.update(extra)
        return e

    def hyprland_lua(self):
        return (self.hypr / "hyprland.lua").read_text()


class InstallLook(Sandbox):
    def setUp(self):
        super().setUp()
        self.kit = self.tmp / "kit" / "look"
        shutil.copytree(KIT / "look", self.kit)
        self.gs = self.tmp / "gsettings-state"
        self.gs.write_text("appmenu:close")
        # a fake gsettings with a real memory: get prints the stored value quoted, set stores it, reset restores Omarchy's default
        self.fb = fake_bin(self.tmp / "fb",
                           gsettings=f'''case "$1" in
                             get) echo "'$(cat "{self.gs}")'";;
                             set) printf '%s' "$4" | sed "s/^'//; s/'\\$//" > "{self.gs}";;
                             reset) printf '%s' "appmenu:close" > "{self.gs}";;
                           esac\n''',
                           omarchy="true\n", hyprctl='case "$1" in configerrors) ;; esac\n')

    def go(self, *args):
        return subprocess.run(["bash", str(self.kit / "install-look"), *args], capture_output=True, text=True, timeout=60, env=self.env())

    def test_unknown_option_exits_2_and_changes_nothing(self):
        r = self.go("--nope")
        self.assertEqual(r.returncode, 2)
        self.assertFalse((self.cfg / "fontconfig").exists())
        self.assertEqual(self.gs.read_text(), "appmenu:close")

    def test_install_puts_the_font_rule_the_module_and_the_button_layout_in_place(self):
        r = self.go()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue((self.cfg / "fontconfig/conf.d/60-kit-mac-ui-font.conf").exists())
        self.assertTrue((self.hypr / "macglass.lua").exists())
        self.assertEqual(self.hyprland_lua().count('require("hypr.macglass")'), 1)
        self.assertEqual(self.gs.read_text(), "close:")
        self.assertIn("omarchy restart shell", "\n".join(calls(self.fb)))
        self.assertIn("the glass blur is off", r.stdout)

    def test_install_twice_keeps_one_require_line_and_the_first_saved_layout(self):
        self.go()
        self.go()
        self.assertEqual(self.hyprland_lua().count('require("hypr.macglass")'), 1)
        self.assertIn("BUTTON_LAYOUT=appmenu:close", (self.cfg / "omarchy-kit/look-saved.conf").read_text())

    def test_remove_gives_everything_back(self):
        original = self.hyprland_lua()
        self.go()
        (self.cfg / "omarchy-kit").mkdir(exist_ok=True)
        (self.cfg / "omarchy-kit" / "glass").write_text("on")
        r = self.go("--remove")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertFalse((self.cfg / "fontconfig/conf.d/60-kit-mac-ui-font.conf").exists())
        self.assertFalse((self.hypr / "macglass.lua").exists())
        self.assertFalse((self.cfg / "omarchy-kit" / "glass").exists())
        self.assertEqual(self.hyprland_lua(), original)
        self.assertEqual(self.gs.read_text(), "appmenu:close")

    def test_remove_with_nothing_installed_is_harmless(self):
        r = self.go("--remove")
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_hyprland_config_errors_are_reported(self):
        write_exec(self.fb / "hyprctl", 'case "$1" in configerrors) echo "line 2: boom";; esac\n')
        r = self.go()
        self.assertEqual(r.returncode, 1)
        self.assertIn("config errors", r.stdout)


class MacGlass(Sandbox):
    def setUp(self):
        super().setUp()
        self.fb = fake_bin(self.tmp / "fb", hyprctl='case "$1" in configerrors) ;; esac\n')

    def go(self, *args):
        return subprocess.run(["bash", str(KIT / "look" / "mac-glass"), *args], capture_output=True, text=True, timeout=60, env=self.env())

    def test_bad_arguments_exit_2(self):
        for args in ([], ["maybe"], ["--on"]):
            self.assertEqual(self.go(*args).returncode, 2, args)

    def test_status_defaults_to_off_and_changes_nothing(self):
        r = self.go("status")
        self.assertEqual((r.returncode, r.stdout.strip()), (0, "glass: off"))
        self.assertEqual(calls(self.fb), [])

    def test_it_refuses_without_the_module(self):
        r = self.go("on")
        self.assertEqual(r.returncode, 1)
        self.assertIn("install-look", r.stderr)

    def test_on_and_off_write_the_state_and_reload_hyprland(self):
        (self.hypr / "macglass.lua").write_text("-- module")
        self.assertEqual(self.go("on").stdout.strip(), "glass: on")
        self.assertEqual((self.cfg / "omarchy-kit" / "glass").read_text().strip(), "on")
        self.assertEqual(self.go("status").stdout.strip(), "glass: on")
        self.assertEqual(self.go("off").stdout.strip(), "glass: off")
        self.assertEqual([c for c in calls(self.fb) if c.startswith("hyprctl reload")], ["hyprctl reload"] * 2)

    def test_the_module_reads_the_same_file_the_script_writes(self):
        lua = (KIT / "look" / "macglass.lua").read_text()
        self.assertIn(".config/omarchy-kit/glass", lua)
        self.assertIn("blur = true", lua)
        luac = shutil.which("luac")
        if luac:
            self.assertEqual(run([luac, "-p", str(KIT / "look" / "macglass.lua")]).returncode, 0)

    def test_the_bar_itself_is_never_blurred(self):
        lua = (KIT / "look" / "macglass.lua").read_text()
        first = re.search(r'namespace = "([^"]+)"', lua).group(1)
        self.assertNotIn("omarchy-bar", first.replace("^", ""))   # only its popups are (blur_popups)
        self.assertIn("blur_popups = true", lua)


if __name__ == "__main__":
    unittest.main()
