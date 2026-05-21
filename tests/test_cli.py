from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from pegasus.cli import ClaudeCreateResult, ClaudeListResult, create_claude_routine, main


class PegasusCliTests(unittest.TestCase):
    def test_run_creates_spec_task_status_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            code = main(["run", tmp, "--goal", "Build a demo", "--task", "Create demo"])
            self.assertEqual(code, 0)
            root = Path(tmp)
            self.assertIn("Build a demo", (root / "spec" / "current.md").read_text())
            self.assertTrue((root / "spec" / "tasks" / "001-create-demo.md").exists())
            self.assertIn("running", (root / "workflow" / "status.md").read_text())
            self.assertTrue((root / "workflow" / "questions.md").exists())
            self.assertTrue((root / "workflow" / "agent-requests" / "001-create-demo.md").exists())

    def test_tell_appends_updates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            main(["run", tmp])
            code = main(["tell", tmp, "Add mobile support"])
            self.assertEqual(code, 0)
            updates = (Path(tmp) / "spec" / "updates.md").read_text()
            self.assertIn("Add mobile support", updates)

    def test_status_reports_task_specs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            main(["run", tmp, "--task", "Ship feature"])
            with patch("builtins.print") as printed:
                code = main(["status", tmp])
            self.assertEqual(code, 0)
            output = "\n".join(str(call.args[0]) for call in printed.call_args_list if call.args)
            self.assertIn("workflow/status.md", output)
            self.assertIn("spec/tasks/001-ship-feature.md", output)
            self.assertIn("workflow/agent-requests/001-ship-feature.md", output)


    def test_stop_without_routine_record_is_not_reported_incomplete(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            code = main(["stop", tmp])
            self.assertEqual(code, 0)
            text = (Path(tmp) / "workflow" / "status.md").read_text()
            self.assertIn("No Claude routine record was present", text)
            self.assertNotIn("cleanup incomplete", text.lower())

    def test_done_status_without_routine_record_is_not_reported_incomplete(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "workflow").mkdir(parents=True)
            (root / "workflow" / "status.md").write_text("# Status\n\nPhase: done\n")
            with patch("builtins.print") as printed:
                code = main(["status", tmp])
            self.assertEqual(code, 0)
            output = "\n".join(str(call.args[0]) for call in printed.call_args_list if call.args)
            self.assertIn("Claude routine already absent", output)
            self.assertNotIn("cleanup incomplete", output.lower())

    def test_stop_marks_project_stopped(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            main(["run", tmp])
            code = main(["stop", tmp])
            self.assertEqual(code, 0)
            self.assertIn("stopped", (Path(tmp) / "workflow" / "status.md").read_text())

    def test_run_preserves_existing_status_on_continue(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            main(["run", tmp])
            status = root / "workflow" / "status.md"
            status.write_text("# Status\n\nPhase: verified\n\nEvidence: keep this\n")
            code = main(["run", tmp])
            self.assertEqual(code, 0)
            text = status.read_text()
            self.assertIn("Evidence: keep this", text)
            self.assertIn("continued", text)

    def test_task_specs_include_repo_source_of_truth_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            main(["run", tmp, "--task", "Ship feature"])
            task = Path(tmp) / "spec" / "tasks" / "001-ship-feature.md"
            text = task.read_text()
            self.assertIn("spec/current.md", text)
            self.assertIn("spec/updates.md", text)
            self.assertIn("workflow/status.md", text)
            self.assertIn("workflow/questions.md", text)

    def test_agent_requests_point_to_task_specs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            main(["run", tmp, "--task", "Ship feature"])
            request = Path(tmp) / "workflow" / "agent-requests" / "001-ship-feature.md"
            text = request.read_text()
            self.assertIn("spec/tasks/001-ship-feature.md", text)
            self.assertIn("spec/current.md", text)
            self.assertIn("spec/updates.md", text)

    def test_run_creates_one_claude_routine_named_after_project(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            main(["run", tmp, "--name", "demo-project"])
            routine = root / "workflow" / "claude-routine.md"
            self.assertIn("Name: demo-project", routine.read_text())
            main(["run", tmp, "--name", "demo-project"])
            self.assertIn("Name: demo-project", routine.read_text())
            with self.assertRaises(SystemExit):
                main(["run", tmp, "--name", "other-project"])

    def test_stop_deletes_claude_routine_record(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            main(["run", tmp, "--name", "demo-project"])
            self.assertTrue((root / "workflow" / "claude-routine.md").exists())
            main(["stop", tmp])
            self.assertFalse((root / "workflow" / "claude-routine.md").exists())

    def test_stop_terminates_verified_live_claude_routine_after_absence_verified(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            agent = {"name": "demo-project", "cwd": tmp, "sessionId": "session-1", "pid": 12345}
            with patch("pegasus.cli.list_claude_agents", return_value=ClaudeListResult(True, [agent])):
                main(["run", tmp, "--name", "demo-project"])
            with patch(
                "pegasus.cli.list_claude_agents",
                side_effect=[ClaudeListResult(True, [agent]), ClaudeListResult(True, [])],
            ), patch("pegasus.cli.os.kill") as kill:
                main(["stop", tmp])
            kill.assert_called_once()
            self.assertFalse((root / "workflow" / "claude-routine.md").exists())

    def test_stop_keeps_record_when_verified_routine_still_present_after_sigterm(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            agent = {"name": "demo-project", "cwd": tmp, "sessionId": "session-1", "pid": 12345}
            with patch("pegasus.cli.list_claude_agents", return_value=ClaudeListResult(True, [agent])):
                main(["run", tmp, "--name", "demo-project"])
            with patch(
                "pegasus.cli.list_claude_agents",
                side_effect=[ClaudeListResult(True, [agent]), ClaudeListResult(True, [agent])],
            ), patch("pegasus.cli.os.kill") as kill:
                main(["stop", tmp])
            kill.assert_called_once()
            self.assertTrue((root / "workflow" / "claude-routine.md").exists())
            self.assertIn("cleanup incomplete", (root / "workflow" / "status.md").read_text().lower())

    def test_stop_blocks_cleanup_on_duplicate_exact_matches(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            agents = [
                {"name": "demo-project", "cwd": tmp, "sessionId": "session-1", "pid": 123},
                {"name": "demo-project", "cwd": tmp, "sessionId": "session-2", "pid": 456},
            ]
            with patch("pegasus.cli.list_claude_agents", return_value=ClaudeListResult(True, [])), patch(
                "pegasus.cli.create_claude_routine", return_value=ClaudeCreateResult(True, False, "no safe create")
            ):
                main(["run", tmp, "--name", "demo-project"])
            with patch("pegasus.cli.list_claude_agents", return_value=ClaudeListResult(True, agents)), patch(
                "pegasus.cli.os.kill"
            ) as kill:
                main(["stop", tmp])
            kill.assert_not_called()
            self.assertTrue((root / "workflow" / "claude-routine.md").exists())
            self.assertIn("Status: conflict", (root / "workflow" / "claude-routine.md").read_text())

    def test_status_deletes_claude_routine_when_done(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            main(["run", tmp, "--name", "demo-project"])
            (root / "workflow" / "status.md").write_text("# Status\n\nPhase: done\n")
            main(["status", tmp])
            self.assertFalse((root / "workflow" / "claude-routine.md").exists())

    def test_run_marks_claude_routine_pending_until_verified(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with patch("pegasus.cli.list_claude_agents", return_value=ClaudeListResult(True, [])), patch(
                "pegasus.cli.create_claude_routine",
                return_value=ClaudeCreateResult(True, False, "no safe create surface"),
            ):
                main(["run", tmp, "--name", "demo-project"])
            routine = Path(tmp) / "workflow" / "claude-routine.md"
            text = routine.read_text()
            self.assertIn("Status: pending_start", text)
            self.assertIn("Create attempt: no safe create surface", text)
            self.assertNotIn("Status: registered", text)

    def test_run_marks_claude_routine_registered_when_verified(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            agent = {"name": "demo-project", "cwd": tmp, "sessionId": "session-1", "pid": 123}
            with patch("pegasus.cli.list_claude_agents", return_value=ClaudeListResult(True, [agent])):
                main(["run", tmp, "--name", "demo-project"])
            routine = Path(tmp) / "workflow" / "claude-routine.md"
            text = routine.read_text()
            self.assertIn("Status: registered", text)
            self.assertIn("Session: session-1", text)


    def test_configured_create_command_is_split_without_shell(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {"PEGASUS_CLAUDE_ROUTINE_CREATE": "claude --name {name} --add-dir {root} --print probe"}), patch(
                "pegasus.cli.subprocess.run"
            ) as run:
                run.return_value.returncode = 0
                run.return_value.stderr = ""
                result = create_claude_routine("demo-project", Path(tmp))
            self.assertTrue(result.attempted)
            self.assertTrue(result.ok)
            argv = run.call_args.args[0]
            self.assertEqual(argv[:3], ["claude", "--name", "demo-project"])
            self.assertNotIsInstance(argv, str)

    def test_run_attempts_create_then_requires_post_create_verification(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            agent = {"name": "demo-project", "cwd": tmp, "sessionId": "session-1", "pid": 123}
            with patch(
                "pegasus.cli.list_claude_agents",
                side_effect=[ClaudeListResult(True, []), ClaudeListResult(True, [agent])],
            ), patch(
                "pegasus.cli.create_claude_routine",
                return_value=ClaudeCreateResult(True, True, "launched"),
            ) as create:
                main(["run", tmp, "--name", "demo-project"])
            create.assert_called_once()
            text = (Path(tmp) / "workflow" / "claude-routine.md").read_text()
            self.assertIn("Status: registered", text)
            self.assertIn("Create attempt: launched", text)

    def test_existing_verified_routine_skips_create(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            agent = {"name": "demo-project", "cwd": tmp, "sessionId": "session-1", "pid": 123}
            with patch("pegasus.cli.list_claude_agents", return_value=ClaudeListResult(True, [agent])), patch(
                "pegasus.cli.create_claude_routine"
            ) as create:
                main(["run", tmp, "--name", "demo-project"])
            create.assert_not_called()

    def test_same_name_different_cwd_does_not_register(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as other:
            agent = {"name": "demo-project", "cwd": other, "sessionId": "session-1", "pid": 123}
            with patch("pegasus.cli.list_claude_agents", return_value=ClaudeListResult(True, [agent])), patch(
                "pegasus.cli.create_claude_routine",
                return_value=ClaudeCreateResult(True, False, "no safe create surface"),
            ):
                main(["run", tmp, "--name", "demo-project"])
            text = (Path(tmp) / "workflow" / "claude-routine.md").read_text()
            self.assertIn("Status: pending_start", text)

    def test_duplicate_exact_matches_mark_conflict(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            agents = [
                {"name": "demo-project", "cwd": tmp, "sessionId": "session-1", "pid": 123},
                {"name": "demo-project", "cwd": tmp, "sessionId": "session-2", "pid": 456},
            ]
            with patch("pegasus.cli.list_claude_agents", return_value=ClaudeListResult(True, agents)):
                main(["run", tmp, "--name", "demo-project"])
            text = (Path(tmp) / "workflow" / "claude-routine.md").read_text()
            self.assertIn("Status: conflict", text)
            self.assertIn("exact Claude routines", text)

    def test_status_handles_corrupt_utf8_status_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "workflow").mkdir(parents=True)
            (root / "workflow" / "status.md").write_bytes(b"# Status\n\nPhase: running\n\xff")
            code = main(["status", tmp])
            self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
