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
  dock/hot-corners        choosing a corner's action: other keys kept, bad JSON untouched, bad arguments refused, nothing left behind
  menubar/plugin/apps.json  per-app menus: the file's shape, every shown shortcut checked against what the keyd tables really send, the widget's functions in node,
                          the chord parser in real Lua
  dock/ControlCenter      nothing is built while closed, the services and commands it uses exist, no power action, icons exist, the bar button and the installer agree
  dock/Spotlight          the sum parser, name matching, file sorting and icon rules run in node; no search result can power the machine off;
                          it takes the keyboard only while open; it is registered, installed and bound
  dock polish             the Dock's own functions run in node: which program name `ps` shows for an app, and the drag-to-reorder move
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
        self.assertEqual(set(conf["hotCorners"]), {"topLeft", "topRight", "bottomLeft", "bottomRight"})
        self.assertEqual(set(conf["hotCorners"].values()), {"none"}, "hot corners ship off: a brush of the pointer must never start anything")
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
        self.assertEqual(ids(lay["right"])[-2:], ["omarchykit.controlcenter", "omarchy.clock"])   # the Control Center button, then the clock last
        self.assertNotIn("omarchy.menu", ids(lay["left"] + lay["center"] + lay["right"]))
        self.assertEqual(json.loads(self.shell.read_text())["bar"]["centerAnchor"], "omarchy.workspaces")

    def test_nothing_the_user_had_is_lost_or_duplicated(self):
        self.go()
        lay = self.layout()
        every = ids(lay["left"] + lay["center"] + lay["right"])
        wanted = set(ids(ORIGINAL_BAR["bar"]["layout"]["left"] + ORIGINAL_BAR["bar"]["layout"]["center"] + ORIGINAL_BAR["bar"]["layout"]["right"]))
        self.assertEqual(set(every), (wanted - {"omarchy.menu"}) | {"omarchykit.macmenu", "omarchykit.controlcenter"})
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
        self.assertFalse((self.cfg / "omarchy" / "plugins" / "omarchykit.controlcenter").exists())
        self.assertFalse((self.hypr / "macmenu.lua").exists())
        self.assertNotIn("macmenu", self.hyprland_lua())

    def test_remove_without_a_saved_layout_only_takes_its_own_widget_out(self):
        self.go()
        (self.cfg / "omarchy-kit" / "menubar-layout-before.json").unlink()
        self.assertEqual(self.go("--remove").returncode, 0)
        self.assertFalse({"omarchykit.macmenu", "omarchykit.controlcenter"} & set(ids(sum(self.layout().values(), []))))

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
        self.assertTrue((plugin / "manifest.json").exists() and (plugin / "BarWidget.qml").exists() and (plugin / "apps.json").exists())
        cc = self.cfg / "omarchy" / "plugins" / "omarchykit.controlcenter"
        self.assertTrue((cc / "manifest.json").exists() and (cc / "BarWidget.qml").exists())
        self.assertEqual(json.loads((self.cfg / "omarchy" / "shell.json.bak-menubar").read_text()), ORIGINAL_BAR)

    def test_a_widget_the_user_does_not_have_is_not_invented(self):
        bar = json.loads(self.shell.read_text())
        bar["bar"]["layout"] = {"left": [], "center": [], "right": [{"id": "omarchy.clock"}]}
        self.shell.write_text(json.dumps(bar))
        self.go()
        lay = self.layout()
        self.assertEqual(ids(lay["right"]), ["omarchykit.controlcenter", "omarchy.clock"])
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


