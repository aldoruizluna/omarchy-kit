"""Tests for coadmin/: adding a second administrator with a mirror of this account's settings. Standard library only, no real root, nothing real is touched.

  python3 -B test/test_coadmin.py            # or: test/run-all --fast

The installer runs as fake root in a private user+mount namespace (`unshare -Urm`), with fakes for useradd, getent, id, passwd, chage, userdel and chown, and
wrappers that drop the owner options of rsync and install (the namespace cannot chown to a user that does not exist). A fixture home holds both settings that
must be mirrored and things that must never be copied: keys, tokens, browser and chat data, history, the assistants' folders, and the no-lock-before-hibernate override.

What is covered:
  refusals     not root, unknown option, a bad or existing user name, the same account, --remove of an account this script did not create
  --dry-run    prints the plan, creates nothing
  the account  useradd gets the same supplementary groups and the full name, the home is mode 700, no password is ever handled without a terminal
  the mirror   every allowlisted setting arrives; nothing on the denylist does; the home path is rewritten; enablement links follow the new home
  first login  the helper installed for the new user, and what it runs (against fakes)
"""
import os, pathlib, re, shutil, subprocess, sys, tempfile, textwrap, unittest

sys.dont_write_bytecode = True

KIT = pathlib.Path(__file__).resolve().parent.parent
INSTALLER = KIT / "coadmin" / "install-coadmin"
FIRST_LOGIN = KIT / "coadmin" / "first-login"
SAFE_PATH = "/usr/bin:/bin"
NEWUSER = "newadmin"
NEWNAME = "New Admin"


def run(cmd, env=None, timeout=60, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env=env, **kw)


def userns_ok():
    if os.geteuid() == 0:
        return False
    try:
        return run(["unshare", "-Urm", "true"], timeout=10).returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


USERNS = userns_ok()


def write_exec(path, body):
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("#!/bin/bash\n" + textwrap.dedent(body))
    path.chmod(0o755)


