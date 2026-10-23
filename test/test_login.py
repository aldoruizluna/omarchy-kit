"""login/: the login screen that lists the accounts and the auto-login that is really off (2026-10-23).

Hermetic: the installer runs against a scratch tree through its LOGIN_KIT_* hooks, as a normal user, and the real /etc is never read or written.
The theme itself was also loaded in the real SDDM greeter (sddm-greeter-qt6 --test-mode); that is recorded in the Setup log, not repeated here.
"""
import importlib.util, os, pathlib, re, shutil, subprocess, sys, tempfile, unittest

KIT = pathlib.Path(__file__).resolve().parent.parent
LOGIN = KIT / "login"
INSTALLER = LOGIN / "install-login"
PICTURES = ["logo.png", "lock.png", "lock-failed.png", "entry.png", "entry-failed.png", "bullet.png"]

_spec = importlib.util.spec_from_file_location("sddm_conf", LOGIN / "sddm_conf.py")
SC = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(SC)


def run(args, env=None, **kw):
    return subprocess.run(args, capture_output=True, text=True, env=env, **kw)


class Tree(unittest.TestCase):
    """A scratch root with Omarchy's theme, an autologin file that was only renamed, and the hooks that point the installer at it."""

    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.root = self.tmp / "root"
        self.conf = self.root / "etc/sddm.conf.d"
        self.themes = self.root / "usr/share/sddm/themes"
        self.state = self.root / "etc/omarchy-kit/sddm-disabled"
        self.conf.mkdir(parents=True)
        (self.themes / "omarchy").mkdir(parents=True)
        for p in PICTURES:
            (self.themes / "omarchy" / p).write_bytes(b"\x89PNG " + p.encode())
        (self.conf / "10-theme.conf").write_text("[Theme]\nCurrent=omarchy\n")
        (self.conf / "99-omarchy-login.conf").write_text("[Theme]\nCurrent=omarchy\n\n[Users]\nRememberLastUser=true\n")
        (self.conf / "autologin.conf.disabled").write_text("[Autologin]\nUser=someone\nSession=omarchy.desktop\n")
        self.env = {**os.environ, "LOGIN_KIT_ROOT": str(self.root), "LOGIN_KIT_CONF_DIR": str(self.conf), "LOGIN_KIT_THEMES": str(self.themes),
                    "LOGIN_KIT_STATE": str(self.state), "LOGIN_KIT_TEST": "1"}

    def go(self, *args, env=None):
        return run([str(INSTALLER), *args], env=env or self.env)

    def effective(self, section, key):
        return SC.effective(str(self.root)).get((section, key), "")


class ConfigReader(Tree):
    def test_a_renamed_file_still_counts_because_sddm_reads_every_file(self):
        self.assertEqual(self.effective("Autologin", "User"), "someone", "autologin.conf.disabled still turns auto-login on")
        self.assertEqual([pathlib.Path(p).name for p in SC.autologin_files(str(self.root))], ["autologin.conf.disabled"])

    def test_later_files_win_and_an_empty_user_switches_it_off(self):
        (self.conf / "zz-last.conf").write_text("[Autologin]\nUser=\n")
        self.assertEqual(self.effective("Autologin", "User"), "")
        self.assertEqual(self.effective("Theme", "Current"), "omarchy")

    def test_the_vendor_defaults_come_first_and_sddm_conf_last(self):
        vendor = self.root / "usr/lib/sddm/sddm.conf.d"
        vendor.mkdir(parents=True)
        (vendor / "default.conf").write_text("[Theme]\nCurrent=vendor\n[Autologin]\nUser=\n")
        self.assertEqual(self.effective("Theme", "Current"), "omarchy", "/etc/sddm.conf.d beats the vendor defaults")
        (self.root / "etc/sddm.conf").write_text("[Theme]\nCurrent=main\n")
        self.assertEqual(self.effective("Theme", "Current"), "main", "/etc/sddm.conf is read last")

    def test_comments_sections_and_spaces(self):
        got = SC.parse("# c\n; c\n[Autologin]\n  User = x \nSession=\n[Theme]\nCurrent=t\n")
        self.assertEqual(got, {("Autologin", "User"): "x", ("Autologin", "Session"): "", ("Theme", "Current"): "t"})

    def test_the_command_line(self):
        ok = run([sys.executable, "-I", str(LOGIN / "sddm_conf.py"), "get", "Autologin", "User", "--root", str(self.root)])
        self.assertEqual((ok.returncode, ok.stdout.strip()), (0, "someone"))
        listed = run([sys.executable, "-I", str(LOGIN / "sddm_conf.py"), "autologin-files", "--root", str(self.root)])
        self.assertEqual(listed.stdout.split(), [str(self.conf / "autologin.conf.disabled")])
        for bad in ([], ["get", "A"], ["nope"], ["get", "A", "B", "--root"]):
            self.assertEqual(run([sys.executable, "-I", str(LOGIN / "sddm_conf.py"), *bad]).returncode, 2, bad)


