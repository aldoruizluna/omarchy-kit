pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io

// ~/.config/macdock/dock.json: what is pinned and how the dock looks. Written back when you Keep in Dock / Remove from Dock.
Singleton {
  id: root

  readonly property string path: Quickshell.env("HOME") + "/.config/macdock/dock.json"
  readonly property string downloads: Quickshell.env("HOME") + "/Downloads"

  // Desktop file ids (without .desktop). Ids that are not installed are skipped.
  readonly property var defaultPinned: ["org.gnome.Nautilus", "brave-browser", "foot", "obsidian", "org.telegram.desktop", "signal", "WhatsApp", "Omarchy Kit"]

  property var pinned: defaultPinned
  property real iconSize: 52        // logical pixels
  property real zoom: 1.6           // how much the icon under the pointer grows (1 = no magnification)
  property bool autohide: false
  property bool showTrash: true

  function apply(text) {
    var o = {}
    try { o = JSON.parse(text) } catch (e) { o = {} }
    root.pinned = Array.isArray(o.pinned) ? o.pinned : defaultPinned
    if (typeof o.iconSize === "number") root.iconSize = Math.max(32, Math.min(96, o.iconSize))
    if (typeof o.zoom === "number") root.zoom = Math.max(1, Math.min(2.4, o.zoom))
    if (typeof o.autohide === "boolean") root.autohide = o.autohide
    if (typeof o.showTrash === "boolean") root.showTrash = o.showTrash
  }

  function save() {
    file.setText(JSON.stringify({ pinned: root.pinned, iconSize: root.iconSize, zoom: root.zoom, autohide: root.autohide, showTrash: root.showTrash }, null, 2) + "\n")
  }

  function pin(id) {
    if (root.pinned.indexOf(id) < 0) { root.pinned = root.pinned.concat([id]); save() }
  }

  function unpin(id) {
    root.pinned = root.pinned.filter(function (p) { return p !== id }); save()
  }

  function toggleAutohide() { root.autohide = !root.autohide; save() }

  FileView {
    id: file
    path: root.path
    watchChanges: true
    atomicWrites: true
    onFileChanged: reload()
    onLoaded: root.apply(text())
    onLoadFailed: root.apply("{}")
  }
}
