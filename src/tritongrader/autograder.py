import os
import logging
import shutil
import platform

from tempfile import TemporaryDirectory
from typing import Tuple, List, Optional

from tritongrader.utils import run
from tritongrader.test_case import TestCaseBase, IOTestCaseBulkLoader
from tritongrader.rubric import Rubric

logger = logging.getLogger("tritongrader.autograder")


class Autograder:
    """
    The Autograder class defines one autograder that can be applied to parts of
    an assignment that share common source files and build procedure (e.g. Makefile).

    You MUST provide a solution directory in this repo that contains:
        a) all course-supplied files that need to be copied and compiled along with
           student submissions (e.g. Makefiles, header files, etc.)
        b) an in/ directory containing cmdX and testX files for each test case X, where
           cmdX is a bash script describing how to run the executable, and testX contains
           the input that will be provided to the executable via redirect ('<').
        c) an exp/ directory containing errX and outX files for each test case X, where
           errX contains the expected stderr output from test case X, and outX contains
           the expected stdout output.

    For questions and bug reporting, contact Jerry Yu <jiy066@ucsd.edu>
    """

    ARM_COMPILER = "arm-linux-gnueabihf-gcc"

    def __init__(
        self,
        name: str,
        submission_path: str,
        tests_path: str,
        required_files: List[str] = [],
        supplied_files: List[str] = [],
        verbose_rubric: bool = False,
        build_command: str = None,
        compile_points: int = 0,
        arm=True,
    ):
        """Autograder initializer.
        Initializes fields and paths.

        Args:
            name (str, optional): name of this autograder. Defaults to "".
            required_files (List[str], optional): submission files required by this autograder. Defaults to [].
            supplied_files (List[str], optional): files supplied by the autograder solution. Defaults to [].
            solution_dirname (str, optional): directory containing solution files and test files. Defaults to "".
            verbose_rubric (bool, optional): if rubrics should contain verbose descriptions. Defaults to False.
        """
        self.name = name

        self.tests_path = tests_path
        self.submission_path = submission_path

        self.arm = arm
        self.required_files = required_files
        self.supplied_files = supplied_files
        self.verbose_rubric = verbose_rubric
        self.compile_points = compile_points

        self.build_command = build_command
        self.compiled = False

        self.test_cases: List[TestCaseBase] = []

        self.rubric = Rubric(self.name)

        # A sandbox directory where submission and test files will be copied to.
        self.sandbox: TemporaryDirectory = self.create_sandbox_directory()

    def create_sandbox_directory(self) -> str:
        tmpdir = TemporaryDirectory(prefix="Autograder_")
        logger.info(f"Sandbox created at {tmpdir.name}")
        return tmpdir

    def add_test(self, test_case: TestCaseBase):
        self.test_cases.append(test_case)

    def io_tests_bulk_loader(
        self,
        prefix: str = "",
        default_timeout_ms: float = 500,
        binary_io: bool = False,
        commands_path: Optional[str] = None,
        test_input_path: Optional[str] = None,
        expected_stdout_path: Optional[str] = None,
        expected_stderr_path: Optional[str] = None,
        commands_prefix: Optional[str] = "cmd-",
        test_input_prefix: Optional[str] = "test-",
        expected_stdout_prefix: Optional[str] = "out-",
        expected_stderr_prefix: Optional[str] = "err-",
    ) -> IOTestCaseBulkLoader:
        return IOTestCaseBulkLoader(
            self,
            commands_path=(commands_path or os.path.join(self.tests_path, "in")),
            test_input_path=(test_input_path or os.path.join(self.tests_path, "in")),
            expected_stdout_path=(
                expected_stdout_path or os.path.join(self.tests_path, "exp")
            ),
            expected_stderr_path=(
                expected_stderr_path or os.path.join(self.tests_path, "exp")
            ),
            commands_prefix=commands_prefix,
            test_input_prefix=test_input_prefix,
            expected_stdout_prefix=expected_stdout_prefix,
            expected_stderr_prefix=expected_stderr_prefix,
            prefix=prefix,
            default_timeout_ms=default_timeout_ms,
            binary_io=binary_io,
        )

    def check_missing_files(self):
        logger.info("Checking missing files...")
        missing_files = []
        for filename in self.required_files:
            fpath = os.path.join(self.submission_path, filename)
            if not os.path.exists(fpath):
                missing_files.append(filename)
        if not missing_files:
            self.rubric.add_item(
                name="Missing Files Check",
                output="All required files have been located.",
            )
        else:
            self.rubric.add_item(
                name="Missing Files Check",
                output="Missing files:\n" + "\n".join(missing_files),
                passed=False,
            )
        logger.info("Finished checking missing files.")

    def get_default_build_command(self):
        return "make" if not self.arm else f"make CC={self.ARM_COMPILER}"

    def get_build_command(self):
        return (
            self.build_command
            if self.build_command is not None
            else self.get_default_build_command()
        )

    def copy2sandbox(self, src_dir, item):
        path = os.path.realpath(os.path.join(src_dir, item))
        dst = os.path.join(self.sandbox.name, item)
        if os.path.isfile(path):
            shutil.copy2(path, dst)
            logger.info(f"Copied file from {path} to {dst}...")
        elif os.path.isdir(path):
            shutil.copytree(path, dst)
            logger.info(f"Copied directory from {path} to {dst}...")

    def copy_submission_files(self):
        for f in self.required_files:
            self.copy2sandbox(self.submission_path, f)

    def copy_supplied_files(self):
        for f in self.supplied_files:
            self.copy2sandbox(self.tests_path, f)

    def compile_student_code(self) -> int:
        if self.compiled:
            return 0

        logger.info(f"Compiling student code (arm={self.arm})...")

        self.copy_submission_files()
        self.copy_supplied_files()

        os.chdir(self.sandbox.name)

        build_cmd = self.get_build_command()
        logger.debug(f"build_cmd: {build_cmd}")
        compiler_process = run(build_cmd, capture_output=True, text=True)
        compiled = compiler_process.returncode == 0
        if compiled:
            logger.info("Student code compiled successfully.")
            self.compiled = True
        else:
            logger.info(
                "Student code failed to compile "
                + f"(returncode={compiler_process.returncode}):\n"
                + str(compiler_process.stderr)
            )
            self.compiled = False

        # Generate rubric item for compiling
        rubric_title = "Compiling"

        rubric_output = compiler_process.stdout + "\n" + compiler_process.stderr + "\n"

        self.rubric.add_item(
            name=rubric_title,
            score=self.compile_points if self.compiled else 0,
            max_score=self.compile_points if self.compile_points > 0 else None,
            passed=self.compiled if self.compile_points > 0 else None,
            output=rubric_output,
        )

        return compiler_process.returncode

    def execute(self) -> Rubric:
        cwd = os.getcwd()

        logger.info(f"{self.name} starting...")
        logger.debug(platform.uname())
        self.check_missing_files()

        if self.compile_student_code() != 0:
            logger.info(f"Skipping {self.name} test(s) due to failed compilation.")

        logger.info(f"Running {self.name} test(s) in {self.sandbox.name}...")
        os.chdir(self.sandbox.name)
        for test in self.test_cases:
            test.execute()
            test.add_to_rubric(self.rubric, self.verbose_rubric)

        logger.info(f"Finished running {self.name} test(s). Returning to {cwd}")
        os.chdir(cwd)

        return self.rubric