class Installer(Tree):
    def test_unknown_options_exit_2_and_install_nothing_and_help_prints_the_header(self):
        for bad in (["--bogus"], ["--stage"], ["--remove", "--bogus"], ["x"]):
            with self.subTest(args=bad):
                r = self.go(*bad)
                self.assertEqual(r.returncode, 2, r.stderr)
        self.assertFalse((self.themes / "omarchy-kit-login").exists())
        h = self.go("--help")
        self.assertEqual(h.returncode, 0)
        self.assertIn("Usage: sudo install-login", h.stdout)
        self.assertIn("Ctrl+Alt+F2", h.stdout, "the way back is in the help")

    def test_it_needs_root_unless_previewing_or_staging(self):
        env = {k: v for k, v in self.env.items() if k != "LOGIN_KIT_TEST"}
        if os.geteuid() == 0:
            self.skipTest("running as root")
        r = self.go(env=env)
        self.assertEqual(r.returncode, 1)
        self.assertIn("needs root", r.stderr)
        self.assertTrue((self.conf / "autologin.conf.disabled").exists(), "nothing was touched")
        self.assertEqual(self.go("--dry-run", env=env).returncode, 0)

    def test_dry_run_changes_nothing(self):
        before = sorted(p.name for p in self.conf.iterdir())
        r = self.go("--dry-run")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("dry run", r.stdout)
        self.assertEqual(sorted(p.name for p in self.conf.iterdir()), before)
        self.assertFalse(self.state.exists())
        self.assertFalse((self.themes / "omarchy-kit-login").exists())

    def test_install_turns_auto_login_really_off_and_installs_the_theme(self):
        r = self.go()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self.effective("Autologin", "User"), "", "read the way SDDM reads it")
        self.assertEqual(SC.autologin_files(str(self.root)), [])
        self.assertEqual(self.effective("Theme", "Current"), "omarchy-kit-login")
        self.assertEqual(self.effective("Users", "RememberLastUser"), "true")
        self.assertFalse((self.conf / "autologin.conf.disabled").exists(), "moved out of the folder SDDM reads")
        self.assertEqual((self.state / "autologin.conf.disabled").read_text(), "[Autologin]\nUser=someone\nSession=omarchy.desktop\n", "kept as it was")
        self.assertEqual((self.state / "LIST").read_text().split(), ["autologin.conf.disabled"])
        theme = self.themes / "omarchy-kit-login"
        self.assertEqual(sorted(p.name for p in theme.iterdir()), sorted(["Main.qml", "metadata.desktop", "theme.conf", *PICTURES]))
        self.assertEqual((theme / "logo.png").read_bytes(), (self.themes / "omarchy/logo.png").read_bytes(), "Omarchy's own pictures, copied")
        self.assertEqual(oct((self.conf / "zz-omarchy-kit-login.conf").stat().st_mode & 0o777), "0o644")
        self.assertIn("never", (INSTALLER.read_text()), "the installer documents that it does not restart SDDM")

    def test_installing_twice_is_the_same_and_a_third_file_is_found_too(self):
        self.assertEqual(self.go().returncode, 0)
        snap = {p.name: p.read_bytes() for p in self.conf.iterdir()}
        r = self.go()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("no file in", r.stdout)
        self.assertEqual({p.name: p.read_bytes() for p in self.conf.iterdir()}, snap)
        (self.conf / "autologin.conf").write_text("[Autologin]\nUser=other\n")
        self.assertEqual(self.go().returncode, 0)
        self.assertEqual(self.effective("Autologin", "User"), "")
        self.assertEqual(sorted((self.state / "LIST").read_text().split()), ["autologin.conf", "autologin.conf.disabled"])

    def test_it_does_not_move_files_that_set_no_auto_login_user(self):
        self.assertEqual(self.go().returncode, 0)
        for name in ("10-theme.conf", "99-omarchy-login.conf"):
            self.assertTrue((self.conf / name).exists(), name)

    def test_remove_puts_everything_back(self):
        before = {p.name: p.read_bytes() for p in self.conf.iterdir()}
        self.assertEqual(self.go().returncode, 0)
        r = self.go("--remove")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual({p.name: p.read_bytes() for p in self.conf.iterdir()}, before, "the folder is exactly as it was")
        self.assertFalse((self.themes / "omarchy-kit-login").exists())
        self.assertFalse(self.state.exists())
        self.assertEqual(self.go("--remove").returncode, 0, "twice is fine")

    def test_remove_never_overwrites_a_file_that_is_back_already(self):
        self.assertEqual(self.go().returncode, 0)
        (self.conf / "autologin.conf.disabled").write_text("[Autologin]\nUser=\n")
        r = self.go("--remove")
        self.assertEqual(r.returncode, 0)
        self.assertEqual((self.conf / "autologin.conf.disabled").read_text(), "[Autologin]\nUser=\n")
        self.assertIn("left", r.stderr)

    def test_remove_leaves_a_theme_it_did_not_make_alone(self):
        stranger = self.themes / "omarchy-kit-login"
        stranger.mkdir()
        (stranger / "metadata.desktop").write_text("[SddmGreeterTheme]\nAuthor=Someone Else\n")
        self.assertEqual(self.go("--remove").returncode, 0)
        self.assertTrue(stranger.exists())

    def test_a_missing_picture_stops_it_before_anything_changes(self):
        (self.themes / "omarchy/entry.png").unlink()
        before = sorted(p.name for p in self.conf.iterdir())
        r = self.go()
        self.assertEqual(r.returncode, 1)
        self.assertIn("entry.png", r.stderr)
        self.assertEqual(sorted(p.name for p in self.conf.iterdir()), before)
        self.assertFalse(self.state.exists())

    def test_it_refuses_to_overwrite_a_file_it_kept_before(self):
        self.state.mkdir(parents=True)
        (self.state / "autologin.conf.disabled").write_text("old")
        r = self.go()
        self.assertEqual(r.returncode, 1)
        self.assertIn("refusing", r.stderr)
        self.assertTrue((self.conf / "autologin.conf.disabled").exists())
        self.assertFalse((self.conf / "zz-omarchy-kit-login.conf").exists())

    def test_no_autologin_file_at_all_still_installs_the_picker(self):
        (self.conf / "autologin.conf.disabled").unlink()
        r = self.go()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.effective("Theme", "Current"), "omarchy-kit-login")
        self.assertFalse(self.state.exists())

    def test_vendor_files_outside_etc_are_never_moved(self):
        vendor = self.root / "usr/lib/sddm/sddm.conf.d"
        vendor.mkdir(parents=True)
        (vendor / "default.conf").write_text("[Autologin]\nUser=vendorwide\n")
        r = self.go()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue((vendor / "default.conf").exists(), "a package's file stays where the package put it")
        self.assertEqual(self.effective("Autologin", "User"), "", "the empty user in zz-... still wins over it")

    def test_it_undoes_itself_if_auto_login_would_still_be_on(self):
        # a file in a folder the installer does not manage still sets a user and is read AFTER the drop-in
        (self.root / "etc/sddm.conf").write_text("[Autologin]\nUser=sneaky\n")
        r = self.go()
        self.assertEqual(r.returncode, 1)
        self.assertIn("undoing", r.stderr)
        self.assertTrue((self.conf / "autologin.conf.disabled").exists(), "put back")
        self.assertFalse((self.conf / "zz-omarchy-kit-login.conf").exists())
        self.assertFalse((self.themes / "omarchy-kit-login").exists())

    def test_stage_assembles_the_theme_without_root_for_a_try_in_the_real_greeter(self):
        out = self.tmp / "staged"
        env = {k: v for k, v in self.env.items() if k != "LOGIN_KIT_TEST"}
        r = self.go("--stage", str(out), env=env)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(sorted(p.name for p in out.iterdir()), sorted(["Main.qml", "metadata.desktop", "theme.conf", *PICTURES]))
        self.assertIn("--test-mode", r.stdout)


