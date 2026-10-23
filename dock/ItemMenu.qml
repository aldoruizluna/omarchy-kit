import QtQuick
import Quickshell

// The right-click menu of a dock item: its windows, the app's own actions, Keep in Dock, Quit.
PopupWindow {
  id: root

  property var entries: []     // [{ label, action, separator, header, disabled }]

  function openFor(anchorItem, list) {
    entries = list
    anchor.item = anchorItem
    anchor.edges = Edges.Top
    anchor.gravity = Edges.Top
    anchor.margins.bottom = 14
    visible = true
  }

  color: "transparent"
  implicitWidth: Math.max(190, column.implicitWidth + 16)
  implicitHeight: column.implicitHeight + 16
  visible: false

  Rectangle {
    anchors.fill: parent
    radius: 13
    color: Theme.glassStrong
    border.width: 1
    border.color: Theme.hairline

    Column {
      id: column
      anchors.fill: parent
      anchors.margins: 8
      spacing: 1

      Repeater {
        model: root.entries
        delegate: Item {
          id: row
          required property var modelData
          width: column.width
          height: modelData.separator ? 9 : 27

          Rectangle {
            visible: row.modelData.separator === true
            anchors.verticalCenter: parent.verticalCenter
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.leftMargin: 4
            anchors.rightMargin: 4
            height: 1
            color: Theme.hairline
          }

          Rectangle {
            visible: !row.modelData.separator
            anchors.fill: parent
            radius: 6
            color: area.containsMouse && !row.modelData.header && !row.modelData.disabled ? Theme.accent : "transparent"
            Text {
              anchors.verticalCenter: parent.verticalCenter
              anchors.left: parent.left
              anchors.leftMargin: 10
              anchors.right: parent.right
              anchors.rightMargin: 10
              elide: Text.ElideRight
              text: row.modelData.label || ""
              font.pixelSize: 13
              font.bold: row.modelData.header === true
              color: Theme.label
              opacity: row.modelData.header || row.modelData.disabled ? 0.55 : 1
            }
            MouseArea {
              id: area
              anchors.fill: parent
              hoverEnabled: true
              enabled: !row.modelData.header && !row.modelData.disabled
              onClicked: {
                root.visible = false
                if (row.modelData.action) row.modelData.action()
              }
            }
          }
        }
      }
    }
  }
}
