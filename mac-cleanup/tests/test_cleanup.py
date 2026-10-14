import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


class CleanNodeTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="mac-cleanup-test-")
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name).resolve()
        self.home = self.base / "home"
        self.root = self.home / "Code"
        self.root.mkdir(parents=True)
        self.bin = self.base / "bin"
        self.bin.mkdir()
        self.env = dict(os.environ, HOME=str(self.home), PATH=f"{self.bin}:{os.environ['PATH']}")
        self.env.pop("GIT_DIR", None)
        self.env.pop("GIT_WORK_TREE", None)
        self.stub("pnpm", "exit 0\n")

    def command(self, *args):
        return subprocess.run(args, env=self.env, text=True, capture_output=True)

    def clean(self, *args):
        return self.command(sys.executable, str(SCRIPTS / "clean-node"), *map(str, args))

    def target(self, relative="project/node_modules"):
        path = self.root / relative
        path.mkdir(parents=True)
        (path / "fixture.txt").write_text("fixture")
        return path

    def stub(self, name, content):
        path = self.bin / name
        path.write_text("#!/bin/sh\n" + content)
        path.chmod(0o755)

    def init_repo(self, root, file):
        self.assertEqual(self.command("git", "init", "-q", str(root)).returncode, 0)
        self.assertEqual(self.command("git", "-C", str(root), "add", "-f", str(file)).returncode, 0)

    def plan(self, *args):
        destination = self.base / "plan.json"
        result = self.clean("--plan", destination, *args, self.root)
        self.assertEqual(result.returncode, 0, result.stderr)
        return destination

    def test_lists_untracked_targets_without_deleting(self):
        target = self.target()
        result = self.clean(self.root)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(str(target), result.stdout)
        self.assertTrue(target.exists())

    def test_skips_tracked_content(self):
        target = self.target()
        self.init_repo(self.root, target / "fixture.txt")
        result = self.clean(self.root)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Nothing to clean", result.stdout)

    def test_skips_nested_repositories_and_git_files(self):
        target = self.target()
        nested = target / "local-package"
        nested.mkdir()
        (nested / "source.txt").write_text("source")
        self.init_repo(nested, nested / "source.txt")
        worktree = self.target("other/.next")
        (worktree / ".git").write_text("gitdir: /some/worktree")
        result = self.clean(self.root)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Nothing to clean", result.stdout)

    def test_git_failure_aborts_scan(self):
        target = self.target()
        self.init_repo(self.root, target / "fixture.txt")
        self.stub("git", "echo 'inspection failed' >&2\nexit 128\n")
        result = self.clean(self.root)
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("Nothing to clean", result.stdout)

    def test_rejects_home_ancestors_and_tool_roots_including_aliases(self):
        global_root = self.home / ".bun/install/global"
        global_root.mkdir(parents=True)
        alias = self.root / "alias"
        alias.symlink_to(global_root, target_is_directory=True)
        for root in (self.home, self.base, Path("/"), global_root, alias):
            with self.subTest(root=root):
                result = self.clean(root)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("protected scan root", result.stderr)

    def test_does_not_follow_symlinks(self):
        outside = self.base / "outside/node_modules"
        outside.mkdir(parents=True)
        (self.root / "linked-project").symlink_to(outside.parent, target_is_directory=True)
        result = self.clean(self.root)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Nothing to clean", result.stdout)

    def test_rejects_invalid_age_and_extra_roots(self):
        for args in (("--days", "oops"), ("--days", "-1"), ("--days",), (self.root, self.root)):
            with self.subTest(args=args):
                result = self.clean(*args)
                self.assertNotEqual(result.returncode, 0)
                self.assertNotIn("Nothing to clean", result.stdout)

    def test_age_filter_is_only_target_directory_mtime(self):
        old = self.target("old/node_modules")
        recent = self.target("recent/node_modules")
        timestamp = time.time() - 60 * 86400
        os.utime(old, (timestamp, timestamp))
        (old / "fixture.txt").write_text("fresh edit does not change parent mtime")
        result = self.clean("--days", "30", self.root)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(str(old), result.stdout)
        self.assertNotIn(str(recent), result.stdout)

    def test_measurement_failure_aborts(self):
        self.target()
        self.stub("du", "echo 'measurement failed' >&2\nexit 1\n")
        result = self.clean(self.root)
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("Dry run", result.stdout)

    def test_delete_requires_a_saved_plan(self):
        target = self.target()
        result = self.clean("--delete", self.root)
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(target.exists())

    def test_deletes_only_saved_targets_and_honors_exclusions(self):
        approved = self.target("approved/node_modules")
        excluded = self.target("active/node_modules")
        also_excluded = self.target("also-active/.next")
        plan = self.plan("--exclude", "active", "--exclude", also_excluded.parent)
        new = self.target("added-after-preview/.next")
        preview = self.clean("--from-plan", plan)
        self.assertEqual(preview.returncode, 0, preview.stderr)
        self.assertTrue(approved.exists())
        result = self.clean("--delete", "--from-plan", plan)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(approved.exists())
        for kept in (excluded, also_excluded, new):
            self.assertTrue(kept.exists())

    def test_plan_round_trips_unusual_filenames(self):
        target = self.target('spaces "quotes"\ttab\nnewline/node_modules')
        plan = self.plan()
        result = self.clean("--delete", "--from-plan", plan)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(target.exists())

    def test_changed_target_aborts_before_any_deletion(self):
        first = self.target("a/node_modules")
        changed = self.target("z/.next")
        plan = self.plan()
        changed.rename(changed.with_name("old-next"))
        changed.mkdir()
        result = self.clean("--delete", "--from-plan", plan)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("changed since preview", result.stderr)
        self.assertTrue(first.exists())
        self.assertTrue(changed.exists())

    def test_missing_target_aborts_before_any_deletion(self):
        first = self.target("a/node_modules")
        missing = self.target("z/.next")
        plan = self.plan()
        missing.rename(missing.with_name("moved-next"))
        result = self.clean("--delete", "--from-plan", plan)
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(first.exists())

    def test_symlink_replacement_is_rejected(self):
        target = self.target()
        plan = self.plan()
        moved = target.with_name("moved")
        target.rename(moved)
        target.symlink_to(moved, target_is_directory=True)
        result = self.clean("--delete", "--from-plan", plan)
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue((moved / "fixture.txt").exists())

    def test_newly_tracked_content_is_rejected(self):
        target = self.target()
        self.command("git", "init", "-q", str(self.root))
        plan = self.plan()
        self.command("git", "-C", str(self.root), "add", "-f", str(target / "fixture.txt"))
        result = self.clean("--delete", "--from-plan", plan)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Git content", result.stderr)
        self.assertTrue(target.exists())

    def test_refuses_overwriting_a_plan(self):
        self.target()
        plan = self.plan()
        original = plan.read_bytes()
        self.target("new/.next")
        result = self.clean("--plan", plan, self.root)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(plan.read_bytes(), original)

    def test_rejects_plan_inside_deletion_target(self):
        target = self.target()
        result = self.clean("--plan", target / "plan.json", self.root)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((target / "plan.json").exists())

    def test_rejects_malformed_and_out_of_scope_plans(self):
        target = self.target()
        plan = self.plan()
        original = json.loads(plan.read_text())
        outside = json.loads(plan.read_text())
        outside["targets"][0]["path"] = str(self.base / "node_modules")
        for contents in ("{", "[]", json.dumps(outside), json.dumps({**original, "targets": [None]})):
            with self.subTest(contents=contents):
                plan.write_text(contents)
                result = self.clean("--delete", "--from-plan", plan)
                self.assertNotEqual(result.returncode, 0)
                self.assertTrue(target.exists())

    def test_plan_cannot_be_combined_with_scan_options(self):
        target = self.target()
        plan = self.plan()
        for args in (("--days", "0"), (self.root,), ("--exclude", "project"), ("--plan", "other.json")):
            with self.subTest(args=args):
                result = self.clean("--delete", "--from-plan", plan, *args)
                self.assertNotEqual(result.returncode, 0)
                self.assertTrue(target.exists())


if __name__ == "__main__":
    unittest.main()
