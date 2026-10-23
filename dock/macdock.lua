-- Mac Dock, ⌘Tab app switcher and app shortcuts (Omarchy Kit). Installed by dock/install-dock as ~/.config/hypr/macdock.lua.
--
-- The dock and the switcher are one small Quickshell program (~/.local/share/macdock) started with the session. This file starts it,
-- gives its surfaces a no-animation layer rule like Omarchy's own bar, and binds the keys that talk to it:
--
--   Super+Tab / Super+Shift+Tab   app switcher (⌘Tab / ⇧⌘Tab). Hold Super, press Tab to step, let go to switch.
--   Super+`                       next window of the same app (⌘`)
--   Super+Q                       quit the app: close every window of the focused app (⌘Q)
--   Super+H                       hide the app: its windows go to a hidden workspace (⌘H); the dock and the switcher bring them back
--   Super+M                       hide this window only (⌘M, "minimise")
--   Super+Alt+D                   hide / show the dock (⌥⌘D)
--   Super+Alt+Escape              cancel the switcher (the keyboard remap sends it for Esc while the switcher is up)
--   Shift+Print                   full-screen screenshot (⇧⌘3; ⇧⌘4 is Omarchy's own Print, ⇧⌘5 its capture menu)
--   F3 (the Mission Control key)  Mission Control: all spaces and their windows. Same as Super+Ctrl+Up and four fingers up
--   F4 (the Launchpad key)        the Apps view (macOS 26 replaced Launchpad with Apps in Spotlight); same as the four-finger pinch
--   Super+Ctrl+Up                 Mission Control (⌃↑ on a Mac; plain Ctrl+Up stays a text-editing key until the keyboard remap sends this chord for ⌃↑)
--   Super+Ctrl+Down               App Exposé: only the windows of the focused app, from every space (⌃↓)
--   Super+Ctrl+Shift+Left/Right   previous / next workspace
--
-- What this replaces: Super+Tab and Super+Shift+Tab were "Next workspace" and "Previous workspace" in Omarchy; those moved to
-- Super+Ctrl+Shift+Right and Left (three- and four-finger swipes and Super+1..9 still switch workspaces). Super+Q, Super+H, Super+M,
-- Super+`, Super+Alt+D, Super+Alt+Escape, Shift+Print, F3 and F4 (XF86LaunchA and XF86LaunchB, which did nothing) and Super+Ctrl+Up/Down were free.
--
-- While the switcher is open, Super+Q and Super+H act on the app that is *selected* in it, not on the focused one (that is what ⌘Q and
-- ⌘H do in the macOS switcher); the bind asks Hyprland whether the switcher's layer exists, which needs no round trip to the dock.
-- With the keyboard remap (keys/install-keyd) installed both ⌘ keys are Ctrl and send these Super chords through its Mac chord table (⌃↑/↓ and
-- ⌃←/→ send the Super+Ctrl chords below); without it both ⌘ keys are Super itself.
--
-- Undo: ~/labspace/omarchy-kit/dock/install-dock --remove

local home = os.getenv("HOME") or ""
local share = home .. "/.local/share/macdock"

hl.layer_rule({ match = { namespace = "^(macdock|macswitcher|macmission)$" }, no_anim = true, animation = "none" })

hl.on("hyprland.start", function()
  hl.exec_cmd(o.launch("quickshell -n -p " .. o.shell_quote(share)))
end)

local function shell_ipc(target, fn)
  return "quickshell ipc -p " .. o.shell_quote(share) .. " call " .. target .. " " .. fn
end

-- ---------------------------------------------------------------------------------------------------------------------
-- ⌘Tab. The switcher closes itself when it sees ⌘ released, but only once it has the keyboard; a quick tap can let go before that
-- happens. So, as a second way out, a short timer asks Hyprland whether a ⌘ key (Super, or Ctrl when the keyboard remap makes ⌘ a
-- Ctrl) is still down and commits when none is. If Hyprland cannot tell (no ⌘ looks held when the key fires) the timer is not used.
local watching = false

local function cmd_held()
  for _, key in ipairs({ "Super_L", "Super_R", "Control_L", "Control_R" }) do
    local ok, down = pcall(hl.is_key_down, key)
    if ok and down then
      return true
    end
  end
  return false
end

local function watch_release()
  hl.timer(function()
    if cmd_held() then
      watch_release()
    else
      watching = false
      hl.dispatch(hl.dsp.global("macswitcher:commit"))
    end
  end, { timeout = 40, type = "oneshot" })
end

local function switch(name)
  hl.dispatch(hl.dsp.global("macswitcher:" .. name))
  if not watching and cmd_held() then
    watching = true
    watch_release()
  end
end

hl.unbind("SUPER + TAB")
hl.unbind("SUPER + SHIFT + TAB")
o.bind("SUPER + TAB", "App switcher (⌘Tab)", function() switch("next") end)
o.bind("SUPER + SHIFT + TAB", "App switcher, backwards (⇧⌘Tab)", function() switch("prev") end)
o.bind("SUPER + CTRL + SHIFT + RIGHT", "Next workspace", hl.dsp.focus({ workspace = "e+1" }))
o.bind("SUPER + CTRL + SHIFT + LEFT", "Previous workspace", hl.dsp.focus({ workspace = "e-1" }))

-- ---------------------------------------------------------------------------------------------------------------------
-- Windows of the focused app.
local function app_windows()
  local active = hl.get_active_window()
  local list = {}
  if not active then
    return list, nil
  end
  for _, w in ipairs(hl.get_windows()) do
    if w.mapped and not w.hidden and w.class == active.class then
      list[#list + 1] = w
    end
  end
  return list, active
end

-- ⌘`: focus the window of this app that was used longest ago, so repeating the shortcut walks through all of them.
function o.mac_next_window()
  local list, active = app_windows()
  if #list < 2 then
    return
  end
  table.sort(list, function(a, b) return a.focus_history_id > b.focus_history_id end)
  hl.dispatch(hl.dsp.focus({ window = "address:" .. list[1].address }))
end

-- ⌘Q: close every window of the focused app. Apps that ask first (unsaved work) still ask.
function o.mac_quit_app()
  local list = app_windows()
  for _, w in ipairs(list) do
    hl.dispatch(hl.dsp.window.close({ window = "address:" .. w.address }))
  end
end

o.bind("SUPER + GRAVE", "Next window of this app (⌘`)", o.mac_next_window)
o.bind("SUPER + ALT + D", "Hide or show the dock (⌥⌘D)", shell_ipc("dock", "toggleAutohide"))

-- ⌘H and ⌘M. Tiling has no "minimise", so hiding puts windows on a special workspace nobody looks at. They are still running (the
-- dock keeps their dot) and clicking the app in the dock, or picking it in the switcher, brings them back to the current workspace.
local HIDDEN = "special:hidden"

local function windows_of(class)
  local list = {}
  for _, w in ipairs(hl.get_windows()) do
    if w.mapped and w.class == class then
      list[#list + 1] = w
    end
  end
  return list
end

local function is_hidden(w)
  return w.workspace ~= nil and tostring(w.workspace.name) == HIDDEN
end

local function hide_window(w)
  hl.dispatch(hl.dsp.window.move({ workspace = HIDDEN, follow = false, window = "address:" .. w.address }))
end

function o.mac_hide_class(class)
  for _, w in ipairs(windows_of(class)) do
    if not is_hidden(w) then
      hide_window(w)
    end
  end
end

function o.mac_hide_app()
  local active = hl.get_active_window()
  if active then
    o.mac_hide_class(active.class)
  end
end

function o.mac_hide_window()
  local active = hl.get_active_window()
  if active then
    hide_window(active)
  end
end

-- Bring an app forward: restore its hidden windows to the current workspace, then focus the one used most recently.
function o.mac_focus_class(class)
  local ws = hl.get_active_workspace()
  local list = windows_of(class)
  if #list == 0 then
    return
  end
  for _, w in ipairs(list) do
    if is_hidden(w) and ws then
      hl.dispatch(hl.dsp.window.move({ workspace = tostring(ws.id), follow = false, window = "address:" .. w.address }))
    end
  end
  table.sort(list, function(a, b) return a.focus_history_id < b.focus_history_id end)
  hl.dispatch(hl.dsp.focus({ window = "address:" .. list[1].address }))
end

o.bind("SUPER + M", "Hide this window (⌘M)", o.mac_hide_window)

-- The binds that depend on whether the switcher is up.
local function switcher_open()
  for _, layer in ipairs(hl.get_layers()) do
    if layer.namespace == "macswitcher" then
      return true
    end
  end
  return false
end

-- Named, so the tests can call them (hyprctl eval 'o.mac_cmd_q()') with the real actions replaced by stubs.
function o.mac_cmd_q()
  if switcher_open() then hl.dispatch(hl.dsp.global("macswitcher:quit")) else o.mac_quit_app() end
end

function o.mac_cmd_h()
  if switcher_open() then hl.dispatch(hl.dsp.global("macswitcher:hide")) else o.mac_hide_app() end
end

o.bind("SUPER + Q", "Quit app (⌘Q)", function() o.mac_cmd_q() end)
o.bind("SUPER + H", "Hide app (⌘H)", function() o.mac_cmd_h() end)
o.bind("SUPER + ALT + ESCAPE", "Cancel the app switcher", function()
  hl.dispatch(hl.dsp.global("macswitcher:cancel"))
end)
o.bind("SHIFT + Print", "Screenshot of the whole screen (⇧⌘3)", "omarchy-capture-screenshot fullscreen")

-- Mission Control and App Exposé (dock/MissionControl.qml). The four-finger swipe up in input.lua opens it too.
o.bind("XF86LaunchA", "Mission Control (F3)", hl.dsp.global("macmission:toggle"))
o.bind("XF86LaunchB", "Apps (F4)", "omarchy-menu toggle apps")
o.bind("SUPER + CTRL + UP", "Mission Control (⌃↑)", hl.dsp.global("macmission:toggle"))
o.bind("SUPER + CTRL + DOWN", "App Exposé (⌃↓)", hl.dsp.global("macmission:appwindows"))
