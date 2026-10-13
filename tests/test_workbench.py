import json
import tempfile
import unittest
from pathlib import Path

from opencog import OpenCogWorkbench
from opencog.agents.agent_zero import Task


ROOT = Path(__file__).resolve().parents[1]


class WorkbenchTests(unittest.TestCase):
    def setUp(self):
        self.workbench = OpenCogWorkbench(tasks_dir=str(ROOT / "tasks"))

    def test_full_catalog_and_ranked_curriculum(self):
        self.assertEqual(95, len(self.workbench.tasks))
        self.assertEqual(95, len(self.workbench.get_curriculum()))
        latex = self.workbench.tasks["multiturn-latex-generation"]
        self.assertTrue(latex.description)
        self.assertTrue(latex.examples)
        self.assertTrue(latex.source)
        self.assertEqual((ROOT / "tasks" / "multiturn-latex-generation.md").read_text(),
                         latex.raw_content)
        self.assertEqual(24, len(self.workbench.tasks["syllogism-reasoning"].examples))

    def test_no_instance_does_not_report_mastery(self):
        result = self.workbench.solve_task("truth-table-completions")
        self.assertFalse(result["success"])
        self.assertFalse(result["validation"]["evaluated"])
        self.assertFalse(self.workbench.agent_zero.performance_history)

    def test_verified_modes_and_guidance(self):
        instance = {"expression": "(P AND Q) OR NOT P"}
        autonomous = self.workbench.solve_task("truth-table-completions", instance=instance)
        collaborative = self.workbench.solve_task(
            "truth-table-completions", orchestration_mode="collaborative", instance=instance
        )
        self.assertTrue(autonomous["success"])
        self.assertTrue(collaborative["success"])
        self.assertEqual(autonomous["answer"], collaborative["answer"])
        self.assertEqual(5, len(collaborative["execution_trace"]))
        self.assertEqual(2, self.workbench.get_statistics()["performance"]["executions"])
        self.assertEqual(1.0, self.workbench.get_statistics()["performance"]["avg_success_rate"])
        self.assertEqual(0, self.workbench.orchestrator.coordinator.monitor_progress()["active_tasks"])
        self.assertTrue(all(
            load == 0 for load in self.workbench.orchestrator.coordinator.agent_load.values()
        ))
        json.dumps(self.workbench.orchestrator.coordinator.task_queue.completed_tasks)
        guided = self.workbench.solve_task("truth-table-completions", "guided", instance)
        self.assertFalse(guided["success"])
        self.assertFalse(guided["evaluated"])
        self.assertNotIn("answer", guided)

    def test_unsupported_does_not_train(self):
        for mode in ("autonomous", "collaborative"):
            result = self.workbench.solve_task(
                "ethical-dilemma-resolution", mode, {"question": "What should I do?"}
            )
            self.assertEqual("unsupported", result["status"])
            self.assertFalse(result["success"])
        self.assertEqual([], self.workbench.agent_zero.performance_history)
        self.assertTrue(all(pattern.use_count == 0
                            for pattern in self.workbench.pattern_library.patterns.values()))

    def test_validator_rejects_wrong_answer_independently(self):
        validation = self.workbench.evaluate_instance(
            "truth-table-completions", {"expression": "P"}, {"rows": []}
        )
        self.assertFalse(validation["success"])
        self.assertTrue(validation["evaluated"])

    def test_injected_executor_cannot_certify_an_incorrect_answer(self):
        from opencog.reasoning import ReasoningBackend

        class IncorrectExecutor(ReasoningBackend):
            def execute(self, task_id, instance):
                result = super().execute(task_id, instance)
                result["answer"]["rows"][0]["value"] = not result["answer"]["rows"][0]["value"]
                return result

        workbench = OpenCogWorkbench(tasks_dir=str(ROOT / "tasks"), backend=IncorrectExecutor())
        for mode in ("autonomous", "collaborative"):
            result = workbench.solve_task(
                "truth-table-completions", mode, {"expression": "P"}
            )
            self.assertEqual("completed", result["status"])
            self.assertFalse(result["success"])
            self.assertTrue(result["validation"]["evaluated"])
        self.assertEqual(0.0, workbench.get_statistics()["performance"]["avg_success_rate"])

    def test_direct_agent_and_strategy_are_honest(self):
        task = Task("unknown", "Unknown", "A problem", "Text only", ["Logic"])
        orchestration = self.workbench.agent_zero.orchestrate_task(task)
        self.assertFalse(orchestration["validation"]["success"])
        strategy = next(iter(self.workbench.strategy_repository.strategies.values()))
        execution = self.workbench.strategy_executor.execute_strategy(
            strategy, {"id": "unknown", "name": "Unknown"}
        )
        self.assertEqual("unsupported", execution["status"])
        self.assertFalse(execution["success"])

    def test_difficulty_does_not_depend_on_example_count(self):
        task = self.workbench.tasks["syllogism-reasoning"]
        before = self.workbench.agent_zero.analyze_task(task)["estimated_difficulty"]
        task.examples *= 4
        after = self.workbench.agent_zero.analyze_task(task)["estimated_difficulty"]
        self.assertEqual(before, after)
        self.assertNotEqual("unrated", before)

    def test_architecture_and_strategy_patterns_resolve(self):
        available = set(self.workbench.pattern_library.patterns)
        for strategy in self.workbench.strategy_repository.strategies.values():
            self.assertTrue(set(strategy.applicable_patterns) <= available)
        for task in self.workbench.tasks.values():
            analysis = self.workbench.agent_zero.analyze_task(task)
            self.assertTrue(set(analysis["required_patterns"]) <= available)

    def test_practice_state_roundtrip(self):
        self.workbench.solve_task("truth-table-completions", instance={"expression": "P XOR Q"})
        before = self.workbench.scheduler.mastery("truth-table-completions")
        with tempfile.TemporaryDirectory() as directory:
            self.workbench.save_state(directory)
            self.assertTrue((Path(directory) / "mastery.json").exists())
            json.loads((Path(directory) / "mastery.json").read_text())
            restored = OpenCogWorkbench(tasks_dir=str(ROOT / "tasks"))
            restored.load_state(directory)
            self.assertEqual(before, restored.scheduler.mastery("truth-table-completions"))
            self.assertEqual(self.workbench.agent_zero.performance_history,
                             restored.agent_zero.performance_history)
            self.assertEqual(self.workbench.recommend_next_tasks(), restored.recommend_next_tasks())

    def test_pipeline_cleans_up_failure(self):
        orchestrator = self.workbench.orchestrator
        orchestrator.create_session("failure", ["executor_01"])

        def fail(context):
            raise RuntimeError("Handler failed")

        with self.assertRaises(RuntimeError):
            orchestrator.run_pipeline("failure", {"id": "failure"},
                                      [("executor_01", "execution", fail)])
        self.assertEqual(0, orchestrator.coordinator.agent_load["executor_01"])
        self.assertEqual(0, orchestrator.coordinator.monitor_progress()["active_tasks"])
        with self.assertRaises(ValueError):
            orchestrator.run_pipeline("failure", {"id": "budget"},
                                      [("executor_01", "execution", fail)], max_steps=0)

    def test_invalid_mode_and_unknown_task(self):
        with self.assertRaises(ValueError):
            self.workbench.solve_task("truth-table-completions", "not-a-mode")
        with self.assertRaises(ValueError):
            self.workbench.solve_task("missing")
        with self.assertRaises(ValueError):
            self.workbench.solve_task(
                "truth-table-completions", instance={"expression": "P", "extra": float("nan")}
            )


if __name__ == "__main__":
    unittest.main()
