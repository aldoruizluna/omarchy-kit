"""Tests for the Mac-style desktop pieces: icons and cursor, the Dock and ⌘Tab switcher, the menu bar. Standard library only, no root, no network;
nothing touches the real system (every installer runs with HOME and the XDG folders in a temporary directory and fakes for the commands it calls).

  python3 -B test/test_macdesktop.py            # or: test/run-all --fast

What is covered:
  icons/install-icons     a wrong checksum installs nothing; a good install lays down the five folders, the theme-set hook and the cursor module;
                          it is idempotent; --remove deletes only what it installed and never a folder it did not create
  icons/mac-icons-hook    picks WhiteSur-light or WhiteSur-dark from the theme's mode, and leaves Omarchy's choice alone if the icons are gone
  dock/install-dock       files, default dock.json (kept on re-run and on --remove), the Hyprland module and its require line, --remove
  menubar/install-menubar the bar layout moves to the Mac order, the original is saved and restored exactly, bad JSON is never touched
  mission control         the overlay's binds, shortcuts and IPC agree, nothing is captured live, and its layout function (run in node)
                          keeps every window's proportions, fits the screen and never overlaps
  contracts               every QML file the dock needs is installed; every item id in the menu widget has a Lua action; Lua and QML parse
"""
import hashlib, io, json, os, pathlib, re, shutil, stat, subprocess, sys, tarfile, tempfile, textwrap, unittest

sys.dont_write_bytecode = True

KIT = pathlib.Path(__file__).resolve().parent.parent
SAFE_PATH = "/usr/bin:/bin"


def write_exec(path, body):
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("#!/bin/bash\n" + textwrap.dedent(body))
    path.chmod(0o755)
    return path


def fake_bin(d, **cmds):
    """Fake commands in directory d (bash bodies). Every fake logs its arguments to <d>/calls.log."""
    d = pathlib.Path(d)
    for name, body in cmds.items():
        write_exec(d / name, f'echo "{name} $*" >> "{d}/calls.log"\n' + textwrap.dedent(body))
    return d


def calls(d):
    f = pathlib.Path(d) / "calls.log"
    return f.read_text().splitlines() if f.exists() else []


def run(cmd, env=None, timeout=60):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env=env)


class Sandbox(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="kit-test-")
        self.addCleanup(self._tmp.cleanup)
        self.tmp = pathlib.Path(self._tmp.name)
        self.home = self.tmp / "home"
        self.cfg = self.home / ".config"
        self.data = self.home / ".local" / "share"
        self.hypr = self.cfg / "hypr"
        self.hypr.mkdir(parents=True)
        # the file Omarchy's template gives every user; the installers add their require line after the gpu one
        (self.hypr / "hyprland.lua").write_text('require("hypr.monitors")\nrequire("hypr.gpu")\nrequire("hypr.mackeys")\n-- end\n')
        self.fb = self.tmp / "fb"

    def env(self, **extra):
        e = {"PATH": f"{self.fb}:{SAFE_PATH}", "HOME": str(self.home), "XDG_CONFIG_HOME": str(self.cfg),
             "XDG_DATA_HOME": str(self.data), "XDG_CACHE_HOME": str(self.home / ".cache"), "DBUS_SESSION_BUS_ADDRESS": "fake"}
        e.update(extra)
        return e

    def hyprland_lua(self):
        return (self.hypr / "hyprland.lua").read_text()


# ======================================================================================================================
# icons/install-icons and icons/mac-icons-hook
# ======================================================================================================================
def make_ws_tarball(path):
    """A fake WhiteSur release: its install.sh creates the three variants inside the -d folder, like the real one."""
    install_sh = textwrap.dedent("""\
        #!/usr/bin/env bash
        set -e
        while [ $# -gt 0 ]; do case "$1" in -d) dest="$2"; shift 2;; *) shift;; esac; done
        for v in WhiteSur WhiteSur-light WhiteSur-dark; do mkdir -p "$dest/$v/apps"; echo "[Icon Theme]" > "$dest/$v/index.theme"; done
        """).encode()
    with tarfile.open(path, "w:gz") as t:
        info = tarfile.TarInfo("WhiteSur-icon-theme-fake/install.sh")
        info.size, info.mode = len(install_sh), 0o755
        t.addfile(info, io.BytesIO(install_sh))


def make_cursor_tarball(path):
    with tarfile.open(path, "w:xz") as t:
        for d in ("macOS", "macOS-White"):
            data = b"cursor"
            info = tarfile.TarInfo(f"{d}/cursors/left_ptr")
            info.size = len(data)
            t.addfile(info, io.BytesIO(data))