class DockHoverArea(unittest.TestCase):
    """The icons magnify only when the pointer is ON the dock (2026-10-23: they grew when it was a few pixels away). The numbers were checked
    on the real pointer: 0 at 20 px above, 3 and 10 px beside, 110 px above; 1 on the pill; still 1 at 30 px above once on it; 0 at 45 px."""
    QML = (KIT / "dock" / "Dock.qml").read_text()

    def test_the_idle_hit_area_is_the_pill_and_the_strip_under_it_not_the_whole_window(self):
        self.assertIn("readonly property real idleBand: gap + pillH", self.QML)
        height = re.search(r"\n\s+height: (.+)\n", self.QML[self.QML.index("id: hit"):]).group(1)
        self.assertIn("win.idleBand", height)
        self.assertIn("win.magnifiedBand", height, "it grows over the magnified icons only once the pointer is in")
        self.assertIn("win.implicitHeight", height, "and covers the whole window only while an icon is being dragged")
        self.assertIn("win.dragActive", height)
        width = re.search(r"\n\s+width: (.+)\n", self.QML[self.QML.index("id: hit"):]).group(1)
        self.assertIn("pill.width + (hover.hovered ? 16 : 0)", width, "no side margin while idle")

    def test_a_dragged_icon_keeps_the_hover_so_pulling_it_off_the_dock_still_works(self):
        self.assertIn("onDraggingChanged: win.dragActive = dragging", self.QML)

    def test_the_test_hook_reports_the_magnification_and_the_geometry(self):
        self.assertIn("function magnification(): string", self.QML)


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
# dock/hot-corners, and the Dock's own functions
# ======================================================================================================================
class HotCornersTool(Sandbox):
    def setUp(self):
        super().setUp()
        self.json = self.tmp / "dock.json"
        self.json.write_text(json.dumps({"pinned": ["a", "b"], "iconSize": 60, "autohide": True}, indent=2) + "\n")
        self.tool = KIT / "dock" / "hot-corners"

    def go(self, *args):
        return run([sys.executable, "-I", str(self.tool), *args], env={"PATH": SAFE_PATH, "HOME": str(self.home), "MACDOCK_JSON": str(self.json)})

    def conf(self):
        return json.loads(self.json.read_text())

    def test_it_is_executable_and_help_prints_the_usage_and_changes_nothing(self):
        self.assertTrue(os.access(self.tool, os.X_OK))
        before = self.json.read_text()
        r = self.go("--help")
        self.assertEqual(r.returncode, 0)
        for word in ("bottom-right", "quicknote", "missioncontrol", "hot-corners off"):
            self.assertIn(word, r.stdout)
        self.assertEqual(self.json.read_text(), before)

    def test_unknown_arguments_exit_2_and_change_nothing(self):
        before = self.json.read_text()
        for args in (["bogus"], ["top-left"], ["top-left", "bogus"], ["nowhere", "apps"], ["top-left", "apps", "x"], ["delay"], ["delay", "x"],
                     ["delay", "99"], ["delay", "2001"], ["delay", "-5"], ["off", "now"], ["--nope"]):
            with self.subTest(args=args):
                self.assertEqual(self.go(*args).returncode, 2)
                self.assertEqual(self.json.read_text(), before)

    def test_showing_needs_no_change_and_defaults_to_off(self):
        r = self.go()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual([l.split()[1] for l in r.stdout.splitlines()[:4]], ["none"] * 4)
        self.assertIn("350 ms", r.stdout)

    def test_setting_a_corner_keeps_every_other_key_and_doing_it_twice_changes_nothing_more(self):
        r = self.go("bottom-right", "quicknote")
        self.assertEqual(r.returncode, 0, r.stderr)
        c = self.conf()
        self.assertEqual(c["hotCorners"], {"topLeft": "none", "topRight": "none", "bottomLeft": "none", "bottomRight": "quicknote"})
        self.assertEqual((c["pinned"], c["iconSize"], c["autohide"]), (["a", "b"], 60, True))
        once = self.json.read_text()
        self.go("bottom-right", "quicknote")
        self.assertEqual(self.json.read_text(), once)
        self.go("top-left", "missioncontrol")
        self.assertEqual(self.conf()["hotCorners"]["bottomRight"], "quicknote", "one corner does not undo another")
        self.assertIn("bottom-right  quicknote", self.go().stdout)

    def test_every_action_is_accepted_and_off_turns_all_four_off(self):
        for action in ("none", "missioncontrol", "appexpose", "apps", "quicknote", "lock", "notifications"):
            self.assertEqual(self.go("top-right", action).returncode, 0, action)
            self.assertEqual(self.conf()["hotCorners"]["topRight"], action)
        for corner in ("top-left", "top-right", "bottom-left", "bottom-right"):
            self.go(corner, "apps")
        self.assertEqual(self.go("off").returncode, 0)
        self.assertEqual(set(self.conf()["hotCorners"].values()), {"none"})
        self.assertEqual(self.conf()["pinned"], ["a", "b"])

    def test_the_delay_is_stored_as_a_number(self):
        self.assertEqual(self.go("delay", "500").returncode, 0)
        self.assertEqual(self.conf()["hotCornerDelay"], 500)
        self.assertEqual(self.go("delay", "100").returncode, 0)
        self.assertEqual(self.go("delay", "2000").returncode, 0)

    def test_a_missing_or_broken_dock_json_is_never_created_or_overwritten(self):
        self.json.unlink()
        r = self.go("top-left", "apps")
        self.assertEqual(r.returncode, 1)
        self.assertIn("install-dock", r.stderr)
        self.assertFalse(self.json.exists())
        for text in ("{not json", "[1, 2]", ""):
            self.json.write_text(text)
            r = self.go("top-left", "apps")
            self.assertEqual((r.returncode, self.json.read_text()), (1, text), text)

    def test_no_temporary_file_is_left_behind_and_the_file_ends_with_a_newline(self):
        self.go("bottom-left", "lock")
        self.assertEqual(sorted(p.name for p in self.tmp.iterdir() if p.name.startswith("dock")), ["dock.json"])
        self.assertTrue(self.json.read_text().endswith("\n"))

    def test_an_unknown_action_already_in_the_file_is_shown_as_none(self):
        self.json.write_text(json.dumps({"hotCorners": {"topLeft": "format-the-disk", "bottomRight": "apps"}}))
        lines = self.go().stdout.splitlines()
        self.assertEqual((lines[0].split()[1], lines[3].split()[1]), ("none", "apps"))


