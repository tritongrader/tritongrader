import os
import time
import traceback
import binascii
import logging
import subprocess
import threading

from typing import Callable, Optional, Tuple

from tritongrader.utils import run, get_countable_unit_string
from tritongrader.rubric import Rubric

logger = logging.getLogger("tritongrader.test_case")


class TestCaseResultBase:
	"""
	running_time: in seconds
	"""

	def __init__(self):
		self.score: int = 0
		self.passed: bool = False
		self.timed_out: bool = False
		self.error: bool = False
		self.running_time: float = None
		self.has_run: bool = False


class TestCaseBase:
	DEFAULT_TIMEOUT: float = 1

	def __init__(
		self,
		name: str = "Test Case",
		point_value: float = 1,
		timeout: float = DEFAULT_TIMEOUT,
		hidden: bool = False,
	):
		self.name: str = name
		self.point_value: float = point_value
		self.timeout: float = timeout
		self.hidden: bool = hidden

	def execute(self):
		raise NotImplementedError

	def add_to_rubric(self, rubric: Rubric, verbose=True):
		raise NotImplementedError


class IOTestCaseResult(TestCaseResultBase):

	def __init__(self):
		super().__init__()
		self.retcode: str = None
		self.stderr: str = ""
		self.stdout: str = ""
		self.stdout_binary: bytes = b""
		self.stderr_binary: bytes = b""


