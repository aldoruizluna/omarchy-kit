"""Content for the From-macOS, Reference (glossary) and Your-MacBook pages.

Shortcuts are named by Omarchy's binding description ("k"), never hard-coded, so the pages always show
your current keys. "how" says how close the Omarchy way is to the Mac habit:
  same = same muscle memory · similar = same idea, different keys · different = new concept · none = not available
Hardware facts come from a read-only audit of this MacBookPro11,3 (2026-10-04); "status" is honest about
what was verified.
"""

import kitconf
DRAG = kitconf.three_fingers() == "drag"  # three fingers drag instead of swiping spaces (trackpad/three-fingers)

EXTRA_INFO = {  # letter: (Mac action EN, ES, binding description, the Ctrl chord apps expect)
    "W": ("Close tab or window", "Cerrar pestaña o ventana", "Close tab or window (⌘W)", "Ctrl+W"),
    "T": ("New tab", "Pestaña nueva", "New tab (⌘T)", "Ctrl+T"),
    "F": ("Find", "Buscar", "Find (⌘F)", "Ctrl+F"),
    "S": ("Save", "Guardar", "Save (⌘S)", "Ctrl+S"),
    "L": ("Address bar", "Barra de direcciones", "Address bar (⌘L)", "Ctrl+L"),
    "G": ("Find next", "Buscar siguiente", "Find next (⌘G)", "Ctrl+G"),
    "P": ("Print", "Imprimir", "Print (⌘P)", "Ctrl+P"),
}


def extras_rows():
    """The Mac keys Omarchy already uses: shown as mapped for the ones switched on (keys/mac-key-extras), Ctrl for the rest."""
    on = kitconf.mackeys_extra()
    off = [k for k in "WTFSLGP" if k not in on]
    rows = []
    if on:
        rows.append({"mac": {"en": ", ".join(EXTRA_INFO[k][0].lower() for k in on).capitalize(), "es": ", ".join(EXTRA_INFO[k][1].lower() for k in on).capitalize()},
                     "mk": " ".join("⌘" + k for k in on), "how": "same", "k": [EXTRA_INFO[k][2] for k in on],
                     "note": {"en": "You switched these on: in apps, Super+key sends Ctrl+key. In terminals the Omarchy action stays, and everywhere it moved to Super+Alt+key (W, T, L) or Super+Ctrl+Alt+key (F, S, G, P).",
                              "es": "Las activaste: en las apps, Super+tecla envía Ctrl+tecla. En terminales se queda la acción de Omarchy, y en todas partes pasó a Super+Alt+tecla (W, T, L) o Super+Ctrl+Alt+tecla (F, S, G, P)."}})
    if off:
        rows.append({"mac": {"en": ", ".join(EXTRA_INFO[k][0].lower() for k in off).capitalize(), "es": ", ".join(EXTRA_INFO[k][1].lower() for k in off).capitalize()},
                     "mk": " ".join("⌘" + k for k in off), "how": "different", "k": [], "lit": " · ".join(EXTRA_INFO[k][3] for k in off),
                     "note": {"en": "Still Ctrl inside apps: each of these Super keys already runs an Omarchy action (close window, float, full screen, scratchpad, layout, grouping, pseudo-tiling). Turn any of them on, key by key, with keys/mac-key-extras; terminals always keep the Omarchy meaning.",
                              "es": "Siguen siendo Ctrl dentro de las apps: cada una de estas teclas Super ya ejecuta una acción de Omarchy (cerrar ventana, flotar, pantalla completa, scratchpad, diseño, agrupar, pseudo-mosaico). Activa las que quieras, tecla por tecla, con keys/mac-key-extras; las terminales siempre conservan el significado de Omarchy."}})
    return rows


