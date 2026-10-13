"""Standard-library tests for the versioned curriculum evidence ledger."""

from copy import deepcopy
from datetime import datetime, timedelta, timezone
from pathlib import Path
import json
import unittest
from uuid import uuid4

from opencog.curriculum import (
    BENCHMARK_VERSION, CURRICULUM, CurriculumScheduler, SKILL_CAPABILITIES,
    SKILL_PREREQUISITES,
)


ROOT = Path(__file__).resolve().parents[1]
START = datetime(2026, 1, 1, tzinfo=timezone.utc)
BACKEND_CAPABILITIES = {
    "boolean_evaluation", "deterministic_rules", "knowledge_representation",
    "planning", "recursion", "state_transitions",
}
CAPABILITIES = BACKEND_CAPABILITIES | {
    capability for capabilities in SKILL_CAPABILITIES.values()
    for capability in capabilities
}
TASK = "truth-table-completions"


def validation(success=True, evaluated=True, version="test-evaluator-v1", **extra):
    return {
        "evaluated": evaluated, "success": success,
        "evidence": [{"check": "independent expected answer", "passed": success}],
        "evaluator_version": version, **extra,
    }


def certify(scheduler, task_id=TASK, successes=20, version="test-evaluator-v1"):
    for index in range(20):
        scheduler.record_attempt(
            task_id, f"held-{index}", validation(index < successes, version=version),
            split="held_out", timestamp=START,
        )
    scheduler.record_attempt(
        task_id, "transfer-1", validation(version=version),
        split="transfer", timestamp=START + timedelta(hours=1),
    )
    scheduler.record_attempt(
        task_id, "retention-1", validation(version=version),
        split="retention", timestamp=START + timedelta(hours=25),
    )


