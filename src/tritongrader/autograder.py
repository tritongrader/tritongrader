import os
import logging
import shutil
import platform

from tempfile import TemporaryDirectory
from typing import Tuple, List

from tritongrader.utils import run
from tritongrader.test_case import TestCase
from tritongrader.rubric import Rubric
from tritongrader.visibility import Visibility

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
        hide_scores: bool = True,
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
            hide_scores (bool, optional): if final scores should be hidden. Defaults to True.
            required_files (List[str], optional): submission files required by this autograder. Defaults to [].
            supplied_files (List[str], optional): files supplied by the autograder solution. Defaults to [].
            solution_dirname (str, optional): directory containing solution files and test files. Defaults to "".
            verbose_rubric (bool, optional): if rubrics should contain verbose descriptions. Defaults to False.
        """
        self.name = name

        self.arm = arm
        self.hide_scores = hide_scores
        self.required_files = required_files
        self.supplied_files = supplied_files
        self.verbose_rubric = verbose_rubric
        self.compile_points = compile_points

        self.build_command = build_command
        self.compiled = False

        self.test_cases: List[TestCase] = []

        self.rubric = Rubric(self.name, self.hide_scores)

        #
        # set up paths
        #

        # path to solution directory as specified in docstring
        self.tests_path = tests_path
        # path to the in/ directory containing cmdX and testX files.
        self.tests_in_path = f"{self.tests_path}/in"
        # path to the exp/ directory containing errX and outX files.
        self.tests_exp_path = f"{self.tests_path}/exp"
        # path to the directory containing student submission files.
        self.submission_path = submission_path
        # Copy submission files to separate sandbox folder for testing
        self.sandbox: TemporaryDirectory = self.create_sandbox_directory(
            self.submission_path
        )

    def create_sandbox_directory(self, submission_path: str) -> str:
        tmpdir = TemporaryDirectory(prefix="Autograder_")
        logger.info(f"Sandbox created at {tmpdir.name}")
        shutil.copytree(submission_path, tmpdir.name, dirs_exist_ok=True)
        return tmpdir

    def _add_tests(
        self,
        test_list: List[Tuple[str, int]],
        prefix="",
        default_timeout_ms=500,
        binary_io=False,
        visibility: Visibility = Visibility.VISIBLE,
    ):
        for test_id, point_value in test_list:
            test_case = TestCase(
                command_path=f"{self.tests_in_path}/cmd{test_id}",
                input_path=f"{self.tests_in_path}/test{test_id}",
                exp_stdout_path=f"{self.tests_exp_path}/out{test_id}",
                exp_stderr_path=f"{self.tests_exp_path}/err{test_id}",
                name=str(test_id) if not prefix else f"{prefix} - {test_id}",
                timeout=default_timeout_ms,
                arm=self.arm,
                point_value=point_value,
                binary_io=binary_io,
                visibility=visibility,
            )
            self.test_cases.append(test_case)

    def add_public_tests(
        self,
        test_list: List[Tuple[str, int]],
        prefix="",
        default_timeout_ms=500,
        binary_io=False,
    ):
        self._add_tests(test_list, prefix, default_timeout_ms, binary_io, False)

    def add_private_tests(
        self,
        test_list: List[Tuple[str, int]],
        prefix="",
        default_timeout_ms=500,
        binary_io=False,
    ):
        self._add_tests(
            test_list,
            prefix,
            default_timeout_ms,
            binary_io,
            visibility=Visibility.HIDDEN,
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

    def copy_supplied_files(self):
        for f in self.supplied_files:
            # create directories if supplied files are paths (e.g. "in/BOOK")
            tokens = f.rsplit("/", 1)
            if len(tokens) == 2:
                parent_dir = self.sandbox.name + "/" + tokens[0]
                filename = tokens[1]
                run(f"mkdir -p {parent_dir}")
            else:
                parent_dir = self.sandbox.name
                filename = tokens[0]
            run(f"cp {self.tests_path}/{f} {parent_dir}/{filename}")

    def compile_student_code(self) -> int:
        if self.compiled:
            return 0

        logger.info(f"Compiling student code (arm={self.arm})...")
        self.copy_supplied_files()
        os.chdir(self.sandbox.name)
        build_cmd = self.get_build_command()
        logger.debug(f"{build_cmd=}")
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
        """Execute the autograder

        Returns: All rubric items
        """
        logger.info(f"{self.name} starting...")
        logger.debug(platform.uname())
        self.check_missing_files()

        if self.compile_student_code() != 0:
            logger.info(f"Skipping {self.name} test(s) due to failed compilation.")

        logger.info(f"Running {self.name} test(s)...")
        os.chdir(self.sandbox.name)
        for test in self.test_cases:
            test.execute()
            self.rubric.add_item(
                name=f"{test.name}",
                score=test.result.score,
                max_score=test.result.score,
                output=test.generate_test_summary(verbose=self.verbose_rubric),
                passed=test.result.passed,
                visibility=test.visibility,
                running_time_ms=test.result.running_time_ms,
            )

        logger.info(f"Finished running {self.name} test(s).")

        return self.rubric
