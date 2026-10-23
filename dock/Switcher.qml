import QtQuick
import Quickshell
import Quickshell.Wayland
import Quickshell.Hyprland
import Quickshell.Io

// The ⌘Tab app switcher: a glass panel in the middle of the screen with one big icon per running app, most recently used first.
// Tab / ⇧Tab (or the arrows) move, letting go of ⌘ switches, Esc cancels, Q quits the selected app, H hides it.
PanelWindow {
  id: win

  property bool shown: false
  property var apps: []          // snapshot taken when the switcher opens, so the order does not jump while it is up
  property int selected: 0
  readonly property real tile: 84

  visible: shown
  anchors { top: true; bottom: true; left: true; right: true }
  exclusionMode: ExclusionMode.Ignore
  color: "transparent"
  WlrLayershell.namespace: "macswitcher"
  WlrLayershell.layer: WlrLayer.Overlay
  WlrLayershell.keyboardFocus: shown ? WlrKeyboardFocus.Exclusive : WlrKeyboardFocus.None

  function open(dir) {
    var list = Apps.switcherItems(Apps.toplevels, Apps.mru)
    if (list.length === 0) return
    apps = list
    selected = list.length > 1 ? (dir > 0 ? 1 : list.length - 1) : 0
    shown = true
  }

  function step(dir) {
    if (!shown) { open(dir); return }
    selected = (selected + dir + apps.length) % apps.length
  }

  function commit() {
    if (!shown) return
    shown = false
    var a = apps[selected]
    if (a) Apps.focusApp({ windows: a.windows, entry: a.entry })
  }

  function cancel() { shown = false }

  function quitSelected() {
    var a = apps[selected]
    if (!a) return
    Apps.quitApp({ windows: a.windows })
    var rest = apps.slice()
    rest.splice(selected, 1)
    apps = rest
    if (apps.length === 0) { cancel(); return }
    selected = Math.min(selected, apps.length - 1)
  }

  function hideSelected() {
    var a = apps[selected]
    if (a) Apps.hideApp({ windows: a.windows })
    cancel()
  }

  MouseArea { anchors.fill: parent; onClicked: win.cancel() }

  FocusScope {
    anchors.fill: parent
    focus: true
    Keys.onPressed: function (e) {
      if (e.key === Qt.Key_Tab) win.step((e.modifiers & Qt.ShiftModifier) ? -1 : 1)
      else if (e.key === Qt.Key_Backtab) win.step(-1)
      else if (e.key === Qt.Key_Right || e.key === Qt.Key_Down) win.step(1)
      else if (e.key === Qt.Key_Left || e.key === Qt.Key_Up) win.step(-1)
      else if (e.key === Qt.Key_Escape) win.cancel()
      else if (e.key === Qt.Key_Return || e.key === Qt.Key_Enter) win.commit()
      else if (e.key === Qt.Key_Q) win.quitSelected()
      else if (e.key === Qt.Key_H) win.hideSelected()
      else return
      e.accepted = true
    }
    // Letting go of ⌘ (Super, or Ctrl when the keyboard remap makes ⌘ a Ctrl) switches to the selected app.
    Keys.onReleased: function (e) {
      var k = e.key
      if (k === Qt.Key_Meta || k === Qt.Key_Super_L || k === Qt.Key_Super_R || k === Qt.Key_Control) win.commit()
    }

    Rectangle {
      id: panel
      anchors.centerIn: parent
      width: row.width + 44
      height: win.tile + 78
      radius: 30
      color: Theme.glassStrong
      border.width: 1
      border.color: Theme.hairline

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
        anchors.top: parent.top
        anchors.topMargin: 22
        spacing: 10

        Repeater {
          model: win.apps
          delegate: Item {
            id: cell
            required property var modelData
            required property int index
            width: win.tile + 20
            height: win.tile + 20

            Rectangle {
              anchors.fill: parent
              radius: 22
              color: cell.index === win.selected ? Qt.rgba(Theme.foreground.r, Theme.foreground.g, Theme.foreground.b, 0.20) : "transparent"
              border.width: cell.index === win.selected ? 1 : 0
              border.color: Theme.hairline
            }
            AppIcon {
              anchors.centerIn: parent
              size: win.tile
              icon: cell.modelData.icon || ""
              label: cell.modelData.name || ""
            }
            // a small dot on apps that have more than one window, like the count a Mac shows with ⌘`
            Rectangle {
              visible: cell.modelData.windows.length > 1
              width: 18; height: 18; radius: 9
              anchors.right: parent.right; anchors.top: parent.top; anchors.margins: 4
              color: Theme.accent
              Text { anchors.centerIn: parent; text: cell.modelData.windows.length; font.pixelSize: 11; font.bold: true; color: "#fff" }
            }
            MouseArea {
              anchors.fill: parent
              hoverEnabled: true
              onEntered: win.selected = cell.index
              onClicked: { win.selected = cell.index; win.commit() }
            }
          }
        }
      }

      Text {
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 18
        text: win.apps.length ? win.apps[win.selected].name : ""
        color: Theme.label
        font.pixelSize: 15
        font.bold: true
      }
    }
  }

  GlobalShortcut { appid: "macswitcher"; name: "next"; description: "Next app (⌘Tab)"; onPressed: win.step(1) }
  GlobalShortcut { appid: "macswitcher"; name: "prev"; description: "Previous app (⇧⌘Tab)"; onPressed: win.step(-1) }
  GlobalShortcut { appid: "macswitcher"; name: "commit"; description: "Switch to the selected app"; onPressed: win.commit() }
  GlobalShortcut { appid: "macswitcher"; name: "cancel"; description: "Cancel the app switcher"; onPressed: win.cancel() }
  GlobalShortcut { appid: "macswitcher"; name: "quit"; description: "Quit the selected app"; onPressed: win.quitSelected() }
  GlobalShortcut { appid: "macswitcher"; name: "hide"; description: "Hide the selected app"; onPressed: win.hideSelected() }

  IpcHandler {
    target: "switcher"
    function next(): void { win.step(1) }
    function prev(): void { win.step(-1) }
    function commit(): void { win.commit() }
    function cancel(): void { win.cancel() }
    function visible(): bool { return win.shown }
  }
}
