import os
import traceback
import logging
import threading

from typing import Callable, Optional, Tuple

from tritongrader.rubric import Rubric
from tritongrader.test_case.test_case_base import TestCaseBase, TestResultBase

logger = logging.getLogger("tritongrader.test_case")

class CustomTestResult(TestResultBase):
    def __init__(self):
        super().__init__()
        self.output: str = ""


class CustomTestCase(TestCaseBase):
    def __init__(
        self,
        func: Callable[[CustomTestResult], None],
        name: str = "Test Case",
        point_value: float = 1,
        timeout: float = TestCaseBase.DEFAULT_TIMEOUT_SECS,
        hidden: bool = False,
    ):
        super().__init__(name, point_value, timeout, hidden)
        self.test_func: Callable[[CustomTestResult], bool] = func

    def execute(self):
        self.result = CustomTestResult()
        self.result.has_run = True

        try:
            t = threading.Thread(
                target=self.test_func,
                args=[self.result],
            )
            t.start()
            t.join(timeout=self.timeout)
            if t.is_alive():
                raise TimeoutError
        except TimeoutError:
            logger.info(f"{self.name} timed out (limit={self.timeout}s)!")
            self.result.timed_out = True
            self.result.passed = False
        except Exception as e:
            logger.warn(f"{self.name} raised unexpected exception!\n{str(e)}")
            traceback.print_exc()
            self.result.error = True

    def add_to_rubric(self, rubric: Rubric, verbose=True):
        rubric.add_item(
            name=self.name,
            score=self.result.score,
            max_score=self.point_value,
            output=self.result.output,
            passed=self.result.passed,
            hidden=self.hidden,
            running_time_ms=self.result.running_time_ms,
        )

