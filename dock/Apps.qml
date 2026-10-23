pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Wayland

// What is running and what is pinned, grouped by application. The dock and the switcher both read this.
Singleton {
  id: root

  // Most recently used application keys first. Updated when the focused window changes.
  property var mru: []

  readonly property var toplevels: ToplevelManager.toplevels.values
  readonly property var active: ToplevelManager.activeToplevel

  // Web apps (Omarchy's WhatsApp, Google Maps, ...) are Chromium windows whose class is built from the address:
  // brave-web.whatsapp.com__-Default for https://web.whatsapp.com/. The launcher entry for the same address is the match.
  property var webapps: ({})

  function webappCore(url) {
    var m = /^https?:\/\/([^\/:?#]+)(?::\d+)?([^?#]*)/.exec(url || "")
    return m ? m[1] + "_" + (m[2] || "/").replace(/\//g, "_") : ""
  }

  function indexWebapps() {
    var list = DesktopEntries.applications.values, out = {}
    for (var i = 0; i < list.length; i++) {
      var m = /(?:omarchy-launch-webapp\s+|--app=)["']?(https?:\/\/[^\s"']+)/.exec(list[i].execString || "")
      if (m) out[webappCore(m[1])] = list[i]
    }
    root.webapps = out
  }

  function webappCoreOf(appId) {
    var m = /^(?:brave|chromium|chrome|google-chrome|brave-browser)-(.+)-(?:Default|Profile \d+)$/.exec(appId || "")
    return m ? m[1] : ""
  }

  Connections {
    target: DesktopEntries
    function onApplicationsChanged() { root.indexWebapps() }
  }
  Component.onCompleted: indexWebapps()

  function entryFor(appId) {
    if (!appId) return null
    var core = webappCoreOf(appId)
    if (core) return root.webapps[core] || null      // never let a web app fall through to the browser's own entry
    return DesktopEntries.byId(appId) || DesktopEntries.heuristicLookup(appId) || null
  }

  function keyFor(toplevel) {
    var e = entryFor(toplevel.appId)
    return e ? e.id : "~" + toplevel.appId
  }

  function prettyName(appId) {
    var core = webappCoreOf(appId)
    if (core) {
      var parts = core.split("_")[0].split(".")
      var word = parts.length >= 2 && !/^\d+$/.test(parts[parts.length - 1]) ? parts[parts.length - 2] : parts.join(".")
      return word.charAt(0).toUpperCase() + word.slice(1)
    }
    var s = (appId || "").split(".").pop()
    return s.length ? s.charAt(0).toUpperCase() + s.slice(1) : "App"
  }

  function group(tops) {
    var groups = {}, order = []
    for (var i = 0; i < tops.length; i++) {
      var t = tops[i]
      if (!t.appId) continue
      var k = keyFor(t)
      if (!groups[k]) {
        var e = entryFor(t.appId)
        groups[k] = { key: k, entry: e, name: e ? e.name : prettyName(t.appId), icon: e ? e.icon : t.appId, windows: [] }
        order.push(k)
      }
      groups[k].windows.push(t)
    }
    return { groups: groups, order: order }
  }

  // Apps that run with no window (closed to the tray, a service in the background): the Dock shows them with a lighter dot. There is no
  // window to ask, so the process list is read every few seconds and an app counts when a process carries the name of its launcher.
  property var procs: ({})

  Process {
    id: psProbe
    command: ["ps", "-eo", "comm="]
    stdout: StdioCollector {
      onStreamFinished: {
        var names = {}, lines = text.split("\n")
        for (var i = 0; i < lines.length; i++) if (lines[i].length) names[lines[i].trim()] = true
        root.procs = names
      }
    }
  }
  Timer { interval: 4000; running: true; repeat: true; triggeredOnStart: true; onTriggered: psProbe.running = true }

  // The launchers that start something else: the process to look for is not theirs, so these answer "cannot tell".
  readonly property var wrappers: ({ "sh": 1, "bash": 1, "uwsm-app": 1, "flatpak": 1, "gtk-launch": 1, "setsid": 1, "nohup": 1, "xdg-terminal-exec": 1,
                                     "omarchy-launch-webapp": 1, "omarchy-launch-or-focus": 1, "omarchy-launch-tui": 1, "omarchy-launch-browser": 1 })

  // The name `ps` shows for an entry's program: the first word of its Exec line (past `env VAR=x`), cut to the 15 characters the kernel keeps.
  function processName(entry) {
    var cmd = entry && entry.command ? entry.command : []
    var i = 0
    while (i < cmd.length) {
      var base = String(cmd[i]).split("/").pop()
      if (base === "env") {
        i++
        while (i < cmd.length && (String(cmd[i]).indexOf("=") > 0 || String(cmd[i]).charAt(0) === "-")) i++
        continue
      }
      return root.wrappers[base] ? "" : base.slice(0, 15)
    }
    return ""
  }

  function inBackground(entry) {
    var n = processName(entry)
    return n !== "" && root.procs[n] === true
  }

  // Dock items: pinned first (in the order of dock.json), then the other running apps.
  function dockItems(tops, pinned) {
    var g = group(tops)
    var items = []
    for (var i = 0; i < pinned.length; i++) {
      var e = DesktopEntries.byId(pinned[i])
      if (!e) continue
      var run = g.groups[e.id]
      items.push({ key: e.id, kind: "app", entry: e, name: e.name, icon: e.icon, pinned: true, windows: run ? run.windows : [], background: !run && inBackground(e) })
      delete g.groups[e.id]
    }
    var extras = []
    for (var j = 0; j < g.order.length; j++) {
      var grp = g.groups[g.order[j]]
      if (grp) extras.push({ key: grp.key, kind: "app", entry: grp.entry, name: grp.name, icon: grp.icon, pinned: false, windows: grp.windows })
    }
    return { pinned: items, running: extras }
  }

  // Running applications in most-recently-used order, for the switcher.
  function switcherItems(tops, mruKeys) {
    var g = group(tops)
    var out = [], seen = {}
    for (var i = 0; i < mruKeys.length; i++) {
      var grp = g.groups[mruKeys[i]]
      if (grp) { out.push(grp); seen[mruKeys[i]] = true }
    }
    for (var j = 0; j < g.order.length; j++) {
      if (!seen[g.order[j]]) out.push(g.groups[g.order[j]])
    }
    return out
  }

  onActiveChanged: {
    if (!active || !active.appId) return
    var k = keyFor(active)
    root.mru = [k].concat(root.mru.filter(function (x) { return x !== k })).slice(0, 40)
  }


  // Focusing goes through Hyprland so an app that was hidden with ⌘H comes back to the current workspace first.
  function focusApp(item) {
    if (item.windows && item.windows.length > 0) {
      Quickshell.execDetached(["hyprctl", "eval", "o.mac_focus_class(" + JSON.stringify(item.windows[0].appId) + ")"])
    } else if (item.entry) {
      item.entry.execute()
    }
  }

  function quitApp(item) {
    for (var i = 0; i < item.windows.length; i++) item.windows[i].close()
  }

  function hideApp(item) {
    if (item.windows && item.windows.length > 0)
      Quickshell.execDetached(["hyprctl", "eval", "o.mac_hide_class(" + JSON.stringify(item.windows[0].appId) + ")"])
  }

  function open(path) { Quickshell.execDetached(["xdg-open", path]) }
}
