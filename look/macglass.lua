-- Blur behind the glass (Omarchy Kit). Installed by look/install-look as ~/.config/hypr/macglass.lua; switched with look/mac-glass on|off.
--
-- macOS draws its menus, Dock, notifications and Spotlight on blurred, translucent "glass". In Hyprland that is a layer rule per surface
-- plus the global blur settings. It costs GPU time (this laptop's Intel graphics drive a 2880x1800 panel), so it is OFF until you turn it on:
--     look/mac-glass on      then   hyprctl reload          (mac-glass does the reload)
--     look/mac-glass off
-- The state is the word in ~/.config/omarchy-kit/glass. The windows themselves are not blurred (their opacity stays what Omarchy sets); only
-- the shell's own surfaces and the Dock, switcher and Mission Control are.
--
-- Undo: ~/labspace/omarchy-kit/look/install-look --remove

local function enabled()
  local file = io.open((os.getenv("HOME") or "") .. "/.config/omarchy-kit/glass", "r")
  if not file then
    return false
  end
  local word = (file:read("*a") or ""):gsub("%s+", "")
  file:close()
  return word == "on"
end

if enabled() then
  hl.config({
    decoration = {
      blur = {
        enabled = true,
        size = 7,
        passes = 2,
        noise = 0.012,
        contrast = 0.95,
        brightness = 1.0,
        vibrancy = 0.18,
        new_optimizations = true,
      },
    },
  })

  -- Surfaces that are meant to look like glass. The bar is left out on purpose: the macOS menu bar has no background of its own.
  hl.layer_rule({
    match = { namespace = "^(macdock|macswitcher|macmission|omarchy-menu|omarchy-emojis|omarchy-clipboard|omarchy-keyboard-panel|omarchy-notifications|omarchy-osd|omarchy-polkit|omarchy-reminders)$" },
    blur = true,
    ignore_alpha = 0.2,
  })
  -- The bar's drop-down panels (Wi-Fi, sound, battery, the menus of the Mac menu bar) are popups of the bar's surface.
  hl.layer_rule({ match = { namespace = "^omarchy-bar$" }, blur_popups = true, ignore_alpha = 0.2 })
end