MAC = [
 # (category, mac thing EN/ES, mac keys, how, omarchy keys via binding desc(s) or literal, note EN/ES)
 ("Find & launch", "Buscar y abrir", [
  {"mac": {"en": "Spotlight", "es": "Spotlight"}, "mk": "⌘ Space", "how": "similar", "k": ["Apps menu"],
   "note": {"en": "Type a few letters, press Return. Super+Space opens the Omarchy menu, which has everything else.", "es": "Escribe unas letras y pulsa Return. Super+Space abre el menú de Omarchy, que tiene todo lo demás."}},
  {"mac": {"en": "Launchpad", "es": "Launchpad"}, "mk": "F4 / pinch", "how": "similar", "k": ["Apps menu"], "gesture": "4 pinch",
   "note": {"en": "Pinch with four fingers on the trackpad also opens the apps menu.", "es": "Pellizcar con cuatro dedos en el trackpad también abre el menú de apps."}},
  {"mac": {"en": "Finder", "es": "Finder"}, "mk": "", "how": "similar", "k": ["File manager"],
   "note": {"en": "Nautilus (Files). Space previews a file, like Quick Look (via sushi).", "es": "Nautilus (Archivos). Espacio previsualiza un archivo, como Vista Rápida (con sushi)."}},
  {"mac": {"en": "Safari", "es": "Safari"}, "mk": "", "how": "similar", "k": ["Browser"], "note": {"en": "Brave is your default browser.", "es": "Brave es tu navegador predeterminado."}},
  {"mac": {"en": "Terminal", "es": "Terminal"}, "mk": "", "how": "similar", "k": ["Terminal"], "note": {"en": "", "es": ""}},
 ]),
 ("Windows", "Ventanas", [
  {"mac": {"en": "Close window", "es": "Cerrar ventana"}, "mk": "⌘W", "how": "similar", "k": ["Close window"], "note": {"en": "For most apps, closing the last window quits the app.", "es": "En la mayoría de apps, cerrar la última ventana cierra la app."}},
  {"mac": {"en": "Quit app", "es": "Salir de la app"}, "mk": "⌘Q", "how": "similar", "k": ["Close window"], "note": {"en": "Close its windows. Background apps (chat, Bitwarden) may keep running in the bar.", "es": "Cierra sus ventanas. Las apps en segundo plano (chat, Bitwarden) pueden seguir en la barra."}},
  {"mac": {"en": "Minimize / hide", "es": "Minimizar / ocultar"}, "mk": "⌘M / ⌘H", "how": "different", "k": ["Move window to scratchpad", "Toggle scratchpad"],
   "note": {"en": "No minimizing on a tiling desktop: park the window in the scratchpad, or move it to another space.", "es": "No se minimiza en mosaico: estaciona la ventana en el scratchpad o muévela a otro espacio."}},
  {"mac": {"en": "Switch apps", "es": "Cambiar de app"}, "mk": "⌘Tab", "how": "similar", "k": ["Focus on next window"], "note": {"en": "Cycles windows. Super+arrows moves focus by direction.", "es": "Recorre ventanas. Super+flechas mueve el foco por dirección."}},
  {"mac": {"en": "Full screen", "es": "Pantalla completa"}, "mk": "⌃⌘F", "how": "similar", "k": ["Full screen"], "note": {"en": "", "es": ""}},
  {"mac": {"en": "Split View", "es": "Split View"}, "mk": "", "how": "different", "k": [], "note": {"en": "Automatic: every new window tiles beside the others. Super+J flips the split.", "es": "Automático: cada ventana nueva se acomoda junto a las demás. Super+J cambia la división."}},
  {"mac": {"en": "Move/resize with the mouse", "es": "Mover/redimensionar con el ratón"}, "mk": "", "how": "different", "k": [], "lit": "Super + drag / Super + right-drag",
   "note": {"en": "Hold Super, then drag with the left button (move) or right button (resize).", "es": "Mantén Super y arrastra con el botón izquierdo (mover) o derecho (redimensionar)."}},
  {"mac": {"en": "Force Quit", "es": "Forzar salida"}, "mk": "⌥⌘Esc", "how": "different", "k": ["Activity"],
   "note": {"en": "Open Activity, select the frozen app, press k to kill it. Ctrl+Alt+Delete closes ALL windows, so use it with care.", "es": "Abre Actividad, selecciona la app congelada y pulsa k. Ctrl+Alt+Supr cierra TODAS las ventanas; úsalo con cuidado."}},
 ]),
 ("Desktops & gestures", "Escritorios y gestos", [
  {"mac": {"en": "Spaces", "es": "Spaces"}, "mk": "⌃← / ⌃→", "how": "similar", "k": ["Switch to workspace 1", "Move window to workspace 1"], "gesture": "4 ↔" if DRAG else "3/4 ↔",
   "note": {"en": "Numbered spaces 1–9 (and 0). Super+number jumps, Super+Shift+number sends the window. Swipe " + ("four fingers sideways, as on a Mac that uses three-finger drag." if DRAG else "three or four fingers sideways."), "es": "Espacios numerados 1–9 (y 0). Super+número salta, Super+Shift+número envía la ventana. Desliza " + ("cuatro dedos de lado, como en un Mac con arrastre de tres dedos." if DRAG else "tres o cuatro dedos de lado.")}},
  {"mac": {"en": "Mission Control", "es": "Mission Control"}, "mk": "F3 / ⌃↑", "how": "different", "k": ["Omarchy menu"], "gesture": "4 ↑",
   "note": {"en": "There's no overview of all windows. Four fingers up opens the Omarchy menu instead.", "es": "No hay vista de todas las ventanas. Cuatro dedos arriba abre el menú de Omarchy."}},
  {"mac": {"en": "Show Desktop", "es": "Mostrar escritorio"}, "mk": "F11", "how": "different", "k": ["Toggle scratchpad"], "gesture": "4 ↓",
   "note": {"en": "Go to an empty space instead (Super+number).", "es": "Ve a un espacio vacío (Super+número)."}},
  {"mac": {"en": "Natural scrolling, tap to click, right-click", "es": "Desplazamiento natural, tocar para clic, clic derecho"}, "mk": "", "how": "same", "k": [],
   "note": {"en": "All on, as on your Mac: two-finger click is right-click.", "es": "Todo activado como en tu Mac: clic con dos dedos es clic derecho."}},
  {"mac": {"en": "Three-finger drag", "es": "Arrastrar con tres dedos"}, "mk": "Accessibility", "how": "same" if DRAG else "different", "k": [], "gesture": "3 drag" if DRAG else "", "lit": "" if DRAG else "trackpad/three-fingers drag",
   "note": {"en": ("On: slide three fingers to select text and drag things, with no click, like holding the button down. Like on a Mac that uses it, spaces moved to four fingers. To switch back: trackpad/three-fingers swipe." if DRAG else "Off: three fingers switch spaces instead (a Mac makes you choose too). To turn it on: trackpad/three-fingers drag, then spaces use four fingers."),
            "es": ("Activado: desliza tres dedos para seleccionar texto y arrastrar cosas, sin hacer clic, como mantener pulsado el botón. Como en un Mac que lo usa, los espacios pasaron a cuatro dedos. Para volver: trackpad/three-fingers swipe." if DRAG else "Desactivado: tres dedos cambian de espacio (en un Mac también hay que elegir). Para activarlo: trackpad/three-fingers drag; los espacios pasan a cuatro dedos.")}},
 ]),
 ("Text & clipboard", "Texto y portapapeles", [
  {"mac": {"en": "Copy / paste", "es": "Copiar / pegar"}, "mk": "⌘C / ⌘V", "how": "same", "k": ["Universal copy", "Universal paste"], "note": {"en": "Works in terminals too. Ctrl+C/V also work in most apps.", "es": "También en terminales. Ctrl+C/V también funcionan en la mayoría de apps."}},
  {"mac": {"en": "Clipboard history", "es": "Historial del portapapeles"}, "mk": "", "how": "different", "k": ["Clipboard manager"], "note": {"en": "Something macOS never had built in.", "es": "Algo que macOS nunca trajo integrado."}},
  {"mac": {"en": "Emoji & symbols", "es": "Emoji y símbolos"}, "mk": "⌃⌘Space", "how": "similar", "k": ["Emojis"], "note": {"en": "", "es": ""}},
  {"mac": {"en": "Accents (é ñ ¿ ¡)", "es": "Acentos (é ñ ¿ ¡)"}, "mk": "⌥e e / ⌥n n / ⌥1", "how": "same", "k": [],
   "lit": {"en": "Right ⌥ e, then e  ·  right ⌥ n, then n  ·  right ⌥ 1 = ¡  ·  right ⌥ ⇧ / = ¿", "es": "⌥ derecho e, luego e  ·  ⌥ derecho n, luego n  ·  ⌥ derecho 1 = ¡  ·  ⌥ derecho ⇧ / = ¿"},
   "lit2": {"en": "Also u = ü, i = î, ` = à. The left ⌥ stays Alt.", "es": "También u = ü, i = î, ` = à. El ⌥ izquierdo sigue siendo Alt."},
   "note": {"en": "Your Mac's accent keys, on the right Option key (the Mac layout). Caps Lock is still a Compose key as a second way: press it, release, then ' and e. Real Caps Lock is both Shift keys.", "es": "Las teclas de acentos de tu Mac, en la tecla Option derecha (la distribución Mac). Bloq Mayús sigue siendo una tecla Compose como segunda forma: púlsala, suéltala y escribe ' y e. El Bloq Mayús real es ambos Shift."}},
  {"mac": {"en": "Press-and-hold accent picker", "es": "Selector de acentos al mantener pulsada una tecla"}, "mk": "hold a key", "how": "none", "k": [],
   "note": {"en": "Linux has no general equivalent. The right Option key (⌥e e, ⌥n n) does the same job.", "es": "Linux no tiene un equivalente general. La tecla Option derecha (⌥e e, ⌥n n) hace lo mismo."}},
  {"mac": {"en": "Dictation", "es": "Dictado"}, "mk": "Fn Fn", "how": "similar", "k": ["Toggle dictation"], "lit2": "Fn + F9 (hold)",
   "note": {"en": "Voxtype runs locally, so nothing goes to the cloud. Hold Fn+F9 to talk, or toggle with the shortcut.", "es": "Voxtype funciona localmente, nada va a la nube. Mantén Fn+F9 para hablar o actívalo con el atajo."}},
 ]),
 ("Shortcuts inside apps (⌘)", "Atajos dentro de las apps (⌘)", [
  {"mac": {"en": "Undo / Redo", "es": "Deshacer / Rehacer"}, "mk": "⌘Z / ⇧⌘Z", "how": "same", "k": ["Undo (⌘Z)", "Redo (⇧⌘Z)"],
   "note": {"en": "Your ⌘ key sends Ctrl to the app you are in. Terminals are skipped on purpose (Ctrl+Z there stops a program).", "es": "Tu tecla ⌘ envía Ctrl a la app en la que estás. Las terminales se omiten a propósito (Ctrl+Z ahí detiene un programa)."}},
  {"mac": {"en": "Select all", "es": "Seleccionar todo"}, "mk": "⌘A", "how": "same", "k": ["Select all (⌘A)"], "note": {"en": "", "es": ""}},
  {"mac": {"en": "Reload page", "es": "Recargar página"}, "mk": "⌘R / ⇧⌘R", "how": "same", "k": ["Reload (⌘R)", "Hard reload (⇧⌘R)"], "note": {"en": "", "es": ""}},
  {"mac": {"en": "New window, reopen closed tab", "es": "Ventana nueva, reabrir pestaña"}, "mk": "⌘N / ⇧⌘T", "how": "same", "k": ["New window (⌘N)", "Reopen closed tab (⇧⌘T)"], "note": {"en": "", "es": ""}},
  {"mac": {"en": "Bookmark page", "es": "Guardar en marcadores"}, "mk": "⌘D", "how": "same", "k": ["Bookmark page (⌘D)"], "note": {"en": "", "es": ""}},
  {"mac": {"en": "Bold, italic, underline", "es": "Negrita, cursiva, subrayado"}, "mk": "⌘B ⌘I ⌘U", "how": "same", "k": ["Bold (⌘B)", "Italic (⌘I)", "Underline (⌘U)"], "note": {"en": "In editors and web docs. Brave's own Ctrl+B opens its sidebar.", "es": "En editores y documentos web. El Ctrl+B propio de Brave abre su barra lateral."}},
  {"mac": {"en": "Back / Forward", "es": "Atrás / Adelante"}, "mk": "⌘[ / ⌘]", "how": "same", "k": ["Back (⌘[)", "Forward (⌘])"], "note": {"en": "Browser history, and Files.", "es": "Historial del navegador y Archivos."}},
  *extras_rows(),
 ]),
 ("Screen & capture", "Pantalla y capturas", [
  {"mac": {"en": "Screenshot", "es": "Captura de pantalla"}, "mk": "⌘⇧3 / ⌘⇧4", "how": "similar", "k": ["Screenshot"], "note": {"en": "Your MacBook has no Print key, so this is a custom shortcut. Drag a region, then Return.", "es": "Tu MacBook no tiene tecla Print; este es un atajo propio. Arrastra una región y pulsa Return."}},
  {"mac": {"en": "Screenshot toolbar / recording", "es": "Barra de captura / grabación"}, "mk": "⌘⇧5", "how": "similar", "k": ["Capture menu"], "note": {"en": "Region, window, recording, text from screen (OCR), QR, color picker.", "es": "Región, ventana, grabación, texto de la pantalla (OCR), QR, selector de color."}},
  {"mac": {"en": "Night Shift", "es": "Night Shift"}, "mk": "", "how": "similar", "k": ["Toggle nightlight"], "note": {"en": "", "es": ""}},
  {"mac": {"en": "Zoom", "es": "Zoom"}, "mk": "⌥⌘8 / ⌃ scroll", "how": "similar", "k": ["Zoom in", "Reset zoom"], "note": {"en": "", "es": ""}},
  {"mac": {"en": "Brightness, volume, media", "es": "Brillo, volumen, multimedia"}, "mk": "F1–F12", "how": "same", "k": [], "lit": "F1 F2 · F5 F6 · F7 F8 F9 · F10 F11 F12",
   "note": {"en": "Same top row as macOS. Hold Fn for real F1–F12.", "es": "Misma fila superior que en macOS. Mantén Fn para las F1–F12 reales."}},
 ]),
 ("System", "Sistema", [
  {"mac": {"en": "System Settings", "es": "Ajustes del Sistema"}, "mk": "", "how": "different", "k": ["Omarchy menu"], "menu": "setup",
   "note": {"en": "Omarchy menu → Setup. Direct shortcuts: Wi-Fi Super+Ctrl+W, Bluetooth Super+Ctrl+B, Audio Super+Ctrl+A, Display Super+Ctrl+D, Power Super+Ctrl+P.", "es": "Menú de Omarchy → Setup. Atajos directos: Wi-Fi Super+Ctrl+W, Bluetooth Super+Ctrl+B, Audio Super+Ctrl+A, Pantalla Super+Ctrl+D, Energía Super+Ctrl+P."}},
  {"mac": {"en": "Appearance: Light / Dark / Auto", "es": "Apariencia: Clara / Oscura / Automática"}, "mk": "Appearance", "how": "similar", "k": ["Theme menu"],
   "lit": "auto-appearance on | off | light | dark",
   "note": {"en": "Omarchy themes are more than light and dark: pick one from the Theme menu. Auto (light by day, dark at night) is installed but off; turn it on when you want it. White is the light theme closest to macOS.", "es": "Los temas de Omarchy son más que claro y oscuro: elige uno en el menú de temas. Automática (clara de día, oscura de noche) está instalada pero apagada; actívala cuando quieras. White es el tema claro más parecido a macOS."}},
  {"mac": {"en": "Menu bar clock", "es": "Reloj de la barra de menús"}, "mk": "", "how": "same", "k": [], "lit": "Wed 7 Oct 15:08",
   "note": {"en": "The bar shows the weekday, date and time, like the macOS menu bar (24-hour).", "es": "La barra muestra el día, la fecha y la hora, como la barra de menús de macOS (24 horas)."}},
  {"mac": {"en": "Optimized Battery Charging", "es": "Carga optimizada de batería"}, "mk": "80 % limit", "how": "none", "k": [],
   "note": {"en": "Not possible on this MacBook: its battery gives Linux no charge-limit control.", "es": "No es posible en esta MacBook: su batería no da a Linux ningún control de límite de carga."}},
  {"mac": {"en": "Lock screen", "es": "Bloquear pantalla"}, "mk": "⌃⌘Q", "how": "similar", "k": ["Lock system"], "note": {"en": "", "es": ""}},
  {"mac": {"en": "Sleep / Restart / Shut Down", "es": "Reposo / Reiniciar / Apagar"}, "mk": " menu", "how": "similar", "k": ["System menu"], "menu": "system", "note": {"en": "Closing the lid locks and suspends.", "es": "Cerrar la tapa bloquea y suspende."}},
  {"mac": {"en": "Activity Monitor", "es": "Monitor de Actividad"}, "mk": "", "how": "similar", "k": ["Activity"], "note": {"en": "btop in a terminal; q quits.", "es": "btop en una terminal; q para salir."}},
  {"mac": {"en": "Notification Center / Focus", "es": "Centro de notificaciones / Concentración"}, "mk": "", "how": "similar", "k": ["Open notification history", "Toggle silencing notifications"], "note": {"en": "", "es": ""}},
  {"mac": {"en": "App Store / Homebrew", "es": "App Store / Homebrew"}, "mk": "", "how": "different", "k": [], "menu": "install", "lit": "Omarchy menu → Install · yay -S <name>",
   "note": {"en": "Or the Apps tab of this portal. pacman = official repos, yay = also the community AUR.", "es": "O la pestaña Apps de este portal. pacman = repos oficiales, yay = también el AUR comunitario."}},
  {"mac": {"en": "Software Update", "es": "Actualización de software"}, "mk": "", "how": "different", "k": [], "menu": "update", "lit": "Omarchy menu → Update", "note": {"en": "Weekly is a good rhythm.", "es": "Semanal es buen ritmo."}},
  {"mac": {"en": "Time Machine", "es": "Time Machine"}, "mk": "", "how": "different", "k": [], "lit": "omarchy-snapshot (system) · snapper -c home list (your files)", "lit2": "sudo backup/install-backups",
   "note": {"en": "Today, snapshots cover the SYSTEM only (btrfs restore points). For your files, hourly /home snapshots plus Pika Backup to an external drive are prepared: one sudo command (see Open items on the Setup log). Snapshots on the same disk undo mistakes, not a dead disk.", "es": "Hoy las instantáneas cubren solo el SISTEMA (puntos de restauración btrfs). Para tus archivos están preparadas instantáneas de /home cada hora y Pika Backup a un disco externo: un comando sudo (ver Pendientes en la bitácora). Las instantáneas en el mismo disco deshacen errores, no un disco dañado."}},
 ]),
 ("Apps you knew", "Apps que conocías", [
  {"mac": {"en": "AirDrop", "es": "AirDrop"}, "mk": "", "how": "different", "k": [], "lit": "LocalSend · Taildrop", "note": {"en": "LocalSend (installed) sends files to phones and computers on the same Wi-Fi. Taildrop sends over Tailscale once it's logged in.", "es": "LocalSend (instalado) envía archivos a teléfonos y equipos en la misma red. Taildrop lo hace por Tailscale cuando inicies sesión."}},
  {"mac": {"en": "Keychain / Passwords", "es": "Llavero / Contraseñas"}, "mk": "", "how": "different", "k": ["Bitwarden"], "note": {"en": "Omarchy's Passwords shortcut (Super+Shift+/) expects 1Password, which isn't installed; use Bitwarden.", "es": "El atajo Contraseñas de Omarchy (Super+Shift+/) espera 1Password, que no está instalado; usa Bitwarden."}},
  {"mac": {"en": "Preview", "es": "Vista Previa"}, "mk": "", "how": "similar", "k": [], "lit": "Evince (PDF) · imv (images)", "note": {"en": "Opened automatically when you double-click a file.", "es": "Se abren solos al hacer doble clic en un archivo."}},
  {"mac": {"en": "Notes / TextEdit", "es": "Notas / TextEdit"}, "mk": "", "how": "similar", "k": ["Obsidian", "Anytype", "Omawrite"], "note": {"en": "", "es": ""}},
  {"mac": {"en": "Messages / FaceTime", "es": "Mensajes / FaceTime"}, "mk": "", "how": "different", "k": ["Signal", "Beeper", "Telegram"],
   "note": {"en": "The FaceTime HD camera works (facetimehd driver); Signal, Beeper and browser calls can use it.", "es": "La cámara FaceTime HD funciona (driver facetimehd); Signal, Beeper y las llamadas en el navegador pueden usarla."}},
  {"mac": {"en": "Music / QuickTime", "es": "Música / QuickTime"}, "mk": "", "how": "similar", "k": [], "lit": "mpv · Grayjay", "note": {"en": "mpv plays any audio or video file.", "es": "mpv reproduce cualquier audio o video."}},
 ]),
]