class IOTestCase(TestCaseBase):

	def __init__(
		self,
		command_path: str,
		input_path: str,
		exp_stdout_path: str,
		exp_stderr_path: str,
		name: str = "Test Case",
		point_value: float = 1,
		timeout: float = TestCaseBase.DEFAULT_TIMEOUT,
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

		self.result: IOTestCaseResult = IOTestCaseResult()

	def __str__(self):
		return (f"{self.name} arm={self.arm} cmd_path={self.command_path} cmd={self.command} " +
			f"input_path={self.input_path} exp_stdout_path={self.exp_stdout_path} exp_stderr_path={self.exp_stderr_path}"
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

	def check_stdout(self):
		with open(self.exp_stdout_path, self.open_mode()) as exp_stdout_fp:
			if self.binary_io:
				self.exp_stdout_binary = exp_stdout_fp.read()
				return self.exp_stdout_binary == self.result.stdout_binary
			else:
				self.exp_stdout = exp_stdout_fp.read()
				return self.exp_stdout == self.result.stdout

	def check_stderr(self):
		with open(self.exp_stderr_path, self.open_mode()) as exp_stderr_fp:
			if self.binary_io:
				self.exp_stderr_binary = exp_stderr_fp.read()
				return self.exp_stderr_binary == self.result.stderr_binary
			else:
				self.exp_stderr = exp_stderr_fp.read()
				return self.exp_stderr == self.result.stderr

	def get_execute_command(self):
		self.command = self.extract_command_from_bash_file(self.command_path)
		self.read_test_input(self.input_path)
		# if running in an ARM simulator, we cannot use the bash script
		# and must instead use the command inside directly.
		exe = self.command if self.arm else self.command_path
		if self.input_path:
			exe += f" < {self.input_path}"
		return exe

	def execute(self):
		# reset states
		self.result = IOTestCaseResult()

		# run test case
		self.result.has_run = True
		try:
			exe_cmd = self.get_execute_command()
			logger.info(
				f"Running test case {str(self)} with command \"{exe_cmd}\" and timeout of {self.timeout}s"
			)
			start_ts = time.time()
			test = run(
				exe_cmd,
				capture_output=True,
				print_command=True,
				text=(not self.binary_io),
				timeout=self.timeout,
				arm=self.arm,
			)
			end_ts = time.time()
			self.result.running_time = end_ts - start_ts
			self.result.retcode = ("EXIT_SUCCESS" if test.returncode == 0 else "EXIT_FAILURE")
			if self.binary_io:
				self.result.stderr_binary = test.stderr
				self.result.stdout_binary = test.stdout
			else:
				self.result.stderr = test.stderr
				self.result.stdout = test.stdout
			stderr_ok = self.check_stderr()
			stdout_ok = self.check_stdout()
			# Do not directly AND the two check_stdXXX method calls because file read might be skipped!
			self.result.passed = stderr_ok and stdout_ok
			self.result.score = self.point_value if self.result.passed else 0
		except subprocess.TimeoutExpired:
			logger.info(f"{self.name} timed out (limit={self.timeout}s)!")
			self.result.timed_out = True
		except Exception as e:
			logger.info(f"{self.name} raised unexpected exception!\n{str(e)}")
			traceback.print_exc()
			self.result.error = True

	def add_to_rubric(self, rubric: Rubric, verbose=False):
		rubric.add_item(
			name=self.name,
			score=self.result.score,
			max_score=self.point_value,
			output=self.generate_test_summary(verbose),
			passed=self.result.passed,
			hidden=self.hidden,
			running_time=self.result.running_time,
		)

	def get_point_value_string(self):
		return get_countable_unit_string(self.point_value, "point")

	def _generate_summary(self, verbose=False):
		if not self.result.has_run:
			return "This test was not run."
		if self.result.error:
			return "The test case experienced an unexpected runtime error!"
		if self.result.timed_out:
			return (f"The test case didn't finish within {self.timeout} s.  " +
				"Please check your code for infinite loops.")

		# If this test has binary IO, then we need to convert the
		# binary input/output/expected values into readable strings
		# for readability on Gradescope.
		if self.binary_io:
			self.stringify_binary_io()

		status_str = "PASSED" if self.result.passed else "FAILED"
		summary = f"{status_str} in {self.result.running_time:.2f} s."
		if verbose or not self.result.passed:
			summary += (f"\n==Test command==\n{self.command}\n" +
				f"==Test input==\n{self.input}\n" + f"Return value: {self.result.retcode}\n" +
				f"==EXPECTED STDOUT==\n{self.exp_stdout}\n" +
				f"==EXPECTED STDERR==\n{self.exp_stderr}")
		if not self.result.passed:
			summary += (f"\n==YOUR STDOUT==\n{self.result.stdout}\n" +
				f"==YOUR STDERR==\n{self.result.stderr}\n")

		return summary

	def generate_test_summary(self, verbose=False):
		return self._generate_summary(verbose)


class CustomTestCaseResult(TestCaseResultBase):

	def __init__(self):
		super().__init__()
		self.output: str = ""


class CustomTestCase(TestCaseBase):

	def __init__(
		self,
		func: Callable[[CustomTestCaseResult], None],
		name: str = "Test Case",
		point_value: float = 1,
		timeout: float = TestCaseBase.DEFAULT_TIMEOUT,
		hidden: bool = False,
	):
		super().__init__(name, point_value, timeout, hidden)
		self.test_func: Callable[[CustomTestCaseResult], bool] = func

	def execute(self):
		self.result = CustomTestCaseResult()
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
			running_time=self.result.running_time,
		)


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
		default_timeout: float = 1,
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
		self.default_timeout = default_timeout
		self.binary_io = binary_io

	def add(
		self,
		name: str,
		point_value: float = 1,
		hidden: bool = False,
		timeout: float = None,
		binary_io: bool = False,
		prefix: str = "",
		no_prefix: bool = False,
	) -> "IOTestCaseBulkLoader":
		if timeout is None:
			timeout = self.default_timeout

		cmd = os.path.join(self.commands_path, self.commands_prefix + name)
		stdin = os.path.join(self.test_input_path, self.test_input_prefix + name)
		stdout = os.path.join(self.expected_stdout_path, self.expected_stdout_prefix + name)
		stderr = os.path.join(self.expected_stderr_path, self.expected_stderr_prefix + name)

		test_case = IOTestCase(
			name=name if no_prefix else self.prefix + prefix + name,
			point_value=point_value,
			command_path=cmd,
			input_path=stdin,
			exp_stdout_path=stdout,
			exp_stderr_path=stderr,
			timeout=timeout,
			binary_io=binary_io,
			hidden=hidden,
			arm=self.autograder.arm,
		)

		self.autograder.add_test(test_case)

		return self

	def add_list(self,
		test_list: Tuple[str, float],
		prefix: str = "",
		hidden: bool = False,
		timeout: float = None,
		binary_io: bool = False):
		for name, point_value in test_list:
			self.add(name, point_value, hidden, timeout, binary_io, prefix=prefix)

		return self
