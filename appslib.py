"""Shared helpers: load apps.toml and render the apps page."""
import json, tomllib
from pathlib import Path
HERE = Path(__file__).resolve().parent

def load():
    return tomllib.loads((HERE / "apps.toml").read_text())["app"]

def shell_cmd(a):
    t = a["type"]
    if t == "pacman": return f"sudo pacman -S --needed {a['pkg']}" + (f" && {a['post']}" if a.get("post") else "")
    if t == "aur": return f"yay -S --needed {a['pkg']}"
    if t == "webapp": return f"omarchy-webapp-install {a['name']} {a['url']} {a['icon']}"
    return ""

def render(token=None):
    apps = [{**a, "cmd": shell_cmd(a)} for a in load()]
    data = json.dumps(apps, ensure_ascii=False).replace("</", "<\\/")
    html = (HERE / "apps.template.html").read_text()
    return (html.replace("/*__DATA__*/[]", data)
                .replace("/*__TOKEN__*/null", json.dumps(token)))