class Fixture(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="kit-test-")
        self.addCleanup(self._tmp.cleanup)
        self.tmp = pathlib.Path(self._tmp.name)
        self.base = self.tmp / "home"                      # stands in for /home
        self.src = self.base / "owner"
        self.kit = self.tmp / "kit"
        shutil.copytree(KIT / "coadmin", self.kit / "coadmin")
        self.build_source_home()
        self.fb = self.tmp / "fb"
        self.log = self.tmp / "calls.log"
        self.db = self.tmp / "db"
        self.db.mkdir()
        (self.db / "passwd").write_text(f"owner:x:1000:1000:Owner:{self.src}:/bin/bash\n")
        (self.db / "group").write_text("owner:x:1000:\nwheel:x:998:owner\nvideo:x:985:\n")
        self.fakes()

    # ---- the account being mirrored: what is allowed, what must never travel
    def put(self, rel, text="x\n", link=None):
        p = self.src / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        if link:
            p.symlink_to(link)
        else:
            p.write_text(text)

    def build_source_home(self):
        src = str(self.src)
        # settings that are mirrored
        self.put(".config/hypr/hyprland.lua", 'require("hypr.gpu")\n')
        self.put(".config/hypr/gpu.lua", f'-- keeps Hyprland off the hot GPU; documented at {src}/labspace\n')
        self.put(".config/hypr/input.lua.bak-2026", "old\n")
        self.put(".config/omarchy/shell.json", "{}\n")
        self.put(".config/omarchy/themes/golden-gate/colors.toml", 'mode = "light"\n')
        self.put(".config/omarchy/hooks/theme-set.d/50-mac-icons", "#!/bin/bash\n")
        self.put(".config/omarchy/defaults/agent", "claude\n")
        self.put(".config/macdock/dock.json", "{}\n")
        self.put(".config/fontconfig/conf.d/60-kit-mac-ui-font.conf", "<fontconfig/>\n")
        self.put(".config/pipewire/omarchy-speaker-tuning.conf", "eq\n")
        self.put(".config/fcitx5/profile", "us-mac\n")
        self.put(".config/mimeapps.list", "[Default Applications]\n")
        self.put(".config/user-dirs.dirs", 'XDG_DOWNLOAD_DIR="$HOME/Downloads"\n')
        self.put(".local/share/macdock/shell.qml", "ShellRoot {}\n")
        self.put(".local/share/icons/WhiteSur-dark/index.theme", "[Icon Theme]\n")
        self.put(".local/share/applications/WhatsApp.desktop", "[Desktop Entry]\nName=WhatsApp\n")
        self.put(".local/share/applications/claude-code-url-handler.desktop", f"Exec={src}/bin/claude\n")
        self.put(".local/share/applications/es-de.desktop", f"Exec={src}/Games/es-de\n")
        self.put(".local/share/applications/discord-455712169795780630.desktop", "x\n")
        self.put(".local/state/omarchy/current/theme.name", "mecha-unit\n")
        # user services
        u = ".config/systemd/user"
        for unit in ("omarchy-kit.service", "power-auto.service", "voxtype.service"):
            self.put(f"{u}/{unit}", f"[Service]\nExecStart={src}/labspace/omarchy-kit/{unit}\n")
        self.put(f"{u}/omarchy-sleep-lock.service.d/10-hibernate-no-lock.conf", f"[Service]\nEnvironment=OMARCHY_PATH={src}/x\n")
        self.put(f"{u}/default.target.wants/power-auto.service", link=f"{src}/{u}/power-auto.service")
        self.put(f"{u}/default.target.wants/pipewire-pulse.service", link="/usr/lib/systemd/user/pipewire-pulse.service")
        self.put(f"{u}/graphical-session.target.wants/omarchy-kit.service", link=f"{src}/{u}/omarchy-kit.service")
        self.put(f"{u}/graphical-session.target.wants/voxtype.service", link=f"{src}/{u}/voxtype.service")
        # things that must NEVER be copied
        self.put(".ssh/id_ed25519", "PRIVATE KEY\n")
        self.put(".gnupg/private-keys-v1.d/key", "gpg\n")
        self.put(".config/gh/hosts.yml", "oauth_token: abc\n")
        self.put(".config/git/config", "[user]\nemail = me@example.org\n")
        self.put(".config/BraveSoftware/Brave-Browser/Default/Cookies", "cookies\n")
        self.put(".config/Bitwarden/data.json", "vault\n")
        self.put(".config/anytype/db", "notes\n")
        self.put(".claude/memory.md", "private\n")
        self.put(".claude.json", "{}\n")
        self.put(".bash_history", "secret commands\n")
        self.put("Documents/taxes.pdf", "pdf\n")
        self.put("labspace/omarchy-kit/local.toml", "[coadmin]\nname='x'\n")

    # ---- the fake system
    def fakes(self):
        fb, db, log = self.fb, self.db, self.log
        real_rsync, real_install = shutil.which("rsync") or "/usr/bin/rsync", "/usr/bin/install"
        write_exec(fb / "getent", f'''echo "getent $*" >> "{log}"
            case "$1" in
              passwd) grep -E "^$2:" "{db}/passwd" ;;
              group)  grep -E "^$2:" "{db}/group" ;;
              *) exit 2 ;;
            esac\n''')
        write_exec(fb / "id", f'''case "$1" in
              -gn) if [ "$2" = owner ]; then echo owner; else echo "$2"; fi ;;
              -nG) if [ "$2" = owner ]; then echo "owner wheel ${{FAKE_EXTRA_GROUP:-}}"; else echo "$2"; fi ;;
              *) /usr/bin/id "$@" ;;
            esac\n''')
        write_exec(fb / "useradd", f'''echo "useradd $*" >> "{log}"
            name="${{@: -1}}"; home="{self.base}/$name"; mkdir -p "$home"
            echo "$name:x:2000:2000:x:$home:/bin/bash" >> "{db}/passwd"; echo "$name:x:2000:" >> "{db}/group"\n''')
        write_exec(fb / "userdel", f'''echo "userdel $*" >> "{log}"; name="${{@: -1}}"; rm -rf "{self.base}/$name"; sed -i "/^$name:/d" "{db}/passwd"\n''')
        for name in ("passwd", "chage", "chown", "loginctl", "usermod"):
            write_exec(fb / name, f'echo "{name} $*" >> "{log}"\n')
        # the namespace cannot chown to a user that does not exist: drop the owner options, keep everything else real
        write_exec(fb / "rsync", f'''args=(); for a in "$@"; do case "$a" in --chown=*) ;; *) args+=("$a");; esac; done
            echo "rsync ${{args[*]}}" >> "{log}"; exec {real_rsync} "${{args[@]}}"\n''')
        write_exec(fb / "install", f'''args=(); skip=0; for a in "$@"; do if [ $skip = 1 ]; then skip=0; continue; fi
              case "$a" in -o|-g) skip=1;; *) args+=("$a");; esac; done; exec {real_install} "${{args[@]}}"\n''')

    def go(self, *args, user=NEWUSER, name=NEWNAME, root=True, extra_env=None, with_names=True):
        argv = list(args)
        if with_names:
            argv = ["--user", user, "--name", name] + argv
        env = {"PATH": f"{self.fb}:{SAFE_PATH}", "HOME": str(self.tmp), "SUDO_USER": "owner", "COADMIN_HOME_BASE": str(self.base), **(extra_env or {})}
        cmd = ["bash", str(self.kit / "coadmin" / "install-coadmin"), *argv]
        if root:
            cmd = ["unshare", "-Urm"] + cmd
        return run(cmd, env=env)

    @property
    def new(self):
        return self.base / NEWUSER

    def calls(self):
        return self.log.read_text().splitlines() if self.log.exists() else []


