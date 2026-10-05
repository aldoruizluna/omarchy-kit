#!/usr/bin/env python3
"""Build setup.html — the machine's setup log and admin handbook (EN/ES).

Every status line is checked live against the system when this runs (no sudo needed), so the page
never claims something is done that isn't. The helper re-runs this on each visit to /setup.
Passwords and passphrases are never written here.
"""
import grp, json, os, pwd, re, stat, subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
HOME = Path.home()

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
    c["gestures"] = ("ok" if 'hl.gesture({ fingers = 3, direction = "horizontal"' in i and "natural_scroll = true" in i else "action", "input.lua")
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
  "Omarchy Kit is a bilingual course built from this machine. Start, Learn (24 hands-on lessons that check your real desktop through the local service), From macOS (41 habits translated), Your MacBook (verified hardware status with live readings), Reference (all 367 Omarchy commands, the full menu with 'Show me' buttons, themes, glossary), plus the 3D keyboard and trackpad, Apps and this log. Shortcuts are read from your live config, so the pages follow your changes after a rebuild.",
  "Omarchy Kit es un curso bilingüe hecho con esta máquina. Inicio, Aprender (24 lecciones prácticas que comprueban tu escritorio real vía el servicio local), Desde macOS (41 hábitos traducidos), Tu MacBook (estado verificado del hardware con lecturas en vivo), Referencia (los 367 comandos de Omarchy, el menú completo con botones 'Muéstrame', temas, glosario), más el teclado y trackpad 3D, Apps y esta bitácora. Los atajos se leen de tu configuración real, así que las páginas siguen tus cambios tras reconstruir.",
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
  "macOS-style gestures in ~/.config/hypr/input.lua: 3 or 4 fingers left/right switch spaces, 4 fingers up opens the Omarchy menu, 4 down toggles the scratchpad, 4-finger pinch opens the apps menu. Natural scrolling is on. Undo: restore input.lua.bak-2026-10-04.",
  "Gestos estilo macOS en ~/.config/hypr/input.lua: 3 o 4 dedos izquierda/derecha cambian de espacio, 4 arriba abre el menú de Omarchy, 4 abajo el scratchpad, pellizco con 4 dedos abre el menú de apps. Desplazamiento natural activado. Deshacer: restaurar input.lua.bak-2026-10-04.",
  ""),
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
 ("Co-admin", "Co-administración",
  f"Plan for {CO_NAME} (username {CO_USER}): a wheel member with a sudo password and a private home; Omarchy finishes their setup on first login; the login screen is shown at boot; {CO_FIRST} gets their own LUKS passphrase. The temporary password was given in chat and is not stored here. {CO_FIRST} should run passwd right after their first login.",
  f"Plan para {CO_NAME} (usuario {CO_USER}): miembro de wheel con contraseña para sudo y carpeta privada; Omarchy termina su configuración al primer inicio; pantalla de inicio al arrancar; frase LUKS propia. La contraseña temporal se dio en el chat y no se guarda aquí. {CO_FIRST_ES} debe ejecutar passwd tras su primer inicio.",
  f"passwd   # {CO_FIRST}, first thing after logging in"),
]

ISSUES = [
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


def build():
    data = {"checks": checks(), "status": STATUS, "log": LOG, "issues": ISSUES,
            "built": sh("date", "+%Y-%m-%d %H:%M")}
    tpl = (HERE / "setup.template.html").read_text()
    out = tpl.replace("/*__DATA__*/{}", json.dumps(data, ensure_ascii=False).replace("</", "<\\/"))
    (HERE / "setup.html").write_text(out)
    return out


if __name__ == "__main__":
    build()
    print("wrote setup.html")
