"""Structure of the learning path (portal_lessons.py): no browser, no running service.

Every level, lesson and step must exist in both languages, use a check the Learn page implements, carry an answer pattern that compiles
when it asks the learner to type something, and point at a menu route that exists. Run: python3 -B -m unittest discover -s test
"""
import json, pathlib, re, sys, unittest

sys.dont_write_bytecode = True
KIT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KIT))
import portal_lessons as PL  # noqa: E402

LEARN = (KIT / "learn.template.html").read_text()
CHECKS = set(re.findall(r"^\s{2}(\w+): \(s", LEARN, re.M)) | {"manual", "typed"}
MENU_FILE = KIT / "data" / "menu_ids.json"      # built from the live Omarchy menu; git-ignored, so the menu test skips without it
STEPS = [(lv["id"], ls["id"], i, st) for lv in PL.LEVELS for ls in lv["lessons"] for i, st in enumerate(ls["steps"], 1)]


class LearningPath(unittest.TestCase):
    def test_the_page_knows_the_check_types(self):
        self.assertGreater(len(CHECKS), 10, CHECKS)

    def test_ids_are_unique(self):
        lessons = [ls["id"] for lv in PL.LEVELS for ls in lv["lessons"]]
        self.assertEqual(len(lessons), len(set(lessons)))
        levels = [lv["id"] for lv in PL.LEVELS]
        self.assertEqual(len(levels), len(set(levels)))

    def test_every_level_lesson_and_step_is_bilingual(self):
        for lv in PL.LEVELS:
            for key in ("en", "es"):
                self.assertTrue(lv[key].strip(), f"level {lv['id']} lacks {key}")
            for ls in lv["lessons"]:
                for key in ("en", "es"):
                    self.assertTrue(ls[key].strip(), f"lesson {ls['id']} lacks {key}")
                    self.assertTrue(ls["why"][key].strip(), f"lesson {ls['id']} lacks why.{key}")
                self.assertTrue(ls["steps"], f"lesson {ls['id']} has no steps")
        for lid, sid, i, st in STEPS:
            for key in ("en", "es"):
                self.assertTrue(st[key].strip(), f"{lid}/{sid} step {i} lacks {key}")
            self.assertNotEqual(st["en"].strip(), st["es"].strip(), f"{lid}/{sid} step {i}: Spanish equals English")

    def test_spanish_keeps_the_english_commands(self):
        """A command or path named in the English text must still be named in the Spanish one."""
        for lid, sid, i, st in STEPS:
            for token in re.findall(r"(?<![\w/.-])((?:sleep|power|themes)/[\w-]+|--remove|--check|--list)", st["en"]):
                self.assertIn(token, st["es"], f"{lid}/{sid} step {i}: {token!r} missing from the Spanish text")

    def test_checks_are_implemented_by_the_page(self):
        for lid, sid, i, st in STEPS:
            self.assertIn(st["check"], CHECKS, f"{lid}/{sid} step {i}: unknown check {st['check']!r}")

    def test_typed_steps_have_a_working_box_and_pattern(self):
        typed = [x for x in STEPS if x[3]["check"] == "typed"]
        self.assertGreater(len(typed), 5)
        for lid, sid, i, st in typed:
            self.assertTrue(st.get("box"), f"{lid}/{sid} step {i}: typed step without an input box")
            self.assertTrue(st.get("re"), f"{lid}/{sid} step {i}: typed step without a pattern")
            if "\\p{" not in st["re"]:   # JavaScript's \p{...} has no Python equivalent; the browser suite covers those
                re.compile(st["re"])

    def test_answers_the_lessons_expect_are_accepted(self):
        """The patterns of the Level 6 'read the output' steps accept what the command prints, and reject an empty box."""
        by = {(lid, sid, i): st for lid, sid, i, st in STEPS}
        self.assertRegex("s2idle", by[("l6", "lid", 2)]["re"])
        self.assertRegex("[s2idle]", by[("l6", "lid", 2)]["re"])
        self.assertNotRegex("deep", by[("l6", "lid", 2)]["re"])
        self.assertRegex("yes", by[("l6", "hibernate", 1)]["re"])
        for word in ("lock", "hibernate"):
            self.assertRegex(word, by[("l6", "hibernate", 2)]["re"])
        for st in by.values():
            if st["check"] == "typed":
                self.assertIsNone(re.search(st["re"], "") if st["re"].startswith("^") else None, "a typed step must not pass with an empty box")

    def test_menu_steps_point_at_real_routes(self):
        if not MENU_FILE.exists():
            self.skipTest("data/menu_ids.json is built from the live Omarchy menu (python3 build_portal.py)")
        ids = set(json.loads(MENU_FILE.read_text())) | {"root"}
        for lid, sid, i, st in STEPS:
            if st.get("menu"):
                self.assertTrue(st["menu"] in ids, f"{lid}/{sid} step {i}: unknown menu route {st['menu']!r}")

    def test_commands_that_change_the_machine_are_not_run_by_the_page(self):
        """Steps show commands to copy; none may start a sudo, mkfs, dd or rm -rf / command. Privileged installers are only named in the text."""
        for lid, sid, i, st in STEPS:
            cmd = st.get("cmd", "")
            if re.search(r"(^|[;&|]\s*)(sudo\b|rm -rf /|mkfs\b|dd if=)", cmd):
                self.fail(f"{lid}/{sid} step {i}: a step must not hand out a privileged or destructive command: {cmd!r}")

    def test_the_path_is_the_size_the_docs_claim(self):
        lessons = sum(len(lv["lessons"]) for lv in PL.LEVELS)
        self.assertEqual((len(PL.LEVELS), lessons, len(STEPS)), (6, 34, 97))


if __name__ == "__main__":
    unittest.main()
