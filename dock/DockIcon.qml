import QtQuick
import Quickshell

// One slot in the dock: the icon, its running dot, its name on hover, and the bounce while it launches.
Item {
  id: root

  required property var item            // { key, kind, entry, name, icon, pinned, windows } or { kind: "separator" }
  required property real magnify        // 1 = normal size; the dock computes how much this icon grows
  property real baseSize: Config.iconSize

  signal clicked(var item, int button)
  signal menuRequested(var item, var anchorItem)
  signal dragFinished(var item, real dx, real dy)   // the pointer moved by (dx, dy) while this pinned icon was held

  readonly property bool isSeparator: item.kind === "separator"
  readonly property bool running: !isSeparator && item.windows && item.windows.length > 0
  readonly property bool background: !isSeparator && !running && item.background === true   // runs with no window: a lighter dot
  readonly property bool canDrag: !isSeparator && item.kind === "app" && item.pinned === true
  readonly property real iconW: baseSize * magnify

  property bool launching: false
  property bool hovered: false
  property bool dragging: false
  property real dragDx: 0
  property real dragDy: 0

  z: dragging ? 100 : 0
  transform: Translate { x: root.dragging ? root.dragDx : 0; y: root.dragging ? Math.min(0, root.dragDy) * 0.6 : 0 }   // follows the pointer; rises only gently when pulled up

  width: isSeparator ? 14 : iconW + 6
  height: baseSize

  Rectangle {
    visible: root.isSeparator
    anchors.centerIn: parent
    width: 1
    height: root.baseSize * 0.78
    color: Theme.hairline
  }

  Item {
    id: body
    visible: !root.isSeparator
    anchors.horizontalCenter: parent.horizontalCenter
    anchors.bottom: parent.bottom
    width: root.iconW
    height: root.iconW

    AppIcon {
      id: art
      anchors.fill: parent
      size: root.iconW
      icon: root.item.icon || ""
      plain: root.item.kind === "folder" || root.item.kind === "trash"
      label: root.item.name || ""
    }

    transform: Translate { id: bounce; y: 0 }

    // Name label above the icon, like the macOS Dock.
    Rectangle {
      id: tip
      visible: root.hovered && !root.isSeparator
      anchors.horizontalCenter: parent.horizontalCenter
      anchors.bottom: parent.top
      anchors.bottomMargin: 10
      height: 26
      width: tipText.implicitWidth + 22
      radius: 9
      color: Theme.glassStrong
      border.width: 1
      border.color: Theme.hairline
      Text {
        id: tipText
        anchors.centerIn: parent
        text: root.item.name || ""
        color: Theme.label
        font.pixelSize: 13
      }
    }
  }

  // Running indicator: a full dot while the app has a window, a lighter one while it only runs in the background.
  Rectangle {
    visible: root.running || root.background
    width: 4
    height: 4
    radius: 2
    color: root.running ? Theme.dot : Theme.dotBackground
    anchors.horizontalCenter: parent.horizontalCenter
    anchors.top: parent.bottom
    anchors.topMargin: 2
  }

  SequentialAnimation {
    running: root.launching
    loops: Animation.Infinite
    onRunningChanged: if (!running) bounce.y = 0
    NumberAnimation { target: bounce; property: "y"; to: -root.baseSize * 0.42; duration: 330; easing.type: Easing.OutQuad }
    NumberAnimation { target: bounce; property: "y"; to: 0; duration: 330; easing.type: Easing.InQuad }
  }

  Timer {
    id: launchTimeout
    interval: 12000
    onTriggered: root.launching = false
  }
  onRunningChanged: if (running) root.launching = false

  MouseArea {
    // covers the magnified icon, not just the unmagnified slot
    anchors.left: parent.left
    anchors.right: parent.right
    anchors.bottom: parent.bottom
    height: root.iconW
    visible: !root.isSeparator
    hoverEnabled: true
    acceptedButtons: Qt.LeftButton | Qt.MiddleButton | Qt.RightButton
    cursorShape: root.dragging ? Qt.ClosedHandCursor : Qt.PointingHandCursor
    preventStealing: root.dragging

    // Drag to reorder (pinned apps only). Positions are measured in the window, because the icon itself moves while it is dragged.
    property real pressX: 0
    property real pressY: 0
    property bool moved: false
    onPressed: function (mouse) {
      var p = mapToItem(null, mouse.x, mouse.y)
      pressX = p.x; pressY = p.y; moved = false
    }
    onPositionChanged: function (mouse) {
      if (!pressed || !root.canDrag || !(mouse.buttons & Qt.LeftButton)) return
      var p = mapToItem(null, mouse.x, mouse.y)
      var dx = p.x - pressX, dy = p.y - pressY
      if (!root.dragging && Math.abs(dx) + Math.abs(dy) < 12) return
      root.dragging = true; moved = true; root.hovered = false
      root.dragDx = dx; root.dragDy = dy
    }
    onReleased: function (mouse) {
      if (!root.dragging) return
      var dx = root.dragDx, dy = root.dragDy
      root.dragging = false; root.dragDx = 0; root.dragDy = 0
      root.dragFinished(root.item, dx, dy)
    }
    onEntered: if (!root.dragging) root.hovered = true
    onExited: root.hovered = false
    onClicked: function (mouse) {
      if (moved) { moved = false; return }          // the click that ends a drag is not a click
      if (mouse.button === Qt.RightButton) {
        root.hovered = false
        root.menuRequested(root.item, root)
        return
      }
      if (!root.running && root.item.kind === "app") { root.launching = true; launchTimeout.restart() }
      root.clicked(root.item, mouse.button)
    }
  }
}
