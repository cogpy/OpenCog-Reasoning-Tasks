"""Dependency-aware curriculum and evidence ledger, not a native OpenCog backend.

Ranks describe an instructional order, not measured agent proficiency. Mastery
requires versioned, evaluated held-out evidence, transfer, and delayed retention.
The caller is responsible for running a real evaluator on genuinely held-out
instances; this ledger never treats execution or a self-report as evaluation.
"""

from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
import math
from pathlib import Path


BENCHMARK_VERSION = "reasoning-curriculum-v1"
MIN_HELD_OUT = 20
MASTERY_THRESHOLD = 0.95
RETENTION_DELAY = timedelta(hours=24)

# Every skill is provided by the task families explicitly assigned below.
# Mastering one provider never substitutes for mastering all the others.
SKILL_PREREQUISITES = {
    "logic": (),
    "relations": (),
    "temporal": (),
    "numeracy": (),
    "probability": (),
    "induction": ("relations",),
    "constraints": ("logic",),
    "planning": ("constraints",),
    "spatial": ("relations",),
    "analogy": ("relations", "induction"),
    "language": (),
    "evidence": ("language",),
    "uncertainty": ("probability", "evidence"),
    "causal": ("probability", "evidence"),
    "counterfactual": ("causal",),
    "decisions": ("planning", "uncertainty"),
    "behavior": ("induction", "evidence"),
    "scoped_beliefs": ("temporal", "language"),
    "perspective": ("scoped_beliefs", "behavior"),
    "first_order_belief": ("temporal", "scoped_beliefs"),
    "second_order_belief": ("first_order_belief",),
    "higher_order_belief": ("second_order_belief",),
    "pragmatics": ("language", "evidence", "perspective"),
    "bias": ("language", "evidence"),
    "creative": ("language", "analogy"),
    "legal": ("language", "evidence", "constraints"),
    "forecast": ("counterfactual", "uncertainty"),
    "policy_ethics": ("decisions", "causal", "perspective"),
    "paradoxes": ("logic", "constraints", "language"),
    "multiturn_latex": ("language", "planning", "numeracy"),
}