@unittest.skipUnless(USERNS, "needs unshare -Urm (a private user namespace)")
class Refusals(Fixture):
    def test_without_root_it_refuses_and_changes_nothing(self):
        r = self.go(root=False)
        self.assertEqual(r.returncode, 1)
        self.assertIn("sudo", r.stderr)
        self.assertFalse(any(c.startswith("useradd") for c in self.calls()))

    def test_unknown_option_and_missing_arguments_exit_2(self):
        for args in (["--frobnicate"], ["--user"], ["--name"]):
            self.assertEqual(self.go(*args, with_names=False).returncode, 2, args)

    def test_bad_user_names_exit_2(self):
        for bad in ("Root", "1abc", "has space", "x" * 40, "a:b", ""):
            r = self.go(user=bad)
            self.assertEqual(r.returncode, 2, bad)

    def test_a_bad_full_name_is_refused(self):
        for bad in ("a:b", "x" * 101, ""):
            self.assertEqual(self.go(name=bad).returncode, 2, bad)

    def test_the_same_account_or_an_existing_one_is_refused(self):
        self.assertEqual(self.go(user="owner").returncode, 2)
        (self.db / "passwd").write_text((self.db / "passwd").read_text() + f"{NEWUSER}:x:2000:2000:x:{self.new}:/bin/bash\n")
        r = self.go()
        self.assertEqual(r.returncode, 1)
        self.assertIn("already exists", r.stderr)
        self.assertFalse(any(c.startswith("useradd") for c in self.calls()))

    def test_without_sudo_user_it_refuses(self):
        r = self.go(extra_env={"SUDO_USER": ""})
        self.assertEqual(r.returncode, 1)


@unittest.skipUnless(USERNS, "needs unshare -Urm (a private user namespace)")
class DryRun(Fixture):
    def test_it_prints_the_plan_and_creates_nothing(self):
        r = self.go("--dry-run")
        self.assertEqual(r.returncode, 0, r.stderr)
        for needle in (NEWUSER, NEWNAME, "wheel", "mode 700", "never:"):
            self.assertIn(needle, r.stdout)
        self.assertFalse(self.new.exists())
        self.assertFalse(any(c.startswith(("useradd", "passwd")) for c in self.calls()))

    def test_the_plan_says_what_is_never_copied(self):
        r = self.go("--dry-run")
        self.assertIn("credentials", r.stdout)
        self.assertIn("no-lock-before-hibernate", r.stdout)