GLOSSARY = [
 ("Super key", "Tecla Super", "The ⌘ key on your MacBook. Almost every Omarchy shortcut starts with it.", "La tecla ⌘ de tu MacBook. Casi todos los atajos de Omarchy empiezan con ella."),
 ("Omarchy", "Omarchy", "A ready-made, opinionated Linux desktop built on Arch Linux and Hyprland, by DHH. You're running Omarchy 4 (\"Quattro\").", "Un escritorio Linux listo y con opiniones, basado en Arch Linux y Hyprland, creado por DHH. Usas Omarchy 4 (\"Quattro\")."),
 ("Hyprland", "Hyprland", "The window manager: it draws windows, tiles them, animates, and runs your shortcuts and gestures.", "El gestor de ventanas: dibuja ventanas, las acomoda en mosaico, anima y ejecuta tus atajos y gestos."),
 ("Tiling", "Mosaico (tiling)", "Windows automatically share the screen without overlapping, so you never arrange them by hand.", "Las ventanas comparten la pantalla automáticamente sin solaparse; nunca las acomodas a mano."),
 ("Floating", "Flotante", "A window that sits on top and moves freely, like on macOS.", "Una ventana que flota encima y se mueve libremente, como en macOS."),
 ("Workspace / space", "Espacio de trabajo", "One of ten numbered desktops (1–9, 0).", "Uno de diez escritorios numerados (1–9, 0)."),
 ("Scratchpad", "Scratchpad", "A hidden workspace you summon over anything, used in place of minimizing.", "Un espacio oculto que invocas sobre cualquier cosa; reemplaza a minimizar."),
 ("Group", "Grupo", "Several windows sharing one tile as tabs.", "Varias ventanas compartiendo un mosaico como pestañas."),
 ("Omarchy menu", "Menú de Omarchy", "The hub (Super+Space) for apps, installing, style, settings and system.", "El centro (Super+Space) de apps, instalación, estilo, ajustes y sistema."),
 ("Web app", "Web app", "A website opened in its own window with its own icon, like an app.", "Un sitio web en su propia ventana y con su propio icono, como una app."),
 ("TUI", "TUI", "A full app that runs inside a terminal (btop, lazydocker).", "Una app completa que corre dentro de una terminal (btop, lazydocker)."),
 ("Terminal", "Terminal", "A window where you type commands. Paste with Super+V.", "Una ventana donde escribes comandos. Pega con Super+V."),
 ("sudo", "sudo", "Run one command as administrator; asks for your password. On a Mac, the admin password prompt.", "Ejecutar un comando como administrador; pide tu contraseña. En Mac, el aviso de contraseña de admin."),
 ("pacman", "pacman", "Arch Linux's package manager, for the official repositories.", "El gestor de paquetes de Arch Linux, para los repositorios oficiales."),
 ("AUR / yay", "AUR / yay", "The Arch User Repository: community-maintained packages, installed with yay. Huge, but less vetted.", "El repositorio de usuarios de Arch: paquetes de la comunidad, instalados con yay. Enorme, pero menos revisado."),
 ("Snapshot", "Instantánea", "A restore point of the system files (btrfs), taken before big changes.", "Un punto de restauración de los archivos del sistema (btrfs), tomado antes de cambios grandes."),
 ("LUKS", "LUKS", "Full-disk encryption: the passphrase you type at boot. Like FileVault.", "Cifrado de disco completo: la frase que escribes al arrancar. Como FileVault."),
 ("PipeWire", "PipeWire", "The audio system. Your speaker EQ and high-fidelity settings live there.", "El sistema de audio. Tu EQ de bocinas y ajustes de alta fidelidad viven ahí."),
 ("Compose key", "Tecla Compose", "Caps Lock on Omarchy: press it, release, then two characters, to type accents and symbols. A second way next to the Mac-style right Option key.", "Bloq Mayús en Omarchy: púlsala, suéltala y luego dos caracteres para acentos y símbolos. Una segunda forma junto a la tecla Option derecha estilo Mac."),
 ("Dead key", "Tecla muerta", "A key that types nothing by itself and waits for the next letter to add an accent, like ⌥e then e on a Mac. On your MacBook the right Option key does this.", "Una tecla que no escribe nada sola y espera la siguiente letra para ponerle el acento, como ⌥e y luego e en un Mac. En tu MacBook lo hace la tecla Option derecha."),
 ("Wayland", "Wayland", "The modern Linux display system Hyprland uses (the successor to X11).", "El sistema gráfico moderno de Linux que usa Hyprland (sucesor de X11)."),
 ("Dotfiles", "Dotfiles", "Your settings files in ~/.config. Yours to edit; Omarchy updates don't overwrite them.", "Tus archivos de ajustes en ~/.config. Son tuyos; las actualizaciones de Omarchy no los sobrescriben."),
]

