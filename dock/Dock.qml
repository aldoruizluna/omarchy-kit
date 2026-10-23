import QtQuick
import Quickshell
import Quickshell.Wayland
import Quickshell.Io

// The dock: a translucent pill at the bottom of the screen with magnification, running dots, bounce on launch and a right-click menu.
PanelWindow {
  id: win

  readonly property real icon: Config.iconSize
  readonly property real pad: 9
  readonly property real dotRoom: 7
  readonly property real gap: 8                       // from the screen edge
  readonly property real pillH: icon + pad * 2 + dotRoom
  readonly property real reach: icon * Config.zoom    // tallest an icon can get
  readonly property bool revealed: !Config.autohide || hover.hovered || menu.visible || revealHold.running

  // Layout: pinned, separator, running (not pinned), separator, Downloads, Trash.
  readonly property var model: Apps.dockItems(Apps.toplevels, Config.pinned)
  readonly property var layout: {
    var out = model.pinned.slice()
    if (model.running.length) { out.push({ key: "~sep-run", kind: "separator" }); out = out.concat(model.running) }
    out.push({ key: "~sep-end", kind: "separator" })
    out.push({ key: "~downloads", kind: "folder", name: "Downloads", icon: "folder-download", windows: [], path: Config.downloads })
    if (Config.showTrash) out.push({ key: "~trash", kind: "trash", name: "Trash", icon: trashFull ? "user-trash-full" : "user-trash", windows: [] })
    return out
  }
  property bool trashFull: false

  // Magnification. The scale of each icon depends on how far its centre is from the pointer, and the centres depend on the scales
  // (bigger icons push their neighbours away), so this is iterated a few times, damped, until the two agree. That keeps the
  // biggest icon under the pointer, as on a Mac. `centre` is the pointer x measured from the middle of the dock.
  function computeScales(items, centre, level) {
    var n = items.length, i, scales = []
    for (i = 0; i < n; i++) scales.push(1)
    if (centre === null || level <= 0.001) return scales
    var sigma = 0.95
    for (var iter = 0; iter < 5; iter++) {
      var widths = [], total = 0
      for (i = 0; i < n; i++) {
        var w = items[i].kind === "separator" ? 14 : icon * scales[i] + 6
        widths.push(w); total += w
      }
      var x = -total / 2
      for (i = 0; i < n; i++) {
        var c = x + widths[i] / 2
        x += widths[i]
        if (items[i].kind === "separator") continue
        var d = Math.abs(centre - c) / icon
        var target = 1 + (Config.zoom - 1) * level * Math.exp(-(d * d) / (2 * sigma * sigma))
        scales[i] = scales[i] * 0.4 + target * 0.6
      }
    }
    return scales
  }

  property var pointerCentre: null
  readonly property var scales: computeScales(layout, pointerCentre, hoverLevel)

  property real hoverLevel: hover.hovered ? 1 : 0
  Behavior on hoverLevel { NumberAnimation { duration: 140; easing.type: Easing.OutCubic } }

  anchors { bottom: true; left: true; right: true }
  implicitHeight: reach + pad * 2 + dotRoom + gap + 64
  exclusiveZone: Config.autohide ? 0 : pillH + gap
  color: "transparent"
  WlrLayershell.namespace: "macdock"
  WlrLayershell.layer: WlrLayer.Top
  mask: Region { item: hit }

  Item {
    id: hit
    anchors.horizontalCenter: parent.horizontalCenter
    anchors.bottom: parent.bottom
    width: pill.width + 24
    height: win.revealed ? win.implicitHeight : 5

    HoverHandler {
      id: hover
      onPointChanged: win.pointerCentre = point.position.x - hit.width / 2
      onHoveredChanged: if (!hovered) { win.pointerCentre = null; revealHold.restart() }
    }

    Timer { id: revealHold; interval: 450 }

    Rectangle {
      id: pill
      anchors.horizontalCenter: parent.horizontalCenter
      anchors.bottom: parent.bottom
      anchors.bottomMargin: win.revealed ? win.gap : -(win.pillH + 16)
      Behavior on anchors.bottomMargin { NumberAnimation { duration: 220; easing.type: Easing.OutCubic } }
      width: row.width + win.pad * 2 + 4
      height: win.pillH
      radius: Math.min(26, win.icon * 0.46)
      color: Theme.glass
      border.width: 1
      border.color: Theme.hairline

      // soft inner highlight along the top edge: the "glass" cue
      Rectangle {
        anchors.fill: parent
        anchors.margins: 1
        radius: parent.radius - 1
        color: "transparent"
        border.width: 1
        border.color: Theme.highlight
      }

      Row {
        id: row
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom
        anchors.bottomMargin: win.pad + win.dotRoom
        spacing: 0

        Repeater {
          id: rep
          model: ScriptModel { values: win.layout; objectProp: "key" }
          delegate: DockIcon {
            required property int index
            required property var modelData
            item: modelData
            magnify: win.scales[index] || 1
            onClicked: function (it, button) { win.handleClick(it, button) }
            onMenuRequested: function (it, anchorItem) { win.openMenu(it, anchorItem) }
            onDragFinished: function (it, dx, dy) { win.finishDrag(it, dx, dy) }
          }
        }
      }
    }
  }

  // A pinned icon was dragged by (dx, dy). Pulled well above the dock it is taken off (as on a Mac); sideways it is dropped before or
  // after the pinned app whose middle is nearest to where it was let go.
  function finishDrag(it, dx, dy) {
    if (dy < -(win.pillH + 60)) { Config.unpin(it.key); return }
    var me = -1, i
    for (i = 0; i < win.layout.length; i++) if (win.layout[i].key === it.key) me = i
    var mine = me >= 0 ? rep.itemAt(me) : null
    if (!mine) return
    var cx = mine.x + mine.width / 2 + dx, best = -1, bestDist = 1e9
    for (i = 0; i < win.layout.length; i++) {
      var other = win.layout[i], el = rep.itemAt(i)
      if (!el || i === me || other.kind !== "app" || !other.pinned) continue
      var d = Math.abs(cx - (el.x + el.width / 2))
      if (d < bestDist) { bestDist = d; best = i }
    }
    if (best < 0) return
    var target = rep.itemAt(best)
    Config.moveTo(it.key, win.layout[best].key, cx > target.x + target.width / 2)
  }

  function handleClick(it, button) {
    if (it.kind === "app") {
      if (button === Qt.MiddleButton && it.entry) it.entry.execute()
      else Apps.focusApp(it)
    } else if (it.kind === "folder") {
      Apps.open(it.path)
    } else if (it.kind === "trash") {
      Apps.open("trash:///")
    }
  }

  function openMenu(it, anchorItem) {
    var list = []
    if (it.kind === "app") {
      for (var i = 0; i < it.windows.length; i++) {
        (function (w) { list.push({ label: w.title || it.name, action: function () { w.activate() } }) })(it.windows[i])
      }
      if (it.windows.length) list.push({ separator: true })
      var acts = it.entry ? it.entry.actions : []
      for (var j = 0; j < acts.length; j++) {
        (function (a) { list.push({ label: a.name, action: function () { a.execute() } }) })(acts[j])
      }
      if (acts.length) list.push({ separator: true })
      if (it.entry) {
        list.push(it.pinned
          ? { label: "Remove from Dock", action: function () { Config.unpin(it.key) } }
          : { label: "Keep in Dock", action: function () { Config.pin(it.key) } })
      } else {
        list.push({ label: "Keep in Dock", disabled: true })
      }
      list.push({ separator: true })
      if (it.windows.length) list.push({ label: "Quit", action: function () { Apps.quitApp(it) } })
      else list.push({ label: "Open", action: function () { if (it.entry) it.entry.execute() } })
    } else if (it.kind === "folder") {
      list.push({ label: "Open", action: function () { Apps.open(it.path) } })
    } else if (it.kind === "trash") {
      list.push({ label: "Open Trash", action: function () { Apps.open("trash:///") } })
      list.push({ label: "Empty Trash", disabled: !win.trashFull, action: function () { Quickshell.execDetached(["gio", "trash", "--empty"]) } })
    }
    menu.openFor(anchorItem, list)
  }

  ItemMenu { id: menu; anchor.window: win }

  // The Trash icon is full when there is something in it.
  Process {
    id: trashProbe
    command: ["sh", "-c", "ls -A \"${XDG_DATA_HOME:-$HOME/.local/share}/Trash/files\" 2>/dev/null | head -n1"]
    stdout: StdioCollector { onStreamFinished: win.trashFull = text.trim().length > 0 }
  }
  Timer { interval: 5000; running: true; repeat: true; triggeredOnStart: true; onTriggered: trashProbe.running = true }

  IpcHandler {
    target: "dock"
    function toggleAutohide(): void { Config.toggleAutohide() }
    function reveal(): void { revealHold.restart() }
    // ---- for tests and the Setup log: what the dock shows, as "key:dots" in order (dots: window count, "b" = background, "-" = not running)
    function describe(): string {
      var out = []
      for (var i = 0; i < win.layout.length; i++) {
        var it = win.layout[i]
        if (it.kind === "separator") { out.push("|"); continue }
        var dots = it.windows && it.windows.length ? String(it.windows.length) : (it.background ? "b" : "-")
        out.push(it.key + ":" + dots)
      }
      return out.join(" ")
    }
    function pinned(): string { return Config.pinned.join(",") }
    function moveTo(id: string, target: string, after: bool): bool { return Config.moveTo(id, target, after) }
  }
}
