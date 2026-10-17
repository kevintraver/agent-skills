import contextlib
import importlib.util
import io
from pathlib import Path
import unittest
from unittest import mock
import urllib.parse


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "hn_thread.py"
spec = importlib.util.spec_from_file_location("hn_thread", SCRIPT)
hn = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hn)


class ExtractIdTests(unittest.TestCase):
    def test_ids_and_item_urls(self):
        for target in [
            "123",
            "https://news.ycombinator.com/item?id=123",
            "https://news.ycombinator.com/item?foo=bar&id=123#reply",
            "https://hn.algolia.com/items/123",
            "https://hn.algolia.com/api/v1/items/123",
        ]:
            with self.subTest(target=target):
                self.assertEqual(hn.extract_id(target), 123)

    def test_titles_are_not_ids(self):
        for target in ["1984 and beyond", "Understanding id=999 in URLs", "C++ & C# — 日本語?"]:
            with self.subTest(target=target):
                self.assertIsNone(hn.extract_id(target))

    def test_non_item_urls_are_rejected(self):
        for target in ["https://example.com/?id=123", "https://news.ycombinator.com/item?id=123abc"]:
            with self.subTest(target=target), self.assertRaises(SystemExit) as cm:
                hn.extract_id(target)
            self.assertIn("Use an HN item URL", str(cm.exception.code))


class SearchTitleTests(unittest.TestCase):
    def search(self, title, hits):
        def fake_get_json(url):
            params = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
            self.assertEqual(params["query"], [title])
            self.assertEqual(params["tags"], ["story"])
            self.assertEqual(params["restrictSearchableAttributes"], ["title"])
            return {"hits": hits}

        stderr = io.StringIO()
        with mock.patch.object(hn, "get_json", fake_get_json), contextlib.redirect_stderr(stderr):
            return hn.search_title(title), stderr.getvalue()

    def test_exact_title_beats_higher_ranked_partial_match(self):
        found, stderr = self.search(
            "Ask HN: Startup advice",
            [
                {"objectID": "99", "title": "Ask HN: Startup advice for founders"},
                {"objectID": "123", "title": "ASK HN:  Startup advice"},
            ],
        )
        self.assertEqual(found, 123)
        self.assertIn("https://news.ycombinator.com/item?id=123", stderr)

    def test_fragment_uses_first_ranked_hit(self):
        found, _ = self.search(
            "Startup advice",
            [
                {"objectID": "123", "title": "Ask HN: Startup advice"},
                {"objectID": "99", "title": "Startup advice for founders"},
            ],
        )
        self.assertEqual(found, 123)

    def test_invalid_hits_are_skipped(self):
        found, _ = self.search(
            "Story",
            [
                {"objectID": "99", "title": None},
                {"objectID": "oops", "title": "Story"},
                {"objectID": "88", "title": " "},
                {"objectID": "123", "title": "Story"},
            ],
        )
        self.assertEqual(found, 123)

    def test_no_hits_exits_with_message(self):
        with self.assertRaises(SystemExit) as cm:
            self.search("Missing story", [])
        self.assertIn('No HN stories found for title: "Missing story"', str(cm.exception.code))


def comment(id, *kids, **extra):
    return {"id": id, "by": f"user{id}", "text": f"Comment {id}", "kids": [k[0]["id"] for k in kids], **extra}, kids


def tree_of(*roots):
    tree = {}

    def add(node):
        it, kids = node
        tree[it["id"]] = it
        for k in kids:
            add(k)

    for r in roots:
        add(r)
    return tree, [r[0]["id"] for r in roots]


class FlattenTests(unittest.TestCase):
    def test_gone_comments_keep_live_replies_under_a_placeholder(self):
        tree, roots = tree_of(
            comment(1, comment(2, deleted=True), comment(3, comment(4), dead=True)),
            comment(5, comment(6, deleted=True)),
        )
        lines, live = hn.flatten(tree, roots, 0)
        self.assertEqual(
            lines,
            ["[user1 #1] Comment 1", "  [flagged #3]", "    [user4 #4] Comment 4", "[user5 #5] Comment 5"],
        )
        self.assertEqual(live, 3)

    def test_clean_marks_paragraphs_links_and_code(self):
        text = '<p>See <a href="https://x.dev/a">x.dev</a> &amp; this:<pre><code>a = 1\nb = 2\n</code></pre>'
        self.assertEqual(hn.clean(text), "¶ See https://x.dev/a & this: `a = 1 ⏎ b = 2`")


if __name__ == "__main__":
    unittest.main()
