from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from pegasus.cli import main


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


if __name__ == "__main__":
    unittest.main()