class InstallIcons(Sandbox):
    def setUp(self):
        super().setUp()
        self.kit = self.tmp / "kit" / "icons"
        self.kit.mkdir(parents=True)
        for f in ("install-icons", "mac-icons-hook", "maccursor.lua"):
            shutil.copy(KIT / "icons" / f, self.kit / f)
        self.fixtures = self.tmp / "fixtures"
        self.fixtures.mkdir()
        make_ws_tarball(self.fixtures / "ws.tar.gz")
        make_cursor_tarball(self.fixtures / "cursor.tar.xz")
        self.fb = fake_bin(
            self.tmp / "fb",
            # serves the fixture that matches the URL, whatever the options in between are
            curl='out=""; url=""; while [ $# -gt 0 ]; do case "$1" in -o) out="$2"; shift 2;; -*) shift;; *) url="$1"; shift;; esac; done\n'
                 f'case "$url" in *WhiteSur*) cp "{self.fixtures}/ws.tar.gz" "$out";; *apple_cursor*) cp "{self.fixtures}/cursor.tar.xz" "$out";; *) exit 22;; esac\n',
            gsettings='case "$1" in get) echo "\'fake\'";; esac\n',
            hyprctl='case "$1" in configerrors) ;; esac\n',
            **{"omarchy-theme-color": 'echo "${FAKE_MODE:-dark}"\n', "omarchy-theme-set-gnome": "true\n"},
        )

    def installer(self, good_checksums=True):
        """The installer, with its two pinned checksums swapped for those of the fixtures (or left alone, to test the refusal)."""
        text = (self.kit / "install-icons").read_text()
        if good_checksums:
            text = re.sub(r"^WS_SHA256=.*$", "WS_SHA256=" + hashlib.sha256((self.fixtures / "ws.tar.gz").read_bytes()).hexdigest(), text, flags=re.M)
            text = re.sub(r"^CUR_SHA512=.*$", "CUR_SHA512=" + hashlib.sha512((self.fixtures / "cursor.tar.xz").read_bytes()).hexdigest(), text, flags=re.M)
        p = self.kit / "install-icons.test"
        p.write_text(text)
        p.chmod(0o755)
        return p

    def go(self, *args, good=True, **env):
        return run(["bash", str(self.installer(good)), *args], env=self.env(**env))

    @property
    def icons(self):
        return self.data / "icons"

    def test_unknown_option_exits_2_and_installs_nothing(self):
        r = self.go("--frobnicate")
        self.assertEqual(r.returncode, 2)
        self.assertFalse(self.icons.exists())
        self.assertEqual(calls(self.fb), [])

    def test_help_prints_the_header_and_changes_nothing(self):
        r = self.go("--help")
        self.assertEqual(r.returncode, 0)
        self.assertIn("WhiteSur", r.stdout)
        self.assertFalse(self.icons.exists())

    def test_a_wrong_checksum_installs_nothing(self):
        r = self.go(good=False)
        self.assertEqual(r.returncode, 1)
        self.assertIn("checksum mismatch", r.stderr)
        self.assertFalse((self.icons / "WhiteSur").exists())
        self.assertFalse((self.cfg / "omarchy" / "hooks" / "theme-set.d" / "50-mac-icons").exists())
        self.assertNotIn("maccursor", self.hyprland_lua())

    def test_install_lays_down_folders_hook_and_cursor_module(self):
        r = self.go()
        self.assertEqual(r.returncode, 0, r.stderr)
        for d in ("WhiteSur", "WhiteSur-light", "WhiteSur-dark", "macOS", "macOS-White"):
            self.assertTrue((self.icons / d).is_dir(), d)
        hook = self.cfg / "omarchy" / "hooks" / "theme-set.d" / "50-mac-icons"
        self.assertTrue(os.access(hook, os.X_OK))
        self.assertTrue((self.hypr / "maccursor.lua").exists())
        self.assertEqual(self.hyprland_lua().count('require("hypr.maccursor")'), 1)
        self.assertIn('set org.gnome.desktop.interface icon-theme WhiteSur-dark', "\n".join(calls(self.fb)))
        self.assertTrue((self.hypr / "hyprland.lua.bak-maccursor").exists())

    def test_install_twice_gives_one_require_line_and_the_same_folders(self):
        self.assertEqual(self.go().returncode, 0)
        before = sorted(p.name for p in self.icons.iterdir())
        self.assertEqual(self.go().returncode, 0)
        self.assertEqual(sorted(p.name for p in self.icons.iterdir()), before)
        self.assertEqual(self.hyprland_lua().count('require("hypr.maccursor")'), 1)

    def test_remove_deletes_only_what_it_installed(self):
        self.assertEqual(self.go().returncode, 0)
        (self.icons / "Yaru-blue").mkdir()
        (self.icons / "Yaru-blue" / "keep").write_text("mine")
        r = self.go("--remove")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(sorted(p.name for p in self.icons.iterdir()), ["Yaru-blue"])
        self.assertFalse((self.cfg / "omarchy" / "hooks" / "theme-set.d" / "50-mac-icons").exists())
        self.assertFalse((self.hypr / "maccursor.lua").exists())
        self.assertNotIn("maccursor", self.hyprland_lua())
        self.assertIn("reset org.gnome.desktop.interface cursor-theme", "\n".join(calls(self.fb)))

    def test_remove_with_nothing_installed_is_harmless(self):
        r = self.go("--remove")
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_a_folder_it_did_not_create_is_never_overwritten(self):
        (self.icons / "WhiteSur").mkdir(parents=True)
        (self.icons / "WhiteSur" / "mine").write_text("hand made")
        r = self.go()
        self.assertEqual(r.returncode, 1)
        self.assertIn("not installed by this script", r.stderr)
        self.assertEqual((self.icons / "WhiteSur" / "mine").read_text(), "hand made")
        r = self.go("--remove")                      # and --remove must not delete a folder that is not in its marker
        self.assertTrue((self.icons / "WhiteSur" / "mine").exists())

    def test_nothing_outside_the_sandbox_is_written(self):
        self.go()
        # everything the installer wrote is under the temporary home or the cache it cleans up
        for stray in ("/tmp/WhiteSur", "/tmp/macOS"):
            self.assertFalse(os.path.exists(stray))


