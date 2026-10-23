import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Wayland

// Hot corners: rest the pointer in a screen corner for a moment and something happens (Mission Control, the Apps menu, a quick note...).
// Each active corner is a tiny transparent surface that waits for the pointer to enter it, so nothing polls the pointer. A corner whose
// action is "none" has no surface at all, and with every corner off this creates none. What each corner does is in dock.json
// ("hotCorners"), or `dock/hot-corners` changes it; the file is watched, so a change applies at once.
Scope {
  id: root

  readonly property real size: 3                      // logical pixels; the pointer stops at the last pixel of the screen, which is inside

  // One entry per screen per corner that has an action.
  readonly property var slots: {
    var out = [], screens = Quickshell.screens
    for (var s = 0; s < screens.length; s++)
      for (var c = 0; c < Config.cornerNames.length; c++) {
        var name = Config.cornerNames[c]
        if (Config.hotCorners[name] && Config.hotCorners[name] !== "none") out.push({ screen: screens[s], corner: name, key: screens[s].name + ":" + name })
      }
    return out
  }

  function run(action) {
    switch (action) {
    case "missioncontrol": Quickshell.execDetached(["quickshell", "ipc", "-p", Quickshell.shellDir, "call", "mission", "toggle"]); break
    case "appexpose":      Quickshell.execDetached(["quickshell", "ipc", "-p", Quickshell.shellDir, "call", "mission", "appwindows"]); break
    case "apps":           Quickshell.execDetached(["omarchy-menu", "toggle", "apps"]); break
    case "lock":           Quickshell.execDetached(["omarchy-system-lock"]); break
    case "notifications":  Quickshell.execDetached(["omarchy-shell", "notifications", "showHistory"]); break
    case "quicknote":
      // A new Markdown note in ~/Documents/Quick Notes, named by the minute, opened in Omawrite (or the default editor if that is missing).
      // A note you never write leaves no empty file behind.
      Quickshell.execDetached(["sh", "-c",
        'd="$HOME/Documents/Quick Notes"; mkdir -p "$d"; f="$d/Quick Note $(date "+%Y-%m-%d %H.%M").md"; touch "$f"; ' +
        'if command -v omawrite >/dev/null; then omawrite "$f"; else omarchy-launch-editor "$f"; fi; [ -s "$f" ] || rm -f "$f"'])
      break
    }
  }

  Variants {
    model: root.slots

    PanelWindow {
      id: spot
      required property var modelData
      screen: modelData.screen
      readonly property string corner: modelData.corner
      readonly property string action: Config.hotCorners[modelData.corner] || "none"

      anchors {
        top: corner.indexOf("top") === 0
        bottom: corner.indexOf("bottom") === 0
        left: corner.indexOf("Left") > 0
        right: corner.indexOf("Right") > 0
      }
      implicitWidth: root.size
      implicitHeight: root.size
      exclusionMode: ExclusionMode.Ignore
      color: "transparent"
      WlrLayershell.namespace: "machotcorner"
      WlrLayershell.layer: WlrLayer.Overlay

      // Nothing happens until the pointer has rested here; leaving and coming back starts again. After it fires the corner stays "latched"
      // until the pointer has really moved away: a full-screen overlay (Mission Control) takes the pointer from this surface, and when it
      // closes with the pointer still parked in the corner this surface would see a fresh enter and fire again. It cannot see the pointer
      // while another surface has it, so while latched it asks Hyprland where the pointer is, a few times a second.
      property bool latched: false

      HoverHandler {
        id: hover
        onHoveredChanged: if (hovered && !spot.latched) dwell.restart(); else dwell.stop()
      }
      Timer {
        id: dwell
        interval: Config.hotCornerDelay
        onTriggered: { spot.latched = true; watch.restart(); root.run(spot.action) }
      }
      Timer { id: watch; interval: 700; repeat: true; onTriggered: probe.running = true }
      Process {
        id: probe
        command: ["hyprctl", "cursorpos"]
        stdout: StdioCollector {
          onStreamFinished: {
            var m = /(-?\d+),\s*(-?\d+)/.exec(text)
            if (!m || !spot.screen) return
            var s = spot.screen, tx = spot.corner.indexOf("Right") > 0 ? s.x + s.width - 1 : s.x, ty = spot.corner.indexOf("bottom") === 0 ? s.y + s.height - 1 : s.y
            if (Math.abs(+m[1] - tx) > 12 || Math.abs(+m[2] - ty) > 12) { spot.latched = false; watch.stop() }
          }
        }
      }
    }
  }

  IpcHandler {
    target: "corners"
    function list(): string {
      var out = []
      for (var i = 0; i < Config.cornerNames.length; i++) out.push(Config.cornerNames[i] + "=" + Config.hotCorners[Config.cornerNames[i]])
      return out.join(" ")
    }
    function surfaces(): int { return root.slots.length }
    function trigger(action: string): void { root.run(action) }
  }
}
