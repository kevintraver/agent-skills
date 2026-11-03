"""Each fixture breaks one rule; the clean skill must pass. Run: python3 -m unittest tools/test_skilllint.py"""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import skilllint  # noqa: E402

GOOD_DESC = "Formats files for sharing. Use when the user asks to share a file."


def skill(root, folder, frontmatter, body="", filename="SKILL.md", extra=None):
    d = Path(root) / folder
    d.mkdir()
    (d / filename).write_text(f"---\n{frontmatter}\n---\n{body}")
    for name, text in (extra or {}).items():
        (d / name).parent.mkdir(parents=True, exist_ok=True)
        (d / name).write_text(text)
    return d


def errors(d):
    return {f["rule"] for f in skilllint.lint(d) if f["severity"] == "ERROR"}


class Rules(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def test_clean_skill_passes(self):
        d = skill(self.root, "good", f"name: good\ndescription: {GOOD_DESC}",
                  "Run `scripts/run.sh` and read [the guide](references/guide.md).",
                  extra={"scripts/run.sh": "", "references/guide.md": ""})
        self.assertEqual(errors(d), set())

    def test_skill_md_must_be_exact(self):
        d = skill(self.root, "lower", f"name: lower\ndescription: {GOOD_DESC}", filename="skill.md")
        self.assertIn("E01-skill-md-name", errors(d))

    def test_missing_frontmatter(self):
        d = Path(self.root) / "nofm"
        d.mkdir()
        (d / "SKILL.md").write_text("name: nofm\n")
        self.assertIn("E02-frontmatter", errors(d))

    def test_name_rules(self):
        self.assertIn("E03-name", errors(skill(self.root, "Bad_Name", f"name: Bad_Name\ndescription: {GOOD_DESC}")))
        self.assertIn("E04-name-matches-folder", errors(skill(self.root, "folder", f"name: other\ndescription: {GOOD_DESC}")))
        self.assertIn("E06-reserved-word", errors(skill(self.root, "claude-tool", f"name: claude-tool\ndescription: {GOOD_DESC}")))

    def test_folder_kebab_case(self):
        self.assertIn("E05-folder-kebab", errors(skill(self.root, "My_Skill", f"name: my-skill\ndescription: {GOOD_DESC}")))

    def test_description_rules(self):
        self.assertIn("E07-description", errors(skill(self.root, "long", "name: long\ndescription: " + "word " * 300 + "Use when asked.")))
        self.assertIn("E08-angle-brackets", errors(skill(self.root, "angle", "name: angle\ndescription: Formats <b> files. Use when asked.")))
        self.assertIn("E09-what-and-when", errors(skill(self.root, "nowhen", "name: nowhen\ndescription: Formats files and prints them nicely.")))
        self.assertIn("E09-what-and-when", errors(skill(self.root, "nowhat", "name: nowhat\ndescription: Use when the user says foo.")))

    def test_compatibility_length(self):
        d = skill(self.root, "compat", f"name: compat\ndescription: {GOOD_DESC}\ncompatibility: {'x' * 501}")
        self.assertIn("E10-compatibility", errors(d))

    def test_no_readme(self):
        d = skill(self.root, "readme", f"name: readme\ndescription: {GOOD_DESC}", extra={"README.md": "hi"})
        self.assertIn("E11-no-readme", errors(d))

    def test_body_word_limit(self):
        d = skill(self.root, "big", f"name: big\ndescription: {GOOD_DESC}", "word " * 5000)
        self.assertIn("E12-body-words", errors(d))

    def test_missing_referenced_files(self):
        d = skill(self.root, "refs", f"name: refs\ndescription: {GOOD_DESC}",
                  "See [ref](references/nope.md), run `scripts/missing.sh` and <skill>/scripts/gone.py.\n"
                  "Placeholders like [view](permalink) are not files.")
        msg = " ".join(f["message"] for f in skilllint.lint(d) if f["rule"] == "E13-missing-file")
        for p in ("references/nope.md", "scripts/missing.sh", "scripts/gone.py"):
            self.assertIn(p, msg)
        self.assertNotIn("permalink", msg)

    def test_metadata_and_skills_ref_fields(self):
        d = skill(self.root, "meta", f"name: meta\ndescription: {GOOD_DESC}\nmetadata:\n  tags: [a, b]\nextra: 1")
        self.assertTrue({"E15-metadata", "SR-unexpected-fields", "SR-strictyaml"} <= errors(d))


if __name__ == "__main__":
    unittest.main()
