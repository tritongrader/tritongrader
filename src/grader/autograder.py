import os
import logging
import pprint
import shutil

from tempfile import TemporaryDirectory
from typing import Tuple, List

from grader.utils import *
from test_suite import TestSuite
from rubric import Rubric


class Autograder:
    """
    The Autograder class defines one autograder that can be applied to parts of
    an assignment that share common source files and build procedure (e.g. Makefile).

    You can define multiple test suites for customizable point values in one autograder.

    The submission files can either be compiled natively or on ARM (w/ qemu). You will
    need to specify which platform to use for each test suite.

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

    ARM_COMPILER = "arm-linux-gnueabi-gcc"

    def __init__(
        self,
        name: str = "",
        hide_scores: bool = True,
        submission_dirpath: str = "",
        required_files: List[str] = [],
        supplied_files: List[str] = [],
        solution_dirname: str = "",
        verbose_rubric: bool = False,
        build_command: str = None,
        compile_points: int = 0,
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

        self.hide_scores = hide_scores
        self.required_files = required_files
        self.supplied_files = supplied_files
        self.verbose_rubric = verbose_rubric
        self.compile_points = compile_points

        self.build_command = build_command
        self.compiled = False

        self.test_suites: List[TestSuite] = []

        self.rubric = Rubric(self.name, self.hide_scores)

        #
        # set up paths
        #

        # path to solution directory as specified in docstring
        self.solution_path = solution_dirname
        # path to the in/ directory containing cmdX and testX files.
        self.solution_in_path = f"{self.solution_path}/in"
        # path to the exp/ directory containing errX and outX files.
        self.solution_exp_path = f"{self.solution_path}/exp"
        # path to the directory containing student submission files.
        self.submission_path = submission_dirpath
        # Copy submission files to separate sandbox folder for testing
        self.sandbox: TemporaryDirectory = self.create_sandbox_directory(
            self.submission_path
        )

    def create_sandbox_directory(self, submission_dirpath: str) -> str:
        tmpdir = TemporaryDirectory(prefix="Autograder")
        logging.info(f"Sandbox created at {tmpdir.name}")
        shutil.copytree(submission_dirpath, tmpdir.name, dirs_exist_ok=True)
        return tmpdir

    def add_test_suite(
        self,
        suite_name="",
        default_timeout_ms=500,
        arm=True,
        test_list: List[Tuple[str, int]] = [],
        hidden=False,
        unhide_time=None,
        binary_io=False,
    ):
        suite = TestSuite(
            in_directory=self.solution_in_path,
            command_directory=self.solution_in_path,
            expected_directory=self.solution_exp_path,
            suite_name=suite_name,
            default_timeout_ms=default_timeout_ms,
            arm=arm,
            hidden=hidden,
            unhide_time=unhide_time,
            binary_io=binary_io,
        )
        suite.create_test_cases_from_list(test_list)
        self.test_suites.append(suite)

    def check_missing_files(self):
        logging.info("Checking missing files...")
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
        logging.info("Finished checking missing files.")

    def get_default_build_command(self, arm=False):
        return "make" if not arm else f"make CC={self.ARM_COMPILER}"

    def get_build_command(self, arm=False):
        return (
            self.build_command
            if self.build_command is not None
            else self.get_default_build_command(arm)
        )

    def get_compile_result_message(self):
        if self.compiled:
            return "Your submission compiled successfully.\n"
        else:
            return (
                "Your submission failed to compile.\n"
                + "Please check the Autograder output for more details.\n"
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
            run(f"cp {self.solution_path}/{f} {parent_dir}/{filename}")

    def compile_student_code(self, arm=True) -> int:
        if self.compiled:
            return 0

        logging.info(f"Compiling student code (arm={arm})...")
        self.copy_supplied_files()
        os.chdir(self.sandbox.name)
        build_cmd = self.get_build_command(arm)
        logging.debug(f"{build_cmd=}")
        compiler_process = run(build_cmd, capture_output=True, text=True)
        compiled = compiler_process.returncode == 0
        if compiled:
            logging.info("Student code compiled successfully.")
            self.compiled = True
        else:
            logging.info(
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

    def add_suite_to_rubric(self, suite: TestSuite):
        for test in suite.test_cases:
            vis = Rubric.VIS_AFT_PUBLISH if test.hide_results() else Rubric.VIS_VISIBLE
            self.rubric.add_item(
                name=f"{test.name}",
                score=test.result.score,
                max_score=test.point_value,
                output=test.generate_test_summary(verbose=self.verbose_rubric),
                passed=test.result.passed,
                visibility=vis,
            )

    def run_tests(self):
        for test_suite in self.test_suites:
            if self.compile_student_code(arm=test_suite.arm) != 0:
                logging.info(
                    f"Skipping {test_suite.name} test(s) due to failed compilation."
                )
                continue

            test_suite.run_tests(executable_directory=self.sandbox.name)
            self.add_suite_to_rubric(test_suite)

    def get_test_cases_summary(self):
        summary = f"Test Summary: {self.name}\n" + self.get_compile_result_message()
        for suite in self.test_suites:
            summary += f"\n   - {suite.generate_suite_summary()}"
        return summary

    def execute(self):
        """Execute the autograder

        Returns: All rubric items
        """
        logging.info(f"{self.name} starting...")
        self.check_missing_files()
        self.run_tests()
        return self.rubric.export()


if __name__ == "__main__":
    ag = Autograder(
        name="Test Autograder",
        required_files=["hello.c"],
        submission_dirpath="/home/jerry/gradescope.py/target/submission",
        solution_dirname="/home/jerry/gradescope.py/target/solution",
        build_command="gcc hello.c -o hello",
        verbose_rubric=True,
    )
    ag.add_test_suite(
        suite_name="Basic",
        test_list=[
            ("1", 1),
        ],
    )
    rubric = ag.execute()
    pp = pprint.PrettyPrinter(indent=2)
    pp.pprint(rubric)
