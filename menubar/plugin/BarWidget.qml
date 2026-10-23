import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Hyprland
import Quickshell.Wayland
import qs.Commons
import qs.Ui

// The left side of the macOS menu bar: the system menu, the name of the focused app in bold, and the standard app menus.
//
// Almost no Wayland app publishes a real menu, so the menus are the standard Mac ones and each item does what its ⌘ shortcut
// does in the focused app (see menubar/macmenu.lua, which sends the chord). Moving across the titles while a menu is open
// switches menus, as on a Mac.
BarWidget {
  id: root
  moduleName: "omarchykit.macmenu"

  readonly property var active: ToplevelManager.activeToplevel
  readonly property string appId: active ? active.appId : ""
  readonly property var entry: appId ? (DesktopEntries.byId(appId) || DesktopEntries.heuristicLookup(appId)) : null
  readonly property string appName: appId === "" ? "Omarchy" : (entry ? entry.name : prettify(appId))

  property string openMenu: ""          // "" while closed, else apple | app | file | edit | view | window | help
  property var openItems: []
  property Item openAnchor: null
  property var pendingAction: null
  property var titleItems: ({})

  readonly property color ink: bar ? bar.barForeground : Color.foreground
  readonly property color selectText: Qt.rgba(Color.accent.r, Color.accent.g, Color.accent.b, 1).hslLightness > 0.55 ? "#101010" : "#ffffff"

  visible: !vertical
  implicitWidth: vertical ? 0 : row.implicitWidth
  implicitHeight: barSize

  function prettify(id) {
    var s = String(id).split(".").pop()
    return s.length ? s.charAt(0).toUpperCase() + s.slice(1) : "App"
  }

  function close() { openMenu = "" }
  function closeForPopoutSwitch() { openMenu = "" }

  function itemsFor(name) {
    var n = appName
    var sep = { sep: true }
    if (name === "apple") return [
      { label: "About This Mac", id: "apple.about" }, sep,
      { label: "System Settings…", id: "apple.settings" },
      { label: "Software…", id: "apple.store" },
      { label: "Omarchy Menu", id: "apple.menu" }, sep,
      { label: "Force Quit " + n, id: "apple.forcequit" }, sep,
      { label: "Sleep", id: "apple.sleep" },
      { label: "Restart…", id: "apple.restart" },
      { label: "Shut Down…", id: "apple.shutdown" }, sep,
      { label: "Lock Screen", keys: "⌃⌘Q", id: "apple.lock" },
      { label: "Log Out…", id: "apple.logout" } ]
    if (name === "app") return [
      { label: "Settings…", keys: "⌘,", id: "app.settings" }, sep,
      { label: "Hide " + n, keys: "⌘H", id: "app.hide" }, sep,
      { label: "Quit " + n, keys: "⌘Q", id: "app.quit" } ]
    if (name === "file") return [
      { label: "New Window", keys: "⌘N", id: "file.new" },
      { label: "New Tab", keys: "⌘T", id: "file.newtab" },
      { label: "Open…", keys: "⌘O", id: "file.open" }, sep,
      { label: "Close", keys: "⌘W", id: "file.close" },
      { label: "Save", keys: "⌘S", id: "file.save" }, sep,
      { label: "Print…", keys: "⌘P", id: "file.print" } ]
    if (name === "edit") return [
      { label: "Undo", keys: "⌘Z", id: "edit.undo" },
      { label: "Redo", keys: "⇧⌘Z", id: "edit.redo" }, sep,
      { label: "Cut", keys: "⌘X", id: "edit.cut" },
      { label: "Copy", keys: "⌘C", id: "edit.copy" },
      { label: "Paste", keys: "⌘V", id: "edit.paste" },
      { label: "Select All", keys: "⌘A", id: "edit.selectall" }, sep,
      { label: "Find…", keys: "⌘F", id: "edit.find" },
      { label: "Find Next", keys: "⌘G", id: "edit.findnext" } ]
    if (name === "view") return [
      { label: "Reload", keys: "⌘R", id: "view.reload" }, sep,
      { label: "Zoom In", keys: "⌘+", id: "view.zoomin" },
      { label: "Zoom Out", keys: "⌘−", id: "view.zoomout" },
      { label: "Actual Size", keys: "⌘0", id: "view.actual" }, sep,
      { label: "Enter Full Screen", keys: "⌃⌘F", id: "view.fullscreen" } ]
    if (name === "window") {
      var list = [
        { label: "Float or Tile", id: "window.float" },
        { label: "Center", id: "window.center" }, sep ]
      for (var w = 1; w <= 5; w++) list.push({ label: "Move to Workspace " + w, id: "window.move" + w })
      list.push(sep)
      list.push({ label: "Next Window of This App", keys: "⌘`", id: "window.next" })
      var tops = ToplevelManager.toplevels.values, mine = []
      for (var i = 0; i < tops.length; i++) if (tops[i].appId === appId && appId !== "") mine.push(tops[i])
      if (mine.length) {
        list.push(sep)
        for (var j = 0; j < mine.length; j++) {
          (function (t) { list.push({ label: t.title || n, fn: function () { t.activate() }, mark: t.activated }) })(mine[j])
        }
      }
      return list
    }
    return [
      { label: "Omarchy Kit", id: "help.kit" },
      { label: "Keyboard Shortcuts", id: "help.keys" } ]
  }

  function show(name, anchorItem) {
    openItems = itemsFor(name)
    openAnchor = anchorItem
    openMenu = name
    Qt.callLater(function () { popup.anchor.updateAnchor() })
  }

  function run(it) {
    pendingAction = it
    close()
    delay.restart()   // let the menu release the keyboard so the app is the focused window again
  }

  Timer {
    id: delay
    interval: 110
    onTriggered: {
      var it = root.pendingAction
      root.pendingAction = null
      if (!it) return
      if (it.fn) it.fn()
      else if (it.id) Quickshell.execDetached(["hyprctl", "eval", "o.mac_menu(\"" + it.id + "\")"])
    }
  }

  component Title: Item {
    id: title
    property string name
    property string text
    property bool bold: false
    property string family: root.bar ? root.bar.fontFamily : Style.font.family
    readonly property bool lit: root.openMenu === name
    Component.onCompleted: root.titleItems[name] = title

    implicitWidth: label.implicitWidth + Style.spaceReal(20)
    implicitHeight: root.barSize

    Rectangle {
      anchors.verticalCenter: parent.verticalCenter
      anchors.left: parent.left
      anchors.right: parent.right
      anchors.leftMargin: 1
      anchors.rightMargin: 1
      height: Math.min(parent.height - 4, 24)
      radius: 7
      color: title.lit ? Qt.rgba(root.ink.r, root.ink.g, root.ink.b, 0.24)
        : (area.containsMouse ? Qt.rgba(root.ink.r, root.ink.g, root.ink.b, 0.10) : "transparent")
    }
    Text {
      id: label
      anchors.centerIn: parent
      text: title.text
      textFormat: Text.PlainText
      color: root.ink
      font.family: title.family
      font.pixelSize: Style.font.body
      font.bold: title.bold
      renderType: Text.NativeRendering
    }
    MouseArea {
      id: area
      anchors.fill: parent
      hoverEnabled: true
      cursorShape: Qt.PointingHandCursor
      onEntered: if (root.openMenu !== "" && root.openMenu !== title.name) root.show(title.name, title)
      onClicked: if (root.openMenu === title.name) root.close(); else root.show(title.name, title)
    }
  }

  // `quickshell ipc call omarchykit.macmenu open file` opens a menu without the pointer (also how it is tested).
  IpcHandler {
    target: "omarchykit.macmenu"
    function open(name: string): void { var t = root.titleItems[name]; if (t) root.show(name, t) }
    function close(): void { root.close() }
    function current(): string { return root.openMenu }
    function activate(id: string): void { root.run({ id: id }) }
  }

  Row {
    id: row
    visible: !root.vertical
    spacing: 0

    Title { name: "apple"; text: ""; family: "omarchy" }
    Title { name: "app"; text: root.appName; bold: true }
    Title { name: "file"; text: "File" }
    Title { name: "edit"; text: "Edit" }
    Title { name: "view"; text: "View" }
    Title { name: "window"; text: "Window" }
    Title { name: "help"; text: "Help" }
  }

  PopupWindow {
    id: popup
    readonly property var barWindow: root.openAnchor ? root.openAnchor.QsWindow.window : null
    readonly property real rowH: 26
    readonly property real pad: 6

    visible: root.openMenu !== ""
    color: "transparent"
    // Sized from the longest label (plus its shortcut) rather than measured, so nothing here depends on layout order.
    readonly property real longest: {
      var m = 0
      for (var i = 0; i < root.openItems.length; i++) {
        var it = root.openItems[i]
        if (it.sep) continue
        m = Math.max(m, String(it.label || "").length + (it.keys ? String(it.keys).length + 4 : 0))
      }
      return m
    }
    implicitWidth: Math.max(Style.space(200), longest * Style.font.body * 0.58 + 60)
    implicitHeight: col.implicitHeight + pad * 2

    anchor {
      window: popup.barWindow
      adjustment: PopupAdjustment.Slide
      edges: Edges.Top | Edges.Left
      gravity: Edges.Bottom | Edges.Right
      rect.width: 1
      rect.height: 1
      onAnchoring: {
        if (!root.openAnchor || !popup.barWindow) return
        var p = popup.barWindow.contentItem.mapFromItem(root.openAnchor, 0, root.openAnchor.height + 3)
        popup.anchor.rect.x = Math.round(p.x)
        popup.anchor.rect.y = Math.round(p.y)
      }
    }

    HyprlandFocusGrab {
      active: root.openMenu !== ""
      windows: popup.barWindow ? [popup, popup.barWindow] : [popup]
      onCleared: root.close()
    }

    Rectangle {
      anchors.fill: parent
      radius: 11
      color: Qt.rgba(Color.background.r, Color.background.g, Color.background.b, 0.97)
      border.width: 1
      border.color: Qt.rgba(root.ink.r, root.ink.g, root.ink.b, 0.22)

      Column {
        id: col
        anchors.fill: parent
        anchors.margins: popup.pad
        spacing: 0

        Repeater {
          model: root.openItems
          delegate: Item {
            id: item
            required property var modelData
            width: col.width
            height: modelData.sep ? 9 : popup.rowH

            Rectangle {
              visible: item.modelData.sep === true
              anchors.verticalCenter: parent.verticalCenter
              anchors.left: parent.left
              anchors.right: parent.right
              anchors.leftMargin: 6
              anchors.rightMargin: 6
              height: 1
              color: Qt.rgba(root.ink.r, root.ink.g, root.ink.b, 0.18)
            }

            Rectangle {
              visible: !item.modelData.sep
              anchors.fill: parent
              radius: 6
              color: hit.containsMouse ? Qt.rgba(Color.accent.r, Color.accent.g, Color.accent.b, 0.92) : "transparent"

              Text {
                anchors.verticalCenter: parent.verticalCenter
                anchors.left: parent.left
                anchors.leftMargin: 18
                text: (item.modelData.mark ? "✓ " : "") + (item.modelData.label || "")
                textFormat: Text.PlainText
                color: hit.containsMouse ? root.selectText : root.ink
                font.pixelSize: Style.font.body
              }
              Text {
                anchors.verticalCenter: parent.verticalCenter
                anchors.right: parent.right
                anchors.rightMargin: 12
                text: item.modelData.keys || ""
                color: hit.containsMouse ? root.selectText : Qt.rgba(root.ink.r, root.ink.g, root.ink.b, 0.6)
                font.pixelSize: Style.font.body
              }
              MouseArea {
                id: hit
                anchors.fill: parent
                hoverEnabled: true
                onClicked: root.run(item.modelData)
              }
            }
          }
        }
      }
    }
  }
}
