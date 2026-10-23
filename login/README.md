# login/: a login screen that lists the accounts, and auto-login that is really off

> **TL;DR.** `install-login` makes the computer start at a login screen that **lists every account** (Left / Right / Tab or a click to choose, the last user first), and turns
> auto-login **really** off. The two things that were wrong on 2026-10-23: SDDM reads **every** file in `/etc/sddm.conf.d`, whatever its name, so moving `autologin.conf` to
> `autologin.conf.disabled` changed nothing (two boots in a row logged straight in); and Omarchy's login theme is a single password box for the last user, with no list.
> Needs `sudo`; preview with `--dry-run`; `--remove` puts everything back. It never restarts SDDM (that would end your session): it shows at the next restart or log out.

| Command | What |
|---|---|
| `install-login --dry-run` | prints every move and write; changes nothing, needs no `sudo` |
| `sudo install-login` | moves every file that sets an auto-login user out of `/etc/sddm.conf.d` into `/etc/omarchy-kit/sddm-disabled/` (with a list), installs the theme, writes `/etc/sddm.conf.d/zz-omarchy-kit-login.conf` |
| `sudo install-login --remove` | puts the moved files back where they were (so auto-login comes back if it was on) and removes the theme and the drop-in |
| `install-login --stage DIR` | no `sudo`: assembles the theme in `DIR`, to try it with `sddm-greeter-qt6 --test-mode --theme DIR` (a window; it logs nobody in) |
| `python3 -I sddm_conf.py get Autologin User` | what SDDM will really use, read the way SDDM reads it (also `autologin-files`, and `--root DIR` for a scratch tree) |

## What it installs

- **The theme `omarchy-kit-login`** in `/usr/share/sddm/themes`: Omarchy's own look (its logo, lock, entry and bullet pictures are **copied from its theme when you install**, none is committed
  here) plus a row listing every account. The names come from SDDM (`userModel`), so none is written in the code. The chosen account is bright and bold; **Left / Up / Shift+Tab** and
  **Right / Down / Tab** move along the row (and wrap), a click chooses one, **Return** signs in. Changing the account clears what you typed. The last user to sign in is chosen first.
- **`/etc/sddm.conf.d/zz-omarchy-kit-login.conf`**: `Current=omarchy-kit-login`, remember the last user and session, and an empty `[Autologin] User=` on top. It sorts last, so it wins over
  every other file (SDDM applies the files in name order; the later one wins).
- It **reads the result back the way SDDM reads it** and undoes itself if auto-login would still be on or the theme is not the one selected.

The Omarchy theme itself (`/usr/share/sddm/themes/omarchy`) belongs to the `omarchy-settings` package and is left alone, so an update cannot overwrite this.

## If the login screen ever fails

Press **Ctrl+Alt+F2** (a text login), sign in, then `sudo ~/labspace/omarchy-kit/login/install-login --remove`, or just `sudo rm /etc/sddm.conf.d/zz-omarchy-kit-login.conf` and
`sudo systemctl restart sddm` from the text console.

## What was verified, and what was not

- **Verified:** the theme loads in the real SDDM greeter (`sddm-greeter-qt6 --test-mode`) on this screen; both accounts are listed; Right, Left and Tab change the chosen account and wrap;
  typed characters appear as dots. The installer and the config reader have hermetic tests (`test/test_login.py`: a scratch tree, the real scripts, no root): auto-login is moved and
  read back as off, a second run changes nothing, `--remove` restores the folder byte for byte, a missing Omarchy picture stops it before anything changes, and it undoes itself when
  something it does not manage would still log in.
- **Not verified:** a real boot (the PAM login, the pictures at the real resolution, the keys on the physical keyboard). That needs a restart; the Setup log row is `ok` only when the
  live configuration really lists the accounts and no auto-login.
- The **disk passphrase** (LUKS) still comes first, before this screen. A second account that should unlock the disk by itself needs its own slot (`cryptsetup luksAddKey`), see [coadmin/](../coadmin/README.md).

Checked by the Setup log row **Login screen at boot** (live, from SDDM's real configuration) and its record, which also corrects the earlier claim that renaming the file had worked.

---

Related: [coadmin/](../coadmin/README.md) · [docs/FIELD-NOTES](../docs/FIELD-NOTES.md) · [docs/INDEX](../docs/INDEX.md)
