#!/usr/bin/env python3
"""Build setup.html — the machine's setup log and admin handbook (EN/ES).

Every status line is checked live against the system when this runs (no sudo needed), so the page
never claims something is done that isn't. The helper re-runs this on each visit to /setup.
Passwords and passphrases are never written here.
"""
import grp, json, os, pwd, re, stat, subprocess, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
HOME = Path.home()
import sys as _sys
_sys.path.insert(0, str(HERE))
import portal_content as _pc, portal_lessons as _pl
N_HABITS = sum(len(rows) for _, _, rows in _pc.MAC)
N_LESSONS = sum(len(l["lessons"]) for l in _pl.LEVELS)

# Personal details (the co-admin's name/username) live in local.toml, which is git-ignored:
#   [coadmin]
#   name = "Full Name"
#   user = "username"
try:
    import tomllib
    _co = tomllib.loads((HERE / "local.toml").read_text()).get("coadmin", {})
except Exception:
    _co = {}
CO_NAME, CO_USER = _co.get("name", "your co-admin"), _co.get("user", "coadmin")
CO_FIRST = CO_NAME.split()[0] if "name" in _co else "the co-admin"
CO_FIRST_ES = CO_NAME.split()[0] if "name" in _co else "la persona co-administradora"


def sh(*cmd):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=5).stdout.strip()
    except Exception:
        return ""


def active(unit, user=False):
    return sh("systemctl", *(["--user"] if user else []), "is-active", unit) == "active"


def hypr_json(*args, default=None):
    """hyprctl -j <args> as a dict/list (the live compositor), or default when Hyprland is not reachable."""
    try:
        return json.loads(sh("hyprctl", "-j", *args) or "null") or ({} if default is None else default)
    except Exception:
        return {} if default is None else default


def hypr_opt(name):
    d = hypr_json("getoption", name)
    return d if isinstance(d, dict) else {}


def read(path):
    try:
        return Path(path).read_text()
    except Exception:
        return ""


# ---------------------------------------------------------------- live checks
def checks():
    c = {}
    import sys
    sys.path.insert(0, str(HERE))
    try:
        from appslib import load
        from install_status import installed
        apps = load()
        missing = [a["name"] for a in apps if not installed(a)]
        c["apps"] = ("ok" if not missing else "action", f"{len(apps) - len(missing)}/{len(apps)}" + (f" — missing: {', '.join(missing)}" if missing else ""))
    except Exception as e:
        c["apps"] = ("info", f"could not check ({e})")
    br = sh("xdg-settings", "get", "default-web-browser")
    c["browser"] = ("ok" if br.startswith("brave") else "action", br or "unknown")
    b = read(HOME / ".config/hypr/bindings.lua")
    names = ["Beeper", "Anytype", "Kagi", "Screenshot", "Telegram", "Grayjay", "Bitwarden", "Omarchy Kit"]
    have = [n for n in names if f'"{n}"' in b]
    c["bindings"] = ("ok" if len(have) == len(names) else "action", f"{len(have)}/{len(names)}: " + ", ".join(have))
    i = read(HOME / ".config/hypr/input.lua")
    c["gestures"] = ("ok" if 'hl.gesture({ fingers = 4, direction = "horizontal"' in i and "natural_scroll = true" in i else "action", "input.lua")
    import kitconf
    tf = kitconf.three_fingers()
    drag_live = hypr_opt("input:touchpad:drag_3fg").get("int")
    c["threefingers"] = ("ok" if drag_live == (1 if tf == "drag" else 0) else "action",
                         f"three fingers: {'drag (select and drag without clicking), spaces on four fingers' if tf == 'drag' else 'swipe between spaces'} · live drag_3fg {drag_live if drag_live is not None else '?'}"
                         + ("" if drag_live == (1 if tf == "drag" else 0) else " (does not match input.lua: run hyprctl reload)"))
    variant = hypr_opt("input:kb_variant").get("str", "")
    fcitx = [k for k in (hypr_json("devices").get("keyboards") or []) if "fcitx" in k.get("name", "")]
    fc_pid = sh("pgrep", "-o", "fcitx5")
    if fcitx:  # its virtual keyboard exists only while a text field is focused; then it shows the keymap it copied
        fc_mac, fc_note = all("Macintosh" in k.get("active_keymap", "") for k in fcitx), "on the Mac keymap" if all("Macintosh" in k.get("active_keymap", "") for k in fcitx) else "still on the OLD keymap: restart it"
    elif fc_pid:  # otherwise: was it (re)started after input.lua was last edited? it copies the layout at start
        try:
            started = time.time() - int(sh("ps", "-o", "etimes=", "-p", fc_pid))
            fc_mac = started >= (HOME / ".config/hypr/input.lua").stat().st_mtime
        except (ValueError, OSError):
            fc_mac = True
        fc_note = "started after the layout change" if fc_mac else "started BEFORE the layout change: restart it"
    else:
        fc_mac, fc_note = None, "not running"
    acc_ok = 'kb_variant = "mac"' in i and variant == "mac" and fc_mac is not False
    c["accents"] = ("ok" if acc_ok else "action", f"layout us({variant or 'default'}) · fcitx5 {fc_note}")
    mk_file = (HOME / ".config/hypr/mackeys.lua").exists() and 'require("hypr.mackeys")' in read(HOME / ".config/hypr/hyprland.lua")
    bound = sum(1 for b in (hypr_json("binds", default=[]) or []) if "⌘" in b.get("description", ""))
    c["mackeys"] = ("ok" if mk_file and bound >= 13 else "action", f"mackeys.lua {'installed' if mk_file else 'not installed'} · {bound} ⌘ shortcuts bound")
    pa = sh(str(HERE / "power" / "power-auto"), "--status").replace("\n", " · ")
    pa_on = active("power-auto.service", True) and sh("systemctl", "--user", "is-enabled", "power-auto.service") == "enabled"
    c["powerauto"] = ("ok" if pa_on else "action", f"power-auto.service {'running' if pa_on else 'not installed'} · {pa}")
    try:
        sl = json.loads(sh(str(HERE / "sleep" / "sleep-check"), "--json") or "null")
    except Exception:
        sl = None
    c["sleep"] = (sl["status"], f"{sl['count']} suspends seen · {sl['verdict']}") if sl else ("info", "sleep-check could not read the journal")
    fn = read("/sys/module/hid_apple/parameters/fnmode").strip()
    conf = read("/etc/modprobe.d/hid_apple.conf").strip()
    c["fnmode"] = ("ok" if fn in ("1", "3") and "fnmode=3" in conf else "action", f"live {fn or '?'} · {conf or 'no config'}")
    rates = (HOME / ".config/pipewire/pipewire.conf.d/10-hifi-rates.conf").exists()
    resample = (HOME / ".config/pipewire/client.conf.d/10-resample.conf").exists() and (HOME / ".config/pipewire/pipewire-pulse.conf.d/10-resample.conf").exists()
    c["rates"] = ("ok" if rates else "action", "10-hifi-rates.conf")
    c["resample"] = ("ok" if resample else "action", "10-resample.conf ×2")
    rt = "RR" in sh("bash", "-c", "ps -eLo cls,comm | awk '$2==\"data-loop.0\"{print $1}' | sort -u")
    c["rtkit"] = ("ok" if sh("pacman", "-Q", "rtkit") and rt else "action", "rtkit installed, audio threads SCHED_RR" if rt else "not realtime")
    eq, fol = active("omarchy-speaker-tuning.service", True), active("speaker-eq-follow.service", True)
    ra = Path.home() / ".config/retroarch/retroarch.cfg"
    racfg = read(ra) if ra.exists() else ""
    glob_preset = read(Path.home() / ".config/retroarch/config/global.slangp")
    if not racfg:
        c["retro"] = ("pending", "RetroArch not installed (Omarchy menu → Install → Gaming → RetroArch)")
    else:
        tuned = 'video_driver = "glcore"' in racfg and "zfast-crt" in glob_preset
        c["retro"] = ("ok" if tuned else "action", ("OpenGL · zfast-crt (3D) / crt-hyllian-fast (2D) · saves in ~/Games" if tuned else "Omarchy defaults: Vulkan + crt-royale (45 fps here)"))
    gfx = read(Path.home() / ".config/dolphin-emu/GFX.ini")
    if not sh("pacman", "-Q", "dolphin-emu"):
        c["gamecube"] = ("pending", "Dolphin not installed")
    else:
        tuned = "ShaderCompilationMode = 2" in gfx and "InternalResolution = 2" in gfx
        c["gamecube"] = ("ok" if tuned else "action", "Dolphin: OpenGL · 2x · hybrid ubershaders · 60 fps measured" if tuned else "Dolphin defaults (not tuned for this GPU)")
    try:
        lib = json.loads(sh(str(HERE / "games" / "kit-games"), "status") or "null")
    except Exception:
        lib = None
    if lib and lib.get("cap"):
        c["library"] = ("ok" if lib["used"] <= lib["cap"] else "action",
                        f"{lib['games']} games · {lib['used'] / 1e9:.1f} of {lib['cap'] / 1e9:.0f} GB budget (half the free disk)")
    else:
        c["library"] = ("pending", "run games/kit-games init")
    ply = read("/etc/plymouth/plymouthd.conf")
    simpledrm = "UseSimpledrm=1" in ply
    splash = sh("omarchy-plymouth-current")
    c["bootlook"] = ("ok" if simpledrm and splash.lower() not in ("", "default") else "pending",
                     f"splash theme: {splash or 'unknown'} · early splash {'on' if simpledrm else 'off'}")
    pad = any("Wireless Controller" in l or "DualShock" in l for l in read("/proc/bus/input/devices").splitlines() if l.startswith("N: Name"))
    c["ds4"] = ("ok" if pad else "pending", "PS4 controller connected" if pad else "not connected right now")
    c["eq"] = ("ok" if eq and fol else "action", f"tuning {'active' if eq else 'inactive'} · headphone watcher {'active' if fol else 'inactive'}")
    ts_state = ""
    try:
        ts_state = json.loads(sh("tailscale", "status", "--json") or "{}").get("BackendState", "")
    except Exception:
        pass
    c["tailscale"] = ("ok" if ts_state == "Running" else "action" if active("tailscaled") else "pending",
                      f"tailscaled {'active' if active('tailscaled') else 'inactive'} · {ts_state or 'unknown'}")
    c["ssh"] = ("ok" if active("sshd") else "pending", "sshd " + ("active" if active("sshd") else "not set up"))
    c["fido2"] = ("ok" if Path("/etc/fido2/fido2").exists() else "pending", "registered" if Path("/etc/fido2/fido2").exists() else "no key registered")
    try:
        u = pwd.getpwnam(CO_USER)
        wheel = CO_USER in grp.getgrnam("wheel").gr_mem
        mode = stat.S_IMODE(os.stat(u.pw_dir).st_mode)
        c["coadmin"] = ("ok" if wheel and mode == 0o700 else "action", f"{u.pw_gecos} · {'wheel' if wheel else 'NOT in wheel'} · home {oct(mode)[2:]}")
    except KeyError:
        c["coadmin"] = ("pending", "account not created yet")
    al = Path("/etc/sddm.conf.d/autologin.conf").exists()
    c["autologin"] = ("pending" if al else "ok", "auto-login still on" if al else "login screen at boot")
    c["luks"] = ("info", "needs root to read: sudo cryptsetup luksDump /dev/sda2 | grep -A1 Keyslots")
    import glob
    panel = os.path.realpath((glob.glob("/sys/class/drm/card*-eDP-1") or [""])[0])
    gpp = Path("/sys/firmware/efi/efivars/gpu-power-prefs-fa4ce28d-b62f-4c99-9cc3-6815686e30f9")
    on_intel = "0000:00:02.0" in panel
    try:
        pref = gpp.read_bytes()[4] if gpp.exists() else (1 if on_intel else None)
    except OSError:  # Apple firmware rejects runtime reads (EINVAL); after boot the variable is hidden entirely
        pref = 1
    c["gpu"] = ("ok" if on_intel else "action",
                f"screen on {'Intel' if on_intel else 'NVIDIA'} · firmware boot GPU: {'Intel' if pref == 1 else 'NVIDIA (default)' if pref is None else 'NVIDIA'}"
                + (" · reboot pending" if pref == 1 and not on_intel else ""))
    # sysfs power_state can read D0 after sleep while the card is off; nvidia-off saves vga_switcheroo's real state
    sw = read("/run/nvidia-off.status")
    nv = read("/sys/bus/pci/devices/0000:01:00.0/power_state").strip()
    nv_off = ":Off:" in sw if sw else nv.startswith("D3")
    nv_src = "vga_switcheroo" if sw else nv or "?"
    nv_unit = sh("systemctl", "is-enabled", "nvidia-off.service") == "enabled"
    c["nvoff"] = ("ok" if nv_unit and nv_off else "action" if not nv_unit else "info",
                  f"NVIDIA GPU {'off' if nv_off else 'on'} ({nv_src}) · nvidia-off.service {'enabled' if nv_unit else 'not installed'}")
    cam_mod = Path("/sys/module/facetimehd").exists()
    cam_dev = Path("/dev/video0").exists()
    c["camera"] = ("ok" if cam_mod and cam_dev else "action",
                   f"facetimehd {'loaded' if cam_mod else 'not loaded'} · {'/dev/video0' if cam_dev else 'no video device'}")
    # --- auto appearance (opt-in), bar clock, optional ⌘ takeovers
    ap_inst = (HOME / ".local/bin/auto-appearance").exists()
    ap_on = sh("systemctl", "--user", "is-enabled", "auto-appearance.timer") == "enabled"
    ap_status = sh(str(HOME / ".local/bin/auto-appearance"), "status").replace("\n", " · ") if ap_inst else ""
    c["appearance"] = ("ok" if ap_on else "pending", (ap_status or "not installed") + ("" if ap_on else " (optional)"))
    try:
        clock = [w for w in json.loads(read(HOME / ".config/omarchy/shell.json"))["bar"]["layout"]["center"] if w.get("id") == "omarchy.clock"][0].get("format", "")
    except Exception:
        clock = ""
    c["barclock"] = ("ok" if "d MMM" in clock or "MMM" in clock else "pending", f"clock format: {clock or 'unknown'}")
    import kitconf
    ex = kitconf.mackeys_extra()
    c["mackeysextra"] = ("ok" if ex else "pending", f"⌘{' ⌘'.join(ex)} take over Super+key in apps" if ex else "none enabled (optional; Omarchy's own Super+W/T/F/S/L/G/P keep working)")
    # --- backups
    cfgs = sh("snapper", "list-configs")
    snap_home = any(l.split()[0:1] == ["home"] for l in cfgs.splitlines())
    tl = sh("systemctl", "is-enabled", "snapper-timeline.timer") == "enabled"
    n_snap = len([l for l in sh("snapper", "-c", "home", "list", "--columns", "number").splitlines()[2:] if l.strip() not in ("", "0")]) if snap_home else 0
    c["homesnap"] = ("ok" if snap_home and tl else "pending", (f"/home snapshots on, {n_snap} so far" if snap_home and tl else "no /home snapshots yet (needs sudo, see the command)"))
    # whether a backup job exists is Pika's own state; the format is not read here, so installed is as far as this can honestly say
    pika = bool(sh("pacman", "-Q", "pika-backup"))
    c["pika"] = ("info" if pika else "pending", "Pika Backup is installed: open it to see the last backup and the drive" if pika else "Pika Backup not installed")
    c["helper"] = ("ok" if active("omarchy-kit.service", True) else "action", "omarchy-kit.service")
    return c


