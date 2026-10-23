import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import Quickshell.Hyprland

// Spotlight (⌘Space): one search field and four views, as in macOS 26: Apps (⌘1), Files (⌘2), Actions (⌘3), Clipboard (⌘4).
// Type to search, ↑ ↓ to move, Return to open, Esc to close, Tab for the next view. In Apps, a sum such as 12*7 or sqrt(2)*3 shows its answer
// first (Return copies it). Nothing runs until it is open: the window is not mapped while closed, and the file search only runs in Files.
PanelWindow {
  id: win

  property bool shown: false
  property string mode: "apps"
  property string query: ""
  property var results: []
  property int selected: 0
  property var launches: ({})           // desktop id -> how often it was started from here, so the apps you use come first
  readonly property var views: [
    { id: "apps", name: "Apps", hint: "⌘1", icon: "applications-all" },
    { id: "files", name: "Files", hint: "⌘2", icon: "folder" },
    { id: "actions", name: "Actions", hint: "⌘3", icon: "system-run" },
    { id: "clipboard", name: "Clipboard", hint: "⌘4", icon: "edit-paste" }
  ]
  readonly property string home: Quickshell.env("HOME")
  readonly property string statePath: (Quickshell.env("XDG_STATE_HOME") || (home + "/.local/state")) + "/macdock"
  readonly property string clipboardPath: Quickshell.env("MACDOCK_CLIPBOARD") || (home + "/.local/state/omarchy/clipboard-history.json")
  readonly property real rowH: 48
  readonly property int maxRows: 8

  visible: shown
  anchors { top: true; bottom: true; left: true; right: true }
  exclusionMode: ExclusionMode.Ignore
  color: "transparent"
  WlrLayershell.namespace: "macspotlight"
  WlrLayershell.layer: WlrLayer.Overlay
  WlrLayershell.keyboardFocus: shown ? WlrKeyboardFocus.Exclusive : WlrKeyboardFocus.None

  // ---------------------------------------------------------------------------------------------------------------------
  // Pure functions (the tests run these in node).

  // How well `name` matches the typed text: 0 = not at all. Whole name, start of the name, start of a word, anywhere.
  function matchScore(name, q) {
    name = String(name || "").toLowerCase()
    q = String(q || "").trim().toLowerCase()
    if (!q) return 1
    if (name === q) return 100
    if (name.indexOf(q) === 0) return 80
    var words = name.split(/[\s._-]+/)
    for (var i = 0; i < words.length; i++) if (words[i].indexOf(q) === 0) return 60
    return name.indexOf(q) >= 0 ? 40 : 0
  }

  // A sum from the search field, or null when it is not one. Numbers, + - * / % ^, brackets, pi, e and a few functions; never eval.
  function calc(expr) {
    var s = String(expr || "").replace(/^\s*=/, "").replace(/×/g, "*").replace(/÷/g, "/").toLowerCase()
    if (!/[0-9]/.test(s) || !/^[0-9a-z\s.+\-*\/%^()]+$/.test(s) || !/[+\-*\/%^(]/.test(s)) return null
    var pos = 0
    var funcs = { sqrt: Math.sqrt, sin: Math.sin, cos: Math.cos, tan: Math.tan, ln: Math.log, log: Math.log10, abs: Math.abs,
                  round: Math.round, floor: Math.floor, ceil: Math.ceil, exp: Math.exp }
    function ws() { while (s.charAt(pos) === " ") pos++ }
    function number() {
      var m = /^(\d+\.?\d*|\.\d+)(e[+-]?\d+)?/.exec(s.slice(pos))
      if (!m) return NaN
      pos += m[0].length
      return parseFloat(m[0])
    }
    function atom() {
      ws()
      var c = s.charAt(pos)
      if (c === "(") {
        pos++
        var v = sum()
        ws()
        if (s.charAt(pos) !== ")") return NaN
        pos++
        return v
      }
      var w = /^[a-z]+/.exec(s.slice(pos))
      if (w) {
        pos += w[0].length
        if (w[0] === "pi") return Math.PI
        if (w[0] === "e") return Math.E
        if (!funcs.hasOwnProperty(w[0])) return NaN
        ws()
        if (s.charAt(pos) !== "(") return NaN
        return funcs[w[0]](atom())
      }
      return number()
    }
    // A sign binds more loosely than ^ (-2^2 is -4) but a sign after ^ belongs to the exponent (2^-1 is 0.5).
    function signed() {
      ws()
      var c = s.charAt(pos)
      if (c === "-") { pos++; return -signed() }
      if (c === "+") { pos++; return signed() }
      return power()
    }
    function power() {
      var b = atom()
      ws()
      if (s.charAt(pos) === "^") { pos++; return Math.pow(b, signed()) }
      return b
    }
    function product() {
      var v = signed()
      for (;;) {
        ws()
        var c = s.charAt(pos)
        if (c === "*") { pos++; v = v * signed() }
        else if (c === "/") { pos++; v = v / signed() }
        else if (c === "%") { pos++; v = v % signed() }
        else return v
      }
    }
    function sum() {
      var v = product()
      for (;;) {
        ws()
        var c = s.charAt(pos)
        if (c === "+") { pos++; v = v + product() }
        else if (c === "-") { pos++; v = v - product() }
        else return v
      }
    }
    var out = sum()
    ws()
    return (pos === s.length && isFinite(out)) ? out : null
  }

  function showNumber(v) { return String(parseFloat(v.toPrecision(12))) }

  // Files: best match first. The name counts most; among equals the shorter path (closer to home) wins.
  function sortFiles(paths, q) {
    var rows = []
    for (var i = 0; i < paths.length; i++) {
      var p = paths[i].replace(/\/+$/, "")
      if (!p) continue
      var base = p.split("/").pop()
      rows.push({ path: p, base: base, dir: /\/$/.test(paths[i]), score: matchScore(base, q), len: p.length })   // fd ends a folder's path with a slash
    }
    rows.sort(function (a, b) { return b.score - a.score || a.len - b.len || (a.path < b.path ? -1 : 1) })
    return rows
  }

  function iconFor(path, isDir) {
    if (isDir) return "folder"
    var ext = (path.split(".").length > 1 ? path.split(".").pop() : "").toLowerCase()
    if (/^(png|jpe?g|gif|webp|svg|bmp|heic|avif)$/.test(ext)) return "image-x-generic"
    if (/^(mp3|flac|ogg|wav|m4a|opus)$/.test(ext)) return "audio-x-generic"
    if (/^(mp4|mkv|webm|mov|avi)$/.test(ext)) return "video-x-generic"
    if (ext === "pdf") return "application-pdf"
    if (/^(zip|tar|gz|xz|zst|7z|rar)$/.test(ext)) return "package-x-generic"
    return "text-x-generic"
  }

  function tilde(path) { return path.indexOf(win.home + "/") === 0 ? "~" + path.slice(win.home.length) : path }
  function dirname(path) { var i = path.lastIndexOf("/"); return i > 0 ? path.slice(0, i) : "/" }

  // ---------------------------------------------------------------------------------------------------------------------
  // The four views.

  readonly property var actions: [
    { title: "Lock Screen", sub: "Lock the Mac", keys: "lock screen sleep", icon: "system-lock-screen", cmd: ["omarchy-system-lock"] },
    { title: "Restart, Shut Down or Log Out…", sub: "Omarchy's system menu", keys: "power restart reboot shut down shutdown log out logout sleep suspend", icon: "system-shutdown", cmd: ["omarchy-menu", "toggle", "system"] },
    { title: "Control Center", sub: "Wi-Fi, Bluetooth, sound, brightness and more", keys: "settings wifi wi-fi bluetooth sound volume brightness focus night shift", icon: "preferences-system", ipc: ["controlcenter", "toggle"] },
    { title: "Mission Control", sub: "All spaces and their windows", keys: "spaces desktops overview windows", icon: "view-grid", ipc: ["mission", "toggle"] },
    { title: "Show or Hide the Dock", sub: "Turn Dock hiding on or off", keys: "dock autohide", icon: "preferences-desktop", ipc: ["dock", "toggleAutohide"] },
    { title: "Toggle Night Light", sub: "Warmer colours in the evening", keys: "night shift nightlight warm blue light", icon: "weather-clear-night", cmd: ["omarchy-toggle-nightlight"] },
    { title: "Toggle Do Not Disturb", sub: "Silence notifications", keys: "focus notifications silence quiet dnd", icon: "notification-disabled", cmd: ["omarchy-toggle-notification-silencing"] },
    { title: "Toggle Lock on Idle", sub: "Lock the screen when you step away", keys: "idle screensaver sleep timeout", icon: "preferences-system-time", cmd: ["omarchy-toggle-idle"] },
    { title: "Toggle the Menu Bar", sub: "Hide or show the top bar", keys: "bar menu bar top", icon: "view-fullscreen", cmd: ["omarchy-toggle-bar"] },
    { title: "Take a Screenshot", sub: "Pick an area or a window", keys: "capture screen shot print", icon: "applets-screenshooter", cmd: ["omarchy-capture-screenshot"] },
    { title: "Record the Screen", sub: "Start or stop a screen recording", keys: "capture screen recording video", icon: "media-record", cmd: ["sh", "-c", "omarchy-capture-screenrecording --stop-recording || omarchy-menu toggle trigger.capture.screenrecord"] },
    { title: "Copy Text from the Screen", sub: "Recognise text in an area (OCR)", keys: "ocr text capture live text", icon: "edit-select-all", cmd: ["omarchy-capture-text"] },
    { title: "Pick a Colour", sub: "Copy the colour under the pointer", keys: "color colour picker eyedropper", icon: "color-picker", cmd: ["sh", "-c", "pkill hyprpicker || hyprpicker -a"] },
    { title: "Emoji and Symbols", sub: "Find an emoji and paste it", keys: "emoji symbols characters", icon: "face-smile", cmd: ["omarchy-shell", "shell", "toggle", "omarchy.emojis"] },
    { title: "Calculator", sub: "Open the calculator", keys: "calc math", icon: "accessories-calculator", cmd: ["omacalc"] },
    { title: "Notification History", sub: "Earlier notifications", keys: "notifications centre center history", icon: "preferences-system-notifications", cmd: ["omarchy-shell", "notifications", "showHistory"] },
    { title: "Change the Theme", sub: "Colours and look of the desktop", keys: "appearance dark light theme style", icon: "preferences-desktop-theme", cmd: ["omarchy-menu", "toggle", "theme"] },
    { title: "Change the Wallpaper", sub: "Pick a desktop picture", keys: "background wallpaper desktop picture", icon: "preferences-desktop-wallpaper", cmd: ["omarchy-menu", "toggle", "background"] },
    { title: "Wi-Fi, Bluetooth and Sound…", sub: "Hardware settings", keys: "network wifi wi-fi bluetooth audio sound volume display", icon: "preferences-system-network", cmd: ["omarchy-menu", "toggle", "hardware"] },
    { title: "Keyboard Shortcuts", sub: "Every key binding", keys: "keys keybindings shortcuts hotkeys", icon: "input-keyboard", cmd: ["omarchy-menu-keybindings"] },
    { title: "Omarchy Menu", sub: "Apps, style, setup, install, update", keys: "settings system preferences omarchy menu", icon: "preferences-system", cmd: ["omarchy-menu", "toggle", "root"] },
    { title: "About This Mac", sub: "This computer", keys: "about system info computer", icon: "help-about", cmd: ["omarchy-launch-about"] },
    { title: "Clipboard History", sub: "Everything you copied lately", keys: "copy paste history", icon: "edit-paste", view: "clipboard" }
  ]

  property var clipboard: []

  function appResults(q) {
    var out = [], list = DesktopEntries.applications.values
    var sum = calc(q)
    if (sum !== null) out.push({ kind: "calc", title: "= " + showNumber(sum), sub: "Press Return to copy the answer", icon: "accessories-calculator", value: showNumber(sum), verb: "Copy" })
    for (var i = 0; i < list.length; i++) {
      var e = list[i]
      if (e.noDisplay) continue
      var s = matchScore(e.name, q)
      if (!s && q.trim()) {
        var more = (e.genericName || "") + " " + (e.keywords ? e.keywords.join(" ") : "") + " " + (e.comment || "")
        s = more.toLowerCase().indexOf(q.trim().toLowerCase()) >= 0 ? 20 : 0
      }
      if (!s) continue
      var used = win.launches[e.id] || 0
      out.push({ kind: "app", title: e.name, sub: e.genericName || e.comment || "", icon: e.icon, entry: e, score: s + Math.min(used, 20) / 2, used: used, verb: "Open" })
    }
    var apps = out.filter(function (r) { return r.kind === "app" })
    apps.sort(function (a, b) { return b.score - a.score || (a.title < b.title ? -1 : 1) })
    // With nothing typed, show what you use most (and a few more) instead of the whole alphabet.
    if (!q.trim()) apps = apps.filter(function (r) { return r.used > 0 }).concat(apps.filter(function (r) { return r.used === 0 })).slice(0, 12)
    return out.filter(function (r) { return r.kind === "calc" }).concat(apps.slice(0, 60))
  }

  function actionResults(q) {
    var out = []
    for (var i = 0; i < win.actions.length; i++) {
      var a = win.actions[i]
      var s = Math.max(matchScore(a.title, q), (!q.trim() || (a.keys + " " + a.sub).toLowerCase().indexOf(q.trim().toLowerCase()) >= 0) ? 20 : 0)
      if (s) out.push({ kind: "action", title: a.title, sub: a.sub, icon: a.icon, action: a, score: s, verb: a.view ? "Show" : "Run" })
    }
    return out
  }

  function clipboardResults(q) {
    var out = [], text = q.trim().toLowerCase()
    for (var i = 0; i < win.clipboard.length && out.length < 60; i++) {
      var c = win.clipboard[i]
      if (c.type === "text") {
        var line = String(c.text).replace(/\s+/g, " ").trim()
        if (text && line.toLowerCase().indexOf(text) < 0) continue
        out.push({ kind: "clip", title: line.length > 90 ? line.slice(0, 90) + "…" : line, sub: String(c.text).length > 90 ? String(c.text).length + " characters" : "Text", icon: "text-x-generic", index: i, verb: "Paste" })
      } else if (c.type === "image" && !text) {
        out.push({ kind: "clipimage", title: "Image", sub: c.path, icon: "image-x-generic", path: c.path, mime: c.mime, verb: "Copy" })
      }
    }
    return out
  }

  function refresh() {
    selected = 0
    if (mode === "apps") results = appResults(query)
    else if (mode === "actions") results = actionResults(query)
    else if (mode === "clipboard") results = clipboardResults(query)
    else { results = []; findSoon.restart() }
    list.positionViewAtBeginning()
  }

  // Files: fd, one at a time, only while the Files view has two or more characters to look for.
  property string findFor: ""
  property string findPending: ""
  Timer { id: findSoon; interval: 180; onTriggered: win.startFind() }

  function startFind() {
    var q = win.query.trim()
    if (win.mode !== "files" || q.length < 2) { win.results = []; return }
    if (finder.running) { win.findPending = q; return }
    win.findFor = q
    finder.command = ["fd", "-F", "-i", "--max-results", "120", "--color", "never", "--exclude", "node_modules", "--type", "f", "--type", "d", "--", q, win.home]
    finder.running = true
  }

  Process {
    id: finder
    stdout: StdioCollector {
      onStreamFinished: {
        if (win.findFor !== win.query.trim() || win.mode !== "files") return      // an answer to a question nobody is asking any more
        var rows = win.sortFiles(text.split("\n").filter(function (l) { return l.length }), win.findFor).slice(0, 50)
        win.results = rows.map(function (r) {
          return { kind: "file", title: r.base, sub: win.tilde(win.dirname(r.path)), icon: win.iconFor(r.path, r.dir), path: r.path, verb: r.dir ? "Open Folder" : "Open" }
        })
        win.selected = 0
      }
    }
    onRunningChanged: if (!running && win.findPending !== "") { win.findPending = ""; win.startFind() }
  }

  // ---------------------------------------------------------------------------------------------------------------------
  // Opening, closing, running.

  function open(view) {
    win.mode = view || "apps"
    win.query = ""
    field.text = ""
    win.shown = true
    win.readClipboard()
    win.refresh()
    field.forceActiveFocus()
  }

  function close() { win.shown = false }
  function toggle() { if (win.shown) win.close(); else win.open("apps") }

  function setMode(id) {
    if (win.mode === id) return
    win.mode = id
    if (id === "clipboard") win.readClipboard()
    win.refresh()
  }

  function cycle(dir) {
    var i = 0
    for (var k = 0; k < win.views.length; k++) if (win.views[k].id === win.mode) i = k
    win.setMode(win.views[(i + dir + win.views.length) % win.views.length].id)
  }

  function move(delta) {
    if (win.results.length === 0) return
    win.selected = Math.max(0, Math.min(win.results.length - 1, win.selected + delta))
    list.positionViewAtIndex(win.selected, ListView.Contain)
  }

  property var pending: []
  Timer { id: later; interval: 220; onTriggered: { if (win.pending.length) Quickshell.execDetached(win.pending); win.pending = [] } }

  // Run something once Spotlight is gone, so a screenshot or a paste sees the window that had the focus before.
  function runLater(cmd) { win.pending = cmd; later.restart() }

  function activate(reveal) {
    var r = win.results[win.selected]
    if (!r) return
    if (r.kind === "app") {
      win.bump(r.entry.id)
      win.close()
      r.entry.execute()
    } else if (r.kind === "calc") {
      win.close()
      Quickshell.execDetached(["wl-copy", r.value])
    } else if (r.kind === "file") {
      win.close()
      Quickshell.execDetached(["xdg-open", reveal ? win.dirname(r.path) : r.path])
    } else if (r.kind === "action") {
      if (r.action.view) { win.setMode(r.action.view); return }
      win.close()
      if (r.action.ipc) win.runLater(["quickshell", "ipc", "-p", Quickshell.shellDir, "call", r.action.ipc[0], r.action.ipc[1]])
      else win.runLater(r.action.cmd)
    } else if (r.kind === "clip") {
      win.close()
      win.runLater(["omarchy-clipboard-paste-text", "--shift-insert", "--history-index", String(r.index)])
    } else if (r.kind === "clipimage") {
      win.close()
      win.runLater(["sh", "-c", "wl-copy -t \"$2\" < \"$1\"", "sh", r.path, r.mime || "image/png"])
    }
  }

  // ---- how often each app was started from here
  function bump(id) {
    var next = {}
    for (var k in win.launches) next[k] = win.launches[k]
    next[id] = (next[id] || 0) + 1
    win.launches = next
    usage.setText(JSON.stringify({ launches: next }, null, 2) + "\n")
  }

  Process { command: ["mkdir", "-p", win.statePath]; running: true }
  FileView {
    id: usage
    path: win.statePath + "/spotlight.json"
    atomicWrites: true
    printErrors: false      // the first run has no file yet
    onLoaded: { try { win.launches = JSON.parse(text()).launches || ({}) } catch (e) { win.launches = ({}) } }
    onLoadFailed: win.launches = ({})
  }

  // ---- clipboard history, written by Omarchy's clipboard overlay
  function readClipboard() { clipFile.reload() }
  FileView {
    id: clipFile
    printErrors: false
    path: win.clipboardPath
    onLoaded: {
      var rows = []
      try { var data = JSON.parse(text()); if (Array.isArray(data)) rows = data } catch (e) { rows = [] }
      win.clipboard = rows
      if (win.mode === "clipboard") win.refresh()
    }
    onLoadFailed: { win.clipboard = []; if (win.mode === "clipboard") win.refresh() }
  }

  // ---------------------------------------------------------------------------------------------------------------------
  // The window.

  MouseArea { anchors.fill: parent; onClicked: win.close() }

  Rectangle {
    id: panel
    anchors.horizontalCenter: parent.horizontalCenter
    y: Math.round(parent.height * 0.16)
    width: Math.min(680, parent.width - 40)
    height: header.height + (win.results.length > 0 || emptyHint.visible ? 10 + body.height + 10 : 0)
    radius: 22
    color: Qt.rgba(Theme.background.r, Theme.background.g, Theme.background.b, 0.97)     // readable over anything
    border.width: 1
    border.color: Theme.hairline
    Behavior on height { NumberAnimation { duration: 90; easing.type: Easing.OutCubic } }

    MouseArea { anchors.fill: parent }      // clicks inside never reach the backdrop

    Column {
      id: header
      width: parent.width
      Item {
        width: parent.width
        height: 58
        Text {
          id: glass
          anchors.left: parent.left
          anchors.leftMargin: 22
          anchors.verticalCenter: parent.verticalCenter
          text: "⌕"
          font.pixelSize: 26
          color: Theme.label
          opacity: 0.6
        }
        TextInput {
          id: field
          anchors.left: glass.right
          anchors.leftMargin: 12
          anchors.right: parent.right
          anchors.rightMargin: 22
          anchors.verticalCenter: parent.verticalCenter
          font.pixelSize: 22
          color: Theme.label
          selectionColor: Theme.accent
          clip: true
          focus: true
          onTextChanged: { win.query = text; win.refresh() }
          Text {
            visible: field.text.length === 0
            anchors.fill: parent
            verticalAlignment: Text.AlignVCenter
            text: win.mode === "files" ? "Search files and folders" : win.mode === "actions" ? "Search actions" : win.mode === "clipboard" ? "Search the clipboard" : "Spotlight Search"
            font.pixelSize: 22
            color: Theme.label
            opacity: 0.4
          }
          Keys.onPressed: function (e) {
            var held = e.modifiers & (Qt.ControlModifier | Qt.AltModifier | Qt.MetaModifier)
            var ctrl = e.modifiers & Qt.ControlModifier
            if (e.key === Qt.Key_Escape) win.close()
            else if (e.key === Qt.Key_Down || (ctrl && e.key === Qt.Key_N)) win.move(1)
            else if (e.key === Qt.Key_Up || (ctrl && e.key === Qt.Key_P)) win.move(-1)
            else if (e.key === Qt.Key_PageDown) win.move(win.maxRows - 1)
            else if (e.key === Qt.Key_PageUp) win.move(-(win.maxRows - 1))
            else if (e.key === Qt.Key_Return || e.key === Qt.Key_Enter) win.activate(ctrl)
            else if (e.key === Qt.Key_Tab) win.cycle(1)
            else if (e.key === Qt.Key_Backtab) win.cycle(-1)
            else if (held && e.key >= Qt.Key_1 && e.key <= Qt.Key_4) win.setMode(win.views[e.key - Qt.Key_1].id)
            else return
            e.accepted = true
          }
        }
      }

      // The four views.
      Row {
        leftPadding: 18
        spacing: 6
        height: 36
        Repeater {
          model: win.views
          delegate: Rectangle {
            required property var modelData
            readonly property bool on: win.mode === modelData.id
            height: 28
            width: chip.implicitWidth + 22
            radius: 14
            color: on ? Qt.rgba(Theme.accent.r, Theme.accent.g, Theme.accent.b, 0.85) : "transparent"
            border.width: on ? 0 : 1
            border.color: Theme.hairline
            Text {
              id: chip
              anchors.centerIn: parent
              text: modelData.name + "  " + modelData.hint
              font.pixelSize: 13
              color: on ? "white" : Theme.label
              opacity: on ? 1 : 0.8
            }
            MouseArea { anchors.fill: parent; onClicked: { win.setMode(modelData.id); field.forceActiveFocus() } }
          }
        }
      }
    }

    Item {
      id: body
      anchors.top: header.bottom
      anchors.topMargin: 10
      anchors.left: parent.left
      anchors.right: parent.right
      anchors.leftMargin: 10
      anchors.rightMargin: 10
      height: Math.max(win.rowH, Math.min(win.results.length, win.maxRows) * win.rowH)

      Text {
        id: emptyHint
        visible: win.shown && win.results.length === 0
        anchors.centerIn: parent
        text: win.mode === "files" && win.query.trim().length < 2 ? "Type two letters of a file or folder name" : "No results"
        font.pixelSize: 15
        color: Theme.label
        opacity: 0.5
      }

      ListView {
        id: list
        anchors.fill: parent
        clip: true
        model: win.results
        currentIndex: win.selected
        boundsBehavior: Flickable.StopAtBounds
        delegate: Rectangle {
          required property int index
          required property var modelData
          readonly property bool on: index === win.selected
          width: list.width
          height: win.rowH
          radius: 12
          color: on ? Qt.rgba(Theme.accent.r, Theme.accent.g, Theme.accent.b, 0.85) : "transparent"

          AppIcon {
            id: ico
            anchors.left: parent.left
            anchors.leftMargin: 12
            anchors.verticalCenter: parent.verticalCenter
            size: 30
            icon: modelData.icon || ""
            label: modelData.title || ""
            plain: modelData.kind !== "app"
          }
          Column {
            anchors.left: ico.right
            anchors.leftMargin: 12
            anchors.right: verb.left
            anchors.rightMargin: 10
            anchors.verticalCenter: parent.verticalCenter
            Text {
              width: parent.width
              text: modelData.title
              elide: Text.ElideRight
              font.pixelSize: 15
              color: on ? "white" : Theme.label
            }
            Text {
              width: parent.width
              visible: text.length > 0
              text: modelData.sub || ""
              elide: Text.ElideMiddle
              font.pixelSize: 12
              color: on ? "white" : Theme.label
              opacity: on ? 0.85 : 0.55
            }
          }
          Text {
            id: verb
            anchors.right: parent.right
            anchors.rightMargin: 14
            anchors.verticalCenter: parent.verticalCenter
            visible: on
            text: "↩ " + (modelData.verb || "Open")
            font.pixelSize: 12
            color: "white"
            opacity: 0.9
          }
          MouseArea {
            anchors.fill: parent
            hoverEnabled: true
            onEntered: win.selected = index
            onClicked: { win.selected = index; win.activate(false) }
          }
        }
      }
    }
  }

  GlobalShortcut { appid: "macspotlight"; name: "toggle"; description: "Spotlight (⌘Space)"; onPressed: win.toggle() }

  IpcHandler {
    target: "spotlight"
    function toggle(): void { win.toggle() }
    function open(view: string): void { win.open(view || "apps") }
    function close(): void { win.close() }
    function visible(): bool { return win.shown }
    // ---- for tests: type without a keyboard and describe what is listed
    function search(text: string): void { field.text = text }
    function mode(): string { return win.mode }
    function setMode(id: string): void { win.setMode(id) }
    function titles(): string { return win.results.map(function (r) { return r.kind + ":" + r.title }).join(" | ") }
    function selectedTitle(): string { return win.results[win.selected] ? win.results[win.selected].title : "" }
  }
}