class MacIconsHook(Sandbox):
    def go(self, mode, installed=True):
        self.fb = fake_bin(self.tmp / "fb", gsettings="true\n", **{"omarchy-theme-color": f'echo "{mode}"\n'})
        for d in ("WhiteSur-light", "WhiteSur-dark") if installed else ():
            (self.data / "icons" / d).mkdir(parents=True, exist_ok=True)
        return run(["bash", str(KIT / "icons" / "mac-icons-hook")], env=self.env())

    def test_light_theme_gets_the_light_icons(self):
        self.assertEqual(self.go("light").returncode, 0)
        self.assertIn("icon-theme WhiteSur-light", "\n".join(calls(self.fb)))

    def test_dark_theme_gets_the_dark_icons(self):
        self.assertEqual(self.go("dark").returncode, 0)
        self.assertIn("icon-theme WhiteSur-dark", "\n".join(calls(self.fb)))

    def test_icons_that_are_gone_leave_omarchys_choice_alone(self):
        self.assertEqual(self.go("dark", installed=False).returncode, 0)
        self.assertNotIn("gsettings set", "\n".join(calls(self.fb)))

    def test_without_a_session_bus_it_does_nothing(self):
        self.fb = fake_bin(self.tmp / "fb", gsettings="true\n", **{"omarchy-theme-color": 'echo dark\n'})
        env = self.env()
        env.pop("DBUS_SESSION_BUS_ADDRESS")
        r = run(["bash", str(KIT / "icons" / "mac-icons-hook")], env=env)
        self.assertEqual(r.returncode, 0)
        self.assertEqual(calls(self.fb), [])


