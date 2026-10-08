"""The documentation stays connected and true. Standard library only; reads files, runs nothing on the machine.

Links and anchors resolve, every document is in the map and in llms.txt, llms-full.txt is current, every document opens with a TL;DR and closes
with a Related line, the counts the README states match the code, and, when KIT_PRIVATE_NAMES lists them, the public repository names no private project.

  python3 -B -m unittest test.test_docs        # or: test/run-all --fast
"""
import os, re, subprocess, sys, unittest
from pathlib import Path

sys.dont_write_bytecode = True
KIT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KIT))
RAW = "https://raw.githubusercontent.com/aldoruizluna/omarchy-kit/main/"


def tracked(*patterns):
    r = subprocess.run(["git", "-C", str(KIT), "ls-files", "-co", "--exclude-standard", *patterns], capture_output=True, text=True)
    if r.returncode:
        return sorted(str(p.relative_to(KIT)) for pat in patterns for p in KIT.rglob(pat))
    return sorted(r.stdout.split())


MD = tracked("*.md")
FENCE = re.compile(r"^(```|~~~)")
LINK = re.compile(r"(?<!\!)\[([^\]]*)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")


def strip_code(text):
    """Text without fenced blocks and inline code, so links shown as examples are not checked."""
    out, fenced = [], False
    for line in text.splitlines():
        if FENCE.match(line.strip()):
            fenced = not fenced
            continue
        if not fenced:
            out.append(re.sub(r"`[^`]*`", "", line))
    return "\n".join(out)


def slug(heading):
    h = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", heading)          # links keep their text
    h = re.sub(r"[`*~]", "", h).strip().lower()
    h = re.sub(r"[^\w\- ]", "", h, flags=re.UNICODE)
    return h.replace(" ", "-")


def anchors(path):
    seen, out, fenced = {}, set(), False
    for line in Path(path).read_text().splitlines():
        if FENCE.match(line.strip()):
            fenced = not fenced
        if fenced:
            continue
        m = HEADING.match(line)
        if m:
            s = slug(m[2])
            n = seen.get(s, 0)
            seen[s] = n + 1
            out.add(s if n == 0 else f"{s}-{n}")
    return out


class Links(unittest.TestCase):
    def test_every_relative_link_and_anchor_resolves(self):
        bad = []
        for rel in MD:
            src = KIT / rel
            for text, target in LINK.findall(strip_code(src.read_text())):
                if re.match(r"^(https?:|mailto:|data:)", target):
                    continue
                path, _, frag = target.partition("#")
                dest = src if not path else (src.parent / path).resolve()
                if not dest.exists():
                    bad.append(f"{rel}: [{text}]({target}) -> missing file")
                elif frag and dest.suffix == ".md" and frag not in anchors(dest):
                    bad.append(f"{rel}: [{text}]({target}) -> no heading #{frag} in {dest.name}")
        self.assertEqual(bad, [], "\n" + "\n".join(bad))

    def test_the_slug_rule_matches_github_for_the_headings_we_link_to(self):
        self.assertEqual(slug("One password: the no-lock shim"), "one-password-the-no-lock-shim")
        self.assertEqual(slug("What the firmware says (read from this Mac's DSDT)"), "what-the-firmware-says-read-from-this-macs-dsdt")
        self.assertEqual(slug("Add a `lesson` or a step"), "add-a-lesson-or-a-step")


