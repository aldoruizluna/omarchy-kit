-- macOS pointer (Omarchy Kit). Installed by icons/install-icons as ~/.config/hypr/maccursor.lua.
-- The macOS cursor set lives in ~/.local/share/icons/macOS (an open-source re-drawing, not Apple artwork).
-- Hyprland does not read GNOME's cursor setting, so tell it here; GTK apps follow gsettings (install-icons sets that too).
-- Undo: ~/labspace/omarchy-kit/icons/install-icons --remove
hl.env("XCURSOR_THEME", "macOS")
hl.env("XCURSOR_SIZE", "24")
-- Applied to the running session too, so a reload (not only the next login) shows it.
hl.exec_cmd("hyprctl setcursor macOS 24")
