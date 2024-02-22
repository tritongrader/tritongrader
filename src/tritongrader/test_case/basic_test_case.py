import logging
import subprocess
import time
import traceback

from tritongrader.test_case.test_case_base import TestCaseBase, TestCaseResultBase
from tritongrader.utils import run

logger = logging.getLogger("tritongrader.test_case.basic_test_case")


class BasicTestCaseResult(TestCaseResultBase):
    def __init__(self):
        super().__init__()
        self.retcode: int = None
        self.stderr: str = ""
        self.stdout: str = ""


class BasicTestCase(TestCaseBase):
    """
    A basic test case executes a command and evaluates pass/fail
    based on the return value (retcode).
    """

    def __init__(
        self,
        command: str,
        name: str = "Test Case",
        point_value: float = 1,
        expected_retcode: int = 0,
        timeout: float = TestCaseBase.DEFAULT_TIMEOUT_SECS,
        arm: bool = True,
        binary_io: bool = False,
        hidden: bool = False,
    ):
        super().__init__(name, point_value, timeout, hidden)

        self.arm: bool = arm
        self.binary_io: bool = binary_io

        self.command: str = command
        self.expected_retcode: int = expected_retcode

        self.result: BasicTestCaseResult = None

    def _execute(self):
        self.result.has_run = True
        start_ts = time.time()
        testproc = run(
            self.command,
            capture_output=True,
            print_command=True,
            text=(not self.binary_io),
            timeout=self.timeout,
            arm=self.arm,
        )
        end_ts = time.time()

        self.result.running_time_ms = (end_ts - start_ts) * 1000
        self.result.retcode = testproc.returncode
        self.result.passed = self.result.retcode == self.expected_retcode

        self.result.stdout = testproc.stdout
        self.result.stderr = testproc.stderr
        self.result.score = self.point_value if self.result.passed else 0

    def execute(self):
        self.result = BasicTestCaseResult()

        try:
            self._execute()
        except subprocess.TimeoutExpired:
            logger.info(f"{self.name} timed out (limit={self.timeout}s)!")
            self.result.timed_out = True
        except Exception as e:
            logger.info(f"{self.name} raised unexpected exception!\n{str(e)}")
            traceback.print_exc()
            self.result.error = True

    def add_to_rubric(self, rubric, verbose=False):
        rubric.add_item(
            name=self.name,
            score=self.result.score,
            output=f"returncode={self.result.retcode}\n {self.result.stdout}\n {self.result.stderr}\n",
            max_score=self.point_value,
            passed=self.result.passed,
            hidden=self.hidden,
            running_time_ms=self.result.running_time_ms,
        )