class Theme(unittest.TestCase):
    QML = (LOGIN / "theme" / "Main.qml").read_text()

    def test_every_picture_the_theme_uses_is_one_the_installer_copies(self):
        used = set(re.findall(r'"([\w-]+\.png)"', self.QML))
        self.assertEqual(used, set(PICTURES))

    def test_it_lists_every_account_and_logs_in_the_chosen_one(self):
        self.assertIn("model: userModel", self.QML)
        self.assertIn("sddm.login(root.currentUser, password.text, root.sessionIndex)", self.QML)
        for key in ("Qt.Key_Left", "Qt.Key_Right", "Qt.Key_Tab", "Qt.Key_Backtab"):
            self.assertIn(key, self.QML)
        self.assertIn("onClicked: root.selectUser(index)", self.QML)
        self.assertIn("userModel.lastIndex", self.QML, "the last user is chosen first")

    def test_no_account_name_or_home_is_written_in_the_theme(self):
        import getpass, pwd
        names = {p.pw_name for p in pwd.getpwall() if 1000 <= p.pw_uid < 60000} | {getpass.getuser()}
        for name in names:
            if len(name) > 3:
                self.assertNotIn(name, self.QML + (LOGIN / "install-login").read_text() + (LOGIN / "README.md").read_text())
        self.assertNotIn("/home/", self.QML)

    def test_the_metadata_names_the_theme_the_dropin_selects_and_the_installer_can_recognise(self):
        meta = (LOGIN / "theme" / "metadata.desktop").read_text()
        self.assertIn("Author=Omarchy Kit\n", meta, "remove only deletes a theme that carries this line")
        self.assertIn("MainScript=Main.qml", meta)
        self.assertIn("QtVersion=6", meta)
        self.assertIn("NAME=omarchy-kit-login", (LOGIN / "install-login").read_text())

    def test_no_picture_is_shipped_in_the_repository(self):
        self.assertEqual(sorted(p.name for p in (LOGIN / "theme").iterdir()), ["Main.qml", "metadata.desktop", "theme.conf"],
                         "Omarchy's pictures are copied at install time; none is committed (original art only)")


if __name__ == "__main__":
    unittest.main()
