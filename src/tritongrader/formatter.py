from typing import Dict, Callable, List

from tritongrader.test_case import TestCaseBase, TestCaseResultBase
from tritongrader.test_case import IOTestCase, IOTestCaseResult
from tritongrader.test_case import BasicTestCase, BasicTestCaseResult
from tritongrader.test_case import CustomTestCase, CustomTestCaseResult


class ResultsFormatterBase:
    def __init__(self):
        self.formatters: Dict[TestCaseBase, Callable[[TestCaseResultBase], None]] = {
            IOTestCase: self.format_io_test,
            BasicTestCase: self.format_basic_test,
            CustomTestCase: self.format_custom_test,
        }

    def format_io_test(self, result: IOTestCaseResult):
        raise NotImplementedError

    def format_basic_test(self, result: BasicTestCaseResult):
        raise NotImplementedError

    def format_custom_test(self, result: CustomTestCaseResult):
        raise NotImplementedError

    def execute(self, results: List[TestCaseResultBase]):
        for result in results:
            self.formatters[type(result)](result)


class GradescopeResultsFormatter(ResultsFormatterBase):
    def __init__(self):
        super().__init__()

    def format_io_test(self, result: IOTestCaseResult):
        print("gradescope: format_io_test")

    def format_basic_test(self, result: BasicTestCaseResult):
        print("gradescope: format_basic_test")

    def format_custom_test(self, result: CustomTestCaseResult):
        print("gradescope: format_custom_test")


if __name__ == "__main__":
    formatter = GradescopeResultsFormatter()
    formatter.formatters[IOTestCase](None)
