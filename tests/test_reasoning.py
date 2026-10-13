"""Standard-library tests for bounded execution and independent evaluation."""

import copy
import itertools
import json
import unittest
from unittest.mock import patch

from opencog.reasoning import ReasoningBackend


def statement(kind, subject, predicate):
    return {"kind": kind, "subject": subject, "predicate": predicate}


class ReasoningTests(unittest.TestCase):
    def setUp(self):
        self.backend = ReasoningBackend()

    def test_truth_enumeration_and_independent_validator(self):
        instance = {"expression": "(P AND Q) OR NOT P"}
        result = self.backend.run("truth-table-completions", instance)
        self.assertTrue(result["success"])
        self.assertEqual([row["value"] for row in result["answer"]["rows"]],
                         [True, True, False, True])
        with patch.object(self.backend, "execute", side_effect=AssertionError("must not solve")):
            self.assertTrue(self.backend.validate("truth-table-completions", instance,
                                                 result["answer"])["success"])
        json.dumps(result)

    def test_boolean_operators(self):
        operations = {
            "P AND Q": [False, False, False, True],
            "P OR Q": [False, True, True, True],
            "P XOR Q": [False, True, True, False],
            "P IMPLIES Q": [True, True, False, True],
            "P IFF Q": [True, False, False, True],
            "!(P & Q)": [True, True, True, False],
        }
        for expression, values in operations.items():
            with self.subTest(expression=expression):
                result = self.backend.run("truth-table-completions", {"expression": expression})
                self.assertTrue(result["success"])
                self.assertEqual([row["value"] for row in result["answer"]["rows"]], values)

    def test_eight_variable_limit_and_associativity(self):
        expression = " OR ".join("P" + str(index) for index in range(8))
        result = self.backend.run("truth-table-completions", {"expression": expression})
        self.assertTrue(result["success"])
        self.assertEqual(len(result["answer"]["rows"]), 256)
        self.assertEqual(sum(row["value"] for row in result["answer"]["rows"]), 255)
        result = self.backend.run("truth-table-completions",
                                  {"expression": "P IMPLIES Q IMPLIES R"})
        self.assertTrue(result["success"])
        for row in result["answer"]["rows"]:
            assignment = row["assignment"]
            self.assertEqual(row["value"], not assignment["P"] or
                             (not assignment["Q"] or assignment["R"]))

    def test_truth_wrong_duplicate_missing_and_nonboolean_rows(self):
        instance = {"expression": "P OR Q"}
        correct = self.backend.execute("truth-table-completions", instance)["answer"]
        bad = []
        answer = copy.deepcopy(correct)
        answer["rows"][0]["value"] = True
        bad.append(answer)
        answer = copy.deepcopy(correct)
        answer["rows"][1] = answer["rows"][0]
        bad.append(answer)
        answer = copy.deepcopy(correct)
        answer["rows"].pop()
        bad.append(answer)
        answer = copy.deepcopy(correct)
        answer["rows"][0]["value"] = 0
        bad.append(answer)
        answer = copy.deepcopy(correct)
        answer["rows"][0]["assignment"]["P"] = 0
        bad.append(answer)
        bad.extend([None, {"variables": ["P", "Q"], "rows": "malicious"}])
        for answer in bad:
            with self.subTest(answer=answer):
                validation = self.backend.validate("truth-table-completions", instance, answer)
                self.assertTrue(validation["evaluated"])
                self.assertFalse(validation["success"])

    def test_expression_invalid_and_bounded(self):
        for expression in ["", "P AND", "(P", "P Q", "P)", "__import__('os')",
                           "P; print(1)", "P + Q", "AND P"]:
            with self.subTest(expression=expression):
                self.assertEqual(self.backend.run("truth-table-completions",
                                                  {"expression": expression})["status"],
                                 "invalid_input")
        for expression in [" OR ".join("P" + str(i) for i in range(9)),
                           "(" * 40 + "P" + ")" * 40, "P" * 1025,
                           " AND ".join(["P"] * 150), " OR ".join(["P"] * 40)]:
            self.assertEqual(self.backend.execute("truth-table-completions",
                                                  {"expression": expression})["status"],
                             "unsupported")
        for variables in [["P", "P"], ["Q"], [1], "P"]:
            self.assertEqual(self.backend.execute("truth-table-completions",
                                                  {"expression": "P", "variables": variables})["status"],
                             "invalid_input")

    def test_syllogism_deduction_negatives_and_no_existential_import(self):
        cases = [
            ([statement("all", "men", "mortal"), statement("is", "socrates", "men")],
             statement("is", "socrates", "mortal"), (True, False, True)),
            ([statement("all", "men", "mortal")],
             statement("some", "men", "mortal"), (False, False, True)),
            ([statement("no", "cats", "dogs"), statement("is", "felix", "cats")],
             statement("is", "felix", "dogs"), (False, True, True)),
            ([statement("some_not", "cats", "dogs")],
             statement("all", "cats", "dogs"), (False, True, True)),
            ([statement("some", "cats", "dogs")],
             statement("some", "dogs", "cats"), (True, False, True)),
            ([statement("all", "a", "b"), statement("all", "b", "c")],
             statement("all", "a", "c"), (True, False, True)),
        ]
        for premises, query, expected in cases:
            with self.subTest(query=query):
                result = self.backend.run("syllogism-reasoning",
                                          {"premises": premises, "query": query})
                self.assertTrue(result["success"])
                self.assertEqual(tuple(result["answer"][key] for key in
                                       ("entailed", "contradicted", "consistent")), expected)

    def test_four_predicates_two_constants_and_independent_checker(self):
        instance = {
            "premises": [statement("all", "a", "b"), statement("all", "b", "c"),
                         statement("all", "c", "d"), statement("is", "x", "a"),
                         statement("is_not", "y", "d")],
            "query": statement("is", "x", "d"),
        }
        result = self.backend.run("syllogism-reasoning", instance)
        self.assertTrue(result["success"])
        self.assertTrue(result["answer"]["entailed"])
        with patch("opencog.reasoning._solve_syllogism", side_effect=AssertionError("must not solve")):
            self.assertTrue(self.backend.validate("syllogism-reasoning", instance,
                                                 result["answer"])["success"])

    def test_inconsistent_premises_do_not_explode(self):
        for premises in [
                [statement("is", "x", "a"), statement("is_not", "x", "a")],
                [statement("no", "a", "b"), statement("some", "a", "b")]]:
            result = self.backend.run("syllogism-reasoning",
                                      {"premises": premises, "query": statement("all", "a", "b")})
            self.assertTrue(result["success"])
            self.assertEqual(result["answer"], {"consistent": False, "entailed": False,
                                              "contradicted": False})

    def test_syllogism_solver_checker_agreement(self):
        statements = [statement(kind, subject, predicate)
                      for kind in ("all", "no", "some", "some_not")
                      for subject, predicate in itertools.product(("a", "b"), repeat=2)]
        statements += [statement(kind, "x", predicate)
                       for kind in ("is", "is_not") for predicate in ("a", "b")]
        for index in range(0, len(statements), 2):
            for query in statements:
                result = self.backend.run("syllogism-reasoning",
                                          {"premises": statements[index:index + 2], "query": query})
                self.assertTrue(result["success"], result)

    def test_syllogism_bad_answers_input_and_bounds(self):
        instance = {"premises": [], "query": statement("all", "a", "b")}
        for answer in [None, {"entailed": True}, {"entailed": 0, "contradicted": False,
                                                "consistent": True},
                       {"entailed": True, "contradicted": False, "consistent": True}]:
            self.assertFalse(self.backend.validate("syllogism-reasoning", instance, answer)["success"])
        self.assertEqual(self.backend.execute("syllogism-reasoning",
                                              {"premises": "text", "query": instance["query"]})["status"],
                         "invalid_input")
        self.assertEqual(self.backend.execute("syllogism-reasoning",
                                              {"premises": [statement("all", "p" + str(i), "q")
                                                            for i in range(5)],
                                               "query": instance["query"]})["status"], "unsupported")
        self.assertEqual(self.backend.execute("syllogism-reasoning",
                                              {"premises": [statement("is", "x" + str(i), "a")
                                                            for i in range(3)],
                                               "query": instance["query"]})["status"], "unsupported")

    def test_hanoi_replay_and_bounds(self):
        for disks in (1, 3, 10):
            result = self.backend.run("towers-of-hanoi", {"disks": disks})
            self.assertTrue(result["success"])
            self.assertEqual(len(result["answer"]["moves"]), (1 << disks) - 1)
        instance = {"disks": 3, "source": "left", "target": "right", "auxiliary": "middle"}
        correct = self.backend.run("towers-of-hanoi", instance)
        self.assertTrue(correct["success"])
        bad = copy.deepcopy(correct["answer"])
        bad["moves"][0] = {"from": "middle", "to": "right"}
        self.assertFalse(self.backend.validate("towers-of-hanoi", instance, bad)["success"])
        wrong_goal = self.backend.execute("towers-of-hanoi",
                                          dict(instance, target="middle", auxiliary="right"))["answer"]
        self.assertFalse(self.backend.validate("towers-of-hanoi", instance, wrong_goal)["success"])
        larger_on_smaller = copy.deepcopy(correct["answer"])
        larger_on_smaller["moves"][1] = {"from": "left", "to": "right"}
        self.assertFalse(self.backend.validate("towers-of-hanoi", instance,
                                              larger_on_smaller)["success"])
        for disks in (0, -1, True, 1.0, "3"):
            self.assertEqual(self.backend.execute("towers-of-hanoi", {"disks": disks})["status"],
                             "invalid_input")
        self.assertEqual(self.backend.execute("towers-of-hanoi", {"disks": 11})["status"], "unsupported")
        self.assertEqual(self.backend.execute("towers-of-hanoi",
                                              {"disks": 3, "source": "A", "target": "A"})["status"],
                         "invalid_input")

    def test_stack_replay(self):
        for steps in ([], ["one", "two", "one"]):
            result = self.backend.run("stack-based-reasoning", {"steps": steps})
            self.assertTrue(result["success"])
            self.assertEqual(result["answer"]["pop_order"], steps[::-1])
        for answer in [{"pop_order": ["one", "two"]}, {"pop_order": ["two"]},
                       {"pop_order": ["two", "one", "extra"]}, {"pop_order": [1]}]:
            self.assertFalse(self.backend.validate("stack-based-reasoning",
                                                  {"steps": ["one", "two"]}, answer)["success"])
        self.assertEqual(self.backend.execute("stack-based-reasoning", {"steps": [1]})["status"],
                         "invalid_input")
        self.assertEqual(self.backend.execute("stack-based-reasoning", {"steps": ["x"] * 1025})["status"],
                         "unsupported")

    def test_unsupported_and_unstructured_instances(self):
        for task_id in ("ethical-dilemma-resolution", "learning", None, []):
            result = self.backend.run(task_id, {"description": "pretend success"})
            self.assertEqual(result["status"], "unsupported")
            self.assertFalse(result["success"])
            self.assertEqual(result["validation"]["validation_status"], "unsupported")
            self.assertFalse(result["validation"]["evaluated"])
        for instance in ("P OR Q", None, {"task_description": "P OR Q"}):
            result = self.backend.run("truth-table-completions", instance)
            self.assertEqual(result["status"], "invalid_input")
            self.assertFalse(result["success"])

    def test_execution_and_validation_fail_independently_without_false_success(self):
        instance = {"expression": "P"}
        with patch("opencog.reasoning._execute_boolean", return_value=True):
            result = self.backend.run("truth-table-completions", instance)
            self.assertEqual(result["status"], "completed")
            self.assertFalse(result["success"])
            self.assertEqual(result["validation"]["validation_status"], "failed")
        with patch("opencog.reasoning._execute_boolean", side_effect=RuntimeError("failure")):
            with patch.object(self.backend, "validate", side_effect=AssertionError("must not evaluate")):
                result = self.backend.run("truth-table-completions", instance)
            self.assertEqual(result["status"], "error")
            self.assertFalse(result["success"])
            self.assertFalse(result["validation"]["evaluated"])
        with patch("opencog.reasoning._check_boolean", side_effect=RuntimeError("failure")):
            result = self.backend.run("truth-table-completions", instance)
            self.assertEqual(result["status"], "completed")
            self.assertFalse(result["success"])
            self.assertFalse(result["validation"]["evaluated"])

    def test_none_and_unknown_tasks_keep_standard_result_keys(self):
        execution_keys = {"status", "answer", "evidence", "confidence", "resource_usage", "errors"}
        validation_keys = {"validation_status", "evaluated", "success", "quality_score",
                           "evidence", "issues", "evaluator_version"}
        for task_id, instance, status in [
                ("truth-table-completions", None, "invalid_input"),
                ("unsupported-task", None, "unsupported"),
                (None, None, "unsupported"), ([], None, "unsupported")]:
            execution = self.backend.execute(task_id, instance)
            validation = self.backend.validate(task_id, instance, None)
            result = self.backend.run(task_id, instance)
            self.assertEqual(set(execution), execution_keys)
            self.assertEqual(set(validation), validation_keys)
            self.assertEqual(execution["status"], status)
            self.assertEqual(validation["validation_status"], status)
            self.assertFalse(result["success"])
            self.assertFalse(result["validation"]["evaluated"])


if __name__ == "__main__":
    unittest.main()
