"""Curriculum for the Learn page.

Each lesson has steps. A step names the binding it teaches by Omarchy's own description ("k"), which
build_portal.py resolves to your current keys, and a "check" the page verifies live through the local
helper (/api/state) — so the lesson knows you actually did it. Check types (see learn.template.html):
  newWindow{cls}  closeWindow  wsIs{ws}  wsChange  moved  floating{v}  fullscreen{v}  special{v}
  toSpecial  focusChange  grouped  themeChanged  volumeChanged  newShot  typed{re}  manual
"""

import kitconf

DRAG = kitconf.three_fingers() == "drag"  # three fingers drag instead of swiping spaces (trackpad/three-fingers)
FN = "4" if DRAG else "3"  # fingers for the space swipe the lessons teach


def S(en, es, k=None, check="manual", menu=None, **kw):
    d = {"en": en, "es": es, "check": check}
    if k: d["k"] = k
    if menu: d["menu"] = menu
    d.update(kw)
    return d


LEVELS = [
 {"id": "l1", "en": "1 · Survival: your first hour", "es": "1 · Supervivencia: tu primera hora", "lessons": [
  {"id": "super", "en": "The Super key is your ⌘", "es": "La tecla Super es tu ⌘",
   "why": {"en": "On your MacBook, the ⌘ command key acts as Omarchy's Super key. Almost every shortcut starts with it, much as most macOS shortcuts start with ⌘.",
           "es": "En tu MacBook, la tecla ⌘ (comando) funciona como la tecla Super de Omarchy. Casi todos los atajos empiezan con ella, igual que la mayoría en macOS empiezan con ⌘."},
   "steps": [S("Open the list of every shortcut. Read it, then close it with Esc.", "Abre la lista de todos los atajos. Léela y ciérrala con Esc.", k="Keybindings"),
             S("Open a terminal. It's your power tool, like Terminal.app.", "Abre una terminal. Es tu herramienta más potente, como Terminal.app.", k="Terminal", check="newWindow", cls="terminal|foot|alacritty|ghostty|kitty")]},
  {"id": "close", "en": "Closing windows", "es": "Cerrar ventanas",
   "why": {"en": "There are no red/yellow/green buttons. Windows close from the keyboard; for most apps, closing the last window also quits the app.",
           "es": "No hay botones rojo/amarillo/verde. Las ventanas se cierran con el teclado; en la mayoría de apps, cerrar la última ventana también cierra la app."},
   "steps": [S("Close the terminal you opened.", "Cierra la terminal que abriste.", k="Close window", check="closeWindow")]},
  {"id": "launch", "en": "Launching apps (your Spotlight)", "es": "Abrir apps (tu Spotlight)",
   "why": {"en": "The apps menu works like Spotlight: open it, type a few letters, press Return. The Omarchy menu is the hub for everything else: installing, style, settings, system.",
           "es": "El menú de apps funciona como Spotlight: ábrelo, escribe unas letras y pulsa Return. El menú de Omarchy es el centro para todo lo demás: instalar, estilo, ajustes, sistema."},
   "steps": [S("Open the apps menu, type “nautilus” (the file manager) and press Return.", "Abre el menú de apps, escribe “nautilus” (el gestor de archivos) y pulsa Return.", k="Apps menu", check="newWindow"),
             S("Open the Omarchy menu and look around. Esc closes it.", "Abre el menú de Omarchy y explóralo. Esc lo cierra.", k="Omarchy menu", menu="root")]},
  {"id": "spaces", "en": "Spaces (workspaces)", "es": "Espacios (workspaces)",
   "why": {"en": "Spaces 1–9 are separate desktops, like Mission Control's Spaces but always there and numbered. Keep a habit: browser on 2, chat on 8, and so on.",
           "es": "Los espacios 1–9 son escritorios separados, como los Spaces de Mission Control pero siempre presentes y numerados. Crea un hábito: navegador en 2, chat en 8, etc."},
   "steps": [S("Jump to space 2.", "Salta al espacio 2.", k="Switch to workspace 2", check="wsIs", ws=2),
             S("Come back to space 1.", "Vuelve al espacio 1.", k="Switch to workspace 1", check="wsIs", ws=1),
             S(f"Now do it with your fingers: swipe left or right with {FN} fingers on the trackpad.", f"Ahora con los dedos: desliza a la izquierda o derecha con {FN} dedos en el trackpad.", check="wsChange", gesture=f"{FN} ↔")]},
  {"id": "move", "en": "Moving a window to another space", "es": "Mover una ventana a otro espacio",
   "why": {"en": "Rather than dragging windows between desktops, you send the focused window to a numbered space.",
           "es": "En lugar de arrastrar ventanas entre escritorios, envías la ventana enfocada a un espacio numerado."},
   "steps": [S("Open any window (a terminal is fine).", "Abre cualquier ventana (una terminal sirve).", k="Terminal", check="newWindow"),
             S("Send it to space 3. You follow it there.", "Envíala al espacio 3. Tú la sigues.", k="Move window to workspace 3", check="moved")]},
  {"id": "system", "en": "Lock, sleep, shut down", "es": "Bloquear, suspender, apagar",
   "why": {"en": "The System menu replaces the Apple menu's Sleep, Restart, Shut Down and Log Out. Closing the lid also locks and suspends.",
           "es": "El menú Sistema reemplaza Suspender, Reiniciar, Apagar y Cerrar sesión del menú Apple. Cerrar la tapa también bloquea y suspende."},
   "steps": [S("Open the System menu, look at the options, then press Esc.", "Abre el menú Sistema, mira las opciones y pulsa Esc.", k="System menu", menu="system"),
             S("Learn the lock shortcut (try it when you're ready; your password unlocks).", "Aprende el atajo de bloqueo (pruébalo cuando quieras; tu contraseña desbloquea).", k="Lock system")]},
 ]},
 {"id": "l2", "en": "2 · Windows like a pro", "es": "2 · Ventanas como profesional", "lessons": [
  {"id": "focus", "en": "Moving focus without the mouse", "es": "Mover el foco sin el ratón",
   "why": {"en": "Windows tile side by side automatically. Move between them with Super and the arrow keys.",
           "es": "Las ventanas se acomodan solas lado a lado. Muévete entre ellas con Super y las flechas."},
   "steps": [S("Make sure two windows share this space (open a second terminal if needed).", "Asegúrate de tener dos ventanas en este espacio (abre otra terminal si hace falta).", k="Terminal", check="newWindow"),
             S("Move focus to the window on the left.", "Mueve el foco a la ventana de la izquierda.", k="Focus on left window", check="focusChange")]},
  {"id": "float", "en": "Floating windows (the macOS way)", "es": "Ventanas flotantes (al estilo macOS)",
   "why": {"en": "Any window can float freely like on a Mac. Drag it with Super and the left mouse button; resize it with Super and the right button.",
           "es": "Cualquier ventana puede flotar libremente como en Mac. Arrástrala con Super + clic izquierdo; cambia su tamaño con Super + clic derecho."},
   "steps": [S("Make the focused window float.", "Haz flotar la ventana enfocada.", k="Toggle window floating/tiling", check="floating", v=True),
             S("Put it back into the tiling layout.", "Devuélvela al mosaico.", k="Toggle window floating/tiling", check="floating", v=False)]},
  {"id": "fullscreen", "en": "Full screen", "es": "Pantalla completa",
   "why": {"en": "Like ⌃⌘F on macOS, but on a tiling desktop it's instant and stays on the same space.", "es": "Como ⌃⌘F en macOS, pero en un escritorio de mosaico es instantáneo y se queda en el mismo espacio."},
   "steps": [S("Make the focused window full screen.", "Pon la ventana enfocada en pantalla completa.", k="Full screen", check="fullscreen", v=True),
             S("Exit full screen.", "Sal de pantalla completa.", k="Full screen", check="fullscreen", v=False)]},
  {"id": "resize", "en": "Resizing and splitting", "es": "Redimensionar y dividir",
   "why": {"en": "Tiles grow and shrink from the keyboard. Super+J flips how the space is split (side by side or stacked).",
           "es": "Los mosaicos crecen y encogen con el teclado. Super+J cambia la división (lado a lado o apilado)."},
   "steps": [S("Grow the focused window.", "Agranda la ventana enfocada.", k="Expand window left"),
             S("Shrink it back.", "Encógela de nuevo.", k="Shrink window left"),
             S("Flip the split direction.", "Cambia la dirección de la división.", k="Toggle window split")]},
  {"id": "scratchpad", "en": "The scratchpad (instead of minimize)", "es": "El scratchpad (en vez de minimizar)",
   "why": {"en": "There's no minimize (⌘M) on a tiling desktop. Instead you park a window in the hidden scratchpad and summon it back over anything.",
           "es": "No existe minimizar (⌘M) en un escritorio de mosaico. En su lugar estacionas una ventana en el scratchpad oculto y la invocas sobre cualquier cosa."},
   "steps": [S("Send the focused window to the scratchpad.", "Envía la ventana enfocada al scratchpad.", k="Move window to scratchpad", check="toSpecial"),
             S("Show the scratchpad.", "Muestra el scratchpad.", k="Toggle scratchpad", check="special", v=True),
             S("Hide it again.", "Ocúltalo otra vez.", k="Toggle scratchpad", check="special", v=False)]},
  {"id": "groups", "en": "Tabbed groups", "es": "Grupos con pestañas",
   "why": {"en": "Several windows can share one tile as tabs, which suits small screens.", "es": "Varias ventanas pueden compartir un mosaico como pestañas; ideal para pantallas pequeñas."},
   "steps": [S("Turn the focused window into a group.", "Convierte la ventana enfocada en un grupo.", k="Toggle window grouping"),
             S("Move a neighbour into the group (Super+Alt+arrow), then switch tabs.", "Mueve una vecina al grupo (Super+Alt+flecha) y cambia de pestaña.", k="Next window in group", check="grouped")]},
 ]},
 {"id": "l3", "en": "3 · Everyday tasks", "es": "3 · Tareas diarias", "lessons": [
  {"id": "accents", "en": "Typing Spanish: á é í ó ú ñ ¿ ¡", "es": "Escribir en español: á é í ó ú ñ ¿ ¡",
   "why": {"en": "Accents work like on your Mac, on the RIGHT Option key (⌥): press ⌥ and e together, release, then type the vowel: ⌥e then a gives á. ⌥n then n gives ñ, ⌥u then u gives ü, ⌥1 gives ¡, and ⌥ Shift / gives ¿. The left Option key stays Alt. A second way: Caps Lock is a Compose key (press it, release, then ' and a gives á). For real Caps Lock, press both Shift keys.",
           "es": "Los acentos funcionan como en tu Mac, con la tecla Option (⌥) DERECHA: pulsa ⌥ y e juntas, suelta y escribe la vocal: ⌥e y luego a da á. ⌥n y luego n da ñ, ⌥u y luego u da ü, ⌥1 da ¡ y ⌥ Shift / da ¿. La tecla Option izquierda sigue siendo Alt. Una segunda forma: Bloq Mayús es una tecla Compose (púlsala, suéltala y escribe ' y a da á). Para el Bloq Mayús real pulsa ambos Shift."},
   "steps": [S("In the box below, type: ¿Año? ¡Sí!   (right ⌥ Shift / for ¿, right ⌥ n then n for ñ, right ⌥ 1 for ¡, right ⌥ e then i for í)", "En el recuadro de abajo escribe: ¿Año? ¡Sí!   (⌥ derecho Shift / para ¿, ⌥ derecho n y luego n para ñ, ⌥ derecho 1 para ¡, ⌥ derecho e y luego i para í)", check="typed", re="¿.*ñ.*\\?.*¡.*í", box=True)]},
  {"id": "copy", "en": "Copy, paste and clipboard history", "es": "Copiar, pegar e historial del portapapeles",
   "why": {"en": "Super+C and Super+V copy and paste everywhere, terminals included, so your ⌘C/⌘V muscle memory keeps working. The clipboard manager remembers what you copied earlier.",
           "es": "Super+C y Super+V copian y pegan en todas partes, incluso en terminales, así que tu memoria de ⌘C/⌘V sigue sirviendo. El gestor de portapapeles recuerda lo que copiaste antes."},
   "steps": [S("Select this word: Omarchy, then copy it with the universal copy.", "Selecciona esta palabra: Omarchy, y cópiala con el copiar universal.", k="Universal copy"),
             S("Open the clipboard history and pick it again.", "Abre el historial del portapapeles y elígela de nuevo.", k="Clipboard manager"),
             S("Paste it into the box below.", "Pégala en el recuadro de abajo.", k="Universal paste", check="typed", re="Omarchy", box=True)]},
  {"id": "cmdkeys", "en": "Your ⌘ shortcuts inside apps", "es": "Tus atajos ⌘ dentro de las apps",
   "why": {"en": "Inside apps, your ⌘ key now sends Ctrl for the common Mac shortcuts: ⌘A select all, ⌘Z undo (⇧⌘Z redo), ⌘R reload, ⌘N new window, ⇧⌘T reopen a closed tab, ⌘D bookmark, ⌘B/⌘I/⌘U bold, italic, underline, ⌘[ and ⌘] back and forward. Terminals are skipped on purpose. ⌘W, ⌘T, ⌘F, ⌘S, ⌘L, ⌘G and ⌘P are opt-in, key by key, because Super+those keys already do Omarchy things (see From macOS).",
           "es": "Dentro de las apps, tu tecla ⌘ ahora envía Ctrl para los atajos comunes de Mac: ⌘A seleccionar todo, ⌘Z deshacer (⇧⌘Z rehacer), ⌘R recargar, ⌘N ventana nueva, ⇧⌘T reabrir pestaña cerrada, ⌘D marcador, ⌘B/⌘I/⌘U negrita, cursiva y subrayado, ⌘[ y ⌘] atrás y adelante. Las terminales se omiten a propósito. ⌘W, ⌘T, ⌘F, ⌘S, ⌘L, ⌘G y ⌘P son opcionales, tecla por tecla, porque Super+esas teclas ya hacen cosas de Omarchy (ver Desde macOS)."},
   "steps": [S("In the box below, type: casa. Then press Select all, and type: hogar. The box should end up holding only “hogar”.", "En el recuadro de abajo escribe: casa. Luego pulsa Seleccionar todo y escribe: hogar. El recuadro debe quedar solo con “hogar”.", k="Select all (⌘A)", check="typed", re="^hogar$", box=True),
             S("Press Undo in the box: the previous text comes back.", "Pulsa Deshacer en el recuadro: vuelve el texto anterior.", k="Undo (⌘Z)"),
             S("Press Reload: this page refreshes, like ⌘R in Safari. Then come back to the Learn page.", "Pulsa Recargar: esta página se actualiza, como ⌘R en Safari. Luego vuelve a la página Aprender.", k="Reload (⌘R)")]},
  {"id": "shots", "en": "Screenshots and screen recording", "es": "Capturas y grabación de pantalla",
   "why": {"en": "Your MacBook has no Print key, so you have a custom shortcut for screenshots, and the Capture menu has everything else: region, window, recording, text recognition (OCR), QR codes, color picker.",
           "es": "Tu MacBook no tiene tecla Print, así que tienes un atajo propio para capturas, y el menú Captura tiene todo lo demás: región, ventana, grabación, reconocimiento de texto (OCR), códigos QR, selector de color."},
   "steps": [S("Take a screenshot: drag over an area, then press Return to save it.", "Toma una captura: arrastra sobre un área y pulsa Return para guardarla.", k="Screenshot", check="newShot"),
             S("Open the Capture menu to see the other tools.", "Abre el menú Captura para ver las otras herramientas.", k="Capture menu", menu="trigger.capture")]},
  {"id": "emoji", "en": "Emoji 😀", "es": "Emoji 😀", "why": {"en": "Like ⌃⌘Space on macOS.", "es": "Como ⌃⌘Espacio en macOS."},
   "steps": [S("Click in the box below, open the emoji picker and choose one.", "Haz clic en el recuadro, abre el selector de emoji y elige uno.", k="Emojis", check="typed", re="\\p{Extended_Pictographic}", box=True)]},
  {"id": "notifs", "en": "Notifications and focus", "es": "Notificaciones y concentración",
   "why": {"en": "Dismiss notifications from the keyboard, see what you missed, and silence everything (Do Not Disturb).", "es": "Descarta notificaciones con el teclado, revisa lo que te perdiste y silencia todo (No molestar)."},
   "steps": [S("Dismiss the last notification.", "Descarta la última notificación.", k="Dismiss last notification"),
             S("Open the notification history.", "Abre el historial de notificaciones.", k="Open notification history"),
             S("Toggle Do Not Disturb (twice to turn it back on).", "Activa No molestar (dos veces para volver).", k="Toggle silencing notifications")]},
  {"id": "nightlight", "en": "Night light and the Activity monitor", "es": "Luz nocturna y monitor de actividad",
   "why": {"en": "Night light is Night Shift. Activity is the Activity Monitor: see what's using CPU and memory, and kill a frozen app.", "es": "La luz nocturna es Night Shift. Actividad es el Monitor de Actividad: ve qué usa CPU y memoria, y cierra una app congelada."},
   "steps": [S("Toggle night light (and back).", "Activa la luz nocturna (y desactívala).", k="Toggle nightlight"),
             S("Open the Activity monitor; press q to quit it.", "Abre el monitor de actividad; pulsa q para salir.", k="Activity", check="newWindow")]},
 ]},
 {"id": "l4", "en": "4 · Make it yours", "es": "4 · Hazlo tuyo", "lessons": [
  {"id": "theme", "en": "Themes", "es": "Temas",
   "why": {"en": "One click restyles the whole desktop: colors, terminal, bar, wallpaper and lock screen. There are 22 built in.", "es": "Un clic cambia el estilo de todo el escritorio: colores, terminal, barra, fondo y pantalla de bloqueo. Hay 22 incluidos."},
   "steps": [S("Open the theme menu and pick a different theme.", "Abre el menú de temas y elige otro tema.", k="Theme menu", check="themeChanged", menu="style.theme"),
             S("Change the background.", "Cambia el fondo.", k="Background switcher", menu="style.background"),
             S("Hide and show the top bar.", "Oculta y muestra la barra superior.", k="Toggle top bar")]},
  {"id": "rebind", "en": "Your own shortcuts", "es": "Tus propios atajos",
   "why": {"en": "Your shortcuts live in ~/.config/hypr/bindings.lua, which Omarchy never overwrites. Add a line, save, and it applies at once.",
           "es": "Tus atajos viven en ~/.config/hypr/bindings.lua, que Omarchy nunca sobrescribe. Añade una línea, guarda y se aplica al instante."},
   "steps": [S("Open the keybindings settings from the Omarchy menu.", "Abre los ajustes de atajos desde el menú de Omarchy.", menu="setup.keybindings"),
             S("Example line: o.bind(\"SUPER + SHIFT + R\", \"SSH\", \"alacritty -e ssh my-server\")", "Línea de ejemplo: o.bind(\"SUPER + SHIFT + R\", \"SSH\", \"alacritty -e ssh mi-servidor\")", cmd="hyprctl reload && hyprctl configerrors")]},
  {"id": "install", "en": "Installing software", "es": "Instalar software",
   "why": {"en": "Install menu = App Store. pacman/yay = Homebrew. Web apps turn any site into an app. This portal's Apps tab installs your list with one click.",
           "es": "Menú Instalar = App Store. pacman/yay = Homebrew. Las web apps convierten cualquier sitio en app. La pestaña Apps de este portal instala tu lista con un clic."},
   "steps": [S("Open the Install menu and browse it.", "Abre el menú Instalar y explóralo.", menu="install"),
             S("Turn a website into an app with the Web App installer.", "Convierte un sitio web en app con el instalador de Web Apps.", menu="install.webapp")]},
 ]},
 {"id": "l5", "en": "5 · Your MacBook, mastered", "es": "5 · Tu MacBook, dominada", "lessons": [
  {"id": "fnrow", "en": "The top row (F-keys)", "es": "La fila superior (teclas F)",
   "why": {"en": "Your top row works like on macOS: brightness, keyboard light, media and volume without Fn. Hold Fn for F1–F12 (for example Fn+F9 is Omarchy dictation).",
           "es": "Tu fila superior funciona como en macOS: brillo, luz del teclado, multimedia y volumen sin Fn. Mantén Fn para F1–F12 (por ejemplo Fn+F9 es el dictado de Omarchy)."},
   "steps": [S("Press F12 (volume up) or F11 (volume down).", "Pulsa F12 (subir volumen) o F11 (bajar volumen).", check="volumeChanged", keys="F11 / F12"),
             S("Press F5 and F6 to dim and brighten the keyboard backlight.", "Pulsa F5 y F6 para bajar y subir la luz del teclado.", keys="F5 / F6")]},
  {"id": "gestures", "en": "Trackpad gestures", "es": "Gestos del trackpad",
   "why": {"en": ("4 fingers sideways switch spaces; " if DRAG else "3 or 4 fingers sideways switch spaces; ") + "4 up opens the Omarchy menu; 4 down shows the scratchpad; a 4-finger pinch opens the apps menu. " + ("Three fingers drag: slide them to select text or drag things, with no click. " if DRAG else "") + "Two fingers scroll naturally and two-finger click is right-click.",
           "es": ("4 dedos de lado cambian de espacio; " if DRAG else "3 o 4 dedos de lado cambian de espacio; ") + "4 hacia arriba abre el menú de Omarchy; 4 hacia abajo muestra el scratchpad; pellizcar con 4 dedos abre el menú de apps. " + ("Tres dedos arrastran: deslízalos para seleccionar texto o arrastrar cosas, sin hacer clic. " if DRAG else "") + "Dos dedos desplazan de forma natural y el clic con dos dedos es clic derecho."},
   "steps": [S(f"Swipe with {FN} fingers to change space.", f"Desliza con {FN} dedos para cambiar de espacio.", check="wsChange", gesture=f"{FN} ↔")]
             + ([S("Select text on this page by sliding three fingers across it, with no click.", "Selecciona texto de esta página deslizando tres dedos sobre él, sin hacer clic.", gesture="3 drag")] if DRAG else [])
             + [S("Swipe up with 4 fingers to open the Omarchy menu (Esc closes it).", "Desliza hacia arriba con 4 dedos para abrir el menú de Omarchy (Esc lo cierra).", gesture="4 ↑"),
                S("Swipe down with 4 fingers to show the scratchpad.", "Desliza hacia abajo con 4 dedos para mostrar el scratchpad.", check="special", v=True, gesture="4 ↓")]},
  {"id": "health", "en": "Updates, snapshots and help", "es": "Actualizaciones, instantáneas y ayuda",
   "why": {"en": "Update weekly from the Update menu. Before big changes, take a snapshot, a restore point like Time Machine for the system. Super+K lists every shortcut, and this portal is one shortcut away.",
           "es": "Actualiza cada semana desde el menú Actualizar. Antes de cambios grandes toma una instantánea, un punto de restauración como Time Machine para el sistema. Super+K muestra todos los atajos y este portal está a un atajo."},
   "steps": [S("Open the Update menu (you don't have to run it now).", "Abre el menú Actualizar (no hace falta ejecutarlo ahora).", menu="update"),
             S("Open this portal from anywhere.", "Abre este portal desde cualquier lugar.", k="Omarchy Kit")]},
 ]},
]
