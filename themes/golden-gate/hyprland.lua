-- Golden Gate window style: rounded corners with smooth (squircle-like) curvature, a soft deep shadow, a hairline edge, and a faint
-- accent edge on the focused window instead of Omarchy's glowing gradient. The corner radius is also what the shell's popups,
-- menus and notifications use (the shell mirrors decoration:rounding).
local active_border_color = "rgba(0066d68c)"
local inactive_border_color = "rgba(00000024)"

hl.config({
  general = {
    border_size = 1,
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
    rounding = 16,
    rounding_power = 4.0,
    dim_inactive = true,
    dim_strength = 0.06,
    shadow = {
      enabled = true,
      range = 36,
      render_power = 3,
      color = "rgba(0000003d)",
      color_inactive = "rgba(0000001f)",
    },
  },
})

-- Spaces slide, as they do on a Mac and under a swipe between desktops (Omarchy turns the workspace animation off). The curve is
-- defined here so the theme does not depend on the order Omarchy loads its own.
hl.curve("macEase", { type = "bezier", points = { { 0.25, 1 }, { 0.5, 1 } } })
hl.animation({ leaf = "workspaces", enabled = true, speed = 5, bezier = "macEase", style = "slide" })