# ======================================================================================================================
# dock/install-dock
# ======================================================================================================================
class InstallDock(Sandbox):
    def setUp(self):
        super().setUp()
        self.kit = self.tmp / "kit" / "dock"
        shutil.copytree(KIT / "dock", self.kit)
        self.fb = fake_bin(self.tmp / "fb",
                           quickshell="true\n",
                           **{"uwsm-app": 'shift; exec "$@"\n'},
                           hyprctl='case "$1" in layers) echo "namespace: macdock";; esac\n')

    def go(self, *args):
        return run(["bash", str(self.kit / "install-dock"), *args], env=self.env())

    @property
    def share(self):
        return self.data / "macdock"

    def test_unknown_option_exits_2_and_installs_nothing(self):
        r = self.go("--nope")
        self.assertEqual(r.returncode, 2)
        self.assertFalse(self.share.exists())
        self.assertNotIn("macdock", self.hyprland_lua())

    def test_install_puts_the_program_the_module_and_the_default_settings_in_place(self):
        r = self.go()
        self.assertEqual(r.returncode, 0, r.stderr)
        for name in ("shell.qml", "qmldir", "Dock.qml", "Switcher.qml", "Apps.qml", "Theme.qml"):
            self.assertTrue((self.share / name).exists(), name)
        self.assertTrue((self.hypr / "macdock.lua").exists())
        self.assertEqual(self.hyprland_lua().count('require("hypr.macdock")'), 1)
        conf = json.loads((self.cfg / "macdock" / "dock.json").read_text())
        self.assertIn("org.gnome.Nautilus", conf["pinned"])
        self.assertIs(conf["autohide"], False)
        self.assertTrue((self.hypr / "hyprland.lua.bak-macdock").exists())
        self.assertTrue(any(c.startswith("quickshell -n -p") for c in calls(self.fb)))

    def test_your_dock_json_survives_a_reinstall_and_a_remove(self):
        self.go()
        mine = self.cfg / "macdock" / "dock.json"
        mine.write_text('{"pinned": ["only.this"]}\n')
        self.assertEqual(self.go().returncode, 0)
        self.assertEqual(json.loads(mine.read_text())["pinned"], ["only.this"])
        self.assertEqual(self.go("--remove").returncode, 0)
        self.assertEqual(json.loads(mine.read_text())["pinned"], ["only.this"])

    def test_install_twice_keeps_one_require_line(self):
        self.go()
        self.go()
        self.assertEqual(self.hyprland_lua().count('require("hypr.macdock")'), 1)

    def test_remove_takes_out_the_program_and_the_module_and_puts_the_config_back(self):
        original = self.hyprland_lua()
        self.go()
        r = self.go("--remove")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertFalse(self.share.exists())
        self.assertFalse((self.hypr / "macdock.lua").exists())
        self.assertEqual(self.hyprland_lua(), original)

    def test_it_refuses_to_start_without_quickshell(self):
        # a PATH that has the tools the installer needs but no quickshell (the real one lives in /usr/bin)
        bare = self.tmp / "bare"
        bare.mkdir()
        for tool in ("bash", "cp", "mkdir", "install", "grep", "sed", "tr", "pgrep", "seq", "sleep", "mv", "rm", "dirname", "basename", "cat",
                     "env", "sh"):
            found = shutil.which(tool, path=SAFE_PATH)
            if found:
                (bare / tool).symlink_to(found)
        (self.fb / "quickshell").unlink()
        r = run(["bash", str(self.kit / "install-dock")], env=self.env(PATH=f"{bare}:{self.fb}"))
        self.assertEqual(r.returncode, 1)
        self.assertIn("quickshell is not installed", r.stderr)
        self.assertFalse(self.share.exists())

    def test_hyprland_config_errors_are_reported_not_hidden(self):
        write_exec(self.fb / "hyprctl", 'case "$1" in configerrors) echo "line 3: boom";; layers) echo macdock;; esac\n')
        r = self.go()
        self.assertEqual(r.returncode, 1)
        self.assertIn("config errors", r.stdout)


# ======================================================================================================================
# menubar/install-menubar
# ======================================================================================================================
ORIGINAL_BAR = {
    "version": 1,
    "idle": {"screensaver": 150, "lock": 300},
    "bar": {
        "position": "top",
        "transparent": True,
        "centerAnchor": "omarchy.clock",
        "layout": {
            "left": [{"id": "omarchy.menu"}, {"id": "omarchy.workspaces"}],
            "center": [{"id": "omarchy.indicators"}, {"id": "omarchy.clock", "format": "ddd d MMM HH:mm"},
                       {"id": "omarchy.keyboard-layout"}, {"id": "omarchy.weather"}],
            "right": [{"id": "omarchy.tray"}, {"id": "omarchy.bluetooth"}, {"id": "vpn", "type": "command", "exec": "x"},
                      {"id": "omarchy.network"}, {"id": "omarchy.audio"}, {"id": "omarchy.power"}],
        },
    },
    "plugins": [],
}


def ids(section):
    return [e["id"] if isinstance(e, dict) else e for e in section]