@unittest.skipUnless(USERNS, "needs unshare -Urm (a private user namespace)")
class Create(Fixture):
    def setUp(self):
        super().setUp()
        self.r = self.go()

    def test_it_succeeds_and_creates_the_account_with_the_same_groups(self):
        self.assertEqual(self.r.returncode, 0, self.r.stderr)
        useradd = [c for c in self.calls() if c.startswith("useradd")]
        self.assertEqual(len(useradd), 1)
        self.assertIn("-G wheel", useradd[0])
        self.assertIn(f"-c {NEWNAME}", useradd[0])
        self.assertTrue(useradd[0].endswith(NEWUSER))

    def test_the_home_is_private(self):
        self.assertEqual(oct(self.new.stat().st_mode & 0o777), "0o700")

    def test_no_password_is_handled_without_a_terminal(self):
        self.assertFalse(any(c.startswith(("passwd", "chage")) for c in self.calls()))
        self.assertIn(f"sudo passwd {NEWUSER}", self.r.stdout)       # and it says how

    def test_the_settings_arrive(self):
        for rel in (".config/hypr/hyprland.lua", ".config/hypr/gpu.lua", ".config/omarchy/shell.json", ".config/omarchy/themes/golden-gate/colors.toml",
                    ".config/omarchy/hooks/theme-set.d/50-mac-icons", ".config/macdock/dock.json", ".config/fontconfig/conf.d/60-kit-mac-ui-font.conf",
                    ".config/pipewire/omarchy-speaker-tuning.conf", ".config/fcitx5/profile", ".config/mimeapps.list", ".config/user-dirs.dirs",
                    ".local/share/macdock/shell.qml", ".local/share/icons/WhiteSur-dark/index.theme", ".local/share/applications/WhatsApp.desktop"):
            self.assertTrue((self.new / rel).is_file(), rel)

    def test_nothing_private_is_copied(self):
        for rel in (".ssh", ".gnupg", ".config/gh", ".config/git", ".config/BraveSoftware", ".config/Bitwarden", ".config/anytype", ".claude", ".claude.json",
                    ".bash_history", "Documents/taxes.pdf", "labspace/omarchy-kit/local.toml"):
            self.assertFalse((self.new / rel).exists(), rel)

    def test_backups_samples_and_personal_launchers_stay_behind(self):
        for rel in (".config/hypr/input.lua.bak-2026", ".config/omarchy/defaults/agent", ".local/share/applications/claude-code-url-handler.desktop",
                    ".local/share/applications/es-de.desktop", ".local/share/applications/discord-455712169795780630.desktop"):
            self.assertFalse((self.new / rel).exists(), rel)

    def test_the_security_override_is_never_mirrored(self):
        self.assertFalse((self.new / ".config/systemd/user/omarchy-sleep-lock.service.d").exists())

    def test_only_expected_top_level_entries_exist(self):
        names = {p.name for p in self.new.iterdir()}
        self.assertLessEqual(names, {".config", ".local", "Downloads", "Documents", "Pictures", "Music", "Videos", "labspace", "Work"})
        self.assertEqual(sorted(p.name for p in (self.new / ".config").iterdir()),
                         sorted({"hypr", "omarchy", "macdock", "fontconfig", "pipewire", "fcitx5", "mimeapps.list", "user-dirs.dirs", "systemd", "omarchy-kit"}))

    def test_the_old_home_path_is_rewritten(self):
        text = (self.new / ".config/hypr/gpu.lua").read_text()
        self.assertIn(str(self.new), text)
        self.assertNotIn(str(self.src), text)
        unit = (self.new / ".config/systemd/user/omarchy-kit.service").read_text()
        self.assertIn(f"{self.new}/labspace/omarchy-kit/omarchy-kit.service", unit)
        for p in self.new.rglob("*"):
            if p.is_file() and not p.is_symlink() and p.stat().st_size < 100000 and "icons" not in p.parts:
                self.assertNotIn(str(self.src), p.read_text(errors="replace"), str(p))

    def test_the_wanted_units_are_enabled_for_the_new_home_and_voxtype_is_not(self):
        u = self.new / ".config/systemd/user"
        link = u / "default.target.wants/power-auto.service"
        self.assertEqual(os.readlink(link), f"{self.new}/.config/systemd/user/power-auto.service")
        self.assertEqual(os.readlink(u / "default.target.wants/pipewire-pulse.service"), "/usr/lib/systemd/user/pipewire-pulse.service")
        self.assertEqual(os.readlink(u / "graphical-session.target.wants/omarchy-kit.service"), f"{self.new}/.config/systemd/user/omarchy-kit.service")
        self.assertFalse((u / "voxtype.service").exists())
        self.assertFalse((u / "graphical-session.target.wants/voxtype.service").exists())

    def test_the_helper_and_what_it_needs_are_installed(self):
        helper = self.new / ".local/bin/omarchy-kit-first-login"
        self.assertTrue(os.access(helper, os.X_OK))
        self.assertEqual(helper.read_bytes(), FIRST_LOGIN.read_bytes())
        conf = (self.new / ".config/omarchy-kit/mirror.conf").read_text()
        self.assertIn("THEME=mecha-unit", conf)
        self.assertIn("KIT_URL=https://github.com/", conf)
        self.assertNotRegex(conf.lower(), r"pass|secret|token")
        self.assertEqual(oct((self.new / ".config/omarchy-kit/mirror.conf").stat().st_mode & 0o777), "0o600")

    def test_the_usual_folders_and_the_work_link_exist(self):
        for d in ("Downloads", "Documents", "Pictures", "Music", "Videos", "labspace"):
            self.assertTrue((self.new / d).is_dir(), d)
        self.assertEqual(os.readlink(self.new / "Work"), "labspace")

    def test_running_it_again_refuses_because_the_account_exists(self):
        r = self.go()
        self.assertEqual(r.returncode, 1)
        self.assertIn("already exists", r.stderr)

    def test_the_source_account_is_never_modified(self):
        self.assertEqual((self.src / ".config/hypr/gpu.lua").read_text().count(str(self.src)), 1)
        self.assertTrue((self.src / ".ssh/id_ed25519").exists())


