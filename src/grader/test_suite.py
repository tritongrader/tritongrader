from typing import List, Tuple
from datetime import datetime
from typing import List
import logging

from helper_methods import *
from test_cases import TestCase


class TestSuite:
    DEFAULT_TIMEOUT_MS = 100
    DEFAULT_TIMEOUT_SECS = DEFAULT_TIMEOUT_MS / 1000

    def __init__(
        self,
        in_directory: str,
        command_directory: str,
        expected_directory: str,
        suite_name: str = "",
        hidden: bool = False,
        unhide_time: datetime = None,
        default_timeout_ms: int = DEFAULT_TIMEOUT_MS,
        arm: bool = True,
        binary_io: bool = False,
    ):
        """
        in_directory: path to directory containing input files
        command_directory: path to directory containing command files
        expected_directory: path to directory containing expected stdout and stderr files.
        default_timeout: default timeout in ms for each test case in this suite
        arm: if this test suite should be compiled and run in an ARM environment (qemu)
        """
        self.name: str = suite_name
        self.default_timeout: float = default_timeout_ms / 1000
        self.in_path: str = in_directory
        self.cmd_path: str = command_directory
        self.exp_path: str = expected_directory
        self.arm: bool = arm
        self.binary_io: bool = binary_io
        self.hidden: bool = hidden
        self.unhide_time: datetime = unhide_time
        self.test_cases: List[TestCase] = []

    def create_test_cases_from_list(self, test_list: List[Tuple[str, int]]):
        """
        test_list: a list of (test ids, point value) tuples.
        E.g. [("1", 0.5), ("2", 0.5), ("3", 1), ("A", 2)]
        """
        for test_id, point_value in test_list:
            test_case = TestCase(
                suite=self,
                binary_io=self.binary_io,
                command_path=f"{self.cmd_path}/cmd{test_id}",
                input_path=f"{self.in_path}/test{test_id}",
                exp_stdout_path=f"{self.exp_path}/out{test_id}",
                exp_stderr_path=f"{self.exp_path}/err{test_id}",
                name=f"{self.name} - {test_id}",
                timeout=self.default_timeout,
                arm=self.arm,
                point_value=point_value,
            )
            self.test_cases.append(test_case)

    def is_hidden_suite(self):
        return self.hidden

    def hide_results(self):
        if not self.hidden:
            return False

        if self.unhide_time is None:
            return True
        else:
            return datetime.now(self.unhide_time.tzinfo) < self.unhide_time

    def run_tests(self, executable_directory):
        logging.info(f"Running {self.name} test(s)...")
        os.chdir(executable_directory)
        for test in self.test_cases:
            test.execute()
        logging.info(f"Finished running {self.name} test(s).")

    def generate_suite_summary(self):
        passed = 0
        points = 0
        total_points = 0
        total_tests = len(self.test_cases)
        for t in self.test_cases:
            total_points += t.point_value
            passed += 1 if t.result.passed else 0
            points += t.result.score

        out = f"{self.name}: {passed}/{total_tests} passed, ({points}/{total_points} points)."
        if self.hide_results():
            logging.info(out)
            return f"{self.name}: Results hidden at this time."
        else:
            return out