class InstallMenubar(Sandbox):
    def setUp(self):
        super().setUp()
        self.kit = self.tmp / "kit" / "menubar"
        shutil.copytree(KIT / "menubar", self.kit)
        (self.cfg / "omarchy").mkdir(parents=True)
        self.shell = self.cfg / "omarchy" / "shell.json"
        self.shell.write_text(json.dumps(ORIGINAL_BAR, indent=2) + "\n")
        self.fb = fake_bin(self.tmp / "fb", omarchy="true\n", **{"omarchy-shell": "true\n"}, hyprctl="true\n")

    def go(self, *args):
        return run(["bash", str(self.kit / "install-menubar"), *args], env=self.env())

    def layout(self):
        return json.loads(self.shell.read_text())["bar"]["layout"]

    def test_unknown_option_exits_2_and_changes_nothing(self):
        before = self.shell.read_text()
        r = self.go("--nope")
        self.assertEqual(r.returncode, 2)
        self.assertEqual(self.shell.read_text(), before)

    def test_the_bar_takes_the_mac_order(self):
        r = self.go()
        self.assertEqual(r.returncode, 0, r.stderr)
        lay = self.layout()
        self.assertEqual(ids(lay["left"]), ["omarchykit.macmenu"])
        self.assertEqual(ids(lay["center"]), ["omarchy.workspaces"])
        self.assertEqual(ids(lay["right"])[-1], "omarchy.clock")                       # the clock is the last thing on the right
        self.assertNotIn("omarchy.menu", ids(lay["left"] + lay["center"] + lay["right"]))
        self.assertEqual(json.loads(self.shell.read_text())["bar"]["centerAnchor"], "omarchy.workspaces")

    def test_nothing_the_user_had_is_lost_or_duplicated(self):
        self.go()
        lay = self.layout()
        every = ids(lay["left"] + lay["center"] + lay["right"])
        wanted = set(ids(ORIGINAL_BAR["bar"]["layout"]["left"] + ORIGINAL_BAR["bar"]["layout"]["center"] + ORIGINAL_BAR["bar"]["layout"]["right"]))
        self.assertEqual(set(every), (wanted - {"omarchy.menu"}) | {"omarchykit.macmenu"})
        self.assertEqual(len(every), len(set(every)))
        self.assertIn("vpn", every)                                                    # a custom command module keeps its place on the right
        clock = [e for e in lay["right"] if isinstance(e, dict) and e["id"] == "omarchy.clock"][0]
        self.assertEqual(clock["format"], "ddd d MMM HH:mm")                           # and the settings travel with each widget

    def test_everything_outside_the_bar_is_untouched(self):
        self.go()
        now = json.loads(self.shell.read_text())
        self.assertEqual(now["idle"], ORIGINAL_BAR["idle"])
        self.assertEqual(now["bar"]["position"], "top")
        self.assertIs(now["bar"]["transparent"], True)

    def test_install_twice_gives_the_same_layout_and_keeps_the_first_save(self):
        self.go()
        first = self.shell.read_text()
        self.go()
        self.assertEqual(self.shell.read_text(), first)
        saved = json.loads((self.cfg / "omarchy-kit" / "menubar-layout-before.json").read_text())
        self.assertEqual(saved["layout"], ORIGINAL_BAR["bar"]["layout"])

    def test_remove_restores_the_original_layout_exactly(self):
        self.go()
        r = self.go("--remove")
        self.assertEqual(r.returncode, 0, r.stderr)
        now = json.loads(self.shell.read_text())
        self.assertEqual(now["bar"]["layout"], ORIGINAL_BAR["bar"]["layout"])
        self.assertEqual(now["bar"]["centerAnchor"], "omarchy.clock")
        self.assertFalse((self.cfg / "omarchy" / "plugins" / "omarchykit.macmenu").exists())
        self.assertFalse((self.hypr / "macmenu.lua").exists())
        self.assertNotIn("macmenu", self.hyprland_lua())

    def test_remove_without_a_saved_layout_only_takes_its_own_widget_out(self):
        self.go()
        (self.cfg / "omarchy-kit" / "menubar-layout-before.json").unlink()
        self.assertEqual(self.go("--remove").returncode, 0)
        self.assertNotIn("omarchykit.macmenu", ids(sum(self.layout().values(), [])))

    def test_invalid_json_is_never_touched(self):
        self.shell.write_text("{ not json")
        r = self.go()
        self.assertEqual(r.returncode, 1)
        self.assertEqual(self.shell.read_text(), "{ not json")
        self.assertFalse((self.cfg / "omarchy" / "plugins" / "omarchykit.macmenu").exists())

    def test_a_missing_shell_json_is_a_clear_refusal(self):
        self.shell.unlink()
        r = self.go()
        self.assertEqual(r.returncode, 1)
        self.assertIn("shell.json", r.stderr)

    def test_the_plugin_is_copied_and_the_original_file_is_backed_up(self):
        self.go()
        plugin = self.cfg / "omarchy" / "plugins" / "omarchykit.macmenu"
        self.assertTrue((plugin / "manifest.json").exists() and (plugin / "BarWidget.qml").exists())
        self.assertEqual(json.loads((self.cfg / "omarchy" / "shell.json.bak-menubar").read_text()), ORIGINAL_BAR)

    def test_a_widget_the_user_does_not_have_is_not_invented(self):
        bar = json.loads(self.shell.read_text())
        bar["bar"]["layout"] = {"left": [], "center": [], "right": [{"id": "omarchy.clock"}]}
        self.shell.write_text(json.dumps(bar))
        self.go()
        lay = self.layout()
        self.assertEqual(ids(lay["center"]), [])                                       # no workspaces widget existed, so none is added
        self.assertEqual(json.loads(self.shell.read_text())["bar"]["centerAnchor"], "")


