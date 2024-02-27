from typing import Dict, Callable, List, Union, Iterable
from tritongrader import Autograder

from tritongrader.test_case import TestCaseBase
from tritongrader.test_case import IOTestCase
from tritongrader.test_case import BasicTestCase
from tritongrader.test_case import CustomTestCase


class ResultsFormatterBase:
    def __init__(self, src: Union[Autograder, Iterable[Autograder]]):
        self.formatters: Dict[TestCaseBase, Callable[[TestCaseBase], None]] = {
            IOTestCase: self.format_io_test,
            BasicTestCase: self.format_basic_test,
            CustomTestCase: self.format_custom_test,
        }
        self.test_cases: List[TestCaseBase] = []
        ags = [src,] if isinstance(src, Autograder) else src
        for autograder in ags:
            self.test_cases.extend(autograder.test_cases)

    def format_io_test(self, test: IOTestCase):
        raise NotImplementedError

    def format_basic_test(self, test: BasicTestCase):
        raise NotImplementedError

    def format_custom_test(self, test: CustomTestCase):
        raise NotImplementedError

    def format_test(self, test: TestCaseBase):
        return self.formatters[type(test)](test)

    def execute(self):
        raise NotImplementedError


class GradescopeResultsFormatter(ResultsFormatterBase):
    def __init__(
        self,
        src: Union[Autograder, Iterable[Autograder]],
        message: str = "",
        visibility: str = "visible",
        stdout_visibility: str = "hidden",
        hidden_tests_setting: str = "hidden",
        hide_points: bool = False,
    ):
        super().__init__(src)
        self.message = message
        self.visibility: str = visibility
        self.stdout_visibility: str = stdout_visibility
        self.hidden_tests_setting: str = hidden_tests_setting
        self.hide_points: bool = hide_points

        self.rubric = {
            "output": self.message,
            "visibility": self.visibility,
            "stdout_visibility": self.stdout_visibility,
        }

    def format_io_test(self, test: IOTestCase):
        return {
            "output": "gradescope: format_io_test",
            "input": "gradescope: format_io_test",
        }

    def format_basic_test(self, result: BasicTestCase):
        return {"output": "gradescope: format_basic_test"}

    def format_custom_test(self, result: CustomTestCase):
        return {"output": "gradescope: format_custom_test"}

    def format_test(self, test: TestCaseBase):
        item = {
            "name": test.name,
            "visibility": "visible" if not test.hidden else self.hidden_tests_setting,
        }
        if not self.hide_points:
            item["score"] = test.result.score
        if test.point_value is not None:
            item["max_score"] = test.point_value
        if test.result.passed is not None:
            item["status"] = test.result.passed

        item.update(super().format_test(test))
        return item

    def get_total_score(self):
        return sum(i.result.score for i in self.test_cases)

    def execute(self):
        self.rubric.update(
            {
                "score": self.get_total_score(),
                "tests": [self.format_test(i) for i in self.test_cases],
            }
        )
        if self.hide_points:
            self.rubric["score"] = 0
        return self.rubric


if __name__ == "__main__":
    formatter = GradescopeResultsFormatter()
    formatter.formatters[IOTestCase](None)
