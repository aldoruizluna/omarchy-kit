pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io

// Colours for the dock and the app switcher. They follow the active Omarchy theme (colors.toml), so a theme change
// recolours the glass. The glass itself stays neutral and translucent, like macOS: the theme only tints it.
Singleton {
  id: root

  readonly property string colorsPath: Quickshell.env("HOME") + "/.local/state/omarchy/current/theme/colors.toml"

  property bool dark: true
  property color background: "#101014"
  property color foreground: "#f2f2f7"
  property color accent: "#0a84ff"

  // Glass: the theme background at about half strength, a hairline border and a soft shadow.
  readonly property color glass: Qt.rgba(background.r, background.g, background.b, dark ? 0.52 : 0.58)
  readonly property color glassStrong: Qt.rgba(background.r, background.g, background.b, dark ? 0.90 : 0.92)
  readonly property color hairline: Qt.rgba(foreground.r, foreground.g, foreground.b, dark ? 0.20 : 0.28)
  readonly property color highlight: Qt.rgba(foreground.r, foreground.g, foreground.b, dark ? 0.14 : 0.10)
  readonly property color label: foreground
  readonly property color dot: Qt.rgba(foreground.r, foreground.g, foreground.b, 0.85)
  readonly property color dotBackground: Qt.rgba(foreground.r, foreground.g, foreground.b, 0.38)   // an app that runs with no window

  function parse(text) {
    var out = {}
    var lines = text.split("\n")
    for (var i = 0; i < lines.length; i++) {
      var m = lines[i].match(/^\s*([A-Za-z_]+)\s*=\s*"([^"]*)"/)
      if (m) out[m[1]] = m[2]
    }
    if (out.background) root.background = out.background
    if (out.foreground) root.foreground = out.foreground
    if (out.accent) root.accent = out.accent
    root.dark = out.mode !== "light"
  }

  FileView {
    id: file
    path: root.colorsPath
    onLoaded: root.parse(text())
  }

  // Omarchy swaps the theme directory on a theme change; a short poll is simpler and cheaper than chasing the symlink.
  Timer {
    interval: 3000
    running: true
    repeat: true
    onTriggered: file.reload()
  }
}