# ---------------------------------------------------------------- content
# Each status row: key, EN/ES title, EN/ES "what to do if not done", optional command.
STATUS = [
 ("Apps & desktop", "Apps y escritorio", [
  ("apps", "Apps installed (apps.toml)", "Apps instaladas (apps.toml)", "Use the Apps tab or ./install-apps.", "Usa la pestaña Apps o ./install-apps.", ""),
  ("browser", "Brave is the default browser", "Brave es el navegador predeterminado", "", "", "xdg-settings set default-web-browser brave-browser.desktop"),
  ("bindings", "Custom keybindings in bindings.lua", "Atajos propios en bindings.lua", "", "", ""),
  ("helper", "Omarchy Kit runs in the background", "Omarchy Kit corre en segundo plano", "Start it:", "Iniciarlo:", "systemctl --user enable --now omarchy-kit.service"),
 ]),
 ("Hardware", "Hardware", [
  ("fnmode", "Mac-style top row (media keys without Fn)", "Fila superior estilo Mac (multimedia sin Fn)", "", "", "echo 3 | sudo tee /sys/module/hid_apple/parameters/fnmode"),
  ("gpu", "Screen on the efficient Intel GPU", "Pantalla en la GPU Intel eficiente", "Switch at next boot (reversible; see the GPU change below):", "Cambiar en el próximo arranque (reversible; ver el cambio de GPU abajo):", "~/labspace/omarchy-kit/gpu/switch-to-intel"),
  ("nvoff", "Idle NVIDIA GPU powered off", "GPU NVIDIA inactiva apagada", "Install the boot-time switch-off (reversible; see the GPU change below):", "Instalar el apagado al arrancar (reversible; ver el cambio de GPU abajo):", "sudo install -m755 ~/labspace/omarchy-kit/gpu/nvidia-off /usr/local/bin/ && sudo install -m644 ~/labspace/omarchy-kit/gpu/nvidia-off.service /etc/systemd/system/ && sudo systemctl enable nvidia-off.service"),
  ("camera", "FaceTime HD camera driver", "Driver de la cámara FaceTime HD", "Install the driver and load it:", "Instalar el driver y cargarlo:", "yay -S facetimehd-dkms facetimehd-data && sudo modprobe facetimehd"),
  ("gestures", "macOS-style gestures and natural scrolling", "Gestos estilo macOS y desplazamiento natural", "", "", ""),
 ]),
 ("Mac habits", "Hábitos de Mac", [
  ("accents", "Accents on the right Option key (⌥e e = é, ⌥n n = ñ)", "Acentos en la tecla Option derecha (⌥e e = é, ⌥n n = ñ)", "Add kb_variant = \"mac\" to input.lua (see the Mac accents change below), reload, then restart fcitx5:", "Añade kb_variant = \"mac\" a input.lua (ver el cambio de acentos abajo), recarga y reinicia fcitx5:", "hyprctl reload && fcitx5 --disable notificationitem -r -d"),
  ("mackeys", "⌘ shortcuts inside apps (⌘A, ⌘Z, ⌘R…)", "Atajos ⌘ dentro de las apps (⌘A, ⌘Z, ⌘R…)", "Install them (no root):", "Instalarlos (sin root):", "~/labspace/omarchy-kit/keys/install-mackeys"),
  ("threefingers", "Three fingers: swipe spaces or drag (your choice)", "Tres dedos: cambiar de espacio o arrastrar (tú eliges)", "Reload Hyprland so the choice in input.lua takes effect:", "Recarga Hyprland para que la elección de input.lua surta efecto:", "hyprctl reload"),
  ("powerauto", "Power profile follows the charger", "El perfil de energía sigue al cargador", "Install it (no root):", "Instalarlo (sin root):", "~/labspace/omarchy-kit/power/install-power-auto"),
  ("sleep", "Sleep and wake with the lid", "Reposo y despertar con la tapa", "Close the lid for 30 seconds, open it, then check the result:", "Cierra la tapa 30 segundos, ábrela y revisa el resultado:", "~/labspace/omarchy-kit/sleep/sleep-check"),
  ("barclock", "Menu-bar clock shows the date (Wed 7 Oct 15:08)", "El reloj de la barra muestra la fecha (mié 7 oct 15:08)", "Set it:", "Ponerlo:", "omarchy bar set omarchy.clock format \"ddd d MMM HH:mm\""),
  ("mackeysextra", "⌘W ⌘T ⌘F ⌘S ⌘L ⌘G ⌘P in apps (optional)", "⌘W ⌘T ⌘F ⌘S ⌘L ⌘G ⌘P en apps (opcional)", "Your decision (see Open items): each one takes Super+key from an Omarchy action. To choose:", "Decisión tuya (ver Pendientes): cada una le quita Super+tecla a una acción de Omarchy. Para elegir:", "~/labspace/omarchy-kit/keys/mac-key-extras W T F S"),
  ("appearance", "Auto appearance: light by day, dark at night (optional)", "Apariencia automática: clara de día, oscura de noche (opcional)", "Installed but off. Turn it on:", "Instalada pero apagada. Actívala:", "auto-appearance on"),
 ]),
 ("Backups", "Respaldos", [
  ("homesnap", "Hourly snapshots of /home (like Time Machine's local snapshots)", "Instantáneas de /home cada hora (como las locales de Time Machine)", "Needs your password. Preview first with --dry-run, then:", "Pide tu contraseña. Mira antes con --dry-run y luego:", "sudo ~/labspace/omarchy-kit/backup/install-backups"),
  ("pika", "A real backup of your files to an external drive (Pika Backup)", "Un respaldo real de tus archivos en un disco externo (Pika Backup)", "Installed by the command above; then open Pika Backup and choose the drive (that step needs you).", "Lo instala el comando de arriba; luego abre Pika Backup y elige el disco (ese paso te toca a ti).", ""),
 ]),
 ("Audio", "Audio", [
  ("rates", "Native sample rates (bit-perfect 44.1 kHz)", "Frecuencias nativas (44.1 kHz sin conversión)", "", "", ""),
  ("resample", "High-quality resampler (quality 10)", "Remuestreo de alta calidad (calidad 10)", "", "", ""),
  ("rtkit", "Realtime audio priority (rtkit)", "Prioridad de audio en tiempo real (rtkit)", "", "", "sudo pacman -S rtkit && systemctl --user restart pipewire pipewire-pulse wireplumber"),
  ("eq", "Speaker EQ, bypassed for headphones", "EQ de bocinas, omitido con audífonos", "Reinstall:", "Reinstalar:", "~/labspace/omarchy-kit/audio/install-speaker-eq"),
 ]),
 ("Boot", "Arranque", [
  ("bootlook", "Faster, themed boot screen", "Arranque más rápido y con tema", "Theme the splash, then apply (each asks for your password):", "Aplica el tema al arranque y luego los ajustes (cada uno pide tu contraseña):", "omarchy-plymouth-set-by-theme retro-82 ; sudo ~/labspace/omarchy-kit/boot/apply-boot-look"),
 ]),
 ("Retro gaming", "Juegos retro", [
  ("retro", "RetroArch tuned for this GPU", "RetroArch ajustado a esta GPU", "Re-apply Omarchy's defaults, then ask Claude to re-tune:", "Volver a los valores de Omarchy y luego pedir a Claude que ajuste:", "omarchy-install-gaming-retroarch"),
  ("gamecube", "GameCube (Dolphin) tuned for this GPU", "GameCube (Dolphin) ajustado a esta GPU", "Re-apply the measured settings:", "Volver a aplicar los ajustes medidos:", "~/labspace/omarchy-kit/games/kit-games dolphin"),
  ("library", "Game library within its budget", "Biblioteca de juegos dentro de su presupuesto", "See what uses the space:", "Ver qué ocupa el espacio:", "~/labspace/omarchy-kit/games/kit-games budget"),
  ("ds4", "PS4 controller (Bluetooth)", "Control de PS4 (Bluetooth)", "Hold Share + PS until the light bar flashes, then pair it in the Bluetooth menu (Super+Ctrl+B).", "Mantén Share + PS hasta que la barra de luz parpadee y emparéjalo en el menú Bluetooth (Super+Ctrl+B).", ""),
 ]),
 ("Access", "Acceso", [
  ("tailscale", "Tailscale connected", "Tailscale conectado", "Installed but needs a one-time login:", "Instalado pero falta iniciar sesión una vez:", "sudo tailscale up"),
  ("ssh", "SSH server (key-only)", "Servidor SSH (solo llaves)", "Needs a public key from another device or a GitHub username:", "Necesita una llave pública de otro equipo o un usuario de GitHub:", "omarchy-setup-security-sshd"),
  ("fido2", "FIDO2 security key for sudo", "Llave de seguridad FIDO2 para sudo", "Plug in a key, then:", "Conecta una llave y luego:", "omarchy-setup-security-fido2"),
 ]),
 (f"Co-admin: {CO_NAME}", f"Co-administración: {CO_NAME}", [
  ("coadmin", f"Account {CO_USER} (admin, private home)", f"Cuenta {CO_USER} (admin, carpeta privada)", "Create it:", "Crearla:", f'sudo useradd -m -G wheel -s /bin/bash -c "{CO_NAME}" {CO_USER}'),
  ("autologin", "Login screen at boot (no auto-login)", "Pantalla de inicio al arrancar (sin auto-login)", "Turn auto-login off:", "Desactivar auto-login:", "sudo mv /etc/sddm.conf.d/autologin.conf /etc/sddm.conf.d/autologin.conf.disabled"),
  ("luks", f"{CO_FIRST}'s own disk passphrase (LUKS slot)", f"Frase propia de {CO_FIRST_ES} para el disco (ranura LUKS)", f"With {CO_FIRST} present, in a terminal:", f"Con {CO_FIRST_ES} presente, en una terminal:", "sudo cryptsetup luksAddKey /dev/sda2"),
 ]),
]

