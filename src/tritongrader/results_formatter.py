from typing import Dict, Callable

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
    
    def export(self):
        raise NotImplementedError


class GradescopeResultsFormatter(ResultsFormatterBase):
    def __init__(
        self,
        html_diff: bool = True,
        hide_score: bool = False,
    ):
        ResultsFormatterBase.__init__(self)
        self.html_diff: bool = html_diff
        self.hide_score: bool = hide_score
    
    def format_io_test(self, result: IOTestCaseResult):
        pass

    def format_basic_test(self, result: BasicTestCaseResult):
        pass

    def format_custom_test(self, result: CustomTestCaseResult):
        pass

    def export(self):
        pass
        