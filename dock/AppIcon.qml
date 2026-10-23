import QtQuick
import Quickshell

// An application icon. Icons that come from the Mac icon theme are drawn as they are; anything else is set on a neutral rounded tile,
// which is what macOS does with apps that have not been given a new-style icon.
Item {
  id: root

  property string icon: ""
  property string label: ""
  property real size: 52
  property bool plain: false   // folder and Trash icons come from the theme's places, not its apps

  readonly property string resolved: icon ? Quickshell.iconPath(icon, true) : ""
  readonly property bool themed: plain || IconIndex.has(icon)

  // Cleared and restored when the icon theme changes, because Qt would otherwise keep serving the cached pictures of the old theme.
  property string shown: resolved
  Connections {
    target: IconIndex
    function onThemeChanged() { root.shown = ""; Qt.callLater(function () { root.shown = Qt.binding(function () { return root.resolved }) }) }
  }

  width: size
  height: size

  Rectangle {
    visible: !root.themed
    anchors.fill: parent
    radius: root.size * 0.225
    gradient: Gradient {
      GradientStop { position: 0.0; color: Qt.lighter(Theme.glassStrong, 1.7) }
      GradientStop { position: 1.0; color: Theme.glassStrong }
    }
    border.width: 1
    border.color: Theme.hairline
  }

  Image {
    visible: root.resolved !== ""
    anchors.centerIn: parent
    width: root.themed ? root.size : root.size * 0.66
    height: width
    source: root.shown
    sourceSize.width: Math.round(width * 2)
    sourceSize.height: Math.round(height * 2)
    fillMode: Image.PreserveAspectFit
    smooth: true
    mipmap: true
    asynchronous: true
  }

  Text {
    visible: root.resolved === ""
    anchors.centerIn: parent
    text: root.label.charAt(0).toUpperCase()
    font.pixelSize: root.size * 0.45
    font.bold: true
    color: Theme.label
  }
}