# Change log: what was changed, why, where, and how to undo it.
LOG = [
 ("Workspace", "Espacio de trabajo",
  "Everything lives in ~/labspace/omarchy-kit: cheat sheet, keyboard and trackpad pages, the apps installer, audio tuning and the browser test suite. ~/labspace is the default workspace (the `lab` command starts Claude there). ~/Work, Omarchy's default, is now a symlink to ~/labspace, so Omarchy's try (~/Work/tries) and its mise bin/ PATH setting keep working.",
  "Todo vive en ~/labspace/omarchy-kit: guía, páginas de teclado y trackpad, instalador de apps, ajuste de audio y pruebas de navegador. ~/labspace es el espacio de trabajo predeterminado (el comando `lab` inicia Claude ahí). ~/Work, el predeterminado de Omarchy, ahora es un enlace a ~/labspace, así que try (~/Work/tries) y el bin/ de mise siguen funcionando.",
  "python3 ~/labspace/omarchy-kit/build_cheatsheet.py   # rebuild all pages"),
 ("Learning portal", "Portal de aprendizaje",
  f"Omarchy Kit is a bilingual course built from this machine. Start, Learn ({N_LESSONS} hands-on lessons that check your real desktop through the local service), From macOS ({N_HABITS} habits translated), Your MacBook (verified hardware status with live readings), Reference (all 367 Omarchy commands, the full menu with 'Show me' buttons, themes, glossary), plus the 3D keyboard and trackpad, Apps and this log. Shortcuts are read from your live config, so the pages follow your changes after a rebuild.",
  f"Omarchy Kit es un curso bilingüe hecho con esta máquina. Inicio, Aprender ({N_LESSONS} lecciones prácticas que comprueban tu escritorio real vía el servicio local), Desde macOS ({N_HABITS} hábitos traducidos), Tu MacBook (estado verificado del hardware con lecturas en vivo), Referencia (los 367 comandos de Omarchy, el menú completo con botones 'Muéstrame', temas, glosario), más el teclado y trackpad 3D, Apps y esta bitácora. Los atajos se leen de tu configuración real, así que las páginas siguen tus cambios tras reconstruir.",
  "python3 ~/labspace/omarchy-kit/build_cheatsheet.py   # rebuild every page"),
 ("Apps", "Apps",
  "Brave, Signal, Beeper, AnyType, Kagi (web app), Bitwarden, Telegram, Grayjay, QDirStat and Mullvad Browser, listed in apps.toml. Brave is the default browser. Kagi as Brave's search engine is a manual setting.",
  "Brave, Signal, Beeper, AnyType, Kagi (webapp), Bitwarden, Telegram, Grayjay, QDirStat y Mullvad Browser, en apps.toml. Brave es el navegador predeterminado. Kagi como buscador de Brave es un ajuste manual.",
  "./install-apps --list"),
 ("Keybindings", "Atajos",
  "Added to ~/.config/hypr/bindings.lua: Beeper (Super+Shift+Ctrl+B), AnyType (Super+Shift+Ctrl+N), Kagi (Super+Shift+K), Telegram (Super+Shift+Ctrl+T), Grayjay (Super+Shift+Ctrl+J), Bitwarden (Super+Shift+Ctrl+P), Screenshot (Super+Alt+P, since this keyboard has no Print key), Omarchy Kit (Super+Shift+H). A backup of the original file is in omarchy-kit/.",
  "Añadidos a ~/.config/hypr/bindings.lua: Beeper (Super+Shift+Ctrl+B), AnyType (Super+Shift+Ctrl+N), Kagi (Super+Shift+K), Telegram (Super+Shift+Ctrl+T), Grayjay (Super+Shift+Ctrl+J), Bitwarden (Super+Shift+Ctrl+P), Captura (Super+Alt+P, este teclado no tiene tecla Print), Omarchy Kit (Super+Shift+H). Hay copia del archivo original en omarchy-kit/.",
  "hyprctl reload && hyprctl configerrors"),
 ("Trackpad", "Trackpad",
  "macOS-style gestures in ~/.config/hypr/input.lua: 3 or 4 fingers left/right switch spaces (three fingers can drag instead, see Three fingers), 4 fingers up opens the Omarchy menu, 4 down toggles the scratchpad, 4-finger pinch opens the apps menu. Natural scrolling is on. Undo: restore input.lua.bak-2026-10-04.",
  "Gestos estilo macOS en ~/.config/hypr/input.lua: 3 o 4 dedos izquierda/derecha cambian de espacio (tres dedos pueden arrastrar en su lugar, ver Tres dedos), 4 arriba abre el menú de Omarchy, 4 abajo el scratchpad, pellizco con 4 dedos abre el menú de apps. Desplazamiento natural activado. Deshacer: restaurar input.lua.bak-2026-10-04.",
  ""),
 ("Mac accents (right Option key)", "Acentos de Mac (tecla Option derecha)",
  "Added kb_variant = \"mac\" to ~/.config/hypr/input.lua on 2026-10-07 (backup: input.lua.bak-2026-10-07). It selects the 'English (Macintosh, ABC, ANSI)' layout, so the right Option key (⌥) types accents as in macOS: ⌥e, ⌥u, ⌥i, ⌥` and ⌥n are dead keys (press ⌥ and the letter, release, then type the vowel), ⌥1 = ¡ and ⌥⇧/ = ¿. The left Option stays a plain Alt, so every Alt shortcut in Hyprland is unchanged, and Caps Lock stays the Compose key as a second way. The layout was checked key by key with libxkbcommon; the Learn lesson 'Typing Spanish' checks it with your own keys. fcitx5, the input method Omarchy runs, copies the keyboard layout only when it starts, so it was restarted once and picks the layout up at every login. Undo: delete the kb_variant line from input.lua, then hyprctl reload and restart fcitx5.",
  "Se añadió kb_variant = \"mac\" a ~/.config/hypr/input.lua el 2026-10-07 (respaldo: input.lua.bak-2026-10-07). Elige la distribución 'English (Macintosh, ABC, ANSI)', así que la tecla Option derecha (⌥) escribe acentos como en macOS: ⌥e, ⌥u, ⌥i, ⌥` y ⌥n son teclas muertas (pulsa ⌥ y la letra, suelta y escribe la vocal), ⌥1 = ¡ y ⌥⇧/ = ¿. La Option izquierda sigue siendo Alt, así que los atajos con Alt de Hyprland no cambian, y Bloq Mayús sigue como tecla Compose, una segunda forma. La distribución se comprobó tecla por tecla con libxkbcommon; la lección 'Escribir en español' de Aprender la comprueba con tus propias teclas. fcitx5, el método de entrada que usa Omarchy, copia la distribución solo al arrancar, así que se reinició una vez y la toma en cada inicio de sesión. Deshacer: borra la línea kb_variant de input.lua, luego hyprctl reload y reinicia fcitx5.",
  "hyprctl reload && fcitx5 --disable notificationitem -r -d   # apply a layout change"),
 ("Mac ⌘ shortcuts inside apps", "Atajos ⌘ de Mac dentro de las apps",
  "keys/mackeys.lua, installed as ~/.config/hypr/mackeys.lua and loaded from hyprland.lua (backup: hyprland.lua.bak-mackeys), catches Super+key and sends Ctrl+key to the focused app for 13 shortcuts: A (select all), Z and ⇧Z (undo, redo), R and ⇧R (reload, hard reload), N (new window), ⇧T (reopen closed tab), D (bookmark), B, I, U (bold, italic, underline), [ and ] (back, forward, sent as Alt+←/→). They appear in Super+K with ⌘ in the name. Only keys Omarchy does not use are mapped, so nothing Omarchy does was lost, and terminals are skipped on purpose (Ctrl+Z there stops a program). NOT on by default, because Omarchy already uses them: Super+W close window, T float, F full screen, S scratchpad, L layout, P pseudo, G group. So ⌘W, ⌘T, ⌘F, ⌘S, ⌘L, ⌘G and ⌘P stay Ctrl inside apps until you choose them (next entry). test/verify-mackeys.mjs checks every shortcut against a real Brave window, the terminal guard, and that no ⌘ chord collides with another binding (32 checks, including the optional takeovers below). Undo: install-mackeys --remove.",
  "keys/mackeys.lua, instalado como ~/.config/hypr/mackeys.lua y cargado desde hyprland.lua (respaldo: hyprland.lua.bak-mackeys), captura Super+tecla y envía Ctrl+tecla a la app enfocada en 13 atajos: A (seleccionar todo), Z y ⇧Z (deshacer, rehacer), R y ⇧R (recargar, recarga completa), N (ventana nueva), ⇧T (reabrir pestaña cerrada), D (marcador), B, I, U (negrita, cursiva, subrayado), [ y ] (atrás, adelante, enviados como Alt+←/→). Aparecen en Super+K con ⌘ en el nombre. Solo se mapean teclas que Omarchy no usa, así que no se perdió nada de Omarchy, y las terminales se omiten a propósito (Ctrl+Z ahí detiene un programa). NO activados por defecto, porque Omarchy ya los usa: Super+W cerrar ventana, T flotar, F pantalla completa, S scratchpad, L diseño, P pseudo, G grupo. Por eso ⌘W, ⌘T, ⌘F, ⌘S, ⌘L, ⌘G y ⌘P siguen siendo Ctrl dentro de las apps hasta que los elijas (siguiente entrada). test/verify-mackeys.mjs comprueba cada atajo contra una ventana real de Brave, la protección de terminales y que ningún ⌘ choque con otro atajo (32 comprobaciones, incluidos los reemplazos opcionales de abajo). Deshacer: install-mackeys --remove.",
  "~/labspace/omarchy-kit/keys/install-mackeys --remove   # undo"),
 ("Three fingers: swipe or drag", "Tres dedos: deslizar o arrastrar",
  "Three fingers can either switch spaces or drag, never both (libinput stops reporting three-finger swipes once three-finger drag is on; macOS makes you choose the same way). On 2026-10-07 drag was switched on, which also switched your three-finger space swipe off; you asked where it had gone, so the swipe was restored the same day and the choice became one word in ~/.config/hypr/input.lua: local THREE_FINGERS = \"swipe\" (the default) or \"drag\" (slide three fingers to select text and drag things without clicking, as with macOS Accessibility › Pointer Control › Trackpad Options › Three-finger drag; spaces then use four fingers only). Changing it reloads Hyprland and rebuilds the kit pages, so the Trackpad page, Mac page, lessons and this log describe whichever is on. A three-finger tap stays a middle click either way. Backup of the file before any of this: input.lua.bak-2026-10-07.",
  "Tres dedos pueden cambiar de espacio o arrastrar, nunca ambos (libinput deja de reportar deslizamientos de tres dedos cuando el arrastre de tres dedos está activo; macOS también obliga a elegir). El 2026-10-07 se activó el arrastre, lo que también apagó tu cambio de espacio con tres dedos; preguntaste dónde había quedado, así que se restauró el mismo día y la elección pasó a ser una palabra en ~/.config/hypr/input.lua: local THREE_FINGERS = \"swipe\" (la predeterminada) o \"drag\" (desliza tres dedos para seleccionar texto y arrastrar cosas sin hacer clic, como en macOS Accesibilidad › Control del puntero › Opciones del trackpad › Arrastrar con tres dedos; los espacios usan entonces solo cuatro dedos). Al cambiarla se recarga Hyprland y se reconstruyen las páginas del kit, así que la página Trackpad, la de Mac, las lecciones y esta bitácora describen la opción activa. Un toque con tres dedos sigue siendo clic central en ambos casos. Respaldo del archivo antes de todo esto: input.lua.bak-2026-10-07.",
  "~/labspace/omarchy-kit/trackpad/three-fingers drag   # or: swipe"),
 ("Automatic power profile", "Perfil de energía automático",
  "power/power-auto (installed to ~/.local/bin and run by the user service power-auto.service, 2026-10-07) watches the system's power-supply events: unplugging the charger sets Balanced, plugging it in sets Performance (it used to stay on Performance until changed by hand, which drains a 2014 battery and heats the machine). It acts only when the charger state changes, and once at login, so a profile you pick by hand stays until the next plug or unplug. Change the two profiles in ~/.config/omarchy-kit/power-auto.conf with AC_PROFILE= and BATTERY_PROFILE= (power-saver, balanced or performance). Tested with a simulated charger against the real power daemon (KIT_FAKE_AC=0 power-auto --once); a real unplug has not been tried yet. No root needed. Undo: install-power-auto --remove.",
  "power/power-auto (instalado en ~/.local/bin y ejecutado por el servicio de usuario power-auto.service, 2026-10-07) vigila los eventos de alimentación del sistema: al desenchufar el cargador pone Equilibrado y al enchufarlo pone Rendimiento (antes se quedaba en Rendimiento hasta cambiarlo a mano, lo que gasta una batería de 2014 y calienta el equipo). Solo actúa cuando cambia el estado del cargador, y una vez al iniciar sesión, así que un perfil que elijas a mano se queda hasta el próximo enchufe o desenchufe. Cambia los dos perfiles en ~/.config/omarchy-kit/power-auto.conf con AC_PROFILE= y BATTERY_PROFILE= (power-saver, balanced o performance). Probado con un cargador simulado contra el servicio de energía real (KIT_FAKE_AC=0 power-auto --once); aún no se probó con un desenchufe real. No necesita root. Deshacer: install-power-auto --remove.",
  "~/labspace/omarchy-kit/power/power-auto --status"),
 ("Sleep and the lid", "Reposo y la tapa",
  "sleep/sleep-check reads the system journal (no root) for the last 14 days: every suspend, how long it lasted, whether the lid was involved, and which devices may wake the machine. This MacBook has not suspended once since this install, and XHC1 (the USB controller) and LID0 are both allowed to wake it. The MacBookPro11 family is known to wake right after the lid closes when XHC1 may wake it. Test: close the lid for 30 seconds and open it; the status row above and the Your MacBook page then turn green or red from the real result. If it wakes by itself, the fix is to stop XHC1 from waking the machine (echo XHC1 | sudo tee /proc/acpi/wakeup, made permanent with a small systemd unit); that is deliberately not installed until the test shows it is needed. Nothing on the system was changed for this entry.",
  "sleep/sleep-check lee el registro del sistema (sin root) de los últimos 14 días: cada suspensión, cuánto duró, si intervino la tapa y qué dispositivos pueden despertar el equipo. Esta MacBook no ha suspendido ni una vez desde esta instalación, y tanto XHC1 (el controlador USB) como LID0 pueden despertarla. La familia MacBookPro11 es conocida por despertar justo al cerrar la tapa cuando XHC1 puede despertarla. Prueba: cierra la tapa 30 segundos y ábrela; la fila de estado de arriba y la página Tu MacBook se ponen en verde o rojo según el resultado real. Si despierta sola, la solución es impedir que XHC1 la despierte (echo XHC1 | sudo tee /proc/acpi/wakeup, hecho permanente con una pequeña unidad de systemd); a propósito no se instala hasta que la prueba muestre que hace falta. No se cambió nada del sistema para esta entrada.",
  "~/labspace/omarchy-kit/sleep/sleep-check"),
 ("Auto appearance (light by day, dark at night)", "Apariencia automática (clara de día, oscura de noche)",
  "appearance/auto-appearance, a small script plus a user timer (installed 2026-10-07, OFF), switches the Omarchy theme the way macOS 'Appearance: Auto' does: the white theme from 07:00 and your dark theme (retro-82) from 19:00. The timer checks every 10 minutes and switches only when the day/night period changes, so a theme you pick by hand stays until the next boundary. Settings (themes and times) are in ~/.config/omarchy-kit/appearance.conf; any theme from `omarchy theme list` works, and a period that crosses midnight is handled. Tested: the period logic for every hour including a wrap-around schedule, and one real round trip (Retro 82 → White → Retro 82). It is off because it would change your look twice a day without being asked. Turn on: auto-appearance on. Undo: auto-appearance off, or install-auto-appearance --remove.",
  "appearance/auto-appearance, un pequeño script con un temporizador de usuario (instalado el 2026-10-07, APAGADO), cambia el tema de Omarchy como la 'Apariencia: Automática' de macOS: el tema white desde las 07:00 y tu tema oscuro (retro-82) desde las 19:00. El temporizador revisa cada 10 minutos y cambia solo cuando cambia el periodo día/noche, así que un tema que elijas a mano se queda hasta el próximo límite. Los ajustes (temas y horas) están en ~/.config/omarchy-kit/appearance.conf; sirve cualquier tema de `omarchy theme list` y se maneja un periodo que cruza la medianoche. Probado: la lógica de periodos para cada hora, incluido un horario que cruza la medianoche, y un ciclo real (Retro 82 → White → Retro 82). Está apagado porque cambiaría tu aspecto dos veces al día sin que lo pidieras. Activar: auto-appearance on. Deshacer: auto-appearance off, o install-auto-appearance --remove.",
  "auto-appearance status   # then: auto-appearance on"),
 ("Menu-bar clock with the date", "Reloj de la barra con la fecha",
  "The bar clock now reads 'Wed 7 Oct 15:08' (omarchy bar set omarchy.clock format \"ddd d MMM HH:mm\"), like the macOS menu bar, which also shows the date. It was 'Wednesday 15:08' (24-hour kept, as you had it). Checked on a screenshot of the bar. Backup: ~/.config/omarchy/shell.json.bak-2026-10-07. Undo: omarchy bar set omarchy.clock format \"dddd HH:mm\".",
  "El reloj de la barra ahora dice 'mié 7 oct 15:08' (omarchy bar set omarchy.clock format \"ddd d MMM HH:mm\"), como la barra de menús de macOS, que también muestra la fecha. Antes decía 'miércoles 15:08' (se mantiene el formato de 24 horas que tenías). Comprobado con una captura de la barra. Respaldo: ~/.config/omarchy/shell.json.bak-2026-10-07. Deshacer: omarchy bar set omarchy.clock format \"dddd HH:mm\".",
  "omarchy bar set omarchy.clock format \"dddd HH:mm\"   # undo"),
 ("Optional ⌘ takeovers (W T F S L G P)", "Reemplazos ⌘ opcionales (W T F S L G P)",
  "keys/mackeys.lua can also give ⌘W, ⌘T, ⌘F, ⌘S, ⌘L, ⌘G and ⌘P their Mac meaning in apps, but Omarchy already uses Super+W, T, F, S, L, G and P (close window, float, full screen, scratchpad, layout, grouping, pseudo), so it is OFF until you choose, key by key: keys/mac-key-extras W T F S. For each key you turn on, in apps Super+key sends Ctrl+key; in terminals it keeps its Omarchy meaning; and the Omarchy action stays reachable in every window at Super+Alt+W (close), Super+Alt+T (float), Super+Alt+L (layout), Super+Ctrl+Alt+F (full screen), Super+Ctrl+Alt+S (scratchpad), Super+Ctrl+Alt+G (grouping), Super+Ctrl+Alt+P (pseudo). Tested against a real Brave window in both modes, plus the config-file path and a clean revert (test/verify-mackeys.mjs, 32 checks). Undo: keys/mac-key-extras none.",
  "keys/mackeys.lua también puede dar a ⌘W, ⌘T, ⌘F, ⌘S, ⌘L, ⌘G y ⌘P su significado de Mac en las apps, pero Omarchy ya usa Super+W, T, F, S, L, G y P (cerrar ventana, flotar, pantalla completa, scratchpad, diseño, agrupar, pseudo), así que está APAGADO hasta que elijas, tecla por tecla: keys/mac-key-extras W T F S. Por cada tecla activada, en las apps Super+tecla envía Ctrl+tecla; en terminales conserva su significado de Omarchy; y la acción de Omarchy sigue disponible en cualquier ventana en Super+Alt+W (cerrar), Super+Alt+T (flotar), Super+Alt+L (diseño), Super+Ctrl+Alt+F (pantalla completa), Super+Ctrl+Alt+S (scratchpad), Super+Ctrl+Alt+G (agrupar), Super+Ctrl+Alt+P (pseudo). Probado con una ventana real de Brave en ambos modos, además de la ruta del archivo de configuración y una reversión limpia (test/verify-mackeys.mjs, 32 comprobaciones). Deshacer: keys/mac-key-extras none.",
  "~/labspace/omarchy-kit/keys/mac-key-extras   # show / choose"),
 ("Backups (prepared; needs your password)", "Respaldos (preparados; piden tu contraseña)",
  "Nothing was changed on the system for this entry. backup/install-backups does two things, in one sudo command: (1) a snapper config for /home (it is its own btrfs subvolume, @home) with hourly snapshots kept for 6 hours, 7 days, 2 weeks and 1 month, readable by you without sudo, plus the timeline and cleanup timers (the root config keeps timeline snapshots off, so only /home is affected); (2) Pika Backup (a friendly borg GUI, extra repo, 0.8.4) for the real backup to an external drive, encrypted and scheduled; choosing the drive is the one step that needs you. Snapshots live on the same disk: they undo mistakes and deletions, not a dead disk. The script was checked with bash -n and --dry-run (it prints every command and changes nothing); it could not be run here because it needs root. Undo: sudo install-backups --remove (snapshots already taken stay until deleted).",
  "No se cambió nada en el sistema para esta entrada. backup/install-backups hace dos cosas con un solo comando sudo: (1) una configuración de snapper para /home (es su propio subvolumen btrfs, @home) con instantáneas cada hora que se conservan 6 horas, 7 días, 2 semanas y 1 mes, legibles sin sudo, más los temporizadores de línea de tiempo y limpieza (la configuración de root mantiene apagadas las instantáneas por tiempo, así que solo afecta a /home); (2) Pika Backup (una interfaz amable de borg, repositorio extra, 0.8.4) para el respaldo real en un disco externo, cifrado y programado; elegir el disco es el único paso que te toca. Las instantáneas viven en el mismo disco: deshacen errores y borrados, no un disco dañado. El script se revisó con bash -n y --dry-run (imprime cada comando y no cambia nada); no se pudo ejecutar aquí porque necesita root. Deshacer: sudo install-backups --remove (las instantáneas ya hechas se quedan hasta borrarlas).",
  "~/labspace/omarchy-kit/backup/install-backups --dry-run   # preview, no sudo"),
 ("Top row (F-keys)", "Fila superior (teclas F)",
  "/etc/modprobe.d/hid_apple.conf is set to fnmode=3 (auto): media keys first on this Apple keyboard, Fn for F1–F12. Omarchy's dictation key is now Fn+F9. Undo: set fnmode=2 and run sudo limine-mkinitcpio.",
  "/etc/modprobe.d/hid_apple.conf con fnmode=3 (auto): primero multimedia en este teclado Apple, Fn para F1–F12. El dictado de Omarchy ahora es Fn+F9. Deshacer: fnmode=2 y sudo limine-mkinitcpio.",
  "cat /sys/module/hid_apple/parameters/fnmode"),
 ("Graphics: Intel GPU", "Gráficos: GPU Intel",
  "The NVIDIA GT 750M was driving the screen (CPU 90–95 °C, fans near max) because the firmware routes the panel to it at power-on, so the Intel driver logs 'failed to retrieve link info, disabling eDP'. gpu/switch-to-intel sets Apple's gpu-power-prefs firmware variable to 1 (backup kept in gpu/), effective next boot. Revert: gpu/switch-to-nvidia. Black screen after reboot: hold power to switch off, then power on holding Option+Command+P+R until the second chime (NVRAM reset clears the variable). External monitors are wired to the NVIDIA GPU on this model, so they may need switching back. Confirmed after the 2026-10-05 reboot: Intel drives the screen, CPU ~79 °C, fans ~2700 RPM (were ~5900); the firmware then hides gpu-power-prefs from Linux, which is normal. ~/.config/hypr/gpu.lua (loaded from hyprland.lua; backup hyprland.lua.bak-2026-10-05) makes Hyprland draw only on Intel (AQ_DRM_DEVICES) so the NVIDIA GPU can be powered off; it skips this when an external display is plugged in at login. Undo: delete the require(\"hypr.gpu\") line and log out/in. With Hyprland off the NVIDIA card, vga_switcheroo powers it off (nouveau never suspends it on Macs): CPU 80 → 73 °C and fans 2600 → 2450 RPM within two minutes. nvidia-off.service (gpu/nvidia-off, installed to /usr/local/bin) does this at every boot, skipping it when an external display is connected or anything still uses the card. Undo now: echo ON | sudo tee /sys/kernel/debug/vgaswitcheroo/switch; for good: sudo systemctl disable nvidia-off.service.",
  "La NVIDIA GT 750M controlaba la pantalla (CPU 90–95 °C, ventiladores casi al máximo) porque el firmware le asigna el panel al encender, y el driver Intel registra 'failed to retrieve link info, disabling eDP'. gpu/switch-to-intel pone en 1 la variable de firmware gpu-power-prefs de Apple (respaldo en gpu/), efectivo en el próximo arranque. Revertir: gpu/switch-to-nvidia. Pantalla negra tras reiniciar: mantén el botón de encendido para apagar y enciende con Opción+Comando+P+R hasta el segundo sonido (el reinicio de NVRAM borra la variable). En este modelo los monitores externos van a la GPU NVIDIA; podrían requerir volver a cambiar. Confirmado tras reiniciar el 2026-10-05: Intel controla la pantalla, CPU ~79 °C, ventiladores ~2700 RPM (antes ~5900); después el firmware oculta gpu-power-prefs a Linux, lo cual es normal. ~/.config/hypr/gpu.lua (cargado desde hyprland.lua; respaldo hyprland.lua.bak-2026-10-05) hace que Hyprland dibuje solo en Intel (AQ_DRM_DEVICES) para poder apagar la GPU NVIDIA; no lo hace si hay un monitor externo conectado al iniciar sesión. Revertir: borra la línea require(\"hypr.gpu\") y cierra/abre sesión. Con Hyprland fuera de la tarjeta NVIDIA, vga_switcheroo la apaga (nouveau nunca la suspende en Macs): CPU de 80 a 73 °C y ventiladores de 2600 a 2450 RPM en dos minutos. nvidia-off.service (gpu/nvidia-off, instalado en /usr/local/bin) lo hace en cada arranque, salvo si hay un monitor externo conectado o algo aún usa la tarjeta. Revertir ahora: echo ON | sudo tee /sys/kernel/debug/vgaswitcheroo/switch; definitivamente: sudo systemctl disable nvidia-off.service.",
  "~/labspace/omarchy-kit/gpu/gpu-status"),
 ("FaceTime HD camera", "Cámara FaceTime HD",
  "Installed from the AUR on 2026-10-05: facetimehd-dkms 0.7.2 (driver from github.com/patjak/facetimehd; this release fixes the build on 7.2 kernels), facetimehd-firmware (extracted from a macOS 10.11.5 update on Apple's CDN, checksum-verified) and facetimehd-data (sensor calibration from Apple's Boot Camp 5.1). DKMS rebuilds the module for each kernel and it loads automatically at boot. Test photo taken at 1280×720. Undo: sudo pacman -Rns facetimehd-dkms facetimehd-data facetimehd-firmware.",
  "Instalado desde el AUR el 2026-10-05: facetimehd-dkms 0.7.2 (driver de github.com/patjak/facetimehd; esta versión corrige la compilación en kernels 7.2), facetimehd-firmware (extraído de una actualización de macOS 10.11.5 en el CDN de Apple, con checksum verificado) y facetimehd-data (calibración del sensor de Boot Camp 5.1 de Apple). DKMS recompila el módulo para cada kernel y se carga solo al arrancar. Foto de prueba tomada a 1280×720. Deshacer: sudo pacman -Rns facetimehd-dkms facetimehd-data facetimehd-firmware.",
  "v4l2-ctl --list-devices"),
 ("Audio fidelity", "Fidelidad de audio",
  "PipeWire may switch to 44.1/48/88.2/96/176.4/192 kHz to match the music, resampler quality is 10, and rtkit gives audio threads realtime priority. Files: ~/.config/pipewire/{pipewire,client,pipewire-pulse}.conf.d/. Undo: delete them and restart pipewire.",
  "PipeWire puede cambiar a 44.1/48/88.2/96/176.4/192 kHz según la música, remuestreo en calidad 10, y rtkit da prioridad en tiempo real. Archivos: ~/.config/pipewire/{pipewire,client,pipewire-pulse}.conf.d/. Deshacer: borrarlos y reiniciar pipewire.",
  "systemctl --user restart pipewire pipewire-pulse wireplumber"),
 ("Speaker EQ", "EQ de bocinas",
  "\"MacBook Speakers\" is a gentle voicing: high-pass at 85 Hz, +4 dB at 160 Hz, −2.5 dB at 380 Hz, −1.5 dB at 2.8 kHz, +2 dB shelf at 9 kHz, with −3.6 dB pre-gain so it can't clip. Measured within 0.01 dB of the design. It's installed in Omarchy's tuning layout, and headphones bypass it. Source: omarchy-kit/audio/design_eq.py.",
  "\"MacBook Speakers\" es una ecualización suave: paso alto en 85 Hz, +4 dB en 160 Hz, −2.5 dB en 380 Hz, −1.5 dB en 2.8 kHz, +2 dB en 9 kHz, con −3.6 dB de ganancia previa para no saturar. Medida con 0.01 dB de diferencia del diseño. Instalada al estilo de Omarchy; los audífonos la omiten. Fuente: omarchy-kit/audio/design_eq.py.",
  "~/labspace/omarchy-kit/audio/install-speaker-eq --remove   # undo"),
 ("Boot screen", "Pantalla de arranque",
  "Measured: firmware 6.3 s, Limine 7.7 s (Omarchy leaves Limine's 5 s menu timeout), kernel to disk unlock ~3 s of black before the splash because Plymouth ignores the firmware framebuffer (UseSimpledrm=0) and waits for i915. boot/apply-boot-look sets the Limine menu to 1 s (any key still opens it), a wallpaper in the current theme with the menu semi-transparent at 1440x900, Plymouth UseSimpledrm=1 so the splash appears ~0.5 s into the kernel, and rebuilds with limine-mkinitcpio. The splash itself uses Omarchy's omarchy-plymouth-set-by-theme. The Mac firmware's ~6 s cannot be changed. Backups: /boot/limine.conf.bak-boot-look, /etc/plymouth/plymouthd.conf.bak-boot-look.",
  "Medido: firmware 6.3 s, Limine 7.7 s (Omarchy deja el menú de Limine en 5 s), y del kernel al desbloqueo ~3 s en negro antes del splash porque Plymouth ignora el framebuffer del firmware (UseSimpledrm=0) y espera a i915. boot/apply-boot-look deja el menú de Limine en 1 s (cualquier tecla lo abre), un fondo con el tema actual y el menú semitransparente a 1440x900, Plymouth UseSimpledrm=1 para que el splash aparezca ~0.5 s después de iniciar el kernel, y reconstruye con limine-mkinitcpio. El splash usa omarchy-plymouth-set-by-theme de Omarchy. Los ~6 s del firmware de la Mac no se pueden cambiar. Respaldos: /boot/limine.conf.bak-boot-look, /etc/plymouth/plymouthd.conf.bak-boot-look.",
  "sudo ~/labspace/omarchy-kit/boot/apply-boot-look --undo"),
 ("Retro gaming (RetroArch)", "Juegos retro (RetroArch)",
  "Installed with Omarchy's RetroArch installer, then tuned from benchmarks at 2880×1800 (60 fps needed): crt-royale, Omarchy's default CRT filter, ran at 45 fps, so the global filter is zfast-crt (558 fps); 2D consoles use crt-hyllian-fast (272 fps); Game Boy uses authentic_gbc_fast, GBA agb001, DS/PSP a sharp unfiltered preset. Video driver is OpenGL (glcore): Mesa warns that Haswell Vulkan is incomplete. Integer scaling on. Saves and states moved to ~/Games/saves and ~/Games/states for syncing. Files: ~/.config/retroarch/retroarch.cfg and config/*/*.slangp. Undo: restore retroarch.cfg.bak-2026-10-05 and config/global.slangp.bak-2026-10-05.",
  "Instalado con el instalador de RetroArch de Omarchy y ajustado con mediciones a 2880×1800 (se necesitan 60 fps): crt-royale, el filtro CRT por defecto de Omarchy, daba 45 fps, así que el filtro global es zfast-crt (558 fps); las consolas 2D usan crt-hyllian-fast (272 fps); Game Boy usa authentic_gbc_fast, GBA agb001, DS/PSP un preset nítido sin filtro. El driver de video es OpenGL (glcore): Mesa advierte que Vulkan en Haswell está incompleto. Escalado entero activado. Partidas y estados movidos a ~/Games/saves y ~/Games/states para sincronizar. Archivos: ~/.config/retroarch/retroarch.cfg y config/*/*.slangp. Deshacer: restaurar retroarch.cfg.bak-2026-10-05 y config/global.slangp.bak-2026-10-05.",
  "cp ~/.config/retroarch/retroarch.cfg.bak-2026-10-05 ~/.config/retroarch/retroarch.cfg   # undo"),
 ("Retro library, controller and latency", "Biblioteca retro, control y latencia",
  "games/kit-games keeps ~/Games/roms/<console> organised: one RetroArch playlist per console pinned to the best core here, box art from libretro's thumbnail server, and a budget fixed at half the free disk (231 GB) with a plan of ~205 GB: full top 100 for cartridge consoles, PlayStation and Dreamcast; curated sets for Sega CD, PC Engine CD, Saturn and GameCube. PS4 controller hotkeys: PS = menu, Share+R1/L1 save/load state, Share+R2 fast-forward, Share+L2 rewind, Share+Options quit. 2D consoles use 1 frame of run-ahead (removes built-in input lag) and rewind; PS1 at 2x with PGXP, N64 at 960x720 (GLideN64), Dreamcast at 1280x960. Measured: Cave Story (Mega Drive) 202 fps and Mesen 123 fps with everything on. Undo: delete ~/.config/retroarch/config/*/*.cfg and *.opt.",
  "games/kit-games mantiene ordenado ~/Games/roms/<consola>: una lista de RetroArch por consola con el mejor núcleo para esta máquina, carátulas del servidor de libretro y un presupuesto fijo de la mitad del disco libre (231 GB) con un plan de ~205 GB: top 100 completo para consolas de cartucho, PlayStation y Dreamcast; selecciones para Sega CD, PC Engine CD, Saturn y GameCube. Atajos del control de PS4: PS = menú, Share+R1/L1 guardar/cargar estado, Share+R2 avance rápido, Share+L2 rebobinar, Share+Options salir. Las consolas 2D usan 1 cuadro de run-ahead (quita el retraso de entrada original) y rebobinado; PS1 a 2x con PGXP, N64 a 960x720 (GLideN64), Dreamcast a 1280x960. Medido: Cave Story (Mega Drive) 202 fps y Mesen 123 fps con todo activado. Deshacer: borrar ~/.config/retroarch/config/*/*.cfg y *.opt.",
  "~/labspace/omarchy-kit/games/kit-games budget"),
 ("GameCube (Dolphin)", "GameCube (Dolphin)",
  "Benchmarked 2026-10-05 with Retro League GX (an MIT-licensed 3D GameCube homebrew, 3v3 with bots), since no commercial dump is here yet. Standalone Dolphin beats the RetroArch core here: the core can't open the shared OpenGL context Dolphin compiles shaders on, so it stutters on new effects. Uncapped OpenGL: 1x 196 fps, 2x 143, 3x 86 (at 3x the CPU drops to 1.1 GHz because the Iris Pro takes the shared power budget). Vulkan works but is slower (171) and Mesa calls Haswell Vulkan incomplete. Hybrid ubershaders keep the slowest 1% of frames at 80 fps, against 57 for 'skip drawing'. At real speed in fullscreen, 1x and 2x both hold 60.0 fps with 0–0.1% late frames; 2x reaches ~90 °C after a minute and 1x ~85 °C, both without throttling. Chosen: OpenGL, 2x (1280×1056), hybrid ubershaders, VSync, fullscreen. Port 1: PS4 controller (Cross = A, Square = B, Circle = X, Triangle = Y, R1 = Z) and keyboard (X/Z/C/S, D = Z, Q/W = L/R, arrows = stick and D-pad, Return = Start). Hotkeys like RetroArch: Share+Options or Escape quits, Share+R1/F1 save, Share+L1/F2 load, PS or P pauses. Memory cards in ~/Games/saves/dolphin-standalone, states in ~/Games/states/dolphin-standalone. ES-DE launches GameCube games with it. Written by games/kit-games dolphin to ~/.config/dolphin-emu. If a heavy game stutters, set Graphics → Internal Resolution to Native for that game. Undo: rm -r ~/.config/dolphin-emu (Dolphin's defaults) and re-run kit-games esde.",
  "Medido el 2026-10-05 con Retro League GX (homebrew 3D de GameCube con licencia MIT, 3 contra 3 con bots), porque aún no hay copias de juegos comerciales. Dolphin independiente supera al núcleo de RetroArch aquí: el núcleo no puede abrir el contexto OpenGL compartido donde Dolphin compila shaders, así que se traba con efectos nuevos. Sin límite, OpenGL: 1x 196 fps, 2x 143, 3x 86 (a 3x la CPU baja a 1.1 GHz porque la Iris Pro se lleva el presupuesto de energía compartido). Vulkan funciona pero es más lento (171) y Mesa dice que Vulkan en Haswell está incompleto. Los ubershaders híbridos mantienen el 1% más lento en 80 fps, contra 57 con 'omitir dibujo'. A velocidad real en pantalla completa, 1x y 2x sostienen 60.0 fps con 0–0.1% de cuadros tardíos; 2x llega a ~90 °C tras un minuto y 1x a ~85 °C, ambos sin bajar la frecuencia. Elegido: OpenGL, 2x (1280×1056), ubershaders híbridos, VSync, pantalla completa. Puerto 1: control de PS4 (Cruz = A, Cuadrado = B, Círculo = X, Triángulo = Y, R1 = Z) y teclado (X/Z/C/S, D = Z, Q/W = L/R, flechas = palanca y cruceta, Return = Start). Atajos como en RetroArch: Share+Options o Escape sale, Share+R1/F1 guarda, Share+L1/F2 carga, PS o P pausa. Tarjetas de memoria en ~/Games/saves/dolphin-standalone, estados en ~/Games/states/dolphin-standalone. ES-DE abre los juegos de GameCube con él. Lo escribe games/kit-games dolphin en ~/.config/dolphin-emu. Si un juego pesado se traba, pon Gráficos → Resolución interna en Nativa para ese juego. Deshacer: rm -r ~/.config/dolphin-emu (valores de Dolphin) y volver a correr kit-games esde.",
  "~/labspace/omarchy-kit/games/kit-games dolphin"),
 ("Co-admin", "Co-administración",
  f"Plan for {CO_NAME} (username {CO_USER}): a wheel member with a sudo password and a private home; Omarchy finishes their setup on first login; the login screen is shown at boot; {CO_FIRST} gets their own LUKS passphrase. The temporary password was given in chat and is not stored here. {CO_FIRST} should run passwd right after their first login.",
  f"Plan para {CO_NAME} (usuario {CO_USER}): miembro de wheel con contraseña para sudo y carpeta privada; Omarchy termina su configuración al primer inicio; pantalla de inicio al arrancar; frase LUKS propia. La contraseña temporal se dio en el chat y no se guarda aquí. {CO_FIRST_ES} debe ejecutar passwd tras su primer inicio.",
  f"passwd   # {CO_FIRST}, first thing after logging in"),
]