# ---------------------------------------------------------------- Your MacBook (from the read-only audit)
HW = [
 {"id": "gpu", "status": "ok", "en": "Graphics: screen on the efficient Intel GPU", "es": "Gráficos: pantalla en la GPU Intel eficiente",
  "body": {"en": "Your MacBook has two GPUs. The firmware used to hand the screen to the NVIDIA GT 750M, which kept the CPU at 90–95 °C with the fans near 5,900 RPM. Now the Intel Iris Pro drives the screen, Hyprland draws only on Intel, and nvidia-off.service powers the NVIDIA GPU off at every boot. At light load the CPU sits around 75 °C and the fans around 2,200–2,700 RPM. Heavy work such as video in the browser still makes it warm and the fans spin up, which is normal. If you plug in an external monitor, it uses the NVIDIA GPU, so the switch-off is skipped when a display is connected at boot or login. Details and how to undo it are in the Setup log.",
           "es": "Tu MacBook tiene dos GPUs. El firmware le daba la pantalla a la NVIDIA GT 750M, que mantenía la CPU a 90–95 °C con los ventiladores cerca de 5900 RPM. Ahora la Intel Iris Pro controla la pantalla, Hyprland dibuja solo en Intel y nvidia-off.service apaga la GPU NVIDIA en cada arranque. Con poca carga la CPU está cerca de 75 °C y los ventiladores entre 2200 y 2700 RPM. El trabajo pesado, como video en el navegador, aún la calienta y acelera los ventiladores, lo cual es normal. Si conectas un monitor externo, usa la GPU NVIDIA, así que el apagado se omite cuando hay una pantalla conectada al arrancar o al iniciar sesión. Detalles y cómo revertirlo en la bitácora de Setup."},
  "cmd": "~/labspace/omarchy-kit/gpu/gpu-status",
  "live": "gpu"},
 {"id": "camera", "status": "ok", "en": "FaceTime HD camera", "es": "Cámara FaceTime HD",
  "body": {"en": "Works at 1280×720, 30 fps, as /dev/video0 (Broadcom 720p). It uses the community facetimehd driver from the AUR, with firmware and sensor calibration taken from Apple's own downloads. DKMS rebuilds the driver on every kernel update, like the Wi-Fi driver; if the camera disappears after an update, check `dkms status`.", "es": "Funciona a 1280×720, 30 fps, como /dev/video0 (Broadcom 720p). Usa el driver comunitario facetimehd del AUR, con firmware y calibración del sensor tomados de descargas de Apple. DKMS recompila el driver en cada actualización del kernel, como el de Wi-Fi; si la cámara desaparece tras actualizar, revisa `dkms status`."},
  "cmd": "v4l2-ctl --list-devices"},
 {"id": "battery", "status": "warn", "en": "Battery", "es": "Batería",
  "body": {"en": "It holds about 75 % of its original capacity, normal for a 2014 battery. The power profile now follows the charger by itself, as on a Mac: Performance when plugged in, Balanced on battery (power-auto, a small background service). A profile you pick by hand stays until the next plug or unplug.", "es": "Conserva ~75 % de su capacidad original, normal para una batería de 2014. El perfil de energía ahora sigue al cargador solo, como en un Mac: Rendimiento conectado, Equilibrado con batería (power-auto, un pequeño servicio en segundo plano). Un perfil que elijas a mano se queda hasta el próximo enchufe o desenchufe."},
  "k": "Power", "live": "battery"},
 {"id": "sleep", "status": "warn", "en": "Sleep and the lid", "es": "Suspensión y la tapa",
  "body": {"en": "Closing the lid locks and suspends (deep sleep). The real result is tracked on the Setup log (Sleep row) from the system journal: until you close the lid once, it says untested. This model sometimes wakes right after sleeping because USB is allowed to wake it, so test it before trusting it in a bag. After a test, run sleep/sleep-check for the details.", "es": "Cerrar la tapa bloquea y suspende (suspensión profunda). El resultado real se sigue en la bitácora de Setup (fila Reposo) desde el registro del sistema: hasta que cierres la tapa una vez, dice sin probar. Este modelo a veces despierta justo después por la USB como fuente de despertar; pruébalo antes de confiar en él en una mochila. Tras la prueba, corre sleep/sleep-check para ver el detalle."},
  "cmd": "~/labspace/omarchy-kit/sleep/sleep-check", "live": "sleep"},
 {"id": "wifi", "status": "ok", "en": "Wi-Fi", "es": "Wi-Fi",
  "body": {"en": "Works (Broadcom BCM4360, 5 GHz) with the proprietary wl driver. That driver is rebuilt for every kernel update; if Wi-Fi ever disappears after an update, check `dkms status`.", "es": "Funciona (Broadcom BCM4360, 5 GHz) con el driver propietario wl. Se recompila en cada actualización del kernel; si el Wi-Fi desaparece tras actualizar, revisa `dkms status`."},
  "k": "Network"},
 {"id": "bt", "status": "ok", "en": "Bluetooth", "es": "Bluetooth", "body": {"en": "Works.", "es": "Funciona."}, "k": "Bluetooth"},
 {"id": "display", "status": "ok", "en": "Retina display", "es": "Pantalla Retina",
  "body": {"en": "2880×1800 at 1.6× scale. Brightness works on F1/F2 (Shift = max/min, Alt = fine steps). Super+/ and Super+Alt+/ change the scaling.", "es": "2880×1800 a escala 1.6. El brillo funciona en F1/F2 (Shift = máx/mín, Alt = pasos finos). Super+/ y Super+Alt+/ cambian la escala."}, "k": "Display"},
 {"id": "kbd", "status": "ok", "en": "Keyboard and top row", "es": "Teclado y fila superior",
  "body": {"en": "Mac-style top row (media keys first, Fn for F1–F12). Keyboard backlight on F5/F6 (the light is present; pressing the keys is untested). The right Option key types accents like macOS (⌥e e = é, ⌥n n = ñ), Caps Lock is a second way (Compose), and ⌘ shortcuts such as ⌘Z and ⌘A work inside apps.", "es": "Fila superior estilo Mac (multimedia primero, Fn para F1–F12). Luz del teclado en F5/F6 (la luz existe; las teclas no se han probado). La tecla Option derecha escribe acentos como macOS (⌥e e = é, ⌥n n = ñ), Bloq Mayús es una segunda forma (Compose) y atajos ⌘ como ⌘Z y ⌘A funcionan dentro de las apps."}},
 {"id": "trackpad", "status": "ok", "en": "Trackpad", "es": "Trackpad", "body": {"en": "Works, with macOS-style gestures configured: natural scrolling, two-finger right-click, space swipes, and a choice for three fingers (swipe spaces or drag). See the Trackpad page.", "es": "Funciona, con gestos estilo macOS configurados: desplazamiento natural, clic derecho con dos dedos, cambio de espacio y una opción para tres dedos (cambiar de espacio o arrastrar). Ver la página Trackpad."}},
 {"id": "audio", "status": "ok", "en": "Audio", "es": "Audio",
  "body": {"en": "Speakers use a tuned EQ, headphones bypass it, music plays at its native sample rate, and audio threads run at realtime priority. A microphone is present (capture untested).", "es": "Bocinas con EQ ajustado, los audífonos lo omiten, la música suena a su frecuencia nativa y el audio tiene prioridad en tiempo real. Hay micrófono (grabación sin probar)."}, "k": "Audio"},
 {"id": "fans", "status": "ok", "en": "Fans and temperature", "es": "Ventiladores y temperatura",
  "body": {"en": "The Mac's own controller runs the fans, and thermald is active. Most of the heat comes from the GPU issue above.", "es": "El controlador del propio Mac maneja los ventiladores y thermald está activo. La mayor parte del calor viene del problema de GPU de arriba."}, "live": "thermal"},
 {"id": "ports", "status": "warn", "en": "Thunderbolt 2, HDMI, SD card", "es": "Thunderbolt 2, HDMI, tarjeta SD",
  "body": {"en": "The ports are detected. An external display and an SD card haven't been tested yet. Monitors plug into the NVIDIA GPU on this model: connect one before you log in so Hyprland can use it (the NVIDIA GPU then stays on).", "es": "Los puertos se detectan. Aún no se probó un monitor externo ni una tarjeta SD. En este modelo los monitores se conectan a la GPU NVIDIA: conéctalo antes de iniciar sesión para que Hyprland pueda usarlo (la GPU NVIDIA queda encendida)."}, "k": "Display"},
]
