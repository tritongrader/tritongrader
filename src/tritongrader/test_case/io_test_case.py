import os
import time
import traceback
import binascii
import logging
import subprocess

from typing import Optional, Tuple

from tritongrader.test_case.test_case_base import TestCaseBase, TestResultBase
from tritongrader.utils import run, get_countable_unit_string
from tritongrader.runner import CommandRunner

logger = logging.getLogger("tritongrader.test_case.io_test_case")


class IOTestResult(TestResultBase):
    def __init__(self):
        super().__init__()
        self.retcode: str = None
        self.stderr: str = ""
        self.stdout: str = ""


class IOTestCase(TestCaseBase):
    def __init__(
        self,
        command_path: str,
        input_path: str,
        exp_stdout_path: str,
        exp_stderr_path: str,
        name: str = "Test Case",
        point_value: float = 1,
        timeout: float = TestCaseBase.DEFAULT_TIMEOUT_SECS,
        arm: bool = True,
        binary_io: bool = False,
        hidden: bool = False,
    ):
        super().__init__(name, point_value, timeout, hidden)

        self.arm: bool = arm
        self.binary_io: bool = binary_io

        self.command_path: str = command_path
        self.command: str = ""

        self.input_path: str = input_path if os.path.exists(input_path) else None
        self.input: str = ""
        self.input_binary: bytes = b""

        self.exp_stdout_path: str = exp_stdout_path
        self.exp_stdout: str = ""
        self.exp_stdout_binary: bytes = b""

        self.exp_stderr_path: str = exp_stderr_path
        self.exp_stderr: str = ""
        self.exp_stderr_binary: bytes = b""

        self.result: IOTestResult = IOTestResult()
        self.runner: CommandRunner = None

    def __str__(self):
        return (
            f"{self.name} arm={self.arm} cmd_path={self.command_path} cmd={self.command} "
            + f"input_path={self.input_path} exp_stdout_path={self.exp_stdout_path} exp_stderr_path={self.exp_stderr_path}"
        )

    def open_mode(self):
        return "r" if not self.binary_io else "rb"

    def extract_command_from_bash_file(self, bash_file_path):
        # Command files cannot be binary. Can use "r" mode directly here.
        with open(bash_file_path, "r") as cmd_fp:
            test_command = cmd_fp.read().split("\n")[1]
        return test_command

    @staticmethod
    def bin2text(binary: bytes):
        """Attempt to convert binary I/O products to Unicode. Fallback to hexdumps."""
        try:
            return binary.decode()
        except Exception:
            return binascii.hexlify(binary, " ", -2).decode()

    def stringify_binary_io(self):
        self.input = self.bin2text(self.input_binary)
        self.result.stdout = self.bin2text(self.result.stdout_binary)
        self.result.stderr = self.bin2text(self.result.stderr_binary)
        self.exp_stdout = self.bin2text(self.exp_stdout_binary)
        self.exp_stderr = self.bin2text(self.exp_stderr_binary)

    def read_test_input(self, input_file_path):
        if not input_file_path:
            return
        with open(input_file_path, self.open_mode()) as in_fp:
            if self.binary_io:
                self.input_binary = in_fp.read()
            else:
                self.input = in_fp.read()
        return self.input
    
    def check_output(self):
        if not self.runner:
            return False
        stdout_check = self.runner.check_stdout(self.exp_stdout_path)
        stderr_check = self.runner.check_stderr(self.exp_stderr_path)
        return stdout_check and stderr_check

    def get_execute_command(self):
        self.command = self.extract_command_from_bash_file(self.command_path)
        self.read_test_input(self.input_path)
        logger.info(f"Running {str(self)}")
        # if running in an ARM simulator, we cannot use the bash script
        # and must instead use the command inside directly.
        exe = self.command if self.arm else self.command_path
        if self.input_path:
            exe += f" < {self.input_path}"
        return exe
    
    def execute(self):
        # reset states
        self.result = IOTestResult()

        # run test case
        self.result.has_run = True
        try:
            self.runner = CommandRunner(
                command=self.get_execute_command(),
                capture_output=True,
                text=(not self.binary_io),
                timeout_ms=self.timeout,
                arm=self.arm
            )
            self.runner.run()
            self.result.passed = self.check_output()
            self.result.score = self.point_value if self.result.passed else 0
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
            max_score=self.point_value,
            output=self.generate_test_summary(verbose),
            passed=self.result.passed,
            hidden=self.hidden,
            running_time_ms=self.result.running_time_ms,
        )

    def get_point_value_string(self):
        return get_countable_unit_string(self.point_value, "point")

    def _generate_summary(self, verbose=False):
        if not self.result.has_run:
            return "This test was not run."
        if self.result.error:
            return "The test case experienced an unexpected runtime error!"
        if self.result.timed_out:
            return (
                f"The test case timed out. (limit={self.timeout} ms)."
                + "Please check your code for infinite loops."
            )

        # If this test has binary IO, then we need to convert the
        # binary input/output/expected values into readable strings
        # for readability on Gradescope.
        if self.binary_io:
            self.stringify_binary_io()

        status_str = "PASSED" if self.result.passed else "FAILED"
        summary = f"{status_str} in {self.runner.running_time_ms:.2f} ms."
        if verbose or not self.result.passed:
            summary += (
                f"\n==Test command==\n{self.command}\n"
                + f"==Test input==\n{self.input}\n"
                + f"Return value: {self.result.retcode}\n"
                + f"==EXPECTED STDOUT==\n{self.exp_stdout}\n"
                + f"==EXPECTED STDERR==\n{self.exp_stderr}"
            )
        if not self.result.passed:
            summary += (
                f"\n==YOUR STDOUT==\n{self.result.stdout}\n"
                + f"==YOUR STDERR==\n{self.result.stderr}\n"
            )

        return summary

    def generate_test_summary(self, verbose=False):
        return self._generate_summary(verbose)


