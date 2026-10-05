#!/usr/bin/env python3
"""Build the learning portal pages (Start, Learn, From macOS, Your MacBook, Reference).

Everything shown is derived from this machine: shortcuts come from data/bindings.json (exported by
build_cheatsheet.py from Omarchy's live keybinding list), commands from the headers of Omarchy's own
scripts, the menu tree from Omarchy's menu definition. Any shortcut the content names but the system
doesn't have is reported (and shown on the page as "not bound") instead of being invented.
"""
import json, re, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import portal_content as C
import portal_lessons as LS

OMARCHY = Path("/usr/share/omarchy")

# ---------------------------------------------------------------- shortcuts
BIND = json.loads((HERE / "data" / "bindings.json").read_text())
ORDER = ["SUPER", "SHIFT", "CTRL", "ALT"]
OFFKEY = re.compile(r"PRINT|MOUSE|mouse_|XF86|^HOME$|^DELETE$", re.I)


def combo(desc):
    """Best pressable binding for a description: skip Print/mouse/media-only variants when a normal one exists."""
    cands = [b for b in BIND if b["en"] == desc]
    if not cands:
        return None
    cands.sort(key=lambda b: (bool(OFFKEY.search(b["key"])), len(b["mods"])))
    b = cands[0]
    return sorted(b["mods"], key=ORDER.index) + [b["key"]]


def collect_descs():
    names = set()
    for lv in LS.LEVELS:
        for ls in lv["lessons"]:
            for st in ls["steps"]:
                if st.get("k"): names.add(st["k"])
    for _, _, rows in C.MAC:
        for r in rows: names.update(r.get("k", []))
    for h in C.HW:
        if h.get("k"): names.add(h["k"])
    names.update(["Keybindings", "Omarchy menu", "Apps menu", "Terminal", "Close window", "Omarchy Kit", "Switch to workspace 1", "Move window to workspace 1"])
    return names


# ---------------------------------------------------------------- Omarchy's own commands and menu
def commands():
    out = []
    groups = {}
    for line in (OMARCHY / "bin" / "omarchy").read_text().splitlines():
        m = re.match(r'\s*GROUP_DESCRIPTIONS\[(\w[\w-]*)\]="(.*)"', line)
        if m: groups[m[1]] = m[2]
    for f in sorted((OMARCHY / "bin").iterdir()):
        try: head = f.read_text(errors="ignore")[:1500]
        except Exception: continue
        if "omarchy:hidden=true" in head: continue
        m = re.search(r"^# omarchy:summary=(.*)$", head, re.M)
        if not m: continue
        args = re.search(r"^# omarchy:args=(.*)$", head, re.M)
        ex = re.search(r"^# omarchy:examples=(.*)$", head, re.M)
        sudo = "omarchy:requires-sudo=true" in head
        name = f.name
        group = name.split("-")[1] if name.count("-") >= 1 else "other"
        out.append({"cmd": name, "summary": m[1].strip(), "args": args[1].strip() if args else "",
                    "examples": [e.strip() for e in ex[1].split("|")] if ex else [], "sudo": sudo, "group": group})
    return out, groups


def jsonc(path):
    s = Path(path).read_text()
    s = re.sub(r"/\*.*?\*/", "", s, flags=re.S)
    s = re.sub(r'(?m)^\s*//.*$', "", s)
    s = re.sub(r",(\s*[}\]])", r"\1", s)
    return json.loads(s)


def menu():
    d = jsonc(OMARCHY / "default" / "omarchy" / "omarchy-menu.jsonc")
    try: d.update(jsonc(Path.home() / ".config/omarchy/extensions/omarchy-menu.jsonc"))
    except Exception: pass
    items = []
    for k, v in d.items():
        if not isinstance(v, dict): continue
        items.append({"id": k, "label": v.get("label", k), "action": v.get("action", ""), "target": v.get("target", ""),
                      "aliases": v.get("aliases", []), "provider": v.get("provider", ""), "when": bool(v.get("when"))})
    return items