class DockPolish(unittest.TestCase):
    """The Dock's own JavaScript (in Apps.qml and Config.qml), taken out of the QML text and run in node."""
    APPS = (KIT / "dock" / "Apps.qml").read_text()
    CONFIG = (KIT / "dock" / "Config.qml").read_text()

    def node(self, code):
        node = shutil.which("node")
        if not node:
            self.skipTest("node is not installed")
        r = run([node, "-e", code])
        self.assertEqual(r.returncode, 0, r.stderr)
        return json.loads(r.stdout)

    def wrappers(self):
        return re.search(r"readonly property var wrappers: (\(\{.*?\}\))", self.APPS, re.S).group(1)

    def process_names(self, commands, procs=()):
        code = (f"const root = {{ wrappers: {self.wrappers()}, procs: {json.dumps({p: True for p in procs})} }};\n" +
                js_function(self.APPS, "processName") + "\n" + js_function(self.APPS, "inBackground") + "\n" +
                f"process.stdout.write(JSON.stringify({json.dumps(commands)}.map(c => [processName({{ command: c }}), inBackground({{ command: c }})])));")
        return self.node(code)

    def test_the_process_name_is_the_first_word_of_the_launcher_cut_to_what_the_kernel_keeps(self):
        got = self.process_names([["/usr/bin/obsidian", "--no-sandbox"], ["env", "A=1", "B=2", "telegram-desktop"], ["Telegram"], []])
        self.assertEqual([g[0] for g in got], ["obsidian", "telegram-deskto", "Telegram", ""])

    def test_launchers_that_start_something_else_answer_cannot_tell(self):
        got = self.process_names([["sh", "-c", "x"], ["uwsm-app", "--", "foo"], ["flatpak", "run", "org.x.App"], ["omarchy-launch-webapp", "https://x.y"], ["xdg-terminal-exec", "nvim"]])
        self.assertEqual([g[0] for g in got], [""] * 5)

    def test_an_app_is_in_the_background_when_a_process_has_its_name(self):
        got = self.process_names([["/usr/bin/obsidian"], ["signal-desktop"], ["sh", "-c", "obsidian"]], procs=["obsidian"])
        self.assertEqual([g[1] for g in got], [True, False, False], "a wrapper never matches, and an app that is not running does not")

    def test_the_dock_only_asks_apps_without_windows(self):
        self.assertRegex(self.APPS, r"background: !run && inBackground\(e\)")

    def moves(self, pinned, id_, target, after):
        code = ("const root = { pinned: " + json.dumps(pinned) + " }; let saved = 0; const save = () => { saved++ };\n" +
                js_function(self.CONFIG, "moveTo") + "\n" +
                f"const r = moveTo({json.dumps(id_)}, {json.dumps(target)}, {json.dumps(after)});\n"
                "process.stdout.write(JSON.stringify({ r, pinned: root.pinned, saved }));")
        return self.node(code)

    def test_dragging_puts_an_icon_before_or_after_another_and_saves_once(self):
        abcd = ["a", "b", "c", "d"]
        self.assertEqual(self.moves(abcd, "d", "a", False), {"r": True, "pinned": ["d", "a", "b", "c"], "saved": 1})
        self.assertEqual(self.moves(abcd, "a", "c", True), {"r": True, "pinned": ["b", "c", "a", "d"], "saved": 1})
        self.assertEqual(self.moves(abcd, "b", "d", False), {"r": True, "pinned": ["a", "c", "b", "d"], "saved": 1})

    def test_dropping_where_it_already_is_or_on_nothing_changes_and_saves_nothing(self):
        abcd = ["a", "b", "c", "d"]
        for args in (("b", "a", True), ("a", "a", False), ("a", "b", False), ("zz", "a", False), ("a", "zz", False)):
            with self.subTest(args=args):
                self.assertEqual(self.moves(abcd, *args), {"r": False, "pinned": abcd, "saved": 0})


class HotCornersContracts(unittest.TestCase):
    QML = (KIT / "dock" / "HotCorners.qml").read_text()
    CONFIG = (KIT / "dock" / "Config.qml").read_text()
    TOOL = (KIT / "dock" / "hot-corners").read_text()

    def test_the_actions_the_qml_runs_the_config_accepts_and_the_tool_offers_are_the_same_list(self):
        run_cases = set(re.findall(r'case "(\w+)":', self.QML))
        config = set(re.findall(r'"(\w+)"', re.search(r"cornerActions: (\[[^\]]*\])", self.CONFIG).group(1)))
        tool = set(re.findall(r'"(\w+)"', re.search(r"ACTIONS = (\[[^\]]*\])", self.TOOL).group(1)))
        self.assertEqual(config - {"none"}, run_cases)
        self.assertEqual(tool, config)

    def test_the_corner_names_agree(self):
        config = set(re.findall(r'"(\w+)"', re.search(r"cornerNames: (\[[^\]]*\])", self.CONFIG).group(1)))
        tool = set(re.findall(r'"(\w+)": "none"', re.search(r"DEFAULT = (\{[^\}]*\})", self.TOOL).group(1)))
        self.assertEqual(config, tool)
        self.assertEqual(len(config), 4)

    def test_a_corner_that_is_off_has_no_surface_and_the_surface_has_a_layer_rule(self):
        self.assertIn('!== "none"', self.QML)
        self.assertIn('WlrLayershell.namespace: "machotcorner"', self.QML)
        self.assertIn("machotcorner", (KIT / "dock" / "macdock.lua").read_text())

    def test_it_is_instantiated_once_and_every_file_ships(self):
        self.assertEqual((KIT / "dock" / "shell.qml").read_text().count("HotCorners {}"), 1)
        self.assertIn("HotCorners.qml", (KIT / "dock" / "install-dock").read_text())
        self.assertRegex((KIT / "dock" / "qmldir").read_text(), r"HotCorners 1\.0 HotCorners\.qml")

    def test_one_trigger_per_visit_the_corner_latches_until_the_pointer_has_left(self):
        for needle in ("property bool latched", "spot.latched = true", "hyprctl", "cursorpos"):
            self.assertIn(needle, self.QML)