ISSUES = [
 ("Accents still use the old layout after editing input.lua", "Los acentos usan la distribución anterior tras editar input.lua",
  "fcitx5, the input method Omarchy runs, copies the keyboard layout only when it starts. After changing kb_variant or kb_layout in input.lua and running hyprctl reload, restart it with: fcitx5 --disable notificationitem -r -d (or log out and in). Symptom: apps keep typing with the previous layout. The status row 'Accents on the right Option key' warns when this happens.",
  "fcitx5, el método de entrada que usa Omarchy, copia la distribución del teclado solo al arrancar. Tras cambiar kb_variant o kb_layout en input.lua y correr hyprctl reload, reinícialo con: fcitx5 --disable notificationitem -r -d (o cierra y abre sesión). Síntoma: las apps siguen escribiendo con la distribución anterior. La fila de estado 'Acentos en la tecla Option derecha' avisa cuando pasa.")  ,
 ("Harmless graphics warning", "Advertencia gráfica inofensiva",
  "The kernel log may show an i915 'hsw_enable_pc8' warning. It's a known Intel Haswell power-saving message on 2014 MacBooks and the system keeps running.",
  "El registro del kernel puede mostrar una advertencia i915 'hsw_enable_pc8'. Es un mensaje conocido de ahorro de energía en Haswell (MacBook 2014); el sistema sigue funcionando."),
 ("EQ process killed while audio plays", "Proceso del EQ terminado al sonar audio",
  "Fixed: through the desktop portal, the EQ host got a 0 µs realtime budget and the kernel killed it during playback. It now asks RTKit directly (rtportal.enabled = false), like pipewire-pulse. WirePlumber has the same 0 budget but does little realtime work; look there if audio ever drops out completely.",
  "Resuelto: vía el portal, el EQ recibía 0 µs de tiempo real y el kernel lo terminaba al reproducir. Ahora usa RTKit directamente (rtportal.enabled = false), como pipewire-pulse. WirePlumber tiene el mismo 0 pero casi no trabaja en tiempo real; revisar ahí si el audio se corta por completo."),
 ("3D pages and the GPU", "Páginas 3D y la GPU",
  "Brave's GPU compositor mis-culls small tilted layers, so keys are painted onto the deck instead of being 3D boxes. Don't change that back; test/sweep.mjs checks 42 camera angles.",
  "El compositor GPU de Brave descarta mal capas pequeñas inclinadas, por eso las teclas se pintan sobre el chasis y no son cajas 3D. No revertirlo; test/sweep.mjs revisa 42 ángulos."),
]


