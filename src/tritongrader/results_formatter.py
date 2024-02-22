from typing import Dict, Callable
from tritongrader.test_case import TestCaseBase, TestCaseResultBase
from tritongrader.test_case import IOTestCase, IOTestCaseResult
from tritongrader.test_case import BasicTestCase, BasicTestCaseResult
from tritongrader.test_case import CustomTestCase, CustomTestCaseResult


class ResultsFormatterBase:
    def __init__(self):
        self.formatters: Dict[TestCaseBase, Callable[[TestCaseResultBase], None]] = {
            IOTestCase, self.format_io_test,
            BasicTestCase, self.format_basic_test,
            CustomTestCase, self.format_custom_test,
        }

    def format_io_test(self, result: IOTestCaseResult):
        raise NotImplementedError
    
    def format_basic_test(self, result: BasicTestCaseResult):
        raise NotImplementedError

    def format_custom_test(self, result: CustomTestCaseResult):
        raise NotImplementedError


class GradescopeResultsFormatter(ResultsFormatterBase):

    def __init__(self):
        pass
