import os
import json
import logging
from typing import List, Optional

from tritongrader.visibility import GradescopeVisibility

logger = logging.getLogger("tritongrader.rubric")


class RubricItem:

	def __init__(
		self,
		name: str,
		output: str = None,
		input: str = None,
		score: int = 0,
		max_score: Optional[int] = None,
		passed: Optional[bool] = None,
		hidden: bool = False,
		running_time_ms: int = -1,
	):
		self.name: str = name
		self.output: str = output
		self.input: str = input
		self.score: int = score
		self.passed: bool = passed
		self.hidden: bool = hidden
		self.max_score: Optional[int] = max_score
		self.running_time_ms: int = running_time_ms


class Rubric:
	"""
    A Rubric object contains a collection of grading items.
    """

	def __init__(self, name: str):
		self.name: str = name
		self.items: List[RubricItem] = []
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
		hidden: bool = False,
		running_time_ms: int = -1,
	):
		logger.info(
			f"Rubric: {self.name} - Adding rubric item {name} score={score} passed={passed}")
		rubric_item = RubricItem(
			name=f"{self.name}: {name}",
			output=output,
			input=input,
			score=score,
			max_score=max_score,
			passed=passed,
			hidden=hidden,
			running_time_ms=running_time_ms,
		)
		self._add_item(rubric_item)

	def __add__(self, other: 'Rubric'):
		rubric = Rubric(name=self.name + ", " + other.name)
		for ri in self.items + other.items:
			rubric._add_item(ri)
		return rubric


class RubricFormatter:

	def __init__(self, rubric: Rubric):
		self.rubric: Rubric = rubric

	def export(self, filepath=None):
		raise NotImplementedError


class GradescopeRubricFormatter(RubricFormatter):
	"""
    Export rubric contents to a gradescope file.
    See https://gradescope-autograders.readthedocs.io/en/latest/specs/
    """

	DEFAULT_RESULTS_PATH = "/autograder/results/results.json"

	def __init__(
		self,
		rubric,
		message="",
		visibility: GradescopeVisibility = GradescopeVisibility.VISIBLE,
		stdout_visibility: GradescopeVisibility = GradescopeVisibility.HIDDEN,
		hidden_tests_setting: GradescopeVisibility = GradescopeVisibility.HIDDEN,
		hide_points: bool = False,
	):
		super().__init__(rubric)
		self.message = message
		self.visibility: GradescopeVisibility = visibility
		self.stdout_visibility: GradescopeVisibility = stdout_visibility
		self.hidden_tests_setting: GradescopeVisibility = hidden_tests_setting
		self.hide_points: bool = hide_points

	def get_item_visibility_value(self, item: RubricItem) -> GradescopeVisibility:
		if not item.hidden:
			return GradescopeVisibility.VISIBLE.value
		else:
			return self.hidden_tests_setting.value

	def format_item(self, item: RubricItem) -> dict:
		rubric_item = {
			"name": item.name,
			"visibility": self.get_item_visibility_value(item),
		}
		if not self.hide_points:
			rubric_item["score"] = item.score
		if item.passed is not None:
			rubric_item["status"] = "passed" if item.passed else "failed"
		if item.output is not None:
			rubric_item["output"] = item.output
		if item.input is not None:
			rubric_item["input"] = item.input
		if not self.hide_points and item.max_score is not None:
			rubric_item["max_score"] = item.max_score

		return rubric_item

	def get_total_score(self):
		return sum(i.score for i in self.rubric.items)

	def get_total_execution_time_ms(self):
		sum = 0
		for item in self.rubric.items:
			if item.running_time_ms:
				sum += item.running_time_ms
		return sum

	def as_dict(self):
		tests = [self.format_item(i) for i in self.rubric.items]
		ret = {
			"score": self.get_total_score(),
			"execution_time": self.get_total_execution_time_ms() / 1000,
			"output": self.message,
			"visibility": self.visibility.value,
			"stdout_visibility": self.stdout_visibility.value,
			"tests": tests,
		}
		if self.hide_points:
			ret["score"] = 0
		return ret

	def export(self, filepath=DEFAULT_RESULTS_PATH):
		filepath = os.path.realpath(filepath)
		logging.info("Exporting gradescope rubric to " + filepath)
		with open(filepath, "w+") as fp:
			json.dump(self.as_dict(), fp, indent=2)


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