# What is waiting, and on whom. kind: you = needs your hands · sudo = needs your password · decision = yours to make · optional
TODO = [
 ("you", "Close the lid once", "Cierra la tapa una vez",
  "This MacBook has never suspended since the install, so sleep is untested. Close the lid for 30 seconds, open it, then run the command: the Sleep row above and the Your MacBook page turn green or red from the real result. If it wakes by itself, tell Claude: the fix (stop the USB controller XHC1 from waking it) is known and ready to write.",
  "Esta MacBook no ha suspendido ni una vez desde la instalación, así que el reposo no está probado. Cierra la tapa 30 segundos, ábrela y corre el comando: la fila Reposo de arriba y la página Tu MacBook se ponen en verde o rojo según el resultado real. Si despierta sola, avisa a Claude: la solución (impedir que el controlador USB XHC1 la despierte) se conoce y está lista para escribirse.",
  "~/labspace/omarchy-kit/sleep/sleep-check"),
 ("you", "Feel the keyboard and trackpad changes", "Prueba con tus manos el teclado y el trackpad",
  "Accents on the right Option key, the ⌘ shortcuts and the trackpad gestures were verified in software and in a real Brave window, not with physical fingers. The Learn lessons 'Typing Spanish', 'Your ⌘ shortcuts inside apps' and 'Trackpad gestures' check them with your own keys. If a key does the wrong thing, say which.",
  "Los acentos en la tecla Option derecha, los atajos ⌘ y los gestos del trackpad se verificaron en software y en una ventana real de Brave, no con dedos de verdad. Las lecciones de Aprender 'Escribir en español', 'Tus atajos ⌘ dentro de las apps' y 'Gestos del trackpad' los comprueban con tus propias teclas. Si una tecla hace algo mal, di cuál.",
  ""),
 ("you", "Unplug the charger once", "Desenchufa el cargador una vez",
  "The automatic power profile was tested against a simulated charger, not a real unplug. Unplug, wait two seconds, run the command (expect profile: balanced), plug in again (expect performance).",
  "El perfil de energía automático se probó con un cargador simulado, no con un desenchufe real. Desenchufa, espera dos segundos, corre el comando (debe decir profile: balanced), vuelve a enchufar (debe decir performance).",
  "~/labspace/omarchy-kit/power/power-auto --status"),
 ("sudo", "Set up backups", "Configura los respaldos",
  "One command (preview it first with --dry-run): hourly snapshots of /home and Pika Backup. Then open Pika Backup and pick an external drive for the real backup, since snapshots on the same disk do not survive a dead disk. Tip: leave ~/Games out of the backup if the library can be rebuilt.",
  "Un comando (míralo antes con --dry-run): instantáneas de /home cada hora y Pika Backup. Luego abre Pika Backup y elige un disco externo para el respaldo real, porque las instantáneas en el mismo disco no sobreviven a un disco dañado. Consejo: deja ~/Games fuera del respaldo si la biblioteca se puede reconstruir.",
  "sudo ~/labspace/omarchy-kit/backup/install-backups"),
 ("decision", "Which ⌘ keys should replace Omarchy's Super keys in apps?", "¿Qué teclas ⌘ deben reemplazar a las Super de Omarchy en las apps?",
  "Recommended: ⌘W, ⌘T, ⌘F and ⌘S (close tab, new tab, find, save: the four you would miss most). The price: in apps (never in terminals) Omarchy's close window, float toggle, full screen and scratchpad move to Super+Alt+W, Super+Alt+T, Super+Ctrl+Alt+F and Super+Ctrl+Alt+S, and your 4-finger-down gesture still toggles the scratchpad. ⌘L, ⌘G and ⌘P are rarer (address bar, find next, print) and cost the workspace layout, grouping and pseudo-tiling. Everything is built, tested and reversible: it only needs your choice.",
  "Recomendado: ⌘W, ⌘T, ⌘F y ⌘S (cerrar pestaña, pestaña nueva, buscar, guardar: las cuatro que más echarías de menos). El precio: en las apps (nunca en terminales) cerrar ventana, alternar flotante, pantalla completa y scratchpad de Omarchy pasan a Super+Alt+W, Super+Alt+T, Super+Ctrl+Alt+F y Super+Ctrl+Alt+S, y tu gesto de 4 dedos hacia abajo sigue mostrando el scratchpad. ⌘L, ⌘G y ⌘P son menos frecuentes (barra de direcciones, buscar siguiente, imprimir) y cuestan el diseño del espacio, la agrupación y el pseudo-mosaico. Todo está construido, probado y es reversible: solo falta tu elección.",
  "~/labspace/omarchy-kit/keys/mac-key-extras W T F S"),
 ("optional", "Turn on Auto appearance", "Activa la apariencia automática",
  "Light theme (white) from 07:00 and your dark theme from 19:00, like macOS Auto. Installed but off, because it changes your look twice a day. Change the themes or hours in ~/.config/omarchy-kit/appearance.conf first if you like.",
  "Tema claro (white) desde las 07:00 y tu tema oscuro desde las 19:00, como la apariencia Automática de macOS. Instalada pero apagada, porque cambia tu aspecto dos veces al día. Si quieres, cambia antes los temas u horas en ~/.config/omarchy-kit/appearance.conf.",
  "auto-appearance on"),
 ("optional", "A Dock?", "¿Un Dock?",
  "Not installed: a dock fights the tiling idea and the Omarchy menu already launches apps. If you miss seeing what is running at a glance, ask Claude to build and test one (nwg-dock-hyprland 0.4.11 is in the extra repo; installing needs sudo). Not built on a guess.",
  "No instalado: un dock choca con la idea del mosaico y el menú de Omarchy ya abre apps. Si echas de menos ver de un vistazo lo que está abierto, pide a Claude que lo construya y pruebe (nwg-dock-hyprland 0.4.11 está en el repositorio extra; instalarlo requiere sudo). No se construyó a ciegas.",
  ""),
 ("you", "External display and SD card", "Monitor externo y tarjeta SD",
  "Both are detected but untested (see Your MacBook). Plug a monitor in BEFORE logging in so Hyprland can use it; the NVIDIA GPU then stays on.",
  "Ambos se detectan pero no se han probado (ver Tu MacBook). Conecta el monitor ANTES de iniciar sesión para que Hyprland lo use; la GPU NVIDIA se queda entonces encendida.",
  ""),
]

