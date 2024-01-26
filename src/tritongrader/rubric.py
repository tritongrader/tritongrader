import os
import json
import logging
from typing import List, Optional

logger = logging.getLogger("tritongrader.rubric")

# TODO: Separate Rubric interface from specific output formats


class RubricItem:
    def __init__(
        self,
        name: str,
        output: str = None,
        input: str = None,
        score: int = 0,
        max_score: Optional[int] = None,
        passed: Optional[bool] = None,
        # TODO: need to decouple visibility from rubric items as much
        # as possible. While each test should still be defined as
        # hidden or public, there should not be any additional
        # complexitiy here beyond that.
        visibility: str = "visible",
    ):
        assert visibility in [
            Rubric.VIS_VISIBLE,
            Rubric.VIS_AFT_DUE,
            Rubric.VIS_AFT_PUBLISH,
            Rubric.VIS_HIDDEN,
        ]
        self.name: str = name
        self.output: str = output
        self.input: str = input
        self.score: int = score
        self.passed: bool = passed
        self.visibility: str = visibility
        self.max_score: Optional[int] = max_score

    def as_dict(self):
        rubric_item = {
            "name": self.name,
            "score": self.score,
            "visibility": self.visibility,
        }
        if self.passed is not None:
            rubric_item["status"] = "passed" if self.passed else "failed"
        if self.output is not None:
            rubric_item["output"] = self.output
        if self.input is not None:
            rubric_item["input"] = self.input
        if self.max_score is not None:
            rubric_item["max_score"] = self.max_score
        return rubric_item


class Rubric:
    VIS_VISIBLE = "visible"
    VIS_HIDDEN = "hidden"
    VIS_AFT_DUE = "after_due_date"
    VIS_AFT_PUBLISH = "after_published"

    def __init__(self, name: str, hide_scores=False):
        self.name: str = name
        self.items: List[RubricItem] = []
        self.hide_scores = hide_scores
        self._score_for_logging = 0

    def _add_item(self, item: RubricItem):
        self.items.append(item)
        self._score_for_logging += item.score

    def add_item(
        self,
        name: str,
        output: str = "",
        input: str = "",
        score: int = 0,
        max_score: Optional[int] = None,
        passed: Optional[bool] = None,
        visibility: str = VIS_VISIBLE,
    ):
        logger.info(
            f"Rubric: {self.name} - Adding rubric item {name} score={score} passed={passed}"
        )
        rubric_item = RubricItem(
            name=f"{self.name}: {name}",
            output=output,
            input=input,
            score=score if not self.hide_scores else 0,
            max_score=max_score,
            passed=passed,
            visibility=visibility,
        )
        self._add_item(rubric_item)

    def export(self):
        logger.info(f"Rubric: {self.name} - Total score: {self._score_for_logging}")
        return [ri.as_dict() for ri in self.items]

    def __add__(self, other):
        rubric = Rubric(name=self.name + ", " + other.name)
        for ri in self.items + other.rubric_items:
            rubric._add_item(ri)


class RubricFormatter:
    def __init__(self, rubric: Rubric):
        self.rubric = rubric

    def export(self, test=False):
        raise NotImplementedError


class GradescopeRubricFormatter(RubricFormatter):
    """
    Export rubric contents to a gradescope file.
    See https://gradescope-autograders.readthedocs.io/en/latest/specs/
    """

    def __init__(self, message="", visibility="visible", stdout_visibility="visible"):
        super().__init__()
        self.message = message
        self.visibility = visibility
        self.stdout_visibility = stdout_visibility

    def format_item(self, item: RubricItem) -> dict:
        rubric_item = {
            "name": item.name,
            "score": item.score,
            "visibility": self.visibility,
        }

        if item.passed is not None:
            rubric_item["status"] = "passed" if item.passed else "failed"
        if item.output is not None:
            rubric_item["output"] = item.output
        if item.input is not None:
            rubric_item["input"] = item.input
        if item.max_score is not None:
            rubric_item["max_score"] = item.max_score

        return rubric_item

    def export(self, test=False):
        results = {
            "score": 0, # TODO
            "execution_time": 0, # TODO
            "output": self.message,
            "visibility": self.visibility,
            "stdout_visibility": self.stdout_visibility,
            "tests": [self.format_item(item) for item in self.rubric.rubric_items()],
        }
        if test:
            print(json.dumps(results, indent=4, sort_keys=True))
        else:
            with open("/autograder/results/results.json", "w+") as fp:
                json.dump(results, fp)


class TextFormatter(RubricFormatter):
    def export(self):
        pass


###############################################################################
#
# Reference: Gradescope output results.json
#
# { "score": 44.0, // optional, but required if not on each test case below. Overrides total of tests if specified.
#   "execution_time": 136, // optional, seconds
#   "output": "Text relevant to the entire submission", // optional
#   "output_format": "simple_format", // Optional output format settings, see "Output String Formatting" below
#   "test_output_format": "text", // Optional default output format for test case outputs, see "Output String Formatting" below
#   "test_name_format": "text", // Optional default output format for test case names, see "Output String Formatting" below
#   "visibility": "after_due_date", // Optional visibility setting
#   "stdout_visibility": "visible", // Optional stdout visibility setting
#   "extra_data": {}, // Optional extra data to be stored
#   "tests": // Optional, but required if no top-level score
#     [
#         {
#             "score": 2.0, // optional, but required if not on top level submission
#             "max_score": 2.0, // optional
#             "status": "passed", // optional, see "Test case status" below
#             "name": "Your name here", // optional
#             "name_format": "text", // optional formatting for the test case name, see "Output String Formatting" below
#             "number": "1.1", // optional (will just be numbered in order of array if no number given)
#             "output": "Giant multiline string that will be placed in a <pre> tag and collapsed by default", // optional
#             "output_format": "text", // optional formatting for the test case output, see "Output String Formatting" below
#             "tags": ["tag1", "tag2", "tag3"], // optional
#             "visibility": "visible", // Optional visibility setting
#             "extra_data": {} // Optional extra data to be stored
#         },
#         // and more test cases...
#     ],
#   "leaderboard": // Optional, will set up leaderboards for these values
#     [
#       {"name": "Accuracy", "value": .926},
#       {"name": "Time", "value": 15.1, "order": "asc"},
#       {"name": "Stars", "value": "*****"}
#     ]
# }
#
###############################################################################
