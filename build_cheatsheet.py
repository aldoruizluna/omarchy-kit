#!/usr/bin/env python3
"""Build cheatsheet.html (ES/EN) from the live Omarchy keybindings.
Usage: python3 build_cheatsheet.py   (re-run after changing your bindings)"""
import json, re, subprocess, pathlib

HERE = pathlib.Path(__file__).parent
try:
    raw = subprocess.run(["omarchy", "menu", "keybindings", "--print"],
                         capture_output=True, text=True, check=True).stdout
    (HERE / "bindings.snapshot.txt").write_text(raw)
except Exception:
    raw = (HERE / "bindings.snapshot.txt").read_text()

# ---- Spanish translations of binding descriptions ({n} = collapsed number) ----
ES = {
 "Keybindings":"Atajos de teclado","Omarchy menu":"Menú de Omarchy","Terminal":"Terminal",
 "Browser":"Navegador","File manager":"Administrador de archivos","System menu":"Menú del sistema",
 "Theme menu":"Menú de temas","Full screen":"Pantalla completa","Full width":"Ancho completo",
 "Close window":"Cerrar ventana","Close all windows":"Cerrar todas las ventanas","Lock system":"Bloquear sistema",
 "Toggle window floating/tiling":"Alternar ventana flotante/mosaico","Toggle window split":"Alternar división de ventana",
 "Pop window out (float & pin)":"Sacar ventana (flotante y fija)","Universal copy":"Copiar (universal)",
 "Universal paste":"Pegar (universal)","Universal cut":"Cortar (universal)","Clipboard manager":"Gestor del portapapeles",
 "Emojis":"Emojis","Color picker":"Selector de color","Screenshot":"Captura de pantalla","Screenrecording":"Grabar pantalla",
 "Tmux":"Tmux","Herdr":"Herdr","Browser (private)":"Navegador (privado)","File manager (cwd)":"Administrador de archivos (carpeta actual)",
 "Switch to workspace {n}":"Ir al espacio de trabajo {n}","Former workspace":"Espacio de trabajo anterior (alternar)",
 "Previous workspace":"Espacio de trabajo previo","Next workspace":"Espacio de trabajo siguiente",
 "Move window to workspace {n}":"Mover ventana al espacio {n}","Move window silently to workspace {n}":"Mover ventana al espacio {n} sin seguirla",
 "Swap window down":"Intercambiar ventana abajo","Swap window to the left":"Intercambiar ventana a la izquierda",
 "Swap window to the right":"Intercambiar ventana a la derecha","Swap window up":"Intercambiar ventana arriba",
 "Focus on next window":"Enfocar ventana siguiente","Focus on next monitor":"Enfocar monitor siguiente",
 "Focus on previous window":"Enfocar ventana previa","Focus on previous monitor":"Enfocar monitor previo",
 "Focus on below window":"Enfocar ventana de abajo","Focus on left window":"Enfocar ventana de la izquierda",
 "Focus on right window":"Enfocar ventana de la derecha","Focus on above window":"Enfocar ventana de arriba",
 "Move window":"Mover ventana","Resize window":"Redimensionar ventana",
 "Expand window left a little":"Expandir ventana a la izquierda (poco)","Expand window left a lot":"Expandir ventana a la izquierda (mucho)",
 "Expand window left":"Expandir ventana a la izquierda","Expand window down a little":"Expandir ventana hacia abajo (poco)",
 "Expand window down a lot":"Expandir ventana hacia abajo (mucho)","Expand window down":"Expandir ventana hacia abajo",
 "Shrink window left a little":"Reducir ventana desde la izquierda (poco)","Shrink window left a lot":"Reducir ventana desde la izquierda (mucho)",
 "Shrink window left":"Reducir ventana desde la izquierda","Shrink window up a little":"Reducir ventana desde arriba (poco)",
 "Shrink window up a lot":"Reducir ventana desde arriba (mucho)","Shrink window up":"Reducir ventana desde arriba",
 "Move window to scratchpad":"Mover ventana al scratchpad","Toggle scratchpad":"Mostrar/ocultar scratchpad",
 "Invoke last notification":"Invocar última notificación","Dismiss last notification":"Descartar última notificación",
 "Toggle silencing notifications":"Silenciar/activar notificaciones","Open notification history":"Abrir historial de notificaciones",
 "Dismiss all notifications":"Descartar todas las notificaciones","Toggle window transparency":"Alternar transparencia de ventana",
 "Toggle nightlight":"Alternar luz nocturna","Toggle locking on idle":"Alternar bloqueo por inactividad",
 "Start dictation (push-to-talk)":"Iniciar dictado (pulsar para hablar)","Stop dictation (push-to-talk)":"Detener dictado (pulsar para hablar)",
 "Download Video from Web App":"Descargar video desde la webapp","Copy URL from Web App":"Copiar URL desde la webapp",
 "Make webcam overlay smaller":"Reducir superposición de webcam","Make webcam overlay larger":"Agrandar superposición de webcam",
 "Save window width":"Guardar ancho de ventana","Monitor scaling down":"Reducir escala del monitor","Apps menu":"Menú de aplicaciones",
 "Bar panel {n}":"Panel {n} de la barra","Audio":"Audio","Show battery remaining":"Mostrar batería restante","Calendar":"Calendario",
 "Toggle laptop display mirroring":"Alternar duplicado de pantalla del portátil","Show reminders":"Mostrar recordatorios",
 "Show time":"Mostrar la hora","Toggle weather":"Alternar clima","Reset zoom":"Restablecer zoom",
 "Toggle single-window square aspect":"Alternar aspecto cuadrado de ventana única","Bluetooth":"Bluetooth","Capture menu":"Menú de captura",
 "Display":"Pantalla","Toggle laptop display":"Alternar pantalla del portátil","Tiled full screen":"Pantalla completa en mosaico",
 "Hardware menu":"Menú de hardware","Toggle menu":"Menú de alternancias","Transcode":"Transcodificar","Power":"Energía",
 "Extract text (OCR) from screenshot":"Extraer texto (OCR) de captura","Calculator":"Calculadora","Set reminder":"Crear recordatorio",
 "Background switcher":"Cambiar fondo de pantalla","Share":"Compartir","Network":"Red","Activity":"Actividad (monitor del sistema)",
 "Toggle dictation":"Alternar dictado","Zoom in":"Acercar zoom","Restore window width":"Restaurar ancho de ventana",
 "Toggle workspace layout":"Alternar diseño del espacio de trabajo","Pseudo window":"Ventana pseudo-mosaico",
 "ChatGPT":"ChatGPT","Grok":"Grok","Move workspace to down monitor":"Mover espacio al monitor de abajo",
 "New email":"Correo nuevo","WhatsApp":"WhatsApp","Move workspace to left monitor":"Mover espacio al monitor izquierdo",
 "Music TUI":"Música (terminal)","Move workspace to right monitor":"Mover espacio al monitor derecho",
 "Move workspace to up monitor":"Mover espacio al monitor de arriba","X Post":"Publicar en X","Toggle window gaps":"Alternar márgenes entre ventanas",
 "Agent":"Agente","Google Messages":"Mensajes de Google","Clear reminders":"Borrar recordatorios","Docker":"Docker","Email":"Correo",
 "Signal":"Signal","Music":"Música","Editor":"Editor","Obsidian":"Obsidian","Google Photos":"Google Fotos","Google Maps":"Google Maps",
 "Passwords":"Contraseñas","Toggle top bar":"Mostrar/ocultar barra superior","Omawrite":"Omawrite","X":"X","YouTube":"YouTube",
 "Monitor scaling up":"Aumentar escala del monitor","Switch to group window {n}":"Ir a la ventana {n} del grupo",
 "Move window to group on bottom":"Mover ventana al grupo de abajo","Move active window out of group":"Sacar ventana activa del grupo",
 "Move window to group on left":"Mover ventana al grupo de la izquierda","Next window in group":"Siguiente ventana del grupo",
 "Previous window in group":"Ventana previa del grupo","Move window to group on right":"Mover ventana al grupo de la derecha",
 "Move window to group on top":"Mover ventana al grupo de arriba","Move grouped window focus left":"Mover foco de grupo a la izquierda",
 "Move grouped window focus right":"Mover foco de grupo a la derecha","Toggle window grouping":"Alternar agrupación de ventanas",
 "Scroll active workspace forward":"Avanzar espacio de trabajo (rueda)","Scroll active workspace backward":"Retroceder espacio de trabajo (rueda)",
 "Reveal active window on top":"Mostrar ventana activa al frente","Volume down precise":"Bajar volumen (preciso)",
 "Next track":"Pista siguiente","Volume up precise":"Subir volumen (preciso)","Brightness down precise":"Bajar brillo (preciso)",
 "Brightness up precise":"Subir brillo (preciso)",
 "Previous track":"Pista anterior","Switch audio output":"Cambiar salida de audio","Switch media source":"Cambiar fuente multimedia",
 "Brightness minimum":"Brillo mínimo","Brightness maximum":"Brillo máximo","Volume down":"Bajar volumen","Mute microphone":"Silenciar micrófono",
 "Mute":"Silenciar","Pause":"Pausa","Play":"Reproducir","Volume up":"Subir volumen","Eject media":"Expulsar medio",
 "Keyboard brightness down":"Bajar brillo del teclado","Keyboard brightness up":"Subir brillo del teclado",
 "Keyboard backlight cycle":"Alternar retroiluminación del teclado","Brightness down":"Bajar brillo","Brightness up":"Subir brillo",
 "Power menu":"Menú de energía","Disable touchpad":"Desactivar touchpad","Enable touchpad":"Activar touchpad","Toggle touchpad":"Alternar touchpad",
 "Tmux keybindings":"Atajos de Tmux","Herdr keybindings":"Atajos de Herdr",
 # Mac ⌘ shortcuts (keys/mackeys.lua)
 "Select all (⌘A)":"Seleccionar todo (⌘A)","Undo (⌘Z)":"Deshacer (⌘Z)","Redo (⇧⌘Z)":"Rehacer (⇧⌘Z)",
 "Reload (⌘R)":"Recargar (⌘R)","Hard reload (⇧⌘R)":"Recarga completa (⇧⌘R)","New window (⌘N)":"Ventana nueva (⌘N)",
 "Reopen closed tab (⇧⌘T)":"Reabrir pestaña cerrada (⇧⌘T)","Bookmark page (⌘D)":"Guardar en marcadores (⌘D)",
 "Bold (⌘B)":"Negrita (⌘B)","Italic (⌘I)":"Cursiva (⌘I)","Underline (⌘U)":"Subrayado (⌘U)",
 "Back (⌘[)":"Atrás (⌘[)","Forward (⌘])":"Adelante (⌘])",
 # optional takeovers (keys/mac-key-extras) and the Omarchy actions they displace
 "Close tab or window (⌘W)":"Cerrar pestaña o ventana (⌘W)","New tab (⌘T)":"Pestaña nueva (⌘T)","Find (⌘F)":"Buscar (⌘F)",
 "Save (⌘S)":"Guardar (⌘S)","Address bar (⌘L)":"Barra de direcciones (⌘L)","Find next (⌘G)":"Buscar siguiente (⌘G)","Print (⌘P)":"Imprimir (⌘P)",
 "Close window (Omarchy, any app)":"Cerrar ventana (Omarchy, cualquier app)",
 "Toggle window floating/tiling (Omarchy, any app)":"Alternar ventana flotante/mosaico (Omarchy, cualquier app)",
 "Full screen (Omarchy, any app)":"Pantalla completa (Omarchy, cualquier app)",
 "Toggle scratchpad (Omarchy, any app)":"Mostrar/ocultar scratchpad (Omarchy, cualquier app)",
 "Toggle workspace layout (Omarchy, any app)":"Alternar diseño del espacio (Omarchy, cualquier app)",
 "Toggle window grouping (Omarchy, any app)":"Alternar agrupación de ventanas (Omarchy, cualquier app)",
 "Pseudo window (Omarchy, any app)":"Ventana pseudo-mosaico (Omarchy, cualquier app)",
}
CATS = [  # (id, EN, ES, regex on description)
 ("mac","Mac ⌘ shortcuts (in apps)","Atajos ⌘ de Mac (en apps)",r"⌘"),
 ("menus","Menus & system","Menús y sistema",r"menu|keybindings|^Keybindings|touchpad|^Lock|^Power|^Network|^Bluetooth|^Audio|^Display|^Activity|^Share|^Transcode|^Calculator|^Toggle (nightlight|locking|weather|dictation)|Bar panel|top bar|^Show |^Calendar|reminder|Background|dictation|Zoom|zoom|Reset zoom|Toggle laptop|laptop display"),
 ("apps","Apps & web apps","Apps y webapps",r"^(Terminal|Browser|File manager|Tmux|Herdr|ChatGPT|Grok|WhatsApp|Signal|Music|Editor|Obsidian|Google|Passwords|Omawrite|X|X Post|YouTube|Email|New email|Docker|Agent|Calendar)"),
 ("workspaces","Workspaces","Espacios de trabajo",r"workspace"),
 ("groups","Window groups","Grupos de ventanas",r"group"),
 ("windows","Windows & tiling","Ventanas y mosaico",r"window|Focus|Full|Pseudo|Close|scratchpad|gaps|split|float|Reveal|transparency|aspect|layout"),
 ("notifs","Notifications","Notificaciones",r"notification"),
 ("capture","Capture & clipboard","Captura y portapapeles",r"Screenshot|Screenrecording|Color|OCR|Clipboard|Universal|Emojis|Capture"),
 ("media","Media, volume, brightness","Multimedia, volumen, brillo",r"Volume|Brightness|brightness|track|webcam|Video|URL|dictation|Mute|Play|Pause|Eject|media|audio output|backlight"),
 ("display","Monitors","Monitores",r"monitor|Monitor|mirroring"),
]
def categorize(d):
    # order matters; first match wins, but apps/captures checked precisely first
    for cid, _, _, rx in [CATS[0], CATS[2], CATS[6], CATS[7], CATS[4], CATS[3], CATS[9], CATS[5], CATS[8], CATS[1]]:
        if re.search(rx, d): return cid
    return "other"

