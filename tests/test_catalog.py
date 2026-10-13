import importlib.util
import json
from pathlib import Path
import shutil
import unittest
import uuid


ROOT = Path(__file__).resolve().parents[1]
# Keep these stdlib tests independent of the optional workbench dependencies.
SPEC = importlib.util.spec_from_file_location("catalog_under_test", ROOT / "opencog/catalog.py")
catalog = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(catalog)


DEFINITION = """# Sample Task

## Description:

First paragraph.

Second paragraph.

## Modality:

Text only
with multiline instructions

## Examples:

### Example 1:

Input:

```text
## Tags:
### Example 99:
Output:
These are content, not structure.
```

Output:

~~~markdown
# Embedded title
## Description:
Input:
~~~

## Tags:
- Reasoning
- --
"""


class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.scratch = ROOT / ("catalog-test-" + uuid.uuid4().hex)
        self.scratch.mkdir()
        self.addCleanup(shutil.rmtree, self.scratch)

    def write_task(self, text=DEFINITION, name="sample.md"):
        path = self.scratch / name
        path.write_text(text, encoding="utf-8")
        return path

    def test_entire_catalog_is_loaded_without_skips(self):
        tasks, report = catalog.load_catalog(ROOT / "tasks")
        self.assertEqual(report["total_files"], 95)
        self.assertEqual(report["loaded"], 95)
        self.assertEqual(report["skipped"], [])
        self.assertEqual(len({task["id"] for task in tasks}), 95)
        for task in tasks:
            for key in ("name", "description", "modality", "tags", "examples"):
                self.assertTrue(task[key], (task["id"], key))
            self.assertEqual(task["audit_status"], "unreviewed")
            with Path(task["source"]).open(encoding="utf-8", newline="") as handle:
                self.assertEqual(task["raw_content"], handle.read())
            for example in task["examples"]:
                self.assertTrue(example["turns"])
                self.assertEqual(example["parse_status"], "parsed")
                self.assertEqual(example["audit_status"], "unreviewed")
                self.assertFalse(example["provenance"]["verified"])
                self.assertEqual(example["provenance"]["source"], task["source"])

    def test_blank_multiline_fields_and_embedded_fenced_headings(self):
        task = catalog.parse_task_file(self.write_task())
        self.assertEqual(task["description"], "First paragraph.\n\nSecond paragraph.")
        self.assertEqual(task["modality"], "Text only\nwith multiline instructions")
        self.assertEqual(len(task["examples"]), 1)
        example = task["examples"][0]
        self.assertEqual(example["input"],
                         "## Tags:\n### Example 99:\nOutput:\n"
                         "These are content, not structure.")
        self.assertEqual(example["output"], "# Embedded title\n## Description:\nInput:")
        self.assertEqual(task["tags"], ["Reasoning"])
        self.assertTrue(any("garbage tag" in warning for warning in task["warnings"]))

    def test_malformed_required_fields_are_clear_and_explicitly_skipped(self):
        valid = self.write_task()
        for label in ("Description", "Modality", "Tags", "Examples"):
            text = DEFINITION.replace("## " + label + ":", "## Other:")
            malformed = self.write_task(text, label.lower() + ".md")
            with self.assertRaisesRegex(catalog.CatalogParseError, label.lower()):
                catalog.parse_task_file(malformed)
        unnamed = self.write_task(DEFINITION.replace("# Sample Task", ""), "unnamed.md")
        with self.assertRaisesRegex(catalog.CatalogParseError, "name"):
            catalog.parse_task_file(unnamed)
        tasks, report = catalog.load_catalog(self.scratch)
        self.assertEqual([task["source"] for task in tasks], [str(valid)])
        self.assertEqual(report["total_files"], 6)
        self.assertEqual(len(report["skipped"]), 5)
        self.assertTrue(all(item["source"] and item["error"] for item in report["skipped"]))

    def test_missing_and_empty_turns_are_rejected(self):
        for examples in (
            "### Example 1:\nInput: question",
            "### Example 1:\nOutput: answer",
            "### Example 1:\nInput:\nOutput: answer",
            "### Example 1:\nInput: one\nInput: two\nOutput: answer",
            "### Example 1:\nUnparsed\nInput: one\nOutput: answer",
            "not a numbered example",
        ):
            with self.subTest(examples=examples):
                text = "# Test\n## Description:\nTest\n## Modality:\nText only\n"
                text += "## Examples:\n" + examples + "\n## Tags:\n- Test\n"
                with self.assertRaises(catalog.CatalogParseError):
                    catalog.parse_task_file(self.write_task(text))

    def test_latex_all_conversation_and_raw_text_are_preserved(self):
        path = ROOT / "tasks/multiturn-latex-generation.md"
        task = catalog.parse_task_file(path)
        self.assertEqual(task["name"], "Multiturn Latex Generation")
        self.assertIn("Working with various formats", task["description"])
        self.assertEqual(task["raw_content"], path.read_text())
        self.assertEqual([len(example["turns"]) for example in task["examples"]], [3, 1])
        turns = task["examples"][0]["turns"]
        self.assertIn("Sofia Rodriguez", turns[0]["input"])
        self.assertIn("5 million views", turns[1]["input"])
        self.assertEqual(turns[2]["input"], "Yes.")
        self.assertIn("THINKING", turns[1]["output"])
        self.assertIn("\\end{document}", turns[2]["output"])
        self.assertIn("Diagram:", turns[0]["output"])
        self.assertIn("Diagram (Optional):", task["examples"][1]["output"])
        self.assertTrue(any("inferred" in warning for warning in task["warnings"]))

    def test_nonstandard_malformed_conversation_warned_not_silently_parsed(self):
        text = ("**Name: Multiturn Latex Generation**\n**Description:** Test\n"
                "Example(s):\nExample 1:\nUnparsed notes\n"
                "**Input:** one\n**Input:** two\n**Output:** answer\n"
                "Example 2:\nNo labels at all\n## Tags:\n- LaTeX\n")
        task = catalog.parse_task_file(self.write_task(text, "multiturn-latex-generation.md"))
        self.assertEqual(task["raw_content"], text)
        self.assertTrue(any("unparsed text" in warning for warning in task["warnings"]))
        self.assertTrue(any("no Input/Output" in warning for warning in task["warnings"]))
        self.assertTrue(all(example["parse_status"] == "malformed"
                            for example in task["examples"]))
        self.assertEqual(task["examples"][1]["raw_content"], "No labels at all")
        self.assertEqual(task["examples"][1]["turns"], [])
        self.assertEqual(len(task["audit_issues"]), 2)

    def test_multiple_turns_and_extra_metadata(self):
        text = ("# Conversation\n## Description: Description\n## Modality: Text only\n"
                "## Examples:\n### Example 1:\nInput: first\nOutput: answer\n"
                "Input: follow-up\nOutput: final\n## Citations:\nA citation\n"
                "## Diagram:\n![image](diagram.png)\n## Tags:\n- Reasoning\n")
        task = catalog.parse_task_file(self.write_task(text))
        self.assertEqual(task["examples"][0]["turns"],
                         [{"input": "first", "output": "answer"},
                          {"input": "follow-up", "output": "final"}])
        self.assertEqual(task["metadata"]["citations"], "A citation")
        self.assertEqual(task["metadata"]["diagram"], "![image](diagram.png)")

    def test_raw_line_endings_and_longer_fences_are_preserved(self):
        text = ("# Test\r\n## Description:\r\nDescription\r\n## Modality:\r\n"
                "Text only\r\n## Examples:\r\n### Example 1:\r\nInput:\r\n"
                "````markdown\r\n```\r\n## Tags:\r\nOutput:\r\n```\r\n````\r\n"
                "Output: answer\r\n## Tags:\r\n- Test\r\n")
        task = catalog.parse_task_file(self.write_task(text))
        self.assertEqual(task["raw_content"], text)
        self.assertEqual(task["examples"][0]["input"], "```\n## Tags:\nOutput:\n```")
        self.assertEqual(task["examples"][0]["output"], "answer")

    def test_audit_provenance_is_non_ground_truth(self):
        for task_id, code in (
            ("mental-rotation-tasks", "spatial-answer-unverified"),
            ("understanding-time-zones-and-global-time-differences", "timezone-answer-unverified"),
            ("bias-mitigation", "unsupported-bias-correction"),
        ):
            task = catalog.parse_task_file(ROOT / "tasks" / (task_id + ".md"))
            self.assertEqual(task["audit_issues"][0]["code"], code)
            self.assertEqual(task["audit_issues"][0]["severity"], "warning")
            self.assertTrue(task["warnings"])
            self.assertTrue(all(example["audit_status"] == "unreviewed"
                                for example in task["examples"]))

    def test_fence_errors_duplicate_sections_and_invalid_tags(self):
        for text in (
            DEFINITION.replace("~~~\n\n## Tags:", "\n\n## Tags:"),
            DEFINITION + "\n## Tags:\n- Test\n",
            DEFINITION.replace("- Reasoning", "- ---"),
        ):
            with self.assertRaises(catalog.CatalogParseError):
                catalog.parse_task_file(self.write_task(text))
        with self.assertRaises(NotADirectoryError):
            catalog.load_catalog(self.scratch / "absent")

    def test_json_nested_turn_schema_normalization_missing_and_mismatch(self):
        task = catalog.parse_task_file(self.write_task())
        json_dir = self.scratch / "json"
        json_dir.mkdir()
        data = {key: task[key] for key in ("name", "description", "modality", "tags")}
        data["description"] = "First paragraph. Second paragraph."
        data["examples"] = [example["turns"] for example in task["examples"]]
        json_path = json_dir / "sample.json"
        json_path.write_text(json.dumps(data))
        report = catalog.check_json_consistency(self.scratch, json_dir)
        self.assertEqual(report["checked"], 1)
        self.assertEqual(report["mismatches"], [])
        self.assertEqual(report["missing"], [])
        data["examples"][0][0]["output"] = "Changed"
        json_path.write_text(json.dumps(data))
        report = catalog.check_json_consistency(self.scratch, json_dir)
        self.assertEqual(report["mismatches"][0]["fields"], ["examples"])
        json_path.unlink()
        report = catalog.check_json_consistency(self.scratch, json_dir)
        self.assertEqual(report["missing"][0]["json_source"], str(json_path))
        json_path.write_text("not JSON")
        self.assertIn("error", catalog.check_json_consistency(
            self.scratch, json_dir)["mismatches"][0])

    def test_existing_json_consistency_reports_legacy_conversion_loss(self):
        report = catalog.check_json_consistency(ROOT / "tasks", ROOT / "tasks-json")
        self.assertEqual(report["checked"], 95)
        self.assertEqual(report["missing"], [])
        self.assertEqual(len(report["mismatches"]), 1)
        self.assertTrue(report["mismatches"][0]["source"].endswith(
            "multiturn-latex-generation.md"))
        self.assertIn("examples", report["mismatches"][0]["fields"])


if __name__ == "__main__":
    unittest.main()