# ======================================================================================================================
# dock/Spotlight.qml
# ======================================================================================================================
class Spotlight(unittest.TestCase):
    QML = (KIT / "dock" / "Spotlight.qml").read_text()
    LUA = (KIT / "dock" / "macdock.lua").read_text()

    def node(self, names, expr):
        node = shutil.which("node")
        if not node:
            self.skipTest("node is not installed")
        code = "".join(js_function(self.QML, n) + "\n" for n in names) + f"process.stdout.write(JSON.stringify({expr}));"
        r = run([node, "-e", code])
        self.assertEqual(r.returncode, 0, r.stderr)
        return json.loads(r.stdout)

    def calc(self, *exprs):
        return self.node(["calc"], "[" + ", ".join(json.dumps(e) for e in exprs) + "].map(calc)")

    def test_a_sum_is_answered_with_the_usual_precedence(self):
        got = self.calc("12*7", "2+3*4", "(2+3)*4", "2^3^2", "-2^2", "2^-1", "10%3", "sqrt(16)+1", " 2 + 3 ", "=5*5", "5×5", "8÷2", "2026-10-23", "1.5e3+1", "-(2+3)")
        self.assertEqual(got, [84, 14, 20, 512, -4, 0.5, 1, 5, 5, 25, 25, 4, 1993, 1501, -5])

    def test_constants_and_functions(self):
        got = self.calc("pi*2", "e^1", "abs(-3)*2", "floor(2.7)+ceil(2.1)", "log(1000)+ln(1)")
        self.assertAlmostEqual(got[0], 6.283185307179586)
        self.assertAlmostEqual(got[1], 2.718281828459045)
        self.assertEqual(got[2:], [6, 5, 3])

    def test_anything_that_is_not_a_sum_is_not_answered(self):
        for text in ("1password", "7zip", "12", "obs", "", "2+", "(2", "2)", "1/0", "9^9^9", "alert(1)+2", "constructor(1)+1", "__proto__+1", "sqrt16+1", "2 3", "a+b", "1;2", "2*"):
            with self.subTest(text=text):
                self.assertEqual(self.calc(text), [None])

    def test_it_never_uses_eval(self):
        self.assertNotRegex(self.QML, r"\beval\s*\(|new Function|Function\s*\(")

    def test_names_are_matched_whole_then_by_start_then_by_word_then_anywhere(self):
        got = self.node(["matchScore"], '[["Obsidian","obsidian"],["Obsidian","obs"],["Brave Web Browser","browser"],["Files","il"],["x",""],["abc","z"],["60-kit-mac.conf","kit"]].map(a => matchScore(a[0], a[1]))')
        self.assertEqual(got, [100, 80, 60, 40, 1, 0, 60])

    def test_files_sort_by_name_match_then_by_how_close_to_home_they_are(self):
        got = self.node(["matchScore", "sortFiles"], 'sortFiles(["/h/a/x/notes.txt", "/h/a/notes/", "/h/a/deep/er/notes-old.md", "/h/a/old-notes.txt"], "notes").map(r => [r.path, r.dir])')
        self.assertEqual(got, [["/h/a/notes", True], ["/h/a/x/notes.txt", False], ["/h/a/deep/er/notes-old.md", False], ["/h/a/old-notes.txt", False]])

    def test_icons_follow_the_kind_of_file(self):
        got = self.node(["iconFor"], '[["/a/b", true], ["/a/p.PNG", false], ["/a/d.pdf", false], ["/a/noext", false], ["/a/x.tar.gz", false], ["/a/s.flac", false], ["/a/m.mkv", false]].map(a => iconFor(a[0], a[1]))')
        self.assertEqual(got, ["folder", "image-x-generic", "application-pdf", "text-x-generic", "package-x-generic", "audio-x-generic", "video-x-generic"])

    # ---- contracts
    def actions(self):
        block = self.QML[self.QML.index("readonly property var actions: ["):self.QML.index("property var clipboard:")]
        return re.findall(r"\{ title: \"([^\"]+)\"[^}]*?(?:cmd: (\[[^\]]*\])|ipc: (\[[^\]]*\])|view: \"(\w+)\")", block)

    def test_every_action_is_a_command_an_ipc_call_or_a_view_and_none_powers_off_directly(self):
        acts = self.actions()
        self.assertGreaterEqual(len(acts), 20)
        for title, cmd, ipc, view in acts:
            self.assertTrue(cmd or ipc or view, title)
            for word in ("shutdown", "poweroff", "reboot", "logout", "factory-reset", "suspend", "hibernate"):
                self.assertNotIn(word, (cmd or "").lower().replace("omarchy-menu\", \"toggle\", \"system", ""), f"{title}: a search result must never power the machine off or lose the session without a menu in between")
        self.assertIn("omarchy-menu", dict((t, c) for t, c, _, _ in acts)["Restart, Shut Down or Log Out…"])

    def test_the_commands_exist_in_this_omarchy(self):
        bin_dir = pathlib.Path("/usr/share/omarchy/bin")
        if not bin_dir.is_dir():
            self.skipTest("Omarchy is not installed here")
        for title, cmd, _, _ in self.actions():
            if not cmd:
                continue
            first = [w for w in re.findall(r'"([^"]+)"', cmd)][0]
            if first.startswith("omarchy-"):
                self.assertTrue((bin_dir / first).exists(), f"{title}: {first} is not an Omarchy command")

    def test_the_ipc_targets_the_actions_call_exist(self):
        for _, _, ipc, _ in self.actions():
            if ipc:
                target = re.findall(r'"([^"]+)"', ipc)[0]
                self.assertTrue(any(f'target: "{target}"' in p.read_text() for p in (KIT / "dock").glob("*.qml")), target)

    def test_it_takes_the_keyboard_only_while_open_and_is_not_mapped_while_closed(self):
        self.assertIn("visible: shown", self.QML)
        self.assertIn("keyboardFocus: shown ? WlrKeyboardFocus.Exclusive : WlrKeyboardFocus.None", self.QML)
        self.assertIn('WlrLayershell.namespace: "macspotlight"', self.QML)

    def test_the_files_view_only_searches_when_it_is_the_view_and_has_two_letters(self):
        self.assertRegex(self.QML, r'win\.mode !== "files" \|\| q\.length < 2')
        self.assertEqual(len(re.findall(r'finder\.running = true', self.QML)), 1)

    def test_it_is_registered_installed_and_bound(self):
        self.assertEqual((KIT / "dock" / "shell.qml").read_text().count("Spotlight {}"), 1)
        self.assertIn("Spotlight.qml", (KIT / "dock" / "install-dock").read_text())
        self.assertRegex((KIT / "dock" / "qmldir").read_text(), r"Spotlight 1\.0 Spotlight\.qml")
        self.assertIn('hl.unbind("SUPER + ALT + SPACE")', self.LUA)
        self.assertIn('o.bind("SUPER + ALT + SPACE", "Spotlight (⌘Space)", hl.dsp.global("macspotlight:toggle"))', self.LUA)
        self.assertIn('appid: "macspotlight"; name: "toggle"', self.QML)
        self.assertIn("macspotlight", self.LUA.split("hl.layer_rule", 1)[1].split("\n", 1)[0])

    def test_the_clipboard_view_pastes_through_omarchys_own_helper_and_never_writes_the_history(self):
        self.assertIn("omarchy-clipboard-paste-text", self.QML)
        self.assertEqual(len(re.findall(r"setText\(", self.QML)), 1, "the only file it writes is its own usage count")
        self.assertIn("usage.setText", self.QML)