# ---- parse & collapse numbered series ----
rows = {}
RAW = []
for line in raw.splitlines():
    m = re.match(r"^(.*?)\s+(?:\+|→)\s*(.*)$", line) if False else re.match(r"^(.+?)\s{2,}→\s+(.*)$", line)
    if not m: continue
    keyspec, desc = m.group(1).strip(), m.group(2).strip()
    if " + " in keyspec: mods, key = keyspec.rsplit(" + ", 1)
    else: mods, key = "", keyspec
    mods = mods.split()
    nm = re.search(r"(\d+)$", desc)
    _t = (desc[:nm.start()] + "{n}") if (nm and re.fullmatch(r"\d", key)) else desc
    _n = nm.group(1) if (nm and re.fullmatch(r"\d", key)) else ""
    RAW.append({"mods": mods, "key": key, "en": desc,
                "es": ES.get(_t, desc).replace("{n}", _n), "cat": categorize(_t)})
    if nm and re.fullmatch(r"\d", key):
        tmpl = desc[:nm.start()] + "{n}"
        rows.setdefault((tuple(mods), tmpl), []).append(key)
    else:
        rows.setdefault((tuple(mods), key, desc), [None])
out = {}
for k, v in rows.items():
    if len(k) == 2:
        mods, tmpl = k; digits = sorted(v, key=lambda x: (x == "0", int(x)))
        key = "1–" + ("9, 0" if "0" in digits else digits[-1]) if len(digits) > 1 else digits[0]
        desc = tmpl
    else:
        mods, key, desc = k
    en = desc.replace("{n}", "N")
    es = ES.get(desc, None)
    if es is None: print("untranslated:", desc); es = en
    es = es.replace("{n}", "N")
    out.setdefault(categorize(desc), []).append(
        {"mods": list(mods), "key": key, "en": en, "es": es})

