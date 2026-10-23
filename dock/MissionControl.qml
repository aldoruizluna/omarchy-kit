import QtQuick
import Quickshell
import Quickshell.Wayland
import Quickshell.Hyprland
import Quickshell.Widgets
import Quickshell.Io

// Mission Control (F3, Super+Ctrl+Up, four fingers up) and App Exposé (Super+Ctrl+Down).
//
// A full-screen overlay: the wallpaper dimmed and tinted, a Spaces bar across the top with one card per workspace, and the windows of
// the selected space scaled to fit below it, each with its app icon and title. Click a window to go to it; click a space card to look at
// that space, double-click (or Return) to go there; "+" goes to the next empty space. Esc, a click on empty space or the same key again
// closes it. App Exposé shows only the windows of the focused app, from every space.
//
// While it is closed nothing is mapped and nothing is captured. When it opens, each window is captured once (not live): this laptop has
// Intel HD 4600 graphics driving 2880x1800, and a live capture of every window would cost far more than a glance at them is worth.
PanelWindow {
  id: win

  property bool shown: false
  property string mode: "all"            // "all" = Mission Control, "app" = App Exposé
  property var spaces: []                // snapshot taken when it opens: [{ id, name, current, windows: [...] }]
  property int spaceIndex: 0             // selected space; spaces.length means the "+" card
  property int winIndex: 0
  property string area: "windows"        // which row the keyboard moves in: "spaces" or "windows"
  property string exposeName: ""

  readonly property bool withBar: mode === "all"
  readonly property var chosen: spaceIndex < spaces.length ? spaces[spaceIndex] : null
  readonly property var wins: chosen ? chosen.windows : []

  readonly property real barH: withBar ? 150 : 70
  readonly property real areaX: 70
  readonly property real areaY: barH + 24
  readonly property real areaW: width - areaX * 2
  readonly property real areaH: height - areaY - 56
  readonly property real labelH: 40
  readonly property real gap: 30

  visible: shown
  anchors { top: true; bottom: true; left: true; right: true }
  exclusionMode: ExclusionMode.Ignore
  color: "transparent"
  WlrLayershell.namespace: "macmission"
  WlrLayershell.layer: WlrLayer.Overlay
  WlrLayershell.keyboardFocus: shown ? WlrKeyboardFocus.Exclusive : WlrKeyboardFocus.None

  // ------------------------------------------------------------------------------------------------------- data

  function usable(ws) {
    return ws && ws.id > 0 && String(ws.name).indexOf("special:") !== 0   // windows hidden with ⌘H live on special:hidden and are left out
  }

  function describeWindow(t, wsId) {
    var ipc = t.lastIpcObject || {}
    var size = ipc.size || [0, 0]
    var appId = ipc["class"] || (t.wayland ? t.wayland.appId : "")
    var entry = Apps.entryFor(appId)
    return { top: t, wl: t.wayland, address: t.address, appId: appId, title: t.title || "",
             name: entry ? entry.name : Apps.prettyName(appId), icon: entry ? entry.icon : appId,
             w: size[0] || 0, h: size[1] || 0, space: wsId }
  }

  function snapshot(kind) {
    var tops = Hyprland.toplevels.values
    var list = Hyprland.workspaces.values
    var byId = {}, out = []
    function space(ws) {
      if (!byId[ws.id]) { byId[ws.id] = { id: ws.id, name: String(ws.name), current: false, windows: [] }; out.push(byId[ws.id]) }
      return byId[ws.id]
    }
    for (var i = 0; i < list.length; i++) if (usable(list[i])) space(list[i])
    var focused = Hyprland.focusedWorkspace
    if (focused && usable(focused)) { space(focused).current = true }
    var activeClass = ""
    if (Hyprland.activeToplevel) activeClass = (Hyprland.activeToplevel.lastIpcObject || {})["class"] || ""
    var everything = []
    for (var j = 0; j < tops.length; j++) {
      var ws = tops[j].workspace
      if (!usable(ws)) continue
      var d = describeWindow(tops[j], ws.id)
      space(ws).windows.push(d)
      everything.push(d)
    }
    out.sort(function (a, b) { return a.id - b.id })
    if (kind === "app") {
      var mine = everything.filter(function (d) { return d.appId === activeClass })
      win.exposeName = mine.length ? mine[0].name : ""
      return [{ id: 0, name: "app", current: true, windows: mine }]
    }
    return out
  }

  function nextFreeSpace() {
    var used = {}
    for (var i = 0; i < spaces.length; i++) if (spaces[i].windows.length > 0 || spaces[i].current) used[spaces[i].id] = true
    for (var n = 1; n < 100; n++) if (!used[n]) return n
    return 1
  }

  // ------------------------------------------------------------------------------------------------------- layout
  // Mission Control keeps every window's proportions and puts them in rows of one common height, as large as the screen allows: try 1 to
  // 6 rows, split the windows into rows of about equal total width, and keep the arrangement with the tallest rows.
  function layoutCards(list, W, H) {
    var n = list.length
    if (n === 0 || W <= 0 || H <= 0) return []
    var asp = [], tallest = 0, total = 0, i
    for (i = 0; i < n; i++) {
      var a = (list[i].w > 0 && list[i].h > 0) ? list[i].w / list[i].h : 1.6
      asp.push(a); total += a
      tallest = Math.max(tallest, list[i].h > 0 ? list[i].h : 600)
    }
    var best = null
    for (var rows = 1; rows <= Math.min(n, 6); rows++) {
      var groups = [], cur = [], run = 0
      for (i = 0; i < n; i++) {
        cur.push(i); run += asp[i]
        if (groups.length < rows - 1 && run >= total * (groups.length + 1) / rows - 1e-9) { groups.push(cur); cur = [] }
      }
      if (cur.length) groups.push(cur)
      var h = Infinity
      for (var g = 0; g < groups.length; g++) {
        var s = 0
        for (var k = 0; k < groups[g].length; k++) s += asp[groups[g][k]]
        h = Math.min(h, (W - gap * (groups[g].length - 1)) / s)
      }
      h = Math.min(h, (H - groups.length * labelH - gap * (groups.length - 1)) / groups.length, tallest * 0.92)
      if (!best || h > best.h) best = { h: h, groups: groups }
    }
    var used = best.groups.length * (best.h + labelH) + gap * (best.groups.length - 1)
    var y = Math.max(0, (H - used) / 2)
    var cards = new Array(n)
    for (var r = 0; r < best.groups.length; r++) {
      var grp = best.groups[r], rowW = gap * (grp.length - 1)
      for (var m = 0; m < grp.length; m++) rowW += asp[grp[m]] * best.h
      var x = Math.max(0, (W - rowW) / 2)
      for (var q = 0; q < grp.length; q++) {
        var w = asp[grp[q]] * best.h
        cards[grp[q]] = { x: x, y: y, w: w, h: best.h }
        x += w + gap
      }
      y += best.h + labelH + gap
    }
    return cards
  }

  readonly property var cards: layoutCards(wins, areaW, areaH)

  // ------------------------------------------------------------------------------------------------------- actions

  // Hyprland's window and workspace lists are filled by an asynchronous request, so opening asks for a fresh copy and takes the
  // snapshot a moment later (the overlay appears about a tenth of a second after the key). The lists are also asked for once at startup.
  property string pendingKind: ""

  function openOverview(kind) {
    pendingKind = kind
    Hyprland.refreshWorkspaces()
    Hyprland.refreshToplevels()
    settle.restart()
  }

  function finishOpen() {
    var kind = pendingKind
    pendingKind = ""
    if (kind === "") return
    mode = kind
    spaces = snapshot(kind)
    var cur = 0
    for (var i = 0; i < spaces.length; i++) if (spaces[i].current) cur = i
    spaceIndex = cur
    winIndex = 0
    area = "windows"
    shown = true
  }

  function closeOverview() {
    settle.stop()
    pendingKind = ""
    shown = false
    spaces = []          // drops the window captures with it
  }

  function toggle(kind) {
    if (pendingKind !== "") closeOverview()
    else if (shown && mode === kind) closeOverview()
    else if (shown) { closeOverview(); openOverview(kind) }
    else openOverview(kind)
  }

  Timer { id: settle; interval: 120; onTriggered: win.finishOpen() }

  Component.onCompleted: { Hyprland.refreshWorkspaces(); Hyprland.refreshToplevels() }

  function dispatch(expr) { Quickshell.execDetached(["hyprctl", "dispatch", expr]) }

  function goSpace(id) { dispatch("hl.dsp.focus({ workspace = \"" + id + "\" })") }

  function activateWindow(d) {
    closeOverview()
    // focusing by address also switches to the window's own space
    if (d.address) dispatch("hl.dsp.focus({ window = \"address:" + (String(d.address).indexOf("0x") === 0 ? "" : "0x") + d.address + "\" })")
    else if (d.wl) d.wl.activate()
  }

  function activateSelected() {
    if (area === "spaces") {
      if (spaceIndex >= spaces.length) { var id = nextFreeSpace(); closeOverview(); goSpace(id) }
      else { var sid = spaces[spaceIndex].id; closeOverview(); goSpace(sid) }
      return
    }
    if (winIndex < wins.length) activateWindow(wins[winIndex])
  }

  function closeWindow(d) {
    if (d.wl) d.wl.close()
    var copy = spaces.slice()
    for (var i = 0; i < copy.length; i++) {
      var keep = copy[i].windows.filter(function (x) { return x !== d })
      if (keep.length !== copy[i].windows.length) copy[i] = { id: copy[i].id, name: copy[i].name, current: copy[i].current, windows: keep }
    }
    spaces = copy
    winIndex = Math.max(0, Math.min(winIndex, wins.length - 1))
  }

  function clamp(v, lo, hi) { return Math.max(lo, Math.min(hi, v)) }

  // Arrow keys. Left and right move along the row; up and down move between the Spaces bar and the windows, and between rows of windows.
  function move(dx, dy) {
    if (area === "spaces") {
      if (dx) { spaceIndex = clamp(spaceIndex + dx, 0, spaces.length); winIndex = 0 }
      else if (dy > 0 && wins.length) area = "windows"
      return
    }
    if (wins.length === 0) { if (dy < 0 && withBar) area = "spaces"; return }
    if (dx) { winIndex = clamp(winIndex + dx, 0, wins.length - 1); return }
    var c = cards[winIndex]
    if (!c) return
    var cx = c.x + c.w / 2, best = -1, bestDist = 1e9
    for (var i = 0; i < cards.length; i++) {
      if (!cards[i] || i === winIndex) continue
      if (dy > 0 ? cards[i].y <= c.y + 1 : cards[i].y >= c.y - 1) continue
      var rowDist = Math.abs(cards[i].y - c.y)
      var dist = rowDist * 4 + Math.abs(cards[i].x + cards[i].w / 2 - cx)
      if (dist < bestDist) { bestDist = dist; best = i }
    }
    if (best >= 0) winIndex = best
    else if (dy < 0 && withBar) area = "spaces"
  }

  // ------------------------------------------------------------------------------------------------------- picture

  Loader {
    anchors.fill: parent
    active: win.shown
    sourceComponent: Item {
      Image {
        anchors.fill: parent
        source: "file://" + Quickshell.env("HOME") + "/.local/state/omarchy/current/background"
        fillMode: Image.PreserveAspectCrop
        sourceSize.width: Math.round(win.width * win.devicePixelRatio)
        sourceSize.height: Math.round(win.height * win.devicePixelRatio)
        asynchronous: false
        cache: false
      }
      Rectangle { anchors.fill: parent; color: Qt.rgba(Theme.background.r, Theme.background.g, Theme.background.b, Theme.dark ? 0.72 : 0.55) }
    }
  }

  MouseArea { anchors.fill: parent; onClicked: win.closeOverview() }

  FocusScope {
    id: scope
    anchors.fill: parent
    focus: true
    opacity: win.shown ? 1 : 0
    Behavior on opacity { NumberAnimation { duration: 110; easing.type: Easing.OutCubic } }

    Keys.onPressed: function (e) {
      if (e.key === Qt.Key_Escape) win.closeOverview()
      else if (e.key === Qt.Key_Left) win.move(-1, 0)
      else if (e.key === Qt.Key_Right) win.move(1, 0)
      else if (e.key === Qt.Key_Up) win.move(0, -1)
      else if (e.key === Qt.Key_Down) win.move(0, 1)
      else if (e.key === Qt.Key_Return || e.key === Qt.Key_Enter) win.activateSelected()
      else if (e.key === Qt.Key_Tab) win.move(1, 0)
      else if (e.key === Qt.Key_Backtab) win.move(-1, 0)
      else return
      e.accepted = true
    }

    // ---- Spaces bar
    Item {
      id: bar
      visible: win.withBar
      anchors.top: parent.top
      anchors.topMargin: 34
      anchors.horizontalCenter: parent.horizontalCenter
      height: 108
      width: spaceRow.width

      Row {
        id: spaceRow
        spacing: 18
        height: parent.height

        Repeater {
          model: win.shown && win.withBar ? win.spaces : []
          delegate: Rectangle {
            id: sc
            required property var modelData
            required property int index
            readonly property bool selected: win.area === "spaces" && win.spaceIndex === index
            readonly property bool viewing: win.spaceIndex === index
            width: 196
            height: 108
            radius: 14
            color: viewing ? Qt.rgba(Theme.foreground.r, Theme.foreground.g, Theme.foreground.b, 0.18) : Qt.rgba(Theme.foreground.r, Theme.foreground.g, Theme.foreground.b, 0.08)
            border.width: modelData.current ? 3 : (selected ? 2 : 1)
            border.color: modelData.current || selected ? Theme.accent : Theme.hairline

            Text {
              anchors.top: parent.top; anchors.topMargin: 12
              anchors.horizontalCenter: parent.horizontalCenter
              text: "Desktop " + sc.modelData.id
              color: Theme.label; font.pixelSize: 14; font.bold: true
            }
            // the apps on that space, as a row of small icons
            Row {
              anchors.centerIn: parent
              anchors.verticalCenterOffset: 12
              spacing: 8
              Repeater {
                model: {
                  var seen = {}, out = []
                  for (var i = 0; i < sc.modelData.windows.length && out.length < 5; i++) {
                    var d = sc.modelData.windows[i]
                    if (!seen[d.appId]) { seen[d.appId] = true; out.push(d) }
                  }
                  return out
                }
                delegate: AppIcon { required property var modelData; size: 30; icon: modelData.icon || ""; label: modelData.name || "" }
              }
            }
            Text {
              visible: sc.modelData.windows.length === 0
              anchors.centerIn: parent; anchors.verticalCenterOffset: 12
              text: "empty"; color: Theme.label; opacity: 0.5; font.pixelSize: 13
            }
            MouseArea {
              anchors.fill: parent
              onClicked: { win.spaceIndex = sc.index; win.winIndex = 0; win.area = "spaces" }
              onDoubleClicked: { var id = sc.modelData.id; win.closeOverview(); win.goSpace(id) }
            }
          }
        }

        // "+": a new space
        Rectangle {
          readonly property bool selected: win.area === "spaces" && win.spaceIndex === win.spaces.length
          width: 108; height: 108; radius: 14
          color: Qt.rgba(Theme.foreground.r, Theme.foreground.g, Theme.foreground.b, 0.08)
          border.width: selected ? 2 : 1
          border.color: selected ? Theme.accent : Theme.hairline
          Text { anchors.centerIn: parent; text: "+"; color: Theme.label; font.pixelSize: 40; font.weight: Font.Light }
          MouseArea {
            anchors.fill: parent
            onClicked: { var id = win.nextFreeSpace(); win.closeOverview(); win.goSpace(id) }
          }
        }
      }
    }

    // ---- App Exposé title
    Text {
      visible: !win.withBar
      anchors.top: parent.top; anchors.topMargin: 30
      anchors.horizontalCenter: parent.horizontalCenter
      text: win.exposeName
      color: Theme.label; font.pixelSize: 22; font.bold: true
    }

    // ---- The windows
    Item {
      id: grid
      x: win.areaX; y: win.areaY; width: win.areaW; height: win.areaH

      Text {
        visible: win.shown && win.wins.length === 0
        anchors.centerIn: parent
        text: win.withBar ? "No windows on this desktop" : "No windows"
        color: Theme.label; opacity: 0.6; font.pixelSize: 20
      }

      Repeater {
        model: win.shown ? win.wins : []
        delegate: Item {
          id: card
          required property var modelData
          required property int index
          readonly property var box: win.cards[index] || ({ x: 0, y: 0, w: 0, h: 0 })
          readonly property bool selected: win.area === "windows" && win.winIndex === index
          property bool hovered: false

          x: box.x; y: box.y; width: box.w; height: box.h + win.labelH

          ClippingRectangle {
            id: frame
            width: card.width; height: card.box.h
            radius: 12
            color: Qt.rgba(Theme.background.r, Theme.background.g, Theme.background.b, 0.9)
            border.width: card.selected || card.hovered ? 4 : 1
            border.color: card.selected || card.hovered ? Theme.accent : Theme.hairline

            // the window itself, captured once when the overview opened
            ScreencopyView {
              id: shot
              anchors.fill: parent
              captureSource: card.modelData.wl
              live: false
              paintCursor: false
              visible: hasContent
            }
            // when a window cannot be captured: its icon on a dark card
            AppIcon {
              visible: !shot.hasContent
              anchors.centerIn: parent
              size: Math.min(card.width, card.box.h) * 0.42
              icon: card.modelData.icon || ""
              label: card.modelData.name || ""
            }
          }

          Row {
            anchors.top: frame.bottom; anchors.topMargin: 8
            anchors.horizontalCenter: parent.horizontalCenter
            spacing: 8
            AppIcon { size: 22; icon: card.modelData.icon || ""; label: card.modelData.name || "" }
            Text {
              anchors.verticalCenter: parent.verticalCenter
              width: Math.min(implicitWidth, card.width - 40)
              elide: Text.ElideRight
              text: card.modelData.title || card.modelData.name
              color: Theme.label; font.pixelSize: 14
            }
            Text {
              visible: !win.withBar && card.modelData.space !== undefined
              anchors.verticalCenter: parent.verticalCenter
              text: "· Desktop " + card.modelData.space
              color: Theme.label; opacity: 0.55; font.pixelSize: 13
            }
          }

          MouseArea {
            anchors.fill: frame
            hoverEnabled: true
            onEntered: { card.hovered = true; win.area = "windows"; win.winIndex = card.index }
            onExited: card.hovered = false
            onClicked: win.activateWindow(card.modelData)
          }

          // close button (top left, appears on hover like the red one in macOS)
          Rectangle {
            visible: card.hovered
            x: -9; y: -9
            width: 28; height: 28; radius: 14
            color: Theme.glassStrong
            border.width: 1; border.color: Theme.hairline
            Text { anchors.centerIn: parent; text: "×"; color: Theme.label; font.pixelSize: 20; anchors.verticalCenterOffset: -1 }
            MouseArea {
              anchors.fill: parent
              hoverEnabled: true
              onEntered: card.hovered = true
              onClicked: win.closeWindow(card.modelData)
            }
          }
        }
      }
    }
  }

  // ------------------------------------------------------------------------------------------------------- triggers

  GlobalShortcut { appid: "macmission"; name: "toggle"; description: "Mission Control"; onPressed: win.toggle("all") }
  GlobalShortcut { appid: "macmission"; name: "appwindows"; description: "App Exposé (windows of this app)"; onPressed: win.toggle("app") }

  IpcHandler {
    target: "mission"
    function toggle(): void { win.toggle("all") }
    function appwindows(): void { win.toggle("app") }
    function open(): void { if (!win.shown && win.pendingKind === "") win.openOverview("all") }
    function close(): void { win.closeOverview() }
    function visible(): bool { return win.shown }
    // ---- for tests: drive the selection without a pointer and describe what is on screen
    function selectSpace(i: int): void { win.area = "spaces"; win.spaceIndex = win.clamp(i, 0, win.spaces.length); win.winIndex = 0 }
    function selectWindow(i: int): void { win.area = "windows"; win.winIndex = win.clamp(i, 0, Math.max(0, win.wins.length - 1)) }
    function activate(): void { win.activateSelected() }
    function closeSelected(): void { if (win.area === "windows" && win.winIndex < win.wins.length) win.closeWindow(win.wins[win.winIndex]) }
    function describe(): string {
      var parts = []
      for (var i = 0; i < win.spaces.length; i++) parts.push(win.spaces[i].id + ":" + win.spaces[i].windows.length)
      return "mode=" + win.mode + " spaces=" + parts.join(",") + " space=" + win.spaceIndex + " window=" + win.winIndex + " area=" + win.area +
             " windows=" + win.wins.length + " cards=" + win.cards.length
    }
  }
}