# ======================================================================================================================
# dock/MissionControl.qml
# ======================================================================================================================
def js_function(source, name):
    """The text of `function <name>(...) { ... }` out of a QML file (brace matching; no braces appear inside these strings)."""
    start = source.index(f"function {name}(")
    i = source.index("{", start)
    depth = 0
    for j in range(i, len(source)):
        depth += source[j] == "{"
        depth -= source[j] == "}"
        if depth == 0:
            return source[start:j + 1]
    raise AssertionError(f"unbalanced braces in {name}")


class MissionControl(unittest.TestCase):
    QML = (KIT / "dock" / "MissionControl.qml").read_text()
    LUA = (KIT / "dock" / "macdock.lua").read_text()

    def test_every_global_shortcut_the_lua_side_sends_exists_in_the_qml(self):
        sent = set(re.findall(r'hl\.dsp\.global\("macmission:(\w+)"\)', self.LUA))
        declared = set(re.findall(r'GlobalShortcut \{ appid: "macmission"; name: "(\w+)"', self.QML))
        self.assertEqual(sent, {"toggle", "appwindows"})
        self.assertEqual(sent - declared, set())

    def test_the_binds_are_the_ones_documented(self):
        for chord in ('"XF86LaunchA"', '"SUPER + CTRL + UP"', '"SUPER + CTRL + DOWN"'):
            self.assertIn(f"o.bind({chord}", self.LUA)
        header = self.LUA.split("\nlocal home", 1)[0]
        for text in ("F3", "Super+Ctrl+Up", "Super+Ctrl+Down", "Mission Control", "App Expos"):
            self.assertIn(text, header)

    def test_plain_ctrl_arrows_are_never_taken_over(self):
        # Ctrl+Up and Ctrl+Down are text-editing keys; every Mission Control chord that uses them also carries Super
        for m in re.finditer(r'o\.bind\("([^"]*(?:UP|DOWN))"', self.LUA):
            self.assertIn("SUPER", m.group(1), m.group(1))

    def test_the_overlay_surface_has_a_layer_rule_and_the_name_agrees(self):
        self.assertIn('WlrLayershell.namespace: "macmission"', self.QML)
        self.assertRegex(self.LUA, r'namespace = "\^\([^)]*\bmacmission\b[^)]*\)\$"')

    def test_the_ipc_target_has_what_the_tests_and_the_docs_use(self):
        target = self.QML[self.QML.index('target: "mission"'):]
        for fn in ("toggle", "appwindows", "open", "close", "visible", "selectSpace", "selectWindow", "activate", "describe"):
            self.assertIn(f"function {fn}(", target, fn)

    def test_nothing_is_captured_live_and_nothing_is_mapped_while_closed(self):
        self.assertIn("live: false", self.QML)
        self.assertNotIn("live: true", self.QML)
        self.assertIn("visible: shown", self.QML)                               # no surface at all while closed
        self.assertIn("model: win.shown ? win.wins : []", self.QML)             # no ScreencopyView exists while closed
        self.assertIn("spaces = []", self.QML)                                  # captures are dropped on close

    def test_it_is_instantiated_once_and_installed(self):
        self.assertEqual((KIT / "dock" / "shell.qml").read_text().count("MissionControl {}"), 1)
        self.assertIn("MissionControl.qml", (KIT / "dock" / "install-dock").read_text())
        self.assertRegex((KIT / "dock" / "qmldir").read_text(), r"MissionControl 1\.0 MissionControl\.qml")

    # ---- the layout function, run for real in node
    def run_layout(self, windows, W=1300, H=700):
        node = shutil.which("node")
        if not node:
            self.skipTest("node is not installed")
        code = ("const gap = 30, labelH = 40;\n" + js_function(self.QML, "layoutCards") +
                f"\nprocess.stdout.write(JSON.stringify(layoutCards({json.dumps(windows)}, {W}, {H})));")
        r = run([node, "-e", code])
        self.assertEqual(r.returncode, 0, r.stderr)
        return json.loads(r.stdout)

    def assert_sane(self, windows, cards, W=1300, H=700, label=40):
        self.assertEqual(len(cards), len(windows))
        for i, (win, c) in enumerate(zip(windows, cards)):
            self.assertGreaterEqual(c["x"], -0.001)
            self.assertGreaterEqual(c["y"], -0.001)
            self.assertLessEqual(c["x"] + c["w"], W + 0.001, f"card {i} leaves the area on the right")
            self.assertLessEqual(c["y"] + c["h"] + label, H + 0.001, f"card {i} (and its label) leaves the area at the bottom")
            if win["w"] > 0 and win["h"] > 0:
                self.assertAlmostEqual(c["w"] / c["h"], win["w"] / win["h"], places=3, msg=f"card {i} lost its proportions")
        for i in range(len(cards)):
            for j in range(i + 1, len(cards)):
                a, b = cards[i], cards[j]
                apart = a["x"] + a["w"] <= b["x"] + 0.01 or b["x"] + b["w"] <= a["x"] + 0.01 or a["y"] + a["h"] + label <= b["y"] + 0.01 or b["y"] + b["h"] + label <= a["y"] + 0.01
                self.assertTrue(apart, f"cards {i} and {j} overlap")

    def test_no_windows_gives_no_cards(self):
        self.assertEqual(self.run_layout([]), [])

    def test_one_window_is_centred_and_not_blown_up_past_its_real_size(self):
        win = [{"w": 700, "h": 400}]
        cards = self.run_layout(win)
        self.assert_sane(win, cards)
        self.assertLessEqual(cards[0]["h"], 400)
        self.assertAlmostEqual(cards[0]["x"] + cards[0]["w"] / 2, 650, delta=1)

    def test_a_few_mixed_windows_keep_their_proportions_and_fit(self):
        win = [{"w": 701, "h": 767}, {"w": 701, "h": 377}, {"w": 1416, "h": 767}, {"w": 820, "h": 670}]
        self.assert_sane(win, self.run_layout(win))

    def test_many_windows_still_fit_without_overlapping(self):
        win = [{"w": 600 + 40 * i, "h": 400 + 25 * (i % 4)} for i in range(11)]
        self.assert_sane(win, self.run_layout(win))

    def test_windows_without_a_size_get_a_default_shape_instead_of_breaking(self):
        win = [{"w": 0, "h": 0}, {"w": 800, "h": 600}, {"w": 0, "h": 500}]
        cards = self.run_layout(win)
        self.assertEqual(len(cards), 3)
        for c in cards:
            self.assertTrue(c["w"] > 0 and c["h"] > 0)

    def test_a_tiny_area_still_returns_finite_cards(self):
        win = [{"w": 800, "h": 600}] * 3
        for c in self.run_layout(win, W=420, H=260):
            self.assertTrue(all(isinstance(c[k], (int, float)) and c[k] == c[k] for k in ("x", "y", "w", "h")))

    def test_special_workspaces_are_never_listed(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("node is not installed")
        code = js_function(self.QML, "usable") + (
            "\nconst t = [{id: 1, name: '1'}, {id: 7, name: '7'}, {id: -99, name: 'special:hidden'}, {id: 3, name: 'special:scratchpad'}, null].map(w => !!usable(w));"
            "\nprocess.stdout.write(JSON.stringify(t));")
        r = run([node, "-e", code])
        self.assertEqual(json.loads(r.stdout), [True, True, False, False, False])


# ======================================================================================================================
# contracts between the pieces
# ======================================================================================================================
class Contracts(unittest.TestCase):
    def test_every_qml_file_of_the_dock_is_installed_and_registered(self):
        installer = (KIT / "dock" / "install-dock").read_text()
        listed = set(re.search(r"^FILES=\(([^)]*)\)", installer, re.M).group(1).split())
        on_disk = {p.name for p in (KIT / "dock").glob("*.qml")} | {"qmldir"}
        self.assertEqual(listed, on_disk)
        qmldir = (KIT / "dock" / "qmldir").read_text()
        for name in on_disk - {"qmldir", "shell.qml"}:
            self.assertRegex(qmldir, rf"\b{re.escape(name)}\b", f"{name} is not in qmldir")

    def test_every_item_id_in_the_menu_widget_has_a_lua_action(self):
        qml = (KIT / "menubar" / "plugin" / "BarWidget.qml").read_text()
        lua = (KIT / "menubar" / "macmenu.lua").read_text()
        wanted = set(re.findall(r'id: "([a-z]+\.[a-z0-9]+)"', qml))
        wanted.discard("window.move")                       # built as "window.move" + n for n = 1..5, covered below
        defined = set(re.findall(r'\["([a-z]+\.[a-z0-9]+)"\]\s*=', lua)) | {f"window.move{n}" for n in range(1, 6)}
        self.assertTrue(wanted, "no ids found: the pattern is out of date")
        self.assertEqual(sorted(wanted - defined), [])

    def test_the_plugin_id_agrees_everywhere(self):
        manifest = json.loads((KIT / "menubar" / "plugin" / "manifest.json").read_text())
        self.assertIn(f'PLUGIN_ID={manifest["id"]}', (KIT / "menubar" / "install-menubar").read_text())
        self.assertIn(f'moduleName: "{manifest["id"]}"', (KIT / "menubar" / "plugin" / "BarWidget.qml").read_text())
        self.assertIn(f'target: "{manifest["id"]}"', (KIT / "menubar" / "plugin" / "BarWidget.qml").read_text())
        self.assertEqual(manifest["schemaVersion"], 1)
        self.assertIn("bar-widget", manifest["kinds"])

    def test_the_binds_the_dock_module_makes_are_documented_in_its_header(self):
        lua = (KIT / "dock" / "macdock.lua").read_text()
        header = lua.split("\nlocal home", 1)[0]
        for chord in re.findall(r'o\.bind\("SUPER( \+ [A-Z+ ]+)"', lua):
            key = chord.split("+")[-1].strip().lower()
            shown = {"tab": "Tab", "grave": "`", "right": "Right", "left": "Left", "escape": "Escape", "up": "Up", "down": "Down"}.get(key, key.upper())
            self.assertIn(shown, header, f"Super+{shown} is bound but not described in the header of macdock.lua")

    def test_lua_files_parse(self):
        luac = shutil.which("luac")
        if not luac:
            self.skipTest("luac is not installed")
        for f in ("dock/macdock.lua", "menubar/macmenu.lua", "icons/maccursor.lua"):
            r = run([luac, "-p", str(KIT / f)])
            self.assertEqual(r.returncode, 0, f"{f}: {r.stderr}")

    def test_qml_files_have_no_syntax_errors(self):
        qmllint = next((p for p in (shutil.which("qmllint"), "/usr/lib/qt6/bin/qmllint") if p and os.path.exists(p)), None)
        if not qmllint:
            self.skipTest("qmllint is not installed")
        files = [str(p) for p in sorted((KIT / "dock").glob("*.qml")) + sorted((KIT / "menubar" / "plugin").glob("*.qml"))]
        r = run([qmllint, "-I", "/usr/lib/qt6/qml", *files])
        errors = [l for l in (r.stdout + r.stderr).splitlines() if l.startswith("Error")]
        self.assertEqual(errors, [], "\n".join(errors))

    def test_shell_scripts_parse_and_are_executable(self):
        for f in ("icons/install-icons", "icons/mac-icons-hook", "dock/install-dock", "menubar/install-menubar"):
            p = KIT / f
            self.assertTrue(os.access(p, os.X_OK), f"{f} is not executable")
            r = run(["bash", "-n", str(p)])
            self.assertEqual(r.returncode, 0, f"{f}: {r.stderr}")

    def test_no_personal_details_in_the_new_files(self):
        bad = []
        for pattern in ("icons/*", "dock/*", "menubar/*", "menubar/plugin/*"):
            for p in KIT.glob(pattern):
                if not p.is_file():
                    continue
                text = p.read_text(errors="replace")
                for needle in ("/home/", "aldo", "mbpro"):
                    if needle in text.lower():
                        bad.append(f"{p.relative_to(KIT)}: {needle}")
                if re.search(r"[\w.+-]+@[\w-]+\.[a-z]{2,}", text):
                    bad.append(f"{p.relative_to(KIT)}: an email address")
        self.assertEqual(bad, [])

    def test_the_pinned_downloads_are_https_and_checksummed(self):
        text = (KIT / "icons" / "install-icons").read_text()
        for name in ("WS_URL", "CUR_URL"):
            self.assertRegex(text, rf"(?m)^{name}=https://", name)
        self.assertRegex(text, r"(?m)^WS_SHA256=[0-9a-f]{64}$")
        self.assertRegex(text, r"(?m)^CUR_SHA512=[0-9a-f]{128}$")


if __name__ == "__main__":
    unittest.main()