# ======================================================================================================================
# menubar/plugin/apps.json: per-app menus
# ======================================================================================================================
def _load_keyd_config():
    import importlib.machinery, importlib.util
    loader = importlib.machinery.SourceFileLoader("keyd_config_for_menus", str(KIT / "keys" / "keyd-config"))
    mod = importlib.util.module_from_spec(importlib.util.spec_from_loader(loader.name, loader))
    loader.exec_module(mod)
    return mod


class AppMenus(unittest.TestCase):
    DATA = json.loads((KIT / "menubar" / "plugin" / "apps.json").read_text())
    WIDGET = (KIT / "menubar" / "plugin" / "BarWidget.qml").read_text()
    LUA = (KIT / "menubar" / "macmenu.lua").read_text()

    def items(self):
        """(profile id, item) for every item of every custom menu."""
        for p in self.DATA["profiles"]:
            for m in p["menus"]:
                if isinstance(m, dict):
                    for it in m["items"]:
                        yield p["id"], it

    def test_the_file_is_well_formed(self):
        self.assertEqual(self.DATA["version"], 1)
        ids = [p["id"] for p in self.DATA["profiles"]]
        self.assertEqual(len(ids), len(set(ids)), "profile ids are unique")
        self.assertGreaterEqual(len(ids), 5)
        for p in self.DATA["profiles"]:
            re.compile(p["match"])
            for m in p["menus"]:
                if isinstance(m, str):
                    self.assertIn(m, ("file", "edit", "view", "window", "help"), p["id"])
                else:
                    self.assertTrue(m["title"].strip() and m["items"], p["id"])
            self.assertIn("window", p["menus"], f"{p['id']}: every app keeps the Window menu")
            self.assertIn("help", p["menus"])

    def test_every_item_is_a_separator_a_chord_or_a_known_action_and_never_a_command(self):
        lua_ids = set(re.findall(r'\["([a-z]+\.[a-z0-9]+)"\]\s*=', self.LUA))
        for pid, it in self.items():
            with self.subTest(profile=pid, item=it.get("label", "separator")):
                if it.get("sep"):
                    self.assertEqual(set(it), {"sep"})
                    continue
                self.assertTrue(it["label"].strip())
                self.assertEqual(sum(k in it for k in ("send", "id")), 1, "a chord or an action, not both and not neither")
                if "send" in it:
                    self.assertRegex(it["send"], r"^[A-Za-z0-9_]+(\+[A-Za-z0-9_]+)*$")
                    mods = it["send"].split("+")[:-1]
                    self.assertTrue(set(mods) <= {"ctrl", "shift", "alt"} and len(mods) == len(set(mods)), it["send"])
                else:
                    self.assertIn(it["id"], lua_ids, "macmenu.lua has no such action")
                self.assertLessEqual(set(it) - {"label", "send", "id", "keys", "ctl"}, set())

    def test_no_menu_has_two_items_with_the_same_label(self):
        for p in self.DATA["profiles"]:
            for m in p["menus"]:
                if isinstance(m, dict):
                    labels = [i["label"] for i in m["items"] if "label" in i]
                    self.assertEqual(len(labels), len(set(labels)), f"{p['id']} / {m['title']}")

    # ---- the displayed shortcut must be what pressing it does on this keyboard (with the keyd layer)
    GLYPH_KEY = {"←": "left", "→": "right", "↑": "up", "↓": "down", "⇥": "tab", "⌦": "delete", "⌫": "backspace", "⇞": "pageup", "⇟": "pagedown",
                 "+": "equal", "−": "minus", "[": "leftbrace", "]": "rightbrace", ".": "dot", ",": "comma", "`": "grave"}
    XKB_KEY = {"left": "left", "right": "right", "up": "up", "down": "down", "tab": "tab", "delete": "delete", "page_up": "pageup", "page_down": "pagedown",
               "home": "home", "equal": "equal", "minus": "minus", "bracketleft": "leftbrace", "bracketright": "rightbrace", "period": "dot", "comma": "comma"}

    @staticmethod
    def parse_action(action):
        """keyd's 'C-S-tab' as (frozenset of modifiers, key); None for anything that is not a plain chord."""
        m = re.fullmatch(r"((?:[CASM]-)*)([a-z0-9]+)", action)
        return (frozenset(m.group(1).replace("-", "")), m.group(2)) if m else None

    def pressed(self, glyphs, ctl, terminal):
        """What the keyd layer sends when `glyphs` (for example ⇧⌘N) is pressed, as keyd-config's tables say."""
        kc = _load_keyd_config()
        mods = {g for g in glyphs if g in "⌃⌥⇧⌘"}
        rest = "".join(g for g in glyphs if g not in "⌃⌥⇧⌘")
        key = self.GLYPH_KEY.get(rest) or (rest.lower() if not re.fullmatch(r"F\d+", rest) else rest.lower())
        if "⌃" in mods and not ctl:
            self.fail(f"{glyphs}: a Control chord must be marked ctl")
        tables = {frozenset("⌘"): kc.CMD_KEYS, frozenset("⌘⇧"): kc.SHIFT_CMD_KEYS, frozenset("⌘⌥"): kc.ALT_CMD_KEYS, frozenset("⌃"): kc.CONTROL_KEYS,
                  frozenset("⌃⇧"): kc.CONTROL_SHIFT_KEYS, frozenset("⌥"): kc.OPTION_KEYS}
        if mods == {"⌘"}:   # the focus-dependent overlay that keyd-appmap applies: terminal-safe keys in a terminal, plain Ctrl+C and Ctrl+V in an app
            for b in kc.OVERLAYS["terminal" if terminal else "app"]:
                m = re.fullmatch(r"cmd\.(\w+) = ([\w-]+)", b)
                if m and m.group(1) == key:
                    return self.parse_action(m.group(2))
        for k, action, _ in tables.get(frozenset(mods), []):
            if k == key:
                return self.parse_action(action)
        base = {"⌘": "C", "⌃": "C", "⌥": "A", "⇧": "S"}
        # an unlisted key keeps its modifiers, with ⌘ becoming Ctrl
        letters = set()
        for g in mods:
            letters.add(base[g])
        return (frozenset(letters), key)

    def sent(self, spec):
        *mods, key = spec.split("+")
        key = key.lower()
        return (frozenset({"ctrl": "C", "alt": "A", "shift": "S"}[m] for m in mods), self.XKB_KEY.get(key, key))

    def test_every_shortcut_shown_is_what_pressing_it_sends_on_this_keyboard(self):
        checked = 0
        for pid, it in self.items():
            if it.get("sep") or "send" not in it or not it.get("keys"):
                continue
            with self.subTest(profile=pid, item=it["label"], keys=it["keys"]):
                self.assertEqual(self.pressed(it["keys"], bool(it.get("ctl")), pid == "terminal"), self.sent(it["send"]),
                                 f"pressing {it['keys']} does not send {it['send']} through the keyd layer")
                checked += 1
        self.assertGreater(checked, 60, "the check must really run over the shortcuts")

    def test_the_chords_the_keyd_layer_cannot_press_have_no_shortcut_shown(self):
        # Ctrl+Alt+arrows is the window-focus chord on this keyboard, and Ctrl+H, Ctrl+Shift+O and Alt+Home have no Mac key that sends them in these apps:
        # no hint is better than one that does something else
        unreachable = {("obsidian", "ctrl+alt+Left"), ("obsidian", "ctrl+alt+Right"), ("browser", "ctrl+h"), ("browser", "ctrl+shift+o"), ("files", "alt+Home")}
        seen = set()
        for pid, it in self.items():
            if (pid, it.get("send")) in unreachable:
                seen.add((pid, it["send"]))
                self.assertFalse(it.get("keys"), f"{pid}: {it['label']}")
        self.assertEqual(seen, unreachable)

    # ---- which profile an app gets, and the widget's own functions, run in node
    def node(self, body):
        node = shutil.which("node")
        if not node:
            self.skipTest("node is not installed")
        titles = re.search(r"readonly property var builtinTitles: (\(\{.*?\}\))", self.WIDGET, re.S).group(1)
        code = (f"const profiles = {json.dumps(self.DATA['profiles'])}; const builtinTitles = {titles};\n" +
                "".join(js_function(self.WIDGET, n) + "\n" for n in ("findProfile", "buildMenus", "customItems")) +
                f"process.stdout.write(JSON.stringify({body}));")
        r = run([node, "-e", code])
        self.assertEqual(r.returncode, 0, r.stderr)
        return json.loads(r.stdout)

    def test_each_app_gets_its_own_profile_and_others_get_none(self):
        ids = ["brave-browser", "brave-web.whatsapp.com__-Default", "brave-app.hey.com__-Default", "org.gnome.Nautilus", "foot", "obsidian",
               "org.telegram.desktop", "signal", "Alacritty", "", "organization.gnome.nautilus", "brave-extra"]
        got = self.node(f"{json.dumps(ids)}.map(i => {{ const p = findProfile(i); return p ? p.id : null }})")
        self.assertEqual(got, ["browser", "webapp", "webapp", "files", "terminal", "obsidian", None, None, "terminal", None, None, None])

    def test_the_menu_titles_follow_the_profile_and_default_to_the_generic_five(self):
        titles = self.node('[null, ...profiles.map(p => p)].map(p => buildMenus(p).map(m => m.title))')
        self.assertEqual(titles[0], ["File", "Edit", "View", "Window", "Help"])
        by = {p["id"]: t for p, t in zip(self.DATA["profiles"], titles[1:])}
        self.assertEqual(by["browser"], ["File", "Edit", "View", "History", "Bookmarks", "Tab", "Window", "Help"])
        self.assertEqual(by["files"], ["File", "Edit", "View", "Go", "Window", "Help"])
        self.assertEqual(by["terminal"], ["Shell", "Edit", "View", "Window", "Help"])

    def test_names_are_unique_within_a_bar(self):
        names = self.node("profiles.map(p => buildMenus(p).map(m => m.name))")
        for n in names:
            self.assertEqual(len(n), len(set(n)))

    def test_a_menu_file_can_name_a_chord_or_an_action_never_a_command(self):
        items = [{"label": "A", "send": "ctrl+n", "keys": "⌘N"}, {"label": "B", "send": "a;b"}, {"label": "C", "id": "file.close"}, {"label": "D", "id": "File.close"},
                 {"sep": True}, {"label": 5, "send": "ctrl+n"}, None, {"label": "E", "send": "ctrl+n\"); os.execute(\"x"}, {"label": "F"}, {"label": "G", "id": "a.b; rm"}]
        got = self.node(f"customItems({json.dumps(items)})")
        self.assertEqual([i.get("label", "-") for i in got], ["A", "C", "-"])
        self.assertEqual(got[0], {"label": "A", "keys": "⌘N", "send": "ctrl+n"})

    def test_the_widget_has_no_fixed_titles_left_and_closes_a_menu_the_app_no_longer_has(self):
        self.assertNotRegex(self.WIDGET, r'Title \{ name: "(file|edit|view|window|help)"')
        self.assertIn("model: root.menus", self.WIDGET)
        self.assertIn("onMenusChanged", self.WIDGET)
        self.assertIn('o.mac_chord(', self.WIDGET)

    def test_the_installer_ships_the_file_next_to_the_widget(self):
        self.assertIn("plugin/apps.json", (KIT / "menubar" / "install-menubar").read_text())


