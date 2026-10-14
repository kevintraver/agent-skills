import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


class ScriptTests(unittest.TestCase):
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


class CleanNodeTests(ScriptTests):
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

    def test_empty_scan_saves_no_plan(self):
        destination = self.base / "plan.json"
        result = self.clean("--plan", destination, self.root)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Nothing to clean", result.stdout)
        self.assertNotIn("total", result.stdout)
        self.assertFalse(destination.exists())

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

    def test_rejects_hidden_home_folders_and_their_aliases(self):
        installed = self.home / ".local/share/opencode/bin/node_modules"
        installed.mkdir(parents=True)
        alias = self.root / "tools"
        alias.symlink_to(installed.parent, target_is_directory=True)
        for root in (self.home / ".local", self.home / ".local/share", installed.parent, alias):
            with self.subTest(root=root):
                result = self.clean(root)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("protected scan root", result.stderr)
                self.assertTrue(installed.exists())

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

    def test_excluding_nested_content_preserves_its_cleanup_parent(self):
        target = self.target()
        nested = target / "local-package"
        nested.mkdir()
        approved = self.target("other/.next")
        plan = self.plan("--exclude", nested)
        result = self.clean("--delete", "--from-plan", plan)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(nested.exists())
        self.assertFalse(approved.exists())

    def test_protected_tool_alias_preserves_its_cleanup_parent(self):
        target = self.target()
        tool = target / "installed-tool"
        tool.mkdir()
        (self.home / ".bun").symlink_to(tool, target_is_directory=True)
        result = self.clean(self.root)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn(str(target), result.stdout)

    def test_new_tool_alias_aborts_saved_deletion(self):
        target = self.target()
        tool = target / "installed-tool"
        tool.mkdir()
        plan = self.plan()
        (self.home / ".bun").symlink_to(tool, target_is_directory=True)
        result = self.clean("--delete", "--from-plan", plan)
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(tool.exists())

    def test_unreadable_nested_content_aborts_scan(self):
        target = self.target()
        unreadable = target / "unreadable"
        unreadable.mkdir()
        unreadable.chmod(0)
        self.addCleanup(unreadable.chmod, 0o755)
        result = self.clean(self.root)
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("Nothing to clean", result.stdout)

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
        for args in (("--days", "0"), (self.root,), ("--exclude", "project"), ("--plan", "other.json"), ("--prune-store",)):
            with self.subTest(args=args):
                result = self.clean("--delete", "--from-plan", plan, *args)
                self.assertNotEqual(result.returncode, 0)
                self.assertTrue(target.exists())

    def pnpm_store(self, prune_status=0):
        store = self.home / "store"
        store.mkdir()
        marker = self.base / "pnpm-pruned"
        self.env["TEST_STORE"] = str(store)
        self.env["TEST_PRUNE_MARKER"] = str(marker)
        self.stub("pnpm", 'case "$*" in\n'
                  '"store path") printf "%s\\n" "$TEST_STORE" ;;\n'
                  f'"store prune") touch "$TEST_PRUNE_MARKER"; exit {prune_status} ;;\n'
                  '*) exit 2 ;;\nesac\n')
        return store, marker

    def test_ordinary_cleanup_does_not_invoke_pnpm(self):
        target = self.target()
        marker = self.base / "unexpected-pnpm-call"
        self.env["TEST_PRUNE_MARKER"] = str(marker)
        self.stub("pnpm", 'touch "$TEST_PRUNE_MARKER"\nexit 127\n')
        plan = self.plan()
        result = self.clean("--delete", "--from-plan", plan)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(target.exists())
        self.assertFalse(marker.exists())

    def test_pruning_requires_previewed_store_and_is_separate(self):
        self.target()
        store, marker = self.pnpm_store()
        plan = self.plan("--prune-store")
        preview = self.clean("--from-plan", plan)
        self.assertEqual(preview.returncode, 0, preview.stderr)
        self.assertIn(str(store), preview.stdout)
        self.assertIn("shared store", preview.stdout)
        self.assertFalse(marker.exists())
        result = self.clean("--delete", "--from-plan", plan)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(marker.exists())
        self.assertIn("Deleted 1 folders.", result.stdout)
        self.assertIn("pnpm store pruning completed.", result.stdout)

    def test_changed_store_aborts_before_deletion(self):
        target = self.target()
        store, marker = self.pnpm_store()
        plan = self.plan("--prune-store")
        other = store.with_name("other-store")
        other.mkdir()
        self.env["TEST_STORE"] = str(other)
        result = self.clean("--delete", "--from-plan", plan)
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(target.exists())
        self.assertFalse(marker.exists())

    def test_prune_failure_reports_completed_folder_deletion(self):
        target = self.target()
        self.pnpm_store(prune_status=7)
        plan = self.plan("--prune-store")
        result = self.clean("--delete", "--from-plan", plan)
        self.assertEqual(result.returncode, 7)
        self.assertFalse(target.exists())
        self.assertIn("Deleted 1 folders.", result.stdout)
        self.assertIn("pruning failed", result.stderr)

    def test_opt_in_prune_works_with_no_project_targets(self):
        _, marker = self.pnpm_store()
        plan = self.plan("--prune-store")
        result = self.clean("--delete", "--from-plan", plan)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(marker.exists())


