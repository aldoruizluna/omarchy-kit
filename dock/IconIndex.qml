pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io

// Which application icons the active icon theme really has. Anything it lacks falls back to another theme and would look out of place,
// so AppIcon sets those on a neutral tile (what macOS does with old-style icons).
Singleton {
  id: root

  property string theme: ""
  property var names: ({})

  function has(name) { return !!name && root.names[name] === true }

  // Re-read when the Omarchy theme changes: its hook switches the icon variant (light or dark) at the same moment.
  Connections {
    target: Theme
    function onDarkChanged() { probe.running = true }
    function onBackgroundChanged() { probe.running = true }
  }
  Component.onCompleted: probe.running = true

  Process {
    id: probe
    command: ["sh", "-c",
      "t=$(gsettings get org.gnome.desktop.interface icon-theme 2>/dev/null | tr -d \"'\"); echo \"$t\"; " +
      "for r in \"$HOME/.local/share/icons\" /usr/share/icons; do " +
      "  if [ -d \"$r/$t/apps\" ]; then for s in scalable 256 128 96 64 48; do ls -1 \"$r/$t/apps/$s\" 2>/dev/null; done | sed 's/\\.[a-z]*$//' | sort -u; break; fi; done"]
    stdout: StdioCollector {
      onStreamFinished: {
        var lines = text.split("\n")
        var set = {}
        for (var i = 1; i < lines.length; i++) if (lines[i]) set[lines[i]] = true
        root.names = set
        root.theme = lines[0] || ""
      }
    }
  }
}
