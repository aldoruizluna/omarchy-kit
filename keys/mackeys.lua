-- Mac ⌘ shortcuts inside apps (Omarchy Kit). Installed by keys/install-mackeys as ~/.config/hypr/mackeys.lua.
--
-- On a Mac, ⌘ is the key for app shortcuts (⌘Z undo, ⌘R reload, ⌘A select all...). On Omarchy that
-- same key is Super and the apps still expect Ctrl. Each binding below catches Super+<key> and sends
-- Ctrl+<key> to the focused app instead, so the Mac habit works in Brave, Files, editors and web apps.
--
-- Only keys that Omarchy does not already use for itself are mapped, so nothing Omarchy does is lost.
-- Super+W, T, F, S, L, P, G, K, J, O, C, V, X, Shift+N and Super+1..9 keep their Omarchy meaning, which is
-- why ⌘W, ⌘T, ⌘F, ⌘S, ⌘L and ⌘G are not here yet (they would replace close window, float, full screen,
-- scratchpad, layout and grouping).
-- Terminals are skipped on purpose: Ctrl+Z there suspends a program and Ctrl+A moves the cursor, which is
-- never what ⌘Z or ⌘A meant. Copy and paste (Super+C/V/X) already work everywhere through Omarchy.
--
-- Undo: ~/labspace/omarchy-kit/keys/install-mackeys --remove

-- Same approach as Omarchy's own default/hypr/bindings/clipboard.lua: send the chord to the focused
-- surface, with a separate key-up so the synthetic key never sticks.
local function send_shortcut_once(mods, key)
  return function()
    hl.dispatch(hl.dsp.send_key_state({ mods = mods, key = key, state = "down" }))

    hl.timer(function()
      hl.dispatch(hl.dsp.send_key_state({ mods = mods, key = key, state = "up" }))
    end, { timeout = 50, type = "oneshot" })
  end
end

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

local function app_shortcut(mods, key)
  local send = send_shortcut_once(mods, key)
  return function()
    if not active_window_is_terminal() then
      send()
    end
  end
end

-- { the Mac shortcut as a Hyprland key, modifiers to send instead, key to send, description }
local MAP = {
  { "SUPER + A",            "CTRL",       "A",     "Select all (⌘A)" },
  { "SUPER + Z",            "CTRL",       "Z",     "Undo (⌘Z)" },
  { "SUPER + SHIFT + Z",      "CTRL SHIFT", "Z",     "Redo (⇧⌘Z)" },
  { "SUPER + R",            "CTRL",       "R",     "Reload (⌘R)" },
  { "SUPER + SHIFT + R",      "CTRL SHIFT", "R",     "Hard reload (⇧⌘R)" },
  { "SUPER + N",            "CTRL",       "N",     "New window (⌘N)" },
  { "SUPER + SHIFT + T",      "CTRL SHIFT", "T",     "Reopen closed tab (⇧⌘T)" },
  { "SUPER + D",            "CTRL",       "D",     "Bookmark page (⌘D)" },
  { "SUPER + B",            "CTRL",       "B",     "Bold (⌘B)" },
  { "SUPER + I",            "CTRL",       "I",     "Italic (⌘I)" },
  { "SUPER + U",            "CTRL",       "U",     "Underline (⌘U)" },
  { "SUPER + BRACKETLEFT",  "ALT",        "Left",  "Back (⌘[)" },
  { "SUPER + BRACKETRIGHT", "ALT",        "Right", "Forward (⌘])" },
}

-- The handlers are kept in o.mac_shortcuts[description] so test/verify-mackeys.mjs can call them
-- without pressing keys (hyprctl eval 'o.mac_shortcuts["Undo (⌘Z)"]()').
o.mac_shortcuts = {}
for _, m in ipairs(MAP) do
  local handler = app_shortcut(m[2], m[3])
  o.mac_shortcuts[m[4]] = handler
  o.bind(m[1], m[4], handler)
end