cats = [{"id": c[0], "en": c[1], "es": c[2], "rows": out.get(c[0], [])} for c in CATS]
if out.get("other"): cats.append({"id": "other", "en": "Other", "es": "Otros", "rows": out["other"]})
cats = [c for c in cats if c["rows"]]
DATA = json.dumps(cats, ensure_ascii=False)
CATLIST = json.dumps([{"id": c["id"], "en": c["en"], "es": c["es"]} for c in cats], ensure_ascii=False)
RAWJ = json.dumps(RAW, ensure_ascii=False)
(HERE / "data").mkdir(exist_ok=True)
(HERE / "data" / "bindings.json").write_text(RAWJ)  # shared with build_portal.py
kt = HERE / "keyboard.template.html"
if kt.exists():
    # fnmode: 1 = media keys first (Mac style); 3 = auto, which is media-first on a real Apple keyboard
    try: fnmode = int(open("/sys/module/hid_apple/parameters/fnmode").read())
    except Exception: fnmode = 2
    media_first = "true" if fnmode in (1, 3) else "false"
    (HERE / "keyboard.html").write_text(kt.read_text().replace("/*__RAW__*/[]", RAWJ).replace("/*__CATS__*/[]", CATLIST).replace("/*__MEDIAFIRST__*/false", media_first))
    print("wrote keyboard.html:", len(RAW), "bindings")
tt = HERE / "trackpad.template.html"
if tt.exists():
    import kitconf
    (HERE / "trackpad.html").write_text(tt.read_text().replace("/*__DRAG3__*/false", "true" if kitconf.three_fingers() == "drag" else "false")); print("wrote trackpad.html")
tpl = (HERE / "cheatsheet.template.html").read_text()
(HERE / "cheatsheet.html").write_text(tpl.replace("/*__DATA__*/[]", DATA))
print("wrote cheatsheet.html:", sum(len(c["rows"]) for c in cats), "entries")

# setup log (live status checks)
import build_setup
build_setup.build(); print("wrote setup.html")

# learning portal (Start, Learn, From macOS, Your MacBook, Reference)
import build_portal
build_portal.build(); print("wrote portal pages")
