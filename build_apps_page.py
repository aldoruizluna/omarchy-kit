#!/usr/bin/env python3
"""Write apps.html (copy-only mode). For one-click installs use ./apps-helper."""
from appslib import render, HERE
(HERE / "apps.html").write_text(render(None)); print("wrote apps.html")
