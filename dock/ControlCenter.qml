import QtQuick
import QtQuick.Effects
import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import Quickshell.Hyprland
import Quickshell.Bluetooth
import Quickshell.Networking
import Quickshell.Services.Mpris
import Quickshell.Services.Pipewire
import Quickshell.Services.UPower

// Control Center: the macOS panel that the menu bar button opens. Wi-Fi, Bluetooth, Focus (do not disturb) and Night Light as tiles; Display, Sound and Keyboard
// brightness as sliders; what is playing; the battery and the power mode. Everything the panel reads comes from the same services Omarchy's own panels use
// (NetworkManager, BlueZ, PipeWire, UPower, MPRIS) or from Omarchy's commands, and nothing is created while it is closed: the contents sit in a Loader that is only
// active while the panel is open. Click outside it or press Esc to close.
PanelWindow {
  id: win

  property bool shown: false
  property var info: ({ dnd: false, night: false, ssid: "", display: -1, keyboard: -1, profile: "" })
  readonly property string keyboardDevice: "smc::kbd_backlight"

  visible: shown
  anchors { top: true; bottom: true; left: true; right: true }
  exclusionMode: ExclusionMode.Ignore
  color: "transparent"
  WlrLayershell.namespace: "maccontrol"
  WlrLayershell.layer: WlrLayer.Overlay
  WlrLayershell.keyboardFocus: shown ? WlrKeyboardFocus.Exclusive : WlrKeyboardFocus.None

  function toggle() { win.shown = !win.shown }
  function close() { win.shown = false }
  onShownChanged: if (shown) win.refresh()

  // ---------------------------------------------------------------------------------------------------------------------
  // State that is not in a service: asked once when the panel opens, and again after a change.

  function refresh() { probe.running = true }

  Process {
    id: probe
    command: ["sh", "-c",
      'echo dnd=$(omarchy-shell notifications isDnd 2>/dev/null); ' +
      'echo night=$(omarchy-toggle-nightlight --status 2>/dev/null | jq -r .enabled 2>/dev/null); ' +
      'echo ssid=$(nmcli -t -f ACTIVE,SSID dev wifi 2>/dev/null | grep "^yes" | head -n1 | cut -d: -f2-); ' +
      'echo display=$(brightnessctl -m -c backlight 2>/dev/null | head -n1 | cut -d, -f4 | tr -d %); ' +
      'echo keyboard=$(brightnessctl -m -d "' + win.keyboardDevice + '" 2>/dev/null | head -n1 | cut -d, -f4 | tr -d %); ' +
      'echo profile=$(powerprofilesctl get 2>/dev/null)']
    stdout: StdioCollector {
      onStreamFinished: {
        var o = { dnd: false, night: false, ssid: "", display: -1, keyboard: -1, profile: "" }
        var lines = text.split("\n")
        for (var i = 0; i < lines.length; i++) {
          var eq = lines[i].indexOf("=")
          if (eq < 0) continue
          var k = lines[i].slice(0, eq), v = lines[i].slice(eq + 1).trim()
          if (k === "dnd") o.dnd = v === "on"
          else if (k === "night") o.night = v === "true"
          else if (k === "ssid") o.ssid = v
          else if (k === "display" || k === "keyboard") o[k] = v === "" ? -1 : Math.max(0, Math.min(100, parseInt(v)))
          else if (k === "profile") o.profile = v
        }
        win.info = o
      }
    }
  }

  function run(cmd) { Quickshell.execDetached(cmd) }

  function setFocus(on) {
    run(["omarchy-shell", "notifications", "setDnd", on ? "on" : "off"])
    var o = Object.assign({}, info); o.dnd = on; info = o
  }
  function toggleNight() {
    run(["omarchy-toggle-nightlight"])
    var o = Object.assign({}, info); o.night = !o.night; info = o
  }
  function setDisplay(pct) {
    run(["omarchy-brightness-display", "--no-osd", Math.round(Math.max(1, pct)) + "%"])
    var o = Object.assign({}, info); o.display = Math.round(pct); info = o
  }
  function setKeyboard(pct) {
    run(["brightnessctl", "-q", "-d", win.keyboardDevice, "set", Math.round(pct) + "%"])
    var o = Object.assign({}, info); o.keyboard = Math.round(pct); info = o
  }

  readonly property var profiles: ["power-saver", "balanced", "performance"]
  readonly property var profileNames: ({ "power-saver": "Low Power", "balanced": "Automatic", "performance": "High Power" })
  function nextProfile() {
    var i = Math.max(0, profiles.indexOf(info.profile))
    var next = profiles[(i + 1) % profiles.length]
    run(["powerprofilesctl", "set", next])
    var o = Object.assign({}, info); o.profile = next; info = o
  }

  // ---------------------------------------------------------------------------------------------------------------------
  // Pieces.

  readonly property color cardColor: Qt.rgba(Theme.foreground.r, Theme.foreground.g, Theme.foreground.b, Theme.dark ? 0.09 : 0.07)
  readonly property color onColor: Theme.accent
  readonly property color glyphOn: "#ffffff"

  // A symbolic icon, tinted.
  component Glyph: Item {
    id: g
    property string name
    property color tint: Theme.label
    property real size: 18
    width: size
    height: size
    Image {
      id: src
      anchors.fill: parent
      source: g.name ? Quickshell.iconPath(g.name, true) : ""
      sourceSize.width: g.size * 2
      sourceSize.height: g.size * 2
      visible: false
      asynchronous: true
    }
    MultiEffect {
      anchors.fill: parent
      source: src
      colorization: 1.0
      colorizationColor: g.tint
      visible: src.status === Image.Ready
    }
  }

  component Tile: Rectangle {
    id: t
    property string icon
    property string title
    property string subtitle
    property bool on: false
    property bool available: true
    signal toggled()
    height: 64
    radius: 16
    color: win.cardColor
    opacity: available ? 1 : 0.5
    Rectangle {
      id: disc
      anchors.left: parent.left
      anchors.leftMargin: 12
      anchors.verticalCenter: parent.verticalCenter
      width: 38
      height: 38
      radius: 19
      color: t.on ? win.onColor : Qt.rgba(Theme.foreground.r, Theme.foreground.g, Theme.foreground.b, 0.16)
      Glyph { anchors.centerIn: parent; name: t.icon; size: 18; tint: t.on ? win.glyphOn : Theme.label }
    }
    Column {
      anchors.left: disc.right
      anchors.leftMargin: 10
      anchors.right: parent.right
      anchors.rightMargin: 8
      anchors.verticalCenter: parent.verticalCenter
      spacing: 1
      Text { width: parent.width; text: t.title; elide: Text.ElideRight; font.pixelSize: 14; font.weight: Font.DemiBold; color: Theme.label }
      Text { width: parent.width; text: t.subtitle; elide: Text.ElideRight; font.pixelSize: 12; color: Theme.label; opacity: 0.6 }
    }
    MouseArea { anchors.fill: parent; enabled: t.available; cursorShape: Qt.PointingHandCursor; onClicked: t.toggled() }
  }

  component SliderCard: Rectangle {
    id: s
    property string title
    property string icon
    property real value: 0          // 0 to 1
    property bool available: true
    signal moved(real v)
    property real dragValue: -1
    readonly property real shownValue: dragValue >= 0 ? dragValue : Math.max(0, Math.min(1, value))
    height: 62
    radius: 16
    color: win.cardColor
    visible: available
    Text { x: 16; y: 8; text: s.title; font.pixelSize: 13; font.weight: Font.DemiBold; color: Theme.label }
    Item {
      id: track
      anchors.left: parent.left
      anchors.right: parent.right
      anchors.leftMargin: 14
      anchors.rightMargin: 14
      anchors.bottom: parent.bottom
      anchors.bottomMargin: 9
      height: 26
      Rectangle {
        anchors.fill: parent
        radius: height / 2
        color: Qt.rgba(Theme.foreground.r, Theme.foreground.g, Theme.foreground.b, 0.18)
      }
      Rectangle {
        width: Math.max(parent.height, parent.width * s.shownValue)
        height: parent.height
        radius: height / 2
        color: Theme.dark ? "#f2f2f7" : "#ffffff"
        border.width: Theme.dark ? 0 : 1
        border.color: Theme.hairline
        Glyph {
          anchors.left: parent.left
          anchors.leftMargin: 6
          anchors.verticalCenter: parent.verticalCenter
          name: s.icon
          size: 14
          tint: "#303036"
        }
      }
      MouseArea {
        anchors.fill: parent
        preventStealing: true
        cursorShape: Qt.PointingHandCursor
        function at(x) { return Math.max(0, Math.min(1, x / width)) }
        onPressed: function (m) { s.dragValue = at(m.x); s.moved(s.dragValue) }
        onPositionChanged: function (m) { if (pressed) { s.dragValue = at(m.x); s.moved(s.dragValue) } }
        onReleased: s.dragValue = -1
      }
    }
  }

  // ---------------------------------------------------------------------------------------------------------------------
  // The window.

  MouseArea { anchors.fill: parent; onClicked: win.close() }

  Loader {
    id: panelLoader
    active: win.shown
    anchors.top: parent.top
    anchors.right: parent.right
    anchors.topMargin: 34
    anchors.rightMargin: 10

    sourceComponent: FocusScope {
      id: panel
      width: 372
      height: card.height
      focus: true
      Keys.onEscapePressed: win.close()

      readonly property var adapter: Bluetooth.defaultAdapter
      readonly property var sink: Pipewire.defaultAudioSink
      readonly property var player: {
        var list = Mpris.players ? Mpris.players.values : []
        for (var i = 0; i < list.length; i++) if (list[i].isPlaying) return list[i]
        return list.length ? list[0] : null
      }
      readonly property var battery: UPower.displayDevice
      readonly property int batteryPct: battery && battery.isPresent ? Math.round(battery.percentage <= 1 ? battery.percentage * 100 : battery.percentage) : -1
      readonly property string bluetoothNote: {
        if (!adapter) return "Not available"
        if (!adapter.enabled) return "Off"
        var devs = Bluetooth.devices ? Bluetooth.devices.values : []
        for (var i = 0; i < devs.length; i++) if (devs[i].connected) return devs[i].name || devs[i].deviceName || "Connected"
        return "On"
      }

      PwObjectTracker { objects: panel.sink ? [panel.sink] : [] }

      MouseArea { anchors.fill: parent }       // a click on the panel itself must not reach the backdrop

      Rectangle {
        id: card
        width: parent.width
        height: col.implicitHeight + 24
        radius: 24
        color: Qt.rgba(Theme.background.r, Theme.background.g, Theme.background.b, 0.96)
        border.width: 1
        border.color: Theme.hairline

        Column {
          id: col
          x: 12
          y: 12
          width: parent.width - 24
          spacing: 10

          Grid {
            columns: 2
            columnSpacing: 10
            rowSpacing: 10
            width: parent.width
            Tile {
              width: (parent.width - 10) / 2
              icon: "network-wireless-symbolic"
              title: "Wi-Fi"
              subtitle: !Networking.wifiEnabled ? "Off" : (win.info.ssid || "On")
              on: Networking.wifiEnabled
              onToggled: { Networking.wifiEnabled = !Networking.wifiEnabled; refreshLater.restart() }
            }
            Tile {
              width: (parent.width - 10) / 2
              icon: "bluetooth-symbolic"
              title: "Bluetooth"
              subtitle: panel.bluetoothNote
              on: !!panel.adapter && panel.adapter.enabled
              available: !!panel.adapter
              onToggled: if (panel.adapter) panel.adapter.enabled = !panel.adapter.enabled
            }
            Tile {
              width: (parent.width - 10) / 2
              icon: "notifications-disabled-symbolic"
              title: "Focus"
              subtitle: win.info.dnd ? "Do Not Disturb" : "Off"
              on: win.info.dnd
              onToggled: win.setFocus(!win.info.dnd)
            }
            Tile {
              width: (parent.width - 10) / 2
              icon: "night-light-symbolic"
              title: "Night Shift"
              subtitle: win.info.night ? "On" : "Off"
              on: win.info.night
              onToggled: win.toggleNight()
            }
          }

          SliderCard {
            width: parent.width
            title: "Display"
            icon: "display-brightness-symbolic"
            available: win.info.display >= 0
            value: win.info.display / 100
            onMoved: function (v) { displayDebounce.pending = v * 100; displayDebounce.restart() }
          }
          SliderCard {
            width: parent.width
            title: panel.sink && panel.sink.audio && panel.sink.audio.muted ? "Sound (muted)" : "Sound"
            icon: panel.sink && panel.sink.audio && panel.sink.audio.muted ? "audio-volume-muted-symbolic" : "audio-volume-high-symbolic"
            available: !!panel.sink && !!panel.sink.audio
            value: panel.sink && panel.sink.audio ? Math.min(1, panel.sink.audio.volume) : 0
            onMoved: function (v) { if (panel.sink && panel.sink.audio) { panel.sink.audio.muted = false; panel.sink.audio.volume = v } }
          }
          SliderCard {
            width: parent.width
            title: "Keyboard Brightness"
            icon: "keyboard-brightness-symbolic"
            available: win.info.keyboard >= 0
            value: win.info.keyboard / 100
            onMoved: function (v) { keyboardDebounce.pending = v * 100; keyboardDebounce.restart() }
          }

          Rectangle {
            visible: !!panel.player
            width: parent.width
            height: 68
            radius: 16
            color: win.cardColor
            Column {
              anchors.left: parent.left
              anchors.leftMargin: 16
              anchors.right: controls.left
              anchors.rightMargin: 8
              anchors.verticalCenter: parent.verticalCenter
              spacing: 2
              Text { width: parent.width; text: panel.player ? (panel.player.trackTitle || "Not Playing") : ""; elide: Text.ElideRight; font.pixelSize: 14; font.weight: Font.DemiBold; color: Theme.label }
              Text { width: parent.width; text: panel.player ? (panel.player.trackArtist || panel.player.identity || "") : ""; elide: Text.ElideRight; font.pixelSize: 12; color: Theme.label; opacity: 0.6 }
            }
            Row {
              id: controls
              anchors.right: parent.right
              anchors.rightMargin: 12
              anchors.verticalCenter: parent.verticalCenter
              spacing: 6
              Repeater {
                model: [
                  { icon: "media-skip-backward-symbolic", act: "previous" },
                  { icon: panel.player && panel.player.isPlaying ? "media-playback-pause-symbolic" : "media-playback-start-symbolic", act: "toggle" },
                  { icon: "media-skip-forward-symbolic", act: "next" }
                ]
                delegate: Item {
                  required property var modelData
                  width: 34
                  height: 34
                  Glyph { anchors.centerIn: parent; name: modelData.icon; size: 18 }
                  MouseArea {
                    anchors.fill: parent
                    cursorShape: Qt.PointingHandCursor
                    onClicked: {
                      var p = panel.player
                      if (!p) return
                      if (modelData.act === "toggle") p.togglePlaying()
                      else if (modelData.act === "next") p.next()
                      else p.previous()
                    }
                  }
                }
              }
            }
          }

          Rectangle {
            width: parent.width
            height: 52
            radius: 16
            color: win.cardColor
            visible: panel.batteryPct >= 0
            Glyph { x: 16; anchors.verticalCenter: parent.verticalCenter; name: "battery-full-symbolic"; size: 18 }
            Text {
              x: 44
              anchors.verticalCenter: parent.verticalCenter
              text: "Battery  " + panel.batteryPct + " %" + (UPower.onBattery ? "" : "  ·  charging")
              font.pixelSize: 14
              font.weight: Font.DemiBold
              color: Theme.label
            }
            Rectangle {
              visible: win.info.profile !== ""
              anchors.right: parent.right
              anchors.rightMargin: 10
              anchors.verticalCenter: parent.verticalCenter
              height: 30
              width: modeText.implicitWidth + 24
              radius: 15
              color: Qt.rgba(Theme.foreground.r, Theme.foreground.g, Theme.foreground.b, 0.14)
              Text { id: modeText; anchors.centerIn: parent; text: win.profileNames[win.info.profile] || win.info.profile; font.pixelSize: 13; color: Theme.label }
              MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: win.nextProfile() }
            }
          }

          Row {
            spacing: 10
            width: parent.width
            Rectangle {
              width: (parent.width - 10) / 2
              height: 40
              radius: 14
              color: win.cardColor
              Text { anchors.centerIn: parent; text: "Lock Screen"; font.pixelSize: 13; color: Theme.label }
              MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: { win.close(); win.run(["omarchy-system-lock"]) } }
            }
            Rectangle {
              width: (parent.width - 10) / 2
              height: 40
              radius: 14
              color: win.cardColor
              Text { anchors.centerIn: parent; text: "Wi-Fi, Bluetooth, Sound…"; font.pixelSize: 13; color: Theme.label }
              MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: { win.close(); win.run(["omarchy-menu", "toggle", "hardware"]) } }
            }
          }
        }
      }

      // Brightness goes through scripts: send the last value of a drag, not every pixel of it.
      Timer { id: displayDebounce; property real pending: 0; interval: 90; onTriggered: win.setDisplay(pending) }
      Timer { id: keyboardDebounce; property real pending: 0; interval: 90; onTriggered: win.setKeyboard(pending) }
      Timer { id: refreshLater; interval: 1500; onTriggered: win.refresh() }
    }
  }

  GlobalShortcut { appid: "maccontrol"; name: "toggle"; description: "Control Center"; onPressed: win.toggle() }

  IpcHandler {
    target: "controlcenter"
    function toggle(): void { win.toggle() }
    function open(): void { win.shown = true }
    function close(): void { win.close() }
    function visible(): bool { return win.shown }
    // ---- for tests
    function describe(): string { return JSON.stringify(win.info) }
    function refresh(): void { win.refresh() }
    function act(name: string): void {              // what a click on the tile or the power mode does
      if (name === "focus") win.setFocus(!win.info.dnd)
      else if (name === "night") win.toggleNight()
      else if (name === "profile") win.nextProfile()
    }
    function level(which: string, pct: int): void {  // what dragging a slider does
      if (which === "display") win.setDisplay(pct)
      else if (which === "keyboard") win.setKeyboard(pct)
    }
  }
}