# Explicit 25-block membership follows the task catalogue, not alphabetical order.
_BLOCKS = (
    ("logic", (
        "truth-table-completions", "syllogism-reasoning",
        "identifying-logical-inconsistencies", "constructing-valid-arguments")),
    ("relations", (
        "identifying-relationships", "categorizing-information-into-hierarchies",
        "completing-analogies", "evaluating-analogies-for-accuracy")),
    ("temporal", (
        "sequencing-events", "understanding-time-based-relationships",
        "interpreting-and-creating-timelines",
        "understanding-time-zones-and-global-time-differences",
        "identifying-anachronisms")),
    ("numeracy", (
        "mathematical-word-problems", "equation-derivation",
        "solving-word-problems-with-multiple-variables", "calculating-probabilities")),
    ("induction", (
        "recognizing-patterns-in-sequences", "deducing-rules-from-examples",
        "pattern-recognition-in-spatial-arrangements")),
    ("constraints", (
        "deductive-logic-puzzles", "proof-verification",
        "critiquing-argument-structures", "identifying-logical-fallacies",
        "identifying-unstated-assumptions")),
    ("planning", (
        "stack-based-reasoning", "towers-of-hanoi", "reverse-engineering-processes",
        "deconstructing-complex-systems")),
    ("spatial", (
        "describing-spatial-relationships", "mental-rotation-tasks",
        "spatial-problem-solving")),
    ("analogy", ("analogy-creation", "analogical-problem-solving")),
    ("language", (
        "parsing-complex-sentences", "interpreting-ambiguous-statements",
        "deciphering-ambiguous-instructions", "deconstructing-metaphors",
        "solving-riddles-and-word-puzzles")),
    ("evidence", (
        "distinguishing-fact-from-opinion", "evaluating-source-credibility",
        "reconciling-conflicting-information",
        "identifying-hallucination-prone-questions")),
    ("uncertainty", (
        "interpreting-statistical-data", "fermi-estimation", "estimating-duration",
        "inference-drawing-from-incomplete-data", "assessing-risk-and-uncertainty")),
    ("causal", (
        "identifying-cause-and-effect-relationships", "causal-chain-analysis",
        "distinguishing-correlation-from-causation", "hypothesis-formation",
        "evaluating-competing-theories")),
    ("counterfactual", (
        "predicting-outcomes-based-on-scenarios", "counterfactual-analysis",
        "determining-alternative-outcomes", "analyzing-historical-counterfactuals")),
    ("decisions", (
        "analyzing-decision-trees", "analyzing-decision-making-processes",
        "risk-assessment-in-decision-making", "prioritizing-conflicting-goals")),
    ("behavior", (
        "recognizing-patterns-in-behavior", "trait-attribution-in-behavioral-scenarios",
        "deducing-motives-from-actions", "inferring-motivations-from-actions",
        "inferring-emotional-states")),
    ("perspective", (
        "first-order-ignorance", "first-order-false-belief",
        "perspective-taking-in-social-scenarios",
        "critical-factor-identification-in-theory-of-mind")),
    ("second_order_belief", ("second-order-false-belief", "higher-order-false-belief")),
    ("pragmatics", (
        "recognizing-emotional-subtext", "detecting-sarcasm-and-irony",
        "interpreting-body-language-cues", "interpreting-nonverbal-communication",
        "analyzing-cultural-differences", "analyzing-rhetorical-strategies")),
    ("bias", (
        "bias-detection", "identifying-cognitive-biases",
        "identifying-implicit-biases-in-language", "bias-mitigation")),
    ("creative", (
        "narrative-gap-filling", "lateral-thinking-puzzles",
        "generating-creative-solutions")),
    ("legal", ("interpreting-legal-language-and-precedents",)),
    ("forecast", (
        "trend-analysis-and-forecasting", "predicting-market-trends",
        "forecasting-technological-impacts", "evaluating-policy-implications",
        "moral-reasoning-in-everyday-situations", "ethical-dilemma-resolution")),
    ("paradoxes", ("unraveling-paradoxes", "currys-paradox")),
    ("multiturn_latex", ("multiturn-latex-generation",)),
)

_SKILL_OVERRIDES = {
    "calculating-probabilities": "probability",
    "first-order-ignorance": "scoped_beliefs",
    "first-order-false-belief": "first_order_belief",
    "higher-order-false-belief": "higher_order_belief",
    "evaluating-policy-implications": "policy_ethics",
    "moral-reasoning-in-everyday-situations": "policy_ethics",
    "ethical-dilemma-resolution": "policy_ethics",
}


def _build_curriculum():
    result = {}
    for rank, (group_skill, task_ids) in enumerate(_BLOCKS, 1):
        for task_id in task_ids:
            skill = _SKILL_OVERRIDES.get(task_id, group_skill)
            prerequisites = SKILL_PREREQUISITES[skill]
            evaluator = (
                "latex_evaluator" if skill == "multiturn_latex"
                else "symbolic_evaluator" if skill in {
                    "logic", "numeracy", "probability", "temporal", "constraints",
                    "planning", "spatial", "first_order_belief",
                    "second_order_belief", "higher_order_belief"
                } else "rubric_evaluator"
            )
            result[task_id] = {
                "rank": rank,
                "difficulty": "introductory" if rank <= 5 else (
                    "intermediate" if rank <= 16 else "advanced"),
                "rationale": (
                    f"Block {rank} develops {skill.replace('_', ' ')}; "
                    + ("requires mastery of " + ", ".join(prerequisites)
                       if prerequisites else "provides a foundation skill")
                    + ". Rank is a teaching heuristic, not measured proficiency."
                ),
                "skills": [skill],
                "prerequisites": list(prerequisites),
                "required_capabilities": [evaluator],
                "evaluator": evaluator,
                "benchmark_version": BENCHMARK_VERSION,
            }
    return result


CURRICULUM = _build_curriculum()