@unittest.skipUnless(USERNS, "needs unshare -Urm (a private user namespace)")
class ExtraGroups(Fixture):
    def test_extra_groups_of_the_account_are_mirrored_too(self):
        r = self.go(extra_env={"FAKE_EXTRA_GROUP": "video"})
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("-G wheel,video", [c for c in self.calls() if c.startswith("useradd")][0])


@unittest.skipUnless(USERNS, "needs unshare -Urm (a private user namespace)")
class Remove(Fixture):
    def test_it_removes_only_an_account_it_created(self):
        self.go()
        r = self.go("--remove")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(any(c.startswith("userdel -r") for c in self.calls()))
        self.assertFalse(self.new.exists())

    def test_it_refuses_an_account_without_the_marker(self):
        home = self.base / "someone"
        (home).mkdir()
        (self.db / "passwd").write_text((self.db / "passwd").read_text() + f"someone:x:2001:2001:x:{home}:/bin/bash\n")
        r = self.go("--remove", user="someone")
        self.assertEqual(r.returncode, 1)
        self.assertIn("not created by this script", r.stderr)
        self.assertFalse(any(c.startswith("userdel") for c in self.calls()))
        self.assertTrue(home.exists())

    def test_removing_a_missing_account_is_harmless(self):
        r = self.go("--remove")
        self.assertEqual(r.returncode, 0)
        self.assertIn("no user", r.stdout)


