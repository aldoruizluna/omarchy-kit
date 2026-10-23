#!/usr/bin/env python3
"""sddm_conf: what SDDM's configuration really says, read the way SDDM reads it (Omarchy Kit). Standard library only.

  sddm_conf.py get SECTION KEY [--root DIR]          print the effective value ("" if unset)
  sddm_conf.py autologin-files [--root DIR]          print the files in sddm.conf.d that set a non-empty [Autologin] User, one per line

SDDM 0.21 reads EVERY file in /usr/lib/sddm/sddm.conf.d and /etc/sddm.conf.d, whatever its name (ConfigReader.cpp: dir.entryInfoList(QDir::Files),
no name filter), then /etc/sddm.conf. Later files win. So renaming autologin.conf to autologin.conf.disabled does NOT turn auto-login off, which is how
it stayed on across two boots on 2026-10-23. --root DIR reads DIR/usr/lib/sddm/sddm.conf.d, DIR/etc/sddm.conf.d and DIR/etc/sddm.conf (for tests).
"""
import os
import sys


def parse(text):
    """{(section, key): value} from SDDM's ini dialect: [section], key=value, # and ; comments."""
    out, section = {}, ""
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line[0] in "#;":
            continue
        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1].strip()
        elif "=" in line:
            key, _, value = line.partition("=")
            out[(section, key.strip())] = value.strip()
    return out


def config_files(root="/"):
    """Every file SDDM reads, in the order it reads them (later wins)."""
    files = []
    for d in (os.path.join(root, "usr/lib/sddm/sddm.conf.d"), os.path.join(root, "etc/sddm.conf.d")):
        try:
            names = sorted(n for n in os.listdir(d) if os.path.isfile(os.path.join(d, n)))
        except OSError:
            continue
        files += [os.path.join(d, n) for n in names]
    main = os.path.join(root, "etc/sddm.conf")
    if os.path.isfile(main):
        files.append(main)
    return files


def read(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return parse(f.read())
    except OSError:
        return {}


def effective(root="/"):
    merged = {}
    for path in config_files(root):
        merged.update(read(path))
    return merged


def autologin_files(root="/"):
    """Files under sddm.conf.d (either tree) that set a non-empty [Autologin] User."""
    main = os.path.join(root, "etc/sddm.conf")
    return [p for p in config_files(root) if p != main and read(p).get(("Autologin", "User"), "")]


def main(argv):
    root = "/"
    if "--root" in argv:
        i = argv.index("--root")
        if i + 1 >= len(argv):
            print("usage: sddm_conf.py get SECTION KEY | autologin-files   [--root DIR]", file=sys.stderr)
            return 2
        root = argv[i + 1]
        argv = argv[:i] + argv[i + 2:]
    if len(argv) == 3 and argv[0] == "get":
        print(effective(root).get((argv[1], argv[2]), ""))
        return 0
    if argv == ["autologin-files"]:
        for p in autologin_files(root):
            print(p)
        return 0
    print("usage: sddm_conf.py get SECTION KEY | autologin-files   [--root DIR]", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
