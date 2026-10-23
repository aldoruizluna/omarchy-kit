import QtQuick
import Quickshell
import qs.Commons
import qs.Ui

// The Control Center button of the menu bar: two small switches, the way macOS draws it. The panel itself is in the Dock program
// (dock/ControlCenter.qml); this only asks it to open, so nothing here knows about Wi-Fi or sound.
BarWidget {
  id: root
  moduleName: "omarchykit.controlcenter"

  readonly property color ink: bar ? bar.barForeground : Color.foreground
  readonly property string dockPath: (Quickshell.env("XDG_DATA_HOME") || (Quickshell.env("HOME") + "/.local/share")) + "/macdock"

  implicitWidth: vertical ? barSize : Style.spaceReal(34)
  implicitHeight: barSize

  Rectangle {
    anchors.verticalCenter: parent.verticalCenter
    anchors.horizontalCenter: parent.horizontalCenter
    width: Math.min(parent.width - 2, Style.spaceReal(30))
    height: Math.min(parent.height - 4, 24)
    radius: 7
    color: area.pressed ? Qt.rgba(root.ink.r, root.ink.g, root.ink.b, 0.24) : (area.containsMouse ? Qt.rgba(root.ink.r, root.ink.g, root.ink.b, 0.10) : "transparent")
  }

  // two switches: a pill with a dot at one end, then another with the dot at the other
  Column {
    anchors.centerIn: parent
    spacing: 3
    Repeater {
      model: [false, true]
      delegate: Item {
        required property bool modelData
        width: 15
        height: 6
        Rectangle { anchors.fill: parent; radius: 3; color: "transparent"; border.width: 1; border.color: root.ink; opacity: 0.9 }
        Rectangle {
          width: 4
          height: 4
          radius: 2
          y: 1
          x: modelData ? parent.width - width - 1 : 1
          color: root.ink
        }
      }
    }
  }

  MouseArea {
    id: area
    anchors.fill: parent
    hoverEnabled: true
    cursorShape: Qt.PointingHandCursor
    onClicked: Quickshell.execDetached(["quickshell", "ipc", "-p", root.dockPath, "call", "controlcenter", "toggle"])
  }
}
