local active_border_color = { colors = { "#c1082c", "#ff8fba" }, angle = 45 }
local inactive_border_color = "rgba(c99bb0aa)"

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
})