class IOTestCaseBulkLoader:
    def __init__(
        self,
        autograder,
        commands_path: Optional[str],
        test_input_path: Optional[str],
        expected_stdout_path: Optional[str],
        expected_stderr_path: Optional[str],
        commands_prefix: Optional[str] = "cmd-",
        test_input_prefix: Optional[str] = "test-",
        expected_stdout_prefix: Optional[str] = "out-",
        expected_stderr_prefix: Optional[str] = "err-",
        prefix: str = "",
        default_timeout_ms: float = 500,
        binary_io: bool = False,
    ):
        self.autograder = autograder
        self.commands_path = commands_path
        self.test_input_path = test_input_path
        self.expected_stdout_path = expected_stdout_path
        self.expected_stderr_path = expected_stderr_path
        self.commands_prefix = commands_prefix
        self.test_input_prefix = test_input_prefix
        self.expected_stdout_prefix = expected_stdout_prefix
        self.expected_stderr_prefix = expected_stderr_prefix
        self.prefix = prefix
        self.default_timeout_ms = default_timeout_ms
        self.binary_io = binary_io

    def add(
        self,
        name: str,
        point_value: float = 1,
        hidden: bool = False,
        timeout_ms: float = None,
        binary_io: bool = False,
        prefix: str = "",
        no_prefix: bool = False,
    ) -> "IOTestCaseBulkLoader":
        if timeout_ms is None:
            timeout_ms = self.default_timeout_ms

        cmd = os.path.join(self.commands_path, self.commands_prefix + name)
        stdin = os.path.join(self.test_input_path, self.test_input_prefix + name)
        stdout = os.path.join(
            self.expected_stdout_path, self.expected_stdout_prefix + name
        )
        stderr = os.path.join(
            self.expected_stderr_path, self.expected_stderr_prefix + name
        )

        test_case = IOTestCase(
            name=name if no_prefix else self.prefix + prefix + name,
            point_value=point_value,
            command_path=cmd,
            input_path=stdin,
            exp_stdout_path=stdout,
            exp_stderr_path=stderr,
            timeout=timeout_ms,
            binary_io=binary_io,
            hidden=hidden,
            arm=self.autograder.arm,
        )

        self.autograder.add_test(test_case)

        return self

    def add_list(
        self,
        test_list: Tuple[str, float],
        prefix: str = "",
        hidden: bool = False,
        timeout_ms: float = None,
        binary_io: bool = False,
    ):
        for name, point_value in test_list:
            self.add(name, point_value, hidden, timeout_ms, binary_io, prefix=prefix)

        return self
