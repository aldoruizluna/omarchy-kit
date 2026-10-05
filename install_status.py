import subprocess
from pathlib import Path

def installed(a):
    if a["type"] in ("pacman", "aur"):
        return subprocess.run(["pacman", "-Qq", a["pkg"]], capture_output=True).returncode == 0
    if a["type"] == "webapp":
        return (Path.home() / ".local/share/applications" / f"{a['name']}.desktop").exists()
    return False
