from typing import Dict, Callable
from tritongrader.test_case import TestCaseBase, TestCaseResultBase
from tritongrader.test_case import IOTestCase, IOTestCaseResult
from tritongrader.test_case import BasicTestCase, BasicTestCaseResult
from tritongrader.test_case import CustomTestCase, CustomTestCaseResult


class ResultsFormatterBase:
    pass


class GradescopeResultsFormatter(ResultsFormatterBase):
    formatters: Dict[TestCaseBase, Callable[[TestCaseResultBase], None]] = {}

    def __init__(self):
        pass