class InspectionTests(ScriptTests):
    def taps(self):
        return self.command("bash", str(SCRIPTS / "unused-taps.sh"))

    def test_homebrew_inventory_failure_does_not_label_taps_unused(self):
        self.stub("brew", 'case "$1" in\ninfo) echo "lookup failed" >&2; exit 1 ;;\ntap) echo example/tools ;;\nesac\n')
        result = self.taps()
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("UNUSED", result.stdout)

    def test_empty_or_invalid_homebrew_inventory_aborts(self):
        for inventory in ("", "not-json", "{}"):
            with self.subTest(inventory=inventory):
                self.env["TEST_INVENTORY"] = inventory
                self.stub("brew", 'case "$1" in\ninfo) printf "%s" "$TEST_INVENTORY" ;;\ntap) echo example/tools ;;\nesac\n')
                result = self.taps()
                self.assertNotEqual(result.returncode, 0)
                self.assertNotIn("UNUSED", result.stdout)

    def test_homebrew_inventory_distinguishes_formulae_casks_and_unused(self):
        self.env["TEST_INVENTORY"] = json.dumps({
            "formulae": [{"tap": "example/formulae", "name": "tool"}],
            "casks": [{"tap": "example/casks", "token": "app"}],
        })
        self.stub("brew", 'case "$1" in\ninfo) printf "%s" "$TEST_INVENTORY" ;;\ntap) printf "%s\\n" homebrew/core example/formulae example/casks example/empty ;;\nesac\n')
        result = self.taps()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("homebrew/core", result.stdout)
        self.assertRegex(result.stdout, r"example/formulae\s+tool")
        self.assertRegex(result.stdout, r"example/casks\s+app")
        self.assertRegex(result.stdout, r"example/empty\s+UNUSED")

    def test_homebrew_tap_listing_failure_aborts(self):
        self.stub("brew", 'case "$1" in\ninfo) echo \'{"formulae":[],"casks":[]}\' ;;\ntap) exit 1 ;;\nesac\n')
        self.assertNotEqual(self.taps().returncode, 0)

    def overview(self, *args):
        return self.command("bash", str(SCRIPTS / "overview.sh"), *args)

    def overview_stubs(self, du_exit="exit 0"):
        self.stub("df", '[ "$1" = "-k" ] || exit 2\necho "filesystem blocks used available capacity mounted"\necho "disk 1000 100 900 10% /System/Volumes/Data"\n')
        # du -k output (KiB<TAB>path) for a small home folder; logs each call.
        self.du_log = self.base / "du.log"
        self.stub("du", f'echo "$@" >> "{self.du_log}"\n'
                  'printf "%s\\t%s\\n" 4096 "$HOME" 3072 "$HOME/Library" 2048 "$HOME/Library/Caches" \\\n'
                  '  1536 "$HOME/Library/Caches/big-cache" 512 "$HOME/Code" 100 "$HOME/.Trash"\n'
                  f"{du_exit}\n")
        self.stub("docker", "exit 1\n")

    def test_overview_measures_home_once_and_lists_children(self):
        self.overview_stubs()
        result = self.overview()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(self.du_log.read_text().splitlines()), 1)
        subfolders = result.stdout.split("== ~/Library subfolders")[1].split("==")[0]
        self.assertIn("big-cache", subfolders)
        self.assertNotIn(f"{self.home}/Library/Caches\n", subfolders)
        self.assertRegex(result.stdout, r"== Trash\n\s+100K")

    def test_overview_marks_partial_measurement_as_failure(self):
        self.overview_stubs(du_exit='echo "Permission denied" >&2\nexit 1')
        result = self.overview()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("big-cache", result.stdout)
        self.assertIn("Incomplete measurement", result.stderr)
        self.assertIn("Permission denied", result.stderr)

    def test_overview_accepts_limited_output_without_pipeline_failure(self):
        self.overview_stubs()
        result = self.overview("1")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_overview_rejects_invalid_rows(self):
        for args in (("0",), ("-1",), ("oops",), ("1", "2")):
            with self.subTest(args=args):
                self.assertNotEqual(self.overview(*args).returncode, 0)


if __name__ == "__main__":
    unittest.main()