-- ---------------------------------------------------------------------------------------------------------
-- Optional takeovers: the Mac keys that Omarchy already uses (OFF until you list them).
--
-- Enable key by key in ~/.config/omarchy-kit/mackeys.conf:   EXTRA="W T F S"   (or run keys/mac-key-extras W T F S)
-- For each listed key, Super+<key> then does the Mac thing in apps (sends Ctrl+<key>), and keeps doing the
-- Omarchy thing in terminals. The Omarchy action stays reachable in every window at the chord in `home`.
--   key  Mac meaning in apps        Omarchy meaning (kept in terminals)       Omarchy action in apps
--   W    close tab / window         close window                              Super+Alt+W
--   T    new tab                    toggle floating / tiling                  Super+Alt+T
--   F    find                       full screen                               Super+Ctrl+Alt+F
--   S    save                       toggle scratchpad                         Super+Ctrl+Alt+S
--   L    address bar                toggle workspace layout                   Super+Alt+L
--   G    find next                  toggle window grouping                    Super+Ctrl+Alt+G
--   P    print                      pseudo window                             Super+Ctrl+Alt+P
-- The Omarchy side is copied from /usr/share/omarchy/default/hypr/bindings/tiling.lua (one line each).
local EXTRA = {
  W = { mac = "Close tab or window (⌘W)", omarchy = "Close window (Omarchy, any app)", home = "SUPER + ALT + W",
        omarchy_action = function() hl.dispatch(hl.dsp.window.close()) end },
  T = { mac = "New tab (⌘T)", omarchy = "Toggle window floating/tiling (Omarchy, any app)", home = "SUPER + ALT + T",
        omarchy_action = function() hl.dispatch(hl.dsp.window.float({ action = "toggle" })) end },
  F = { mac = "Find (⌘F)", omarchy = "Full screen (Omarchy, any app)", home = "SUPER + CTRL + ALT + F",
        omarchy_action = function() hl.dispatch(hl.dsp.window.fullscreen({ mode = "fullscreen" })) end },
  S = { mac = "Save (⌘S)", omarchy = "Toggle scratchpad (Omarchy, any app)", home = "SUPER + CTRL + ALT + S",
        omarchy_action = function() hl.dispatch(hl.dsp.workspace.toggle_special("scratchpad")) end },
  L = { mac = "Address bar (⌘L)", omarchy = "Toggle workspace layout (Omarchy, any app)", home = "SUPER + ALT + L",
        omarchy_action = function() hl.exec_cmd("omarchy-hyprland-workspace-layout-toggle") end },
  G = { mac = "Find next (⌘G)", omarchy = "Toggle window grouping (Omarchy, any app)", home = "SUPER + CTRL + ALT + G",
        omarchy_action = function() hl.dispatch(hl.dsp.group.toggle()) end },
  P = { mac = "Print (⌘P)", omarchy = "Pseudo window (Omarchy, any app)", home = "SUPER + CTRL + ALT + P",
        omarchy_action = function() hl.dispatch(hl.dsp.window.pseudo()) end },
}

local active = {}

-- Take over the Super+<letter> keys in `letters` (e.g. "W T F S"); also callable from `hyprctl eval` for tests.
function o.mac_extras(letters)
  for key in tostring(letters or ""):upper():gmatch("%a") do
    local spec = EXTRA[key]
    if spec and not active[key] then
      active[key] = true
      local send = send_shortcut_once("CTRL", key)
      local handler = function()
        if active_window_is_terminal() then
          spec.omarchy_action()
        else
          send()
        end
      end
      hl.unbind("SUPER + " .. key)
      o.mac_shortcuts[spec.mac] = handler
      o.bind("SUPER + " .. key, spec.mac, handler)
      o.mac_shortcuts[spec.omarchy] = spec.omarchy_action
      o.bind(spec.home, spec.omarchy, spec.omarchy_action)
    end
  end
end

-- ~/.config/omarchy-kit/mackeys.conf: a line  EXTRA="W T F"  (lines starting with # are comments)
local conf = io.open((os.getenv("HOME") or "") .. "/.config/omarchy-kit/mackeys.conf", "r")
if conf then
  for line in (conf:read("*a") or ""):gmatch("[^\n]+") do
    if not line:match("^%s*#") then
      local letters = line:match('^%s*EXTRA%s*=%s*"([^"]*)"') or line:match("^%s*EXTRA%s*=%s*([%w ]*)")
      if letters then
        o.mac_extras(letters)
      end
    end
  end
  conf:close()
end
