from typing import Dict, Callable, List

from tritongrader.test_case import TestCaseBase, TestResultBase
from tritongrader.test_case import IOTestCase, IOTestResult
from tritongrader.test_case import BasicTestCase, BasicTestResult
from tritongrader.test_case import CustomTestCase, CustomTestResult


class ResultsFormatterBase:
    def __init__(self):
        self.formatters: Dict[TestCaseBase, Callable[[TestResultBase], None]] = {
            IOTestCase: self.format_io_test,
            BasicTestCase: self.format_basic_test,
            CustomTestCase: self.format_custom_test,
        }

    def format_io_test(self, result: IOTestResult):
        raise NotImplementedError

    def format_basic_test(self, result: BasicTestResult):
        raise NotImplementedError

    def format_custom_test(self, result: CustomTestResult):
        raise NotImplementedError

    def execute(self, results: List[TestResultBase]):
        for result in results:
            self.formatters[type(result)](result)


class GradescopeResultsFormatter(ResultsFormatterBase):
    def __init__(self):
        super().__init__()

    def format_io_test(self, result: IOTestResult):
        print("gradescope: format_io_test")

    def format_basic_test(self, result: BasicTestResult):
        print("gradescope: format_basic_test")

    def format_custom_test(self, result: CustomTestResult):
        print("gradescope: format_custom_test")


if __name__ == "__main__":
    formatter = GradescopeResultsFormatter()
    formatter.formatters[IOTestCase](None)
