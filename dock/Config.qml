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

  // Hot corners: what happens when the pointer rests in a screen corner for a moment. "none" turns a corner off (it then has no surface at all).
  readonly property var cornerNames: ["topLeft", "topRight", "bottomLeft", "bottomRight"]
  readonly property var cornerActions: ["none", "missioncontrol", "appexpose", "apps", "quicknote", "lock", "notifications"]
  readonly property var defaultCorners: ({ topLeft: "none", topRight: "none", bottomLeft: "none", bottomRight: "none" })   // off until you choose

  property var pinned: defaultPinned
  property var hotCorners: defaultCorners
  property int hotCornerDelay: 350   // ms the pointer must rest in the corner
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
    var hc = {}
    for (var i = 0; i < cornerNames.length; i++) {
      var name = cornerNames[i], want = o.hotCorners ? o.hotCorners[name] : undefined
      hc[name] = cornerActions.indexOf(want) >= 0 ? want : defaultCorners[name]   // anything unknown falls back to the default, never to an action
    }
    root.hotCorners = hc
    if (typeof o.hotCornerDelay === "number") root.hotCornerDelay = Math.max(100, Math.min(2000, Math.round(o.hotCornerDelay)))
  }

  function save() {
    file.setText(JSON.stringify({ pinned: root.pinned, iconSize: root.iconSize, zoom: root.zoom, autohide: root.autohide, showTrash: root.showTrash,
                                  hotCorners: root.hotCorners, hotCornerDelay: root.hotCornerDelay }, null, 2) + "\n")
  }

  function pin(id) {
    if (root.pinned.indexOf(id) < 0) { root.pinned = root.pinned.concat([id]); save() }
  }

  function unpin(id) {
    root.pinned = root.pinned.filter(function (p) { return p !== id }); save()
  }

  // Drag to reorder: put `id` before (or after) `targetId` among the pinned apps. Returns true when the order changed.
  function moveTo(id, targetId, after) {
    if (id === targetId || root.pinned.indexOf(id) < 0 || root.pinned.indexOf(targetId) < 0) return false
    var list = root.pinned.filter(function (p) { return p !== id })
    var at = list.indexOf(targetId) + (after ? 1 : 0)
    list.splice(at, 0, id)
    if (list.join("\n") === root.pinned.join("\n")) return false
    root.pinned = list; save()
    return true
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
