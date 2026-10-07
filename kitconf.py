"""Settings the kit reads from the user's real config, so pages describe what is actually on."""
import re
from pathlib import Path

INPUT_LUA = Path.home() / ".config/hypr/input.lua"


def three_fingers():
    """What three fingers do on the trackpad: "swipe" (switch spaces) or "drag" (select / drag without clicking).

    Set by `local THREE_FINGERS = "..."` in ~/.config/hypr/input.lua; "swipe" if the line is missing."""
    try:
        m = re.search(r'^\s*local\s+THREE_FINGERS\s*=\s*"(swipe|drag)"', INPUT_LUA.read_text(), re.M)
    except OSError:
        m = None
    return m.group(1) if m else "swipe"


MACKEYS_CONF = Path.home() / ".config/omarchy-kit/mackeys.conf"
EXTRA_KEYS = "WTFSLGP"


def mackeys_extra():
    """Letters of the Mac keys (⌘W ⌘T ⌘F ⌘S ⌘L ⌘G ⌘P) that replace an Omarchy shortcut in apps; "" when none."""
    try:
        for line in MACKEYS_CONF.read_text().splitlines():
            m = re.match(r'\s*EXTRA\s*=\s*"([^"]*)"', line)
            if m and not line.lstrip().startswith("#"):
                return "".join(ch for ch in EXTRA_KEYS if ch in m.group(1).upper())
    except OSError:
        pass
    return ""
