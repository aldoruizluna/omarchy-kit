-- Mac menu bar actions (Omarchy Kit). Installed by menubar/install-menubar as ~/.config/hypr/macmenu.lua.
--
-- The menu bar widget (File, Edit, View, Window, Help and the Apple menu) is shown by Omarchy's shell, but almost no Wayland app
-- publishes a real menu to it, so the menus are the standard Mac ones and each item does what the same ⌘ shortcut would do in
-- the focused app: it sends that chord (Ctrl+key in apps; copy and paste are translated for terminals). The widget calls
-- o.mac_menu("<id>") through `hyprctl eval`; the ids are the keys of ACTIONS below.
--
-- Undo: ~/labspace/omarchy-kit/menubar/install-menubar --remove

local function active_window_is_terminal()
  local window = hl.get_active_window()
  if not window then
    return false
  end
  for _, tag in ipairs(window.tags or {}) do
    if tag:gsub("%*$", "") == "terminal" then
      return true
    end
  end
  return false
end

-- Send a chord to the focused app's window by address, so it still reaches the app while a menu has the pointer or the keyboard.
-- Down now, up 50 ms later, like Omarchy's own universal copy/paste (a combined press sometimes leaves a synthetic key stuck).
local function send(mods, key)
  local window = hl.get_active_window()
  if not window then
    return
  end
  local target = "address:" .. window.address
  hl.dispatch(hl.dsp.send_key_state({ mods = mods, key = key, state = "down", window = target }))
  hl.timer(function()
    hl.dispatch(hl.dsp.send_key_state({ mods = mods, key = key, state = "up", window = target }))
  end, { timeout = 50, type = "oneshot" })
end

local function chord(mods, key)
  return function() send(mods, key) end
end

local function run(command)
  return function() hl.exec_cmd(command) end
end

local ACTIONS = {
  -- Apple menu
  ["apple.about"]    = run(o.launch_webapp("http://127.0.0.1:8787/macbook")),
  ["apple.settings"] = run("omarchy-menu toggle setup"),
  ["apple.store"]    = run("omarchy-menu toggle install"),
  ["apple.menu"]     = run("omarchy-menu toggle"),
  ["apple.forcequit"] = function() hl.dispatch(hl.dsp.window.kill()) end,
  ["apple.sleep"]    = run("systemctl suspend"),
  ["apple.restart"]  = run("omarchy system reboot"),
  ["apple.shutdown"] = run("omarchy system shutdown"),
  ["apple.lock"]     = run("omarchy system lock"),
  ["apple.logout"]   = run("omarchy system logout"),

  -- App menu
  ["app.settings"]   = chord("CTRL", "comma"),
  ["app.hide"]       = function() o.mac_hide_app() end,          -- from dock/macdock.lua
  ["app.quit"]       = function() o.mac_quit_app() end,

  -- File
  ["file.new"]       = chord("CTRL", "N"),
  ["file.newtab"]    = chord("CTRL", "T"),
  ["file.open"]      = chord("CTRL", "O"),
  ["file.close"]     = function()
    if active_window_is_terminal() then hl.dispatch(hl.dsp.window.close()) else send("CTRL", "W") end
  end,
  ["file.save"]      = chord("CTRL", "S"),
  ["file.print"]     = chord("CTRL", "P"),

  -- Edit
  ["edit.undo"]      = chord("CTRL", "Z"),
  ["edit.redo"]      = chord("CTRL SHIFT", "Z"),
  ["edit.cut"]       = chord("CTRL", "X"),
  ["edit.copy"]      = function()
    if active_window_is_terminal() then send("CTRL", "Insert") else send("CTRL", "C") end
  end,
  ["edit.paste"]     = function()
    if active_window_is_terminal() then send("SHIFT", "Insert") else send("CTRL", "V") end
  end,
  ["edit.selectall"] = chord("CTRL", "A"),
  ["edit.find"]      = chord("CTRL", "F"),
  ["edit.findnext"]  = chord("CTRL", "G"),

  -- View
  ["view.reload"]    = chord("CTRL", "R"),
  ["view.zoomin"]    = chord("CTRL", "equal"),
  ["view.zoomout"]   = chord("CTRL", "minus"),
  ["view.actual"]    = chord("CTRL", "0"),
  ["view.fullscreen"] = function() hl.dispatch(hl.dsp.window.fullscreen({ mode = "fullscreen" })) end,

  -- Window
  ["window.float"]   = function() hl.dispatch(hl.dsp.window.float({ action = "toggle" })) end,
  ["window.center"]  = function() hl.dispatch(hl.dsp.window.center()) end,
  ["window.next"]    = function() o.mac_next_window() end,

  -- Help
  ["help.kit"]       = run(o.launch_webapp("http://127.0.0.1:8787/")),
  ["help.keys"]      = run("omarchy-menu keybindings"),
}

for n = 1, 5 do
  ACTIONS["window.move" .. n] = function()
    hl.dispatch(hl.dsp.window.move({ workspace = tostring(n) }))
  end
end

o.mac_menu_actions = ACTIONS

function o.mac_menu(id)
  local action = ACTIONS[id]
  if action then
    action()
  end
end