class ChordParser(unittest.TestCase):
    """macmenu.lua's parse_chord, run for real in Lua with stand-ins for Hyprland's functions."""
    def parse(self, specs):
        lua = shutil.which("lua5.4") or shutil.which("lua")
        if not lua:
            self.skipTest("lua is not installed")
        driver = ("o = { launch_webapp = function(u) return u end }\nhl = {}\n"
                  f"dofile({json.dumps(str(KIT / 'menubar' / 'macmenu.lua'))})\n"
                  "local out = {}\n"
                  f"for _, s in ipairs({{ {', '.join(json.dumps(s) for s in specs)} }}) do\n"
                  "  local mods, key = o.mac_parse_chord(s)\n"
                  "  out[#out + 1] = mods and (mods .. '|' .. key) or 'nil'\n"
                  "end\nprint(table.concat(out, ';'))\n")
        r = run([lua, "-e", driver])
        self.assertEqual(r.returncode, 0, r.stderr)
        return r.stdout.strip().split(";")

    def test_good_chords(self):
        self.assertEqual(self.parse(["ctrl+n", "ctrl+shift+n", "alt+Left", "F11", "ctrl+alt+Left", "shift+Page_Up", "ctrl+equal", "ctrl+0", "Delete"]),
                         ["CTRL|N", "CTRL SHIFT|N", "ALT|Left", "|F11", "CTRL ALT|Left", "SHIFT|Page_Up", "CTRL|equal", "CTRL|0", "|Delete"])

    def test_anything_odd_is_refused(self):
        bad = ["", "+", "ctrl+", "+n", "ctrl++n", "super+q", "ctrl+ctrl+n", "meta+n", "ctrl+n;rm", "ctrl+n\"", "ctrl n", "ctrl+n)", "alt+shift+"]
        self.assertEqual(self.parse(bad), ["nil"] * len(bad))