class FirstLogin(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="kit-test-")
        self.addCleanup(self._tmp.cleanup)
        self.tmp = pathlib.Path(self._tmp.name)
        self.home = self.tmp / "home"
        (self.home / ".config/omarchy-kit").mkdir(parents=True)
        self.conf = self.home / ".config/omarchy-kit/mirror.conf"
        self.conf.write_text("THEME=mecha-unit\nKIT_URL=https://github.com/example/omarchy-kit\nCREATED=2026-10-23\n")
        self.fb = self.tmp / "fb"
        self.log = self.tmp / "calls.log"
        for name, body in {
            "git": f'echo "git $*" >> "{self.log}"; mkdir -p "${{@: -1}}/.git"\n',
            "omarchy": f'echo "omarchy $*" >> "{self.log}"; [ "$2" = list ] && printf "Mecha Unit\\nSolarpunk\\n"; exit 0\n',
            "gsettings": f'echo "gsettings $*" >> "{self.log}"\n',
            "hyprctl": f'echo "hyprctl $*" >> "{self.log}"\n',
            "systemctl": f'echo "systemctl $*" >> "{self.log}"\n',
        }.items():
            write_exec(self.fb / name, body)

    def go(self, *args, signature="sig", conf=True):
        if not conf:
            self.conf.unlink()
        env = {"PATH": f"{self.fb}:{SAFE_PATH}", "HOME": str(self.home), "HYPRLAND_INSTANCE_SIGNATURE": signature}
        if not signature:
            env.pop("HYPRLAND_INSTANCE_SIGNATURE")
        return run(["bash", str(FIRST_LOGIN), *args], env=env)

    def calls(self):
        return self.log.read_text().splitlines() if self.log.exists() else []

    def test_bad_arguments_exit_2(self):
        self.assertEqual(self.go("--nope").returncode, 2)

    def test_without_the_mirror_file_or_the_desktop_it_refuses(self):
        self.assertEqual(self.go(conf=False).returncode, 1)
        self.assertEqual(self.go(signature="").returncode, 1)
        self.assertEqual(self.calls(), [])

    def test_it_clones_the_kit_sets_the_theme_the_cursor_and_the_buttons(self):
        r = self.go()
        self.assertEqual(r.returncode, 0, r.stderr)
        calls = "\n".join(self.calls())
        self.assertIn(f"git clone --depth 1 https://github.com/example/omarchy-kit {self.home}/labspace/omarchy-kit", calls)
        self.assertIn("omarchy theme set mecha-unit", calls)
        self.assertIn("gsettings set org.gnome.desktop.interface cursor-theme macOS", calls)
        self.assertIn("gsettings set org.gnome.desktop.wm.preferences button-layout close:", calls)
        self.assertIn("systemctl --user start omarchy-kit.service", calls)

    def test_running_it_twice_does_not_clone_twice(self):
        self.go()
        self.go()
        self.assertEqual(len([c for c in self.calls() if c.startswith("git clone")]), 1)

    def test_a_clone_address_that_is_not_github_is_refused(self):
        self.conf.write_text("THEME=mecha-unit\nKIT_URL=http://evil.example/x\n")
        r = self.go()
        self.assertEqual(r.returncode, 1)
        self.assertFalse(any(c.startswith("git clone") for c in self.calls()))

    def test_a_theme_name_with_shell_characters_is_refused_not_run(self):
        self.conf.write_text("THEME=$(touch /tmp/pwned)\nKIT_URL=https://github.com/example/x\n")
        r = self.go()
        self.assertEqual(r.returncode, 1)
        self.assertFalse(pathlib.Path("/tmp/pwned").exists())


class Static(unittest.TestCase):
    def test_scripts_parse_and_are_executable(self):
        for p in (INSTALLER, FIRST_LOGIN):
            self.assertTrue(os.access(p, os.X_OK), p.name)
            self.assertEqual(run(["bash", "-n", str(p)]).returncode, 0, p.name)

    def test_no_personal_details_in_the_folder(self):
        bad = []
        for p in (KIT / "coadmin").rglob("*"):
            if p.is_file():
                text = p.read_text(errors="replace")
                for needle in ("/home/", "aldo", "mbpro"):
                    if needle in text.lower() and "aldoruizluna" not in needle:
                        if needle == "aldo" and text.lower().count("aldo") == text.lower().count("aldoruizluna"):
                            continue
                        bad.append(f"{p.name}: {needle}")
                if re.search(r"[\w.+-]+@[\w-]+\.[a-z]{2,}", text):
                    bad.append(f"{p.name}: an email address")
        self.assertEqual(bad, [])

    def test_the_allowlist_never_names_a_secret_location(self):
        text = INSTALLER.read_text()
        listed = re.search(r"ALLOW_DIRS=\((.*?)\)\nALLOW_FILES=\((.*?)\)", text, re.S)
        entries = (listed.group(1) + " " + listed.group(2)).split()
        for entry in entries:
            for secret in (".ssh", ".gnupg", "gh", "git", "BraveSoftware", "chromium", "Bitwarden", "anytype", ".claude", ".bash_history", "keyrings", "Mullvad VPN"):
                self.assertNotEqual(secret.lower(), entry.lower().split("/")[-1], entry)
        self.assertTrue(entries)

    def test_the_sleep_lock_override_is_not_in_the_unit_list(self):
        text = INSTALLER.read_text()
        units = re.search(r"UNITS=\((.*?)\)", text, re.S).group(1)
        self.assertNotIn("sleep-lock", units)
        self.assertNotIn("voxtype", units)


if __name__ == "__main__":
    unittest.main()