class CurriculumTests(unittest.TestCase):
    def setUp(self):
        self.scheduler = CurriculumScheduler(available_capabilities=CAPABILITIES)

    def test_exact_catalogue_coverage_and_schema(self):
        actual_ids = {path.stem for path in (ROOT / "tasks").glob("*.md")}
        self.assertEqual(set(CURRICULUM), actual_ids)
        self.assertEqual(len(CURRICULUM), 95)
        self.assertNotIn("truth-table-completion", CURRICULUM)
        required = {
            "rank", "order", "difficulty", "rationale", "skills", "prerequisites",
            "required_capabilities", "evaluator", "benchmark_version",
        }
        for entry in CURRICULUM.values():
            self.assertEqual(set(entry), required)
            self.assertTrue(entry["rationale"])
            self.assertTrue(entry["required_capabilities"])
            self.assertEqual(entry["benchmark_version"], BENCHMARK_VERSION)
            self.assertEqual(entry["difficulty"], f"D{(entry['rank'] - 1) // 5 + 1}")
            self.assertFalse(any(
                capability.endswith("_evaluator") for capability in entry["required_capabilities"]
            ))
            for skill in entry["skills"]:
                self.assertEqual(entry["prerequisites"], list(SKILL_PREREQUISITES[skill]))

    def test_exact_25_block_assignments(self):
        blocks = [
            "truth-table-completions syllogism-reasoning identifying-logical-inconsistencies constructing-valid-arguments",
            "identifying-relationships categorizing-information-into-hierarchies completing-analogies evaluating-analogies-for-accuracy",
            "sequencing-events understanding-time-based-relationships interpreting-and-creating-timelines understanding-time-zones-and-global-time-differences identifying-anachronisms",
            "mathematical-word-problems equation-derivation solving-word-problems-with-multiple-variables calculating-probabilities",
            "recognizing-patterns-in-sequences deducing-rules-from-examples pattern-recognition-in-spatial-arrangements",
            "deductive-logic-puzzles proof-verification critiquing-argument-structures identifying-logical-fallacies identifying-unstated-assumptions",
            "stack-based-reasoning towers-of-hanoi reverse-engineering-processes deconstructing-complex-systems",
            "describing-spatial-relationships mental-rotation-tasks spatial-problem-solving",
            "analogy-creation analogical-problem-solving",
            "parsing-complex-sentences interpreting-ambiguous-statements deciphering-ambiguous-instructions deconstructing-metaphors solving-riddles-and-word-puzzles",
            "distinguishing-fact-from-opinion evaluating-source-credibility reconciling-conflicting-information identifying-hallucination-prone-questions",
            "interpreting-statistical-data fermi-estimation estimating-duration inference-drawing-from-incomplete-data assessing-risk-and-uncertainty",
            "identifying-cause-and-effect-relationships causal-chain-analysis distinguishing-correlation-from-causation hypothesis-formation evaluating-competing-theories",
            "predicting-outcomes-based-on-scenarios counterfactual-analysis determining-alternative-outcomes analyzing-historical-counterfactuals",
            "analyzing-decision-trees analyzing-decision-making-processes risk-assessment-in-decision-making prioritizing-conflicting-goals",
            "recognizing-patterns-in-behavior trait-attribution-in-behavioral-scenarios deducing-motives-from-actions inferring-motivations-from-actions inferring-emotional-states",
            "first-order-ignorance first-order-false-belief perspective-taking-in-social-scenarios critical-factor-identification-in-theory-of-mind",
            "second-order-false-belief higher-order-false-belief",
            "recognizing-emotional-subtext detecting-sarcasm-and-irony interpreting-body-language-cues interpreting-nonverbal-communication analyzing-cultural-differences analyzing-rhetorical-strategies",
            "bias-detection identifying-cognitive-biases identifying-implicit-biases-in-language bias-mitigation",
            "narrative-gap-filling lateral-thinking-puzzles generating-creative-solutions",
            "interpreting-legal-language-and-precedents",
            "trend-analysis-and-forecasting predicting-market-trends forecasting-technological-impacts evaluating-policy-implications moral-reasoning-in-everyday-situations ethical-dilemma-resolution",
            "unraveling-paradoxes currys-paradox",
            "multiturn-latex-generation",
        ]
        expected = {task: rank for rank, ids in enumerate(blocks, 1) for task in ids.split()}
        self.assertEqual({task: entry["rank"] for task, entry in CURRICULUM.items()}, expected)
        for ids in blocks:
            for order, task in enumerate(ids.split(), 1):
                self.assertEqual(CURRICULUM[task]["order"], order)

    def test_dependency_chains_and_belief_scoping(self):
        expected = {
            "constraints": ("logic",),
            "planning": ("constraints",),
            "decisions": ("planning", "uncertainty"),
            "induction": ("relations",),
            "analogy": ("relations", "induction"),
            "causal": ("probability", "evidence"),
            "counterfactual": ("causal",),
            "forecast": ("counterfactual", "uncertainty"),
            "first_order_belief": ("temporal", "scoped_beliefs"),
            "second_order_belief": ("first_order_belief",),
            "higher_order_belief": ("second_order_belief",),
            "policy_ethics": ("decisions", "causal", "perspective"),
        }
        for skill, prerequisites in expected.items():
            self.assertEqual(SKILL_PREREQUISITES[skill], prerequisites)
        self.assertEqual(CURRICULUM["higher-order-false-belief"]["skills"],
                         ["higher_order_belief"])
        self.assertEqual(CURRICULUM["calculating-probabilities"]["skills"], ["probability"])

    def test_no_capabilities_are_assumed(self):
        result = CurriculumScheduler().readiness(TASK)
        self.assertFalse(result["ready"])
        self.assertEqual(result["missing_capabilities"], ["boolean_evaluation"])
        self.assertTrue(self.scheduler.readiness(TASK)["ready"])
        self.assertFalse(self.scheduler.readiness("deductive-logic-puzzles")["ready"])

    def test_real_backend_foundations_ready_and_unsupported_families_blocked(self):
        implemented = {
            "truth-table-completions", "syllogism-reasoning",
            "towers-of-hanoi", "stack-based-reasoning",
        }
        scheduler = CurriculumScheduler(
            available_capabilities=BACKEND_CAPABILITIES, supported_tasks=implemented,
        )
        self.assertTrue(scheduler.readiness(TASK)["ready"])
        self.assertTrue(scheduler.readiness("syllogism-reasoning")["ready"])
        self.assertFalse(scheduler.readiness("towers-of-hanoi")["ready"])
        self.assertFalse(scheduler.readiness("constructing-valid-arguments")["supported"])
        self.assertIn("not supported", scheduler.readiness(
            "constructing-valid-arguments")["reason"])
        unavailable = CurriculumScheduler(
            available_capabilities=CAPABILITIES, supported_tasks=set(),
        )
        self.assertFalse(unavailable.readiness(TASK)["ready"])
        with self.assertRaisesRegex(ValueError, "unknown supported"):
            CurriculumScheduler(supported_tasks={"invented-task"})

    def test_practice_simulation_and_unevaluated_runs_never_certify(self):
        for split in ("practice", "simulated", "held_out"):
            for index in range(25):
                self.scheduler.record_attempt(
                    TASK, f"{split}-{index}", validation(evaluated=split != "held_out"),
                    split=split, timestamp=START,
                )
        self.assertEqual(self.scheduler.mastery(TASK)["held_out_count"], 0)
        self.assertFalse(self.scheduler.mastery(TASK)["mastered"])

    def test_simulated_flag_and_missing_evidence_are_not_evaluation(self):
        for index in range(20):
            self.scheduler.record_attempt(
                TASK, f"sim-{index}", validation(simulated=True),
                split="held_out", timestamp=START,
            )
            self.scheduler.record_attempt(
                TASK, f"empty-{index}", validation(evidence=[]),
                split="held_out", timestamp=START,
            )
        self.assertEqual(self.scheduler.mastery(TASK)["held_out_count"], 0)

    def test_requires_20_distinct_instances_and_transfer_retention(self):
        for index in range(20):
            self.scheduler.record_attempt(
                TASK, "same-instance", validation(), split="held_out", timestamp=START,
            )
        self.assertEqual(self.scheduler.mastery(TASK)["held_out_count"], 1)
        self.assertFalse(self.scheduler.mastery(TASK)["mastered"])
        for index in range(19):
            self.scheduler.record_attempt(
                TASK, f"fresh-{index}", validation(), split="held_out", timestamp=START,
            )
        result = self.scheduler.mastery(TASK)
        self.assertEqual(result["held_out_count"], 20)
        self.assertFalse(result["mastered"])
        self.assertFalse(result["transfer_passed"])

    def test_threshold_is_inclusive_95_percent(self):
        certify(self.scheduler, successes=19)
        result = self.scheduler.mastery(TASK)
        self.assertEqual(result["accuracy"], 0.95)
        self.assertTrue(result["mastered"])
        self.assertLess(result["uncertainty"]["accuracy_interval"][0], 0.95)
        other = CurriculumScheduler(available_capabilities=CAPABILITIES)
        certify(other, successes=18)
        self.assertFalse(other.mastery(TASK)["mastered"])

    def test_retention_is_24_hours_after_transfer(self):
        certify(self.scheduler)
        self.assertTrue(self.scheduler.mastery(TASK)["mastered"])
        other = CurriculumScheduler(available_capabilities=CAPABILITIES)
        for attempt in self.scheduler.attempts[:-1]:
            other.record_attempt(
                TASK, attempt["instance_id"], attempt["validation"],
                split=attempt["split"], timestamp=attempt["timestamp"],
            )
        other.record_attempt(
            TASK, "early-retention", validation(), split="retention",
            timestamp=START + timedelta(hours=24, minutes=59),
        )
        self.assertFalse(other.mastery(TASK)["mastered"])
        other.record_attempt(
            TASK, "later-retention", validation(), split="retention",
            timestamp=START + timedelta(hours=25),
        )
        self.assertTrue(other.mastery(TASK)["mastered"])

    def test_failed_transfer_or_retention_revokes_mastery(self):
        for split in ("transfer", "retention"):
            with self.subTest(split=split):
                scheduler = CurriculumScheduler(available_capabilities=CAPABILITIES)
                certify(scheduler)
                scheduler.record_attempt(
                    TASK, f"{split}-2", validation(False), split=split,
                    timestamp=START + timedelta(hours=26),
                )
                self.assertFalse(scheduler.mastery(TASK)["mastered"])

    def test_repeated_held_out_failure_updates_not_inflates_counts(self):
        certify(self.scheduler, successes=19)
        self.scheduler.record_attempt(
            TASK, "held-0", validation(False), split="held_out",
            timestamp=START + timedelta(hours=26),
        )
        result = self.scheduler.mastery(TASK)
        self.assertEqual(result["held_out_count"], 20)
        self.assertEqual(result["held_out_successes"], 18)
        self.assertFalse(result["mastered"])

    def test_evaluated_failures_without_evidence_count_and_revoke(self):
        certify(self.scheduler)
        self.scheduler.record_attempt(
            TASK, "held-0", validation(False, evidence=[]),
            split="held_out", timestamp=START,
        )
        result = self.scheduler.mastery(TASK)
        self.assertEqual(result["held_out_count"], 20)
        self.assertEqual(result["accuracy"], 0.95)
        self.assertTrue(result["mastered"])
        self.scheduler.record_attempt(
            TASK, "held-1", validation(False, evidence=[]),
            split="held_out", timestamp=START,
        )
        result = self.scheduler.mastery(TASK)
        self.assertEqual(result["held_out_count"], 20)
        self.assertEqual(result["accuracy"], 0.90)
        self.assertFalse(result["mastered"])
        for split in ("transfer", "retention"):
            with self.subTest(split=split):
                scheduler = CurriculumScheduler(available_capabilities=CAPABILITIES)
                certify(scheduler)
                scheduler.record_attempt(
                    TASK, f"{split}-failure", validation(False, evidence=[]),
                    split=split, timestamp=START + timedelta(hours=26),
                )
                self.assertFalse(scheduler.mastery(TASK)["mastered"])

    def test_cross_split_instance_reuse_is_contamination(self):
        certify(self.scheduler)
        self.scheduler.record_attempt(
            TASK, "held-0", validation(), split="practice",
            timestamp=START + timedelta(hours=26),
        )
        result = self.scheduler.mastery(TASK)
        self.assertEqual(result["held_out_count"], 19)
        self.assertFalse(result["mastered"])

    def test_practice_instances_cannot_later_be_relabelled_held_out(self):
        self.scheduler.record_attempt(
            TASK, "held-0", validation(), split="practice",
            timestamp=START - timedelta(days=1),
        )
        certify(self.scheduler)
        result = self.scheduler.mastery(TASK)
        self.assertEqual(result["held_out_count"], 19)
        self.assertFalse(result["mastered"])

    def test_transfer_flag_never_promotes_practice(self):
        with self.assertRaises(ValueError):
            self.scheduler.record_attempt(TASK, "practice", validation(), transfer=True)
        result = self.scheduler.record_attempt(
            TASK, "transfer", validation(), split="held_out", transfer=True,
        )
        self.assertEqual(result["split"], "transfer")
        self.assertEqual(self.scheduler.mastery(TASK)["held_out_count"], 0)

    def test_benchmark_and_evaluator_versions_do_not_pool(self):
        certify(self.scheduler)
        self.scheduler.record_attempt(
            TASK, "new-evaluator", validation(version="test-evaluator-v2"),
            split="held_out", timestamp=START + timedelta(hours=26),
        )
        result = self.scheduler.mastery(TASK)
        self.assertEqual(result["held_out_count"], 1)
        self.assertFalse(result["mastered"])
        self.scheduler.record_attempt(
            TASK, "old-benchmark", validation(), split="held_out",
            timestamp=START + timedelta(hours=27), benchmark_version="old",
        )
        self.assertEqual(self.scheduler.mastery(TASK)["held_out_count"], 1)
        self.scheduler.metadata[TASK]["benchmark_version"] = "new"
        self.assertEqual(self.scheduler.mastery(TASK)["held_out_count"], 0)

    def test_chronological_order_not_record_order(self):
        certify(self.scheduler)
        self.scheduler.record_attempt(
            TASK, "old-transfer-failure", validation(False), split="transfer",
            timestamp=START - timedelta(hours=1),
        )
        self.assertTrue(self.scheduler.mastery(TASK)["mastered"])

    def test_all_skill_provider_families_must_master(self):
        certify(self.scheduler)
        self.assertFalse(self.scheduler.skill_mastery("logic")["mastered"])
        self.assertFalse(self.scheduler.readiness("deductive-logic-puzzles")["ready"])
        for task_id in self.scheduler.skill_mastery("logic")["missing_tasks"]:
            certify(self.scheduler, task_id)
        self.assertTrue(self.scheduler.skill_mastery("logic")["mastered"])
        self.assertTrue(self.scheduler.readiness("deductive-logic-puzzles")["ready"])
        self.scheduler.record_attempt(
            TASK, "late-failure", validation(False), split="retention",
            timestamp=START + timedelta(days=2),
        )
        self.assertFalse(self.scheduler.readiness("deductive-logic-puzzles")["ready"])

    def test_ready_recommendations_are_deterministic_and_explain_blocking(self):
        first = self.scheduler.recommend(95)
        self.assertEqual(first, self.scheduler.recommend(95))
        blocked_index = next(index for index, item in enumerate(first) if not item["ready"])
        self.assertTrue(all(item["ready"] for item in first[:blocked_index]))
        self.assertTrue(all(not item["ready"] for item in first[blocked_index:]))
        self.assertTrue(all(item["reason"] for item in first))
        certify(self.scheduler)
        self.assertNotIn(TASK, {item["task_id"] for item in self.scheduler.recommend(95)})
        self.assertEqual(self.scheduler.recommend(0), [])

    def test_unknown_tasks_skills_and_cycles_fail_fast(self):
        for action in (
            lambda: self.scheduler.readiness("unknown"),
            lambda: self.scheduler.mastery("unknown"),
            lambda: self.scheduler.skill_mastery("unknown"),
            lambda: self.scheduler.record_attempt("unknown", "one", validation()),
        ):
            with self.assertRaises(ValueError):
                action()
        metadata = deepcopy(CURRICULUM)
        metadata[TASK]["prerequisites"] = ["unknown"]
        with self.assertRaisesRegex(ValueError, "unknown prerequisite"):
            CurriculumScheduler(metadata)
        metadata[TASK]["prerequisites"] = ["logic"]
        with self.assertRaisesRegex(ValueError, "cyclic"):
            CurriculumScheduler(metadata)
        metadata[TASK]["prerequisites"] = ["planning"]
        with self.assertRaisesRegex(ValueError, "cyclic"):
            CurriculumScheduler(metadata)

    def test_bad_inputs_do_not_mutate_ledger(self):
        bad = [
            {"instance_id": "", "validation": validation()},
            {"instance_id": "a", "validation": validation(evaluated=1)},
            {"instance_id": "a", "validation": validation(evidence="text")},
            {"instance_id": "a", "validation": validation(), "split": "training"},
            {"instance_id": "a", "validation": validation(), "timestamp": "2026-01-01"},
            {"instance_id": "a", "validation": validation(), "benchmark_version": ""},
            {"instance_id": "a", "validation": validation(uncertainty=float("nan"))},
        ]
        for kwargs in bad:
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                self.scheduler.record_attempt(TASK, **kwargs)
        self.assertEqual(self.scheduler.attempts, [])
        for limit in (-1, 1.5, True):
            with self.assertRaises(ValueError):
                self.scheduler.recommend(limit)

    def test_defensive_copy_and_empty_custom_curriculum(self):
        metadata = deepcopy(CURRICULUM)
        scheduler = CurriculumScheduler(metadata, CAPABILITIES)
        metadata[TASK]["skills"].append("not-real")
        self.assertEqual(scheduler.metadata[TASK]["skills"], ["logic"])
        result = validation(uncertainty={"confidence": 0.9})
        attempt = scheduler.record_attempt(TASK, "copy", result)
        result["evidence"].clear()
        attempt["validation"]["evidence"].clear()
        self.assertTrue(scheduler.attempts[0]["validation"]["evidence"])
        self.assertEqual(CurriculumScheduler({}).recommend(), [])

    def test_save_load_preserves_evidence_versions_and_uncertainty(self):
        path = ROOT / "tests" / f".curriculum-ledger-{uuid4().hex}.json"
        try:
            certify(self.scheduler)
            self.scheduler.record_attempt(
                TASK, "practice", validation(uncertainty={"confidence": 0.7}),
                timestamp=START, benchmark_version="previous-benchmark",
            )
            self.scheduler.save(path)
            restored = CurriculumScheduler(available_capabilities=CAPABILITIES)
            self.assertIs(restored.load(path), restored)
            self.assertEqual(restored.attempts, self.scheduler.attempts)
            self.assertEqual(restored.mastery(TASK), self.scheduler.mastery(TASK))
            self.assertEqual(restored.recommend(), self.scheduler.recommend())
            unavailable = CurriculumScheduler(supported_tasks=set())
            unavailable.load(path)
            self.assertEqual(unavailable.available_capabilities, set())
            self.assertEqual(unavailable.supported_tasks, set())
            self.assertFalse(unavailable.readiness("syllogism-reasoning")["ready"])
            self.assertTrue(unavailable.mastery(TASK)["mastered"])
            data = json.loads(path.read_text(encoding="utf-8"))
            data["metadata"][TASK]["prerequisites"] = ["logic"]
            path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "cyclic"):
                restored.load(path)
        finally:
            path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