class ControlCenter(unittest.TestCase):
    QML = (KIT / "dock" / "ControlCenter.qml").read_text()
    BUTTON = (KIT / "menubar" / "plugin-controlcenter" / "BarWidget.qml").read_text()
    MANIFEST = json.loads((KIT / "menubar" / "plugin-controlcenter" / "manifest.json").read_text())

    def test_nothing_is_built_while_it_is_closed(self):
        self.assertIn("active: win.shown", self.QML)
        self.assertIn("visible: shown", self.QML)
        self.assertIn("keyboardFocus: shown ? WlrKeyboardFocus.Exclusive : WlrKeyboardFocus.None", self.QML)

    def test_it_uses_the_services_omarchys_own_panels_use(self):
        for name in ("Quickshell.Networking", "Quickshell.Bluetooth", "Quickshell.Services.Pipewire", "Quickshell.Services.Mpris", "Quickshell.Services.UPower"):
            self.assertIn(f"import {name}", self.QML)
        self.assertIn("Networking.wifiEnabled", self.QML)
        self.assertIn("PwObjectTracker", self.QML)

    def test_the_commands_it_runs_are_omarchys_or_the_systems_and_none_powers_off(self):
        cmds = re.findall(r'run\(\[([^\]]*)\]\)', self.QML) + re.findall(r'"(omarchy-[a-z-]+)"', self.QML)
        self.assertTrue(cmds)
        for word in ("shutdown", "reboot", "poweroff", "logout", "suspend"):
            self.assertNotIn(word, self.QML.lower().replace("do not disturb", ""), "Control Center must not be able to end the session")
        bin_dir = pathlib.Path("/usr/share/omarchy/bin")
        if bin_dir.is_dir():
            for name in set(re.findall(r'"(omarchy-[a-z-]+)"', self.QML)):
                self.assertTrue((bin_dir / name).exists(), f"{name} is not an Omarchy command")

    def test_every_icon_it_names_exists_in_the_icon_theme_or_has_a_fallback(self):
        names = set(re.findall(r'"([a-z-]+-symbolic)"', self.QML))
        self.assertGreaterEqual(len(names), 10)
        theme = pathlib.Path.home() / ".local" / "share" / "icons" / "WhiteSur-dark"
        if not theme.is_dir():
            self.skipTest("the WhiteSur icon theme is not installed")
        for n in names:
            self.assertTrue(list(theme.rglob(n + ".svg")), f"{n} is not in WhiteSur")

    def test_the_button_only_asks_the_dock_program_to_toggle_the_panel(self):
        self.assertIn('"controlcenter", "toggle"', self.BUTTON)
        self.assertIn('target: "controlcenter"', self.QML)
        self.assertEqual(self.MANIFEST["id"], "omarchykit.controlcenter")
        self.assertIn('moduleName: "omarchykit.controlcenter"', self.BUTTON)
        self.assertIn("bar-widget", self.MANIFEST["kinds"])

    def test_it_is_registered_installed_and_has_a_layer_rule(self):
        self.assertEqual((KIT / "dock" / "shell.qml").read_text().count("ControlCenter {}"), 1)
        self.assertIn("ControlCenter.qml", (KIT / "dock" / "install-dock").read_text())
        self.assertRegex((KIT / "dock" / "qmldir").read_text(), r"ControlCenter 1\.0 ControlCenter\.qml")
        self.assertIn("maccontrol", (KIT / "dock" / "macdock.lua").read_text().split("hl.layer_rule", 1)[1].split("\n", 1)[0])
        installer = (KIT / "menubar" / "install-menubar").read_text()
        for needle in ("plugin-controlcenter/manifest.json", "plugin-controlcenter/BarWidget.qml", "CC_ID=omarchykit.controlcenter"):
            self.assertIn(needle, installer)

    def test_the_power_mode_cycle_only_offers_the_three_profiles_the_system_has(self):
        self.assertIn('readonly property var profiles: ["power-saver", "balanced", "performance"]', self.QML)


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
            shown = {"tab": "Tab", "grave": "`", "right": "Right", "left": "Left", "escape": "Escape", "up": "Up", "down": "Down", "space": "Space"}.get(key, key.upper())
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
        files = [str(p) for p in sorted((KIT / "dock").glob("*.qml")) + sorted((KIT / "menubar" / "plugin").glob("*.qml")) + sorted((KIT / "menubar" / "plugin-controlcenter").glob("*.qml"))]
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
        for pattern in ("icons/*", "dock/*", "menubar/*", "menubar/plugin/*", "menubar/plugin-controlcenter/*"):
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
