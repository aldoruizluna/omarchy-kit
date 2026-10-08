local active_border_color = "rgb(ff5a36)"
local active_shadow_color = "rgba(ff5a3699)"
local inactive_border_color = "rgba(8f6f8066)"
local inactive_shadow_color = "rgba(4a162077)"

hl.config({
  general = {
    col = {
      active_border = active_border_color,
      inactive_border = inactive_border_color,
    },
  },

  group = {
    col = {
      border_active = active_border_color,
      border_inactive = inactive_border_color,
    },
  },

  decoration = {
    shadow = {
      enabled = true,
      range = 6,
      render_power = 4,
      color = active_shadow_color,
      color_inactive = inactive_shadow_color,
    },
  },
})