def themes():
    cur = ""
    try:
        import subprocess
        cur = subprocess.run(["omarchy-theme-current"], capture_output=True, text=True, timeout=3).stdout.strip()
    except Exception: pass
    return {"all": sorted(p.name for p in (OMARCHY / "themes").iterdir() if p.is_dir()), "current": cur}


def build():
    keys, missing = {}, []
    for d in sorted(collect_descs()):
        c = combo(d)
        if c: keys[d] = c
        else: missing.append(d)
    cmds, groups = commands()
    mitems = menu()
    (HERE / "data").mkdir(exist_ok=True)
    (HERE / "data" / "menu_ids.json").write_text(json.dumps([m["id"] for m in mitems]))
    version = (OMARCHY / "version").read_text().strip() if (OMARCHY / "version").exists() else ""
    data = {"keys": keys, "missing": missing, "levels": LS.LEVELS, "mac": C.MAC, "glossary": C.GLOSSARY, "hw": C.HW,
            "commands": cmds, "groups": groups, "menu": mitems, "themes": themes(), "version": version}
    blob = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    for page in ("index", "learn", "mac", "macbook", "reference", "system"):
        tpl = HERE / f"{page}.template.html"
        if tpl.exists():
            (HERE / f"{page}.html").write_text(tpl.read_text().replace("/*__PORTAL__*/{}", blob))
    write_index(data)
    return data


def write_index(data):
    """data/kit-index.json: everything the Ctrl+K palette searches and the progress badges count."""
    sys.path.insert(0, str(HERE))
    from appslib import load as load_apps
    lessons = [{"id": l["id"], "en": l["en"], "es": l["es"], "level": lv["id"], "steps": len(l["steps"])}
               for lv in LS.LEVELS for l in lv["lessons"]]
    levels = [{"id": lv["id"], "en": lv["en"], "es": lv["es"], "lessons": [l["id"] for l in lv["lessons"]]} for lv in LS.LEVELS]
    keys = [{"en": b["en"], "es": b["es"], "k": sorted(b["mods"], key=ORDER.index) + [b["key"]]} for b in BIND]
    seen, shortcuts = set(), []
    for k in keys:  # one row per description; collapse numbered workspace bindings
        if k["en"] in seen: continue
        seen.add(k["en"]); shortcuts.append(k)
    mac = [{"en": r["mac"]["en"], "es": r["mac"]["es"], "mk": r.get("mk", ""), "group": {"en": g_en, "es": g_es}}
           for g_en, g_es, rows in C.MAC for r in rows]
    gloss = [{"en": g[0], "es": g[1], "den": g[2], "des": g[3]} for g in C.GLOSSARY]
    apps = [{"id": a["id"], "name": a["name"], "en": a.get("desc", {}).get("en", ""), "es": a.get("desc", {}).get("es", "")} for a in load_apps()]
    cmds = [{"cmd": c["cmd"], "summary": c["summary"]} for c in data["commands"]]
    menu = [{"id": m["id"], "label": m["label"]} for m in data["menu"] if m["label"] and not m["when"]]
    idx = {"lessons": lessons, "levels": levels, "shortcuts": shortcuts, "mac": mac, "glossary": gloss,
           "apps": apps, "commands": cmds, "menu": menu}
    (HERE / "data" / "kit-index.json").write_text(json.dumps(idx, ensure_ascii=False))


if __name__ == "__main__":
    d = build()
    n_steps = sum(len(l["steps"]) for lv in d["levels"] for l in lv["lessons"])
    print(f"portal: {sum(len(lv['lessons']) for lv in d['levels'])} lessons / {n_steps} steps, "
          f"{sum(len(r) for _, _, r in d['mac'])} macOS translations, {len(d['commands'])} commands, {len(d['menu'])} menu items, "
          f"{len(d['glossary'])} glossary terms")
    if d["missing"]:
        print("NOT BOUND on this system (shown as 'not bound'):", ", ".join(d["missing"]))