def _timestamp(value=None):
    if value is None:
        result = datetime.now(timezone.utc)
    elif isinstance(value, datetime):
        result = value
    elif isinstance(value, str):
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    elif isinstance(value, (int, float)) and not isinstance(value, bool):
        result = datetime.fromtimestamp(value, timezone.utc)
    else:
        raise ValueError("timestamp must be an ISO string, datetime, or epoch seconds")
    if result.tzinfo is None:
        raise ValueError("timestamp must include a timezone")
    return result.astimezone(timezone.utc)


class CurriculumScheduler:
    """A deterministic scheduler with conservative, revocable mastery.

    ``metadata`` is a complete task-ID mapping with the same schema as
    ``CURRICULUM``. Prerequisites are skill IDs; all providers of a skill must
    be mastered. Capability IDs denote available evaluator implementations,
    not aspirational agent labels. No capabilities are assumed by default.

    Eligible splits are ``held_out``, ``transfer`` and ``retention``. ``practice``
    and ``simulated`` are logged but cannot certify mastery. Instance IDs are
    stable within a task and benchmark; reuse across splits contaminates that
    instance. For repeated evaluations only the latest result counts. Evaluator
    versions never pool evidence, nor do benchmark versions.
    """

    def __init__(self, metadata=None, available_capabilities=None):
        self.metadata = deepcopy(CURRICULUM if metadata is None else metadata)
        if isinstance(available_capabilities, str):
            raise ValueError("available_capabilities must be a collection, not a string")
        self.available_capabilities = set(available_capabilities or ())
        self.attempts = []
        self._providers = {}
        self._validate_metadata()

    def _validate_metadata(self):
        required = set(next(iter(CURRICULUM.values())))
        for task_id, entry in self.metadata.items():
            if not isinstance(task_id, str) or not task_id:
                raise ValueError("task IDs must be nonempty strings")
            if not isinstance(entry, dict) or not required.issubset(entry):
                raise ValueError(f"incomplete curriculum metadata: {task_id}")
            if not isinstance(entry["rank"], int) or entry["rank"] < 1:
                raise ValueError(f"invalid rank: {task_id}")
            for key in ("skills", "prerequisites", "required_capabilities"):
                values = entry[key]
                if not isinstance(values, (list, tuple)) or any(
                    not isinstance(value, str) or not value for value in values
                ):
                    raise ValueError(f"invalid {key}: {task_id}")
            if not entry["skills"]:
                raise ValueError(f"task must provide at least one skill: {task_id}")
            for key in ("difficulty", "rationale", "evaluator", "benchmark_version"):
                if not isinstance(entry[key], str) or not entry[key]:
                    raise ValueError(f"invalid {key}: {task_id}")
            for skill in entry["skills"]:
                self._providers.setdefault(skill, set()).add(task_id)
        graph = {}
        for task_id, entry in self.metadata.items():
            graph[task_id] = set()
            for skill in entry["prerequisites"]:
                if skill not in self._providers:
                    raise ValueError(f"unknown prerequisite skill {skill!r}: {task_id}")
                graph[task_id].update(self._providers[skill])
        visiting, visited = set(), set()

        def visit(task_id):
            if task_id in visiting:
                raise ValueError(f"cyclic curriculum dependency: {task_id}")
            if task_id in visited:
                return
            visiting.add(task_id)
            for dependency in sorted(graph[task_id]):
                visit(dependency)
            visiting.remove(task_id)
            visited.add(task_id)

        for task_id in sorted(graph):
            visit(task_id)

    def _entry(self, task_id):
        if task_id not in self.metadata:
            raise ValueError(f"unknown task ID: {task_id}")
        return self.metadata[task_id]

    def record_attempt(self, task_id, instance_id, validation, *, split="practice",
                       transfer=False, timestamp=None, benchmark_version=None):
        """Log evaluator evidence; recording an attempt is not a mastery claim."""
        entry = self._entry(task_id)
        if not isinstance(instance_id, str) or not instance_id:
            raise ValueError("instance_id must be a nonempty stable string")
        if split not in {"practice", "simulated", "held_out", "transfer", "retention"}:
            raise ValueError(f"unknown evaluation split: {split}")
        if not isinstance(transfer, bool):
            raise ValueError("transfer must be a boolean")
        if transfer and split == "held_out":
            split = "transfer"
        elif transfer and split != "transfer":
            raise ValueError("transfer evidence must use split='held_out' or 'transfer'")
        if not isinstance(validation, dict):
            raise ValueError("validation must be an evaluator result dictionary")
        for key in ("evaluated", "success"):
            if not isinstance(validation.get(key), bool):
                raise ValueError(f"validation.{key} must be a boolean")
        if not isinstance(validation.get("evidence"), list):
            raise ValueError("validation.evidence must be a list")
        if not isinstance(validation.get("evaluator_version"), str):
            raise ValueError("validation.evaluator_version must be a string")
        version = entry["benchmark_version"] if benchmark_version is None else benchmark_version
        if not isinstance(version, str) or not version:
            raise ValueError("benchmark_version must be a nonempty string")
        attempt = {
            "task_id": task_id, "instance_id": instance_id, "split": split,
            "transfer": split == "transfer",
            "timestamp": _timestamp(timestamp).isoformat(),
            "benchmark_version": version, "evaluator": entry["evaluator"],
            "validation": deepcopy(validation),
        }
        # Reject nonportable evidence before mutating the ledger.
        json.dumps(attempt, allow_nan=False)
        self.attempts.append(attempt)
        return deepcopy(attempt)

    @staticmethod
    def _eligible(attempt):
        validation = attempt["validation"]
        return (
            attempt["split"] in {"held_out", "transfer", "retention"}
            and validation["evaluated"]
            and bool(validation["evidence"])
            and bool(validation["evaluator_version"].strip())
            and not validation.get("simulated", False)
        )

    def mastery(self, task_id):
        """Return evidence counts, uncertainty and the current mastery decision."""
        entry = self._entry(task_id)
        attempts = [
            (index, attempt) for index, attempt in enumerate(self.attempts)
            if attempt["task_id"] == task_id
            and attempt["benchmark_version"] == entry["benchmark_version"]
            and attempt["evaluator"] == entry["evaluator"]
        ]
        eligible = [(index, attempt) for index, attempt in attempts if self._eligible(attempt)]
        latest_key = lambda pair: (_timestamp(pair[1]["timestamp"]), pair[0])
        evaluator_version = (
            max(eligible, key=latest_key)[1]["validation"]["evaluator_version"]
            if eligible else None
        )
        splits = {}
        for _, attempt in attempts:
            splits.setdefault(attempt["instance_id"], set()).add(attempt["split"])
        latest = {}
        for pair in eligible:
            _, attempt = pair
            if attempt["validation"]["evaluator_version"] != evaluator_version:
                continue
            if len(splits[attempt["instance_id"]]) != 1:
                continue
            key = (attempt["split"], attempt["instance_id"])
            if key not in latest or latest_key(pair) > latest_key(latest[key]):
                latest[key] = pair
        held_out = [pair for (split, _), pair in latest.items() if split == "held_out"]
        count = len(held_out)
        successes = sum(pair[1]["validation"]["success"] for pair in held_out)
        accuracy = successes / count if count else None
        qualified = count >= MIN_HELD_OUT and accuracy >= MASTERY_THRESHOLD
        qualified_at = max((latest_key(pair)[0] for pair in held_out), default=None)
        transfer_attempts = [pair for (split, _), pair in latest.items() if split == "transfer"]
        retention_attempts = [pair for (split, _), pair in latest.items() if split == "retention"]
        transfer_pair = max(transfer_attempts, key=latest_key, default=None)
        retention_pair = max(retention_attempts, key=latest_key, default=None)
        transferred = bool(
            qualified and transfer_pair
            and transfer_pair[1]["validation"]["success"]
            and latest_key(transfer_pair)[0] >= qualified_at
        )
        retained = bool(
            transferred and retention_pair
            and retention_pair[1]["validation"]["success"]
            and latest_key(retention_pair)[0]
            >= latest_key(transfer_pair)[0] + RETENTION_DELAY
        )
        # Wilson interval is descriptive uncertainty, not a second mastery gate.
        interval = None
        if count:
            z = 1.96
            denominator = 1 + z * z / count
            center = (accuracy + z * z / (2 * count)) / denominator
            radius = z * math.sqrt(
                accuracy * (1 - accuracy) / count + z * z / (4 * count * count)
            ) / denominator
            interval = [max(0, center - radius), min(1, center + radius)]
        return {
            "task_id": task_id, "mastered": qualified and transferred and retained,
            "held_out_count": count, "held_out_successes": successes,
            "accuracy": accuracy, "threshold": MASTERY_THRESHOLD,
            "minimum_instances": MIN_HELD_OUT, "transfer_passed": transferred,
            "retention_passed": retained, "benchmark_version": entry["benchmark_version"],
            "evaluator": entry["evaluator"], "evaluator_version": evaluator_version,
            "uncertainty": {"method": "wilson_95", "accuracy_interval": interval},
            "attempt_count": len(attempts),
        }

    def skill_mastery(self, skill):
        """Certify a skill only when every declared provider family is mastered."""
        if skill not in self._providers:
            raise ValueError(f"unknown skill ID: {skill}")
        providers = sorted(self._providers[skill])
        missing = [task_id for task_id in providers if not self.mastery(task_id)["mastered"]]
        return {"skill": skill, "mastered": not missing,
                "providers": providers, "missing_tasks": missing}

    def readiness(self, task_id):
        entry = self._entry(task_id)
        missing_skills = sorted(
            skill for skill in set(entry["prerequisites"])
            if not self.skill_mastery(skill)["mastered"]
        )
        missing_capabilities = sorted(
            set(entry["required_capabilities"]) - self.available_capabilities
        )
        mastered = self.mastery(task_id)["mastered"]
        ready = not missing_skills and not missing_capabilities
        reasons = []
        if missing_skills:
            reasons.append("unmastered prerequisite skills: " + ", ".join(missing_skills))
        if missing_capabilities:
            reasons.append("unavailable capabilities: " + ", ".join(missing_capabilities))
        return {
            "task_id": task_id, "ready": ready, "mastered": mastered,
            "rank": entry["rank"], "difficulty": entry["difficulty"],
            "missing_prerequisites": missing_skills,
            "missing_capabilities": missing_capabilities,
            "reason": "; ".join(reasons) if reasons else (
                "mastery certified" if mastered else "prerequisites and capabilities available"),
        }

    def recommend(self, limit=10):
        """Return unmastered tasks, ready first, then rank and stable task ID."""
        if not isinstance(limit, int) or isinstance(limit, bool) or limit < 0:
            raise ValueError("limit must be a nonnegative integer")
        recommendations = [self.readiness(task_id) for task_id in sorted(self.metadata)]
        recommendations = [item for item in recommendations if not item["mastered"]]
        recommendations.sort(key=lambda item: (not item["ready"], item["rank"], item["task_id"]))
        return recommendations[:limit]

    def save(self, path):
        """Persist the full evidence ledger, including evaluator uncertainty."""
        data = {
            "schema_version": 1, "metadata": self.metadata,
            "available_capabilities": sorted(self.available_capabilities),
            "attempts": self.attempts,
        }
        Path(path).write_text(json.dumps(data, indent=2, sort_keys=True, allow_nan=False),
                              encoding="utf-8")

    @classmethod
    def load(cls, path):
        """Restore and validate a saved scheduler without trusting mastery flags."""
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        if data.get("schema_version") != 1:
            raise ValueError("unsupported curriculum ledger schema")
        result = cls(data["metadata"], data["available_capabilities"])
        for attempt in data["attempts"]:
            entry = result._entry(attempt["task_id"])
            if attempt["evaluator"] != entry["evaluator"]:
                raise ValueError("saved attempt evaluator does not match metadata")
            if attempt["transfer"] != (attempt["split"] == "transfer"):
                raise ValueError("saved attempt transfer flag does not match split")
            result.record_attempt(
                attempt["task_id"], attempt["instance_id"], attempt["validation"],
                split=attempt["split"], timestamp=attempt["timestamp"],
                benchmark_version=attempt["benchmark_version"],
            )
        return result