# Looked at and deliberately left alone, so the work is not repeated.
SKIPPED = [
 ("System font (San Francisco look)", "Fuente del sistema (aspecto San Francisco)",
  "Tested in a real Brave and reverted. GTK apps and system-ui pages already use Adwaita Sans (GNOME's UI font, derived from Inter, the closest free relative of San Francisco). The stack most sites use (-apple-system, BlinkMacSystemFont) falls through to Liberation Sans, and fontconfig cannot change that in Chromium: it ignores fontconfig substitutes that are not metric-compatible. The generic sans-serif is Omarchy's deliberate Liberation Sans default (/etc/fonts/conf.d/50-omarchy.conf), which its own tools may rely on, so it was not overridden. Nothing was installed.",
  "Probado en un Brave real y revertido. Las apps GTK y las páginas con system-ui ya usan Adwaita Sans (la fuente de GNOME, derivada de Inter, el pariente libre más cercano de San Francisco). La pila que usan la mayoría de sitios (-apple-system, BlinkMacSystemFont) cae en Liberation Sans, y fontconfig no puede cambiarlo en Chromium: ignora sustitutos de fontconfig que no sean compatibles en métricas. El genérico sans-serif es el Liberation Sans que Omarchy elige a propósito (/etc/fonts/conf.d/50-omarchy.conf), del que sus herramientas pueden depender, así que no se sobrescribió. No se instaló nada."),
 ("Optimized Battery Charging (80% limit)", "Carga optimizada de batería (límite del 80 %)",
  "Not possible on this MacBook: the battery exposes no charge-limit control to Linux (no charge_control_end_threshold in /sys/class/power_supply/BAT0). The battery is already at about 75% of its original capacity.",
  "No es posible en esta MacBook: la batería no expone a Linux ningún control de límite de carga (no hay charge_control_end_threshold en /sys/class/power_supply/BAT0). La batería ya conserva cerca del 75 % de su capacidad original."),
 ("Press-and-hold accent picker", "Selector de acentos al mantener pulsada una tecla",
  "Wayland has no equivalent for apps in general. The right Option key (⌥e e, ⌥n n) covers the same need, and Caps Lock is a second way (Compose).",
  "Wayland no tiene un equivalente general para las apps. La tecla Option derecha (⌥e e, ⌥n n) cubre la misma necesidad, y Bloq Mayús es una segunda forma (Compose)."),
 ("Keyboard repeat speed", "Velocidad de repetición del teclado",
  "Currently 40 characters per second after 250 ms (Hyprland's input defaults). Not compared with your Mac's setting, which is not known here: tune repeat_rate and repeat_delay in input.lua if it feels different.",
  "Ahora son 40 caracteres por segundo tras 250 ms (valores por defecto de Hyprland). No se comparó con el ajuste de tu Mac, que aquí no se conoce: ajusta repeat_rate y repeat_delay en input.lua si se siente distinto."),
]


def build():
    data = {"checks": checks(), "status": STATUS, "log": LOG, "issues": ISSUES, "todo": TODO, "skipped": SKIPPED,
            "built": sh("date", "+%Y-%m-%d %H:%M")}
    tpl = (HERE / "setup.template.html").read_text()
    out = tpl.replace("/*__DATA__*/{}", json.dumps(data, ensure_ascii=False).replace("</", "<\\/"))
    (HERE / "setup.html").write_text(out)
    return out


if __name__ == "__main__":
    build()
    print("wrote setup.html")