class Coverage(unittest.TestCase):
    def docs(self):
        return [p for p in MD if p.startswith("docs/") and p != "docs/INDEX.md"]

    def folder_readmes(self):
        return [p for p in MD if p.count("/") == 1 and p.endswith("/README.md")]

    def test_every_document_is_in_the_map(self):
        index = (KIT / "docs/INDEX.md").read_text()
        missing = [p for p in self.docs() if Path(p).name not in index]
        self.assertEqual(missing, [], "docs/INDEX.md does not list: " + ", ".join(missing))
        gaps = [p for p in self.folder_readmes() if p.split("/")[0] + "/README" not in index and p.split("/")[0] + "/README.md" not in index]
        self.assertEqual(gaps, [], "docs/INDEX.md does not link the folder READMEs of: " + ", ".join(gaps))

    def test_every_document_is_in_llms_txt(self):
        txt = (KIT / "llms.txt").read_text()
        listed = {u[len(RAW):] for _, u in re.findall(r"^- \[([^\]]+)\]\(([^)]+)\)", txt, re.M) if u.startswith(RAW)}
        expected = set(self.docs() + self.folder_readmes() + ["README.md", "AGENTS.md", "docs/INDEX.md"] + [p for p in MD if p.startswith("themes/") and p.endswith("THEME.md")])
        self.assertEqual(sorted(expected - listed), [], "llms.txt lacks these documents")
        self.assertEqual(sorted(listed - set(MD)), [], "llms.txt links files that do not exist")

    def test_llms_txt_follows_the_convention(self):
        lines = (KIT / "llms.txt").read_text().splitlines()
        self.assertTrue(lines[0].startswith("# "), "the first line is the title")
        self.assertTrue(any(l.startswith("> ") for l in lines[:6]), "a blockquote summary follows the title")
        self.assertGreaterEqual(sum(1 for l in lines if l.startswith("## ")), 4)
        self.assertTrue(all(re.match(r"^- \[[^\]]+\]\([^)]+\)(: .+)?$", l) for l in lines if l.startswith("- [")), "link lines are '- [name](url): note'")

    def test_llms_full_is_current(self):
        r = subprocess.run([sys.executable, "-B", str(KIT / "scripts/build-llms"), "--check"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr or "run scripts/build-llms")

    def test_claude_code_imports_agents_md(self):
        self.assertIn("@AGENTS.md", (KIT / "CLAUDE.md").read_text())
        self.assertGreater(len((KIT / "AGENTS.md").read_text().splitlines()), 30)


class Shape(unittest.TestCase):
    def test_every_document_opens_with_a_tldr_and_closes_with_related(self):
        bad = []
        for rel in MD:
            if not (rel.startswith("docs/") or (rel.count("/") == 1 and rel.endswith("/README.md"))):
                continue
            lines = (KIT / rel).read_text().strip().splitlines()
            if not any(l.startswith("> **TL;DR") for l in lines[:14]):
                bad.append(f"{rel}: no '> **TL;DR' line near the top")
            if not any(l.startswith("Related:") for l in lines[-6:]):
                bad.append(f"{rel}: no 'Related:' line at the end")
        self.assertEqual(bad, [], "\n" + "\n".join(bad))

    def test_the_folder_readmes_say_how_they_are_checked_or_undone(self):
        for rel in MD:
            if rel.count("/") == 1 and rel.endswith("/README.md") and not rel.startswith(("test/", "docs/")):
                text = (KIT / rel).read_text().lower()
                self.assertTrue("check" in text or "test" in text or "setup log" in text, rel)


class Truth(unittest.TestCase):
    def test_the_counts_the_readme_states_match_the_code(self):
        import portal_lessons, portal_content
        readme = (KIT / "README.md").read_text()
        lessons = sum(len(lv["lessons"]) for lv in portal_lessons.LEVELS)
        habits = sum(len(rows) for _, _, rows in portal_content.MAC)
        fixed_badges = len(re.findall(r'^\s*\["[a-z0-9]+", "[^\x00-\x7f]', (KIT / "kit.js").read_text(), re.M))
        badges = fixed_badges + len(portal_lessons.LEVELS)
        m = re.search(r"(\d+) hands-on lessons in (\w+) levels", readme)
        self.assertTrue(m, "the README should say 'N hands-on lessons in six levels'")
        self.assertEqual(int(m[1]), lessons)
        self.assertEqual(m[2], {5: "five", 6: "six", 7: "seven", 8: "eight"}[len(portal_lessons.LEVELS)])
        self.assertIn(f"{habits} Mac habits", readme)
        self.assertIn(f"{badges} badges", readme)

    def test_the_public_repository_names_no_private_project(self):
        # The names themselves are not written into this public repository: a maintainer supplies them, as for verify-store-page.mjs.
        names = [n.strip().lower() for n in os.environ.get("KIT_PRIVATE_NAMES", "").split(",") if n.strip()]
        if not names:
            self.skipTest("set KIT_PRIVATE_NAMES=name1,name2 to check that no document names a private project")
        hits = []
        for rel in MD + ["llms.txt", "llms-full.txt"]:
            low = (KIT / rel).read_text().lower()
            hits += [f"{rel}: {n}" for n in names if n in low]
        self.assertEqual(hits, [])

    def test_no_personal_paths_in_the_documents(self):
        hits = []
        for rel in MD + ["llms.txt"]:
            for n, line in enumerate((KIT / rel).read_text().splitlines(), 1):
                if re.search(r"/home/(?!yourname|username|you\b)[a-z]+", line):
                    hits.append(f"{rel}:{n}")
        self.assertEqual(hits, [])


if __name__ == "__main__":
    unittest.main()
