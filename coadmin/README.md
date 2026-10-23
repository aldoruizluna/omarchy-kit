# coadmin/: a second administrator with a mirror of your settings

> **TL;DR.** `install-coadmin` adds a second account that has **the same privileges** (the same groups, so the same `sudo`) and a **mirror of your settings**: Hyprland, the Omarchy shell and themes, the Dock, fonts, icons, terminals, the speaker EQ, the web-app launchers and the same user
> services. It copies **settings only**, from a fixed allowlist: never credentials, keys, browser or chat data, history, documents, or the "no lock screen before hibernate" override. You type the temporary password yourself (the script never sees it) and the account must change it at its first login.
> Needs `sudo`; preview with `--dry-run`; `--remove` deletes an account this script created.

| Command | What |
|---|---|
| `sudo install-coadmin --dry-run` | prints the account, the groups, the theme, everything it would mirror and everything it never copies, with sizes; changes nothing |
| `sudo install-coadmin` | creates the account, asks you to type a temporary password, mirrors the settings (the name and user name come from `local.toml`, or `--user NAME --name "Full Name"`) |
| `sudo install-coadmin --remove --user NAME` | deletes the account and its home, only if this script created it (it checks for its own marker file) |
| `omarchy-kit-first-login` | for the **new** user, run once from a terminal after the first login: sets the theme (and with it the icon variant), the pointer and the window buttons, clones the kit from its public repository, starts the kit's portal |

## What "the same privileges" means

The new account gets the same supplementary groups as the account that ran `sudo` (here, `wheel`, which is what grants `sudo` with a password). It is created with a **private home** (mode 700): neither account can read the other's files. If `sudoers` has rules that name your account, the script says so; the new
one gets `wheel`'s rights, not those rules. System-wide things (the packages, the NVIDIA switch-off, sleep and Wi-Fi settings, the camera driver) are shared by every account without copying anything.

## What is mirrored, and what is not

| Mirrored (settings, from an allowlist) | Never copied |
|---|---|
| `~/.config`: `hypr`, `omarchy` (shell, themes, hooks, plugins), `macdock`, `fontconfig`, terminals, `btop`, `fcitx5` (the Mac keyboard layout), `pipewire` and `wireplumber` (the speaker EQ and sample rates), `tmux`, `imv`, `mimeapps.list`, `starship.toml`, `user-dirs.dirs` | SSH and GPG keys, `gh` and `git` configuration, any token |
| `~/.local/share`: the Dock program, the icon themes, the web-app launchers (Omarchy's and the kit's) | browser profiles, chat apps, the password manager, notes stores, the AI assistants' folders |
| user services: the kit's portal, power profile, auto appearance and the audio tuning, with the same enablement links rewritten to the new home | shell history, documents, downloads, the games |
| the folders Downloads, Documents, Pictures, Music, Videos, `labspace` and the `Work` link Omarchy expects | the "no lock screen before hibernate" override (a security decision for each owner), `voxtype` (needs a model downloaded per user), personal launchers, `*.bak*` backups |

Every path in a copied text file that named your home now names the new home (checked: none is left). The script does not touch the **login screen** (auto-login) or the **disk passphrase**: with auto-login on, the machine still starts in your account and the new one logs in after you log out; a LUKS slot of their own
(`sudo cryptsetup luksAddKey`, with them present) and turning auto-login off are separate steps listed in the Setup log.

## Honest status

- **Tested** (`test/test_coadmin.py`, 36 tests): the installer as fake root with fakes for `useradd` and friends against a fixture home that holds both mirrored and forbidden files: refusals, the dry run, the groups, the mode of the home, the allowlist and denylist both ways, path rewriting, enablement links,
  `--remove` only for accounts it created, and the first-login helper against fakes (it refuses a clone address that is not GitHub and a theme name with shell characters).
- **Rehearsed on the real home** as fake root, writing to a scratch folder: 160 MB, home mode 700, no reference to the owner's home left, no secret-looking file, the sleep-lock override absent, enablement links correct, in 2 seconds.
- **Not verified:** a real run (`useradd`, `passwd` and a real login need root and a second person). After it, the Setup log's account check (wheel, home mode 700) and `id`, `ls -ld` and a login tell the rest. One thing to know: the kit's portal listens on one port, so the second account's copy cannot start while the first is logged in.

Undo: `sudo coadmin/install-coadmin --remove --user NAME`.

---

Related: [keys/](../keys/README.md) · [dock/](../dock/README.md) · [look/](../look/README.md) · [docs/MAC-FEEL](../docs/MAC-FEEL.md) · [docs/INDEX](../docs/INDEX.md)
