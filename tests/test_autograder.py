import os
import pprint
import sys

# This is fairly janky, but it works.
sys.path.append(
    os.path.realpath(os.path.realpath(os.path.dirname(__file__)) + "/../src")
)

#
# The following is how a grading script using the tritongrader
# library might look. This test file is constantly updated as
# the library evolves.
#

from tritongrader.autograder import Autograder  # noqa
from tritongrader.formatter import GradescopeResultsFormatter  # noqa
from tritongrader.test_case import ( # noqa
    CustomTestCase,
    CustomTestResult,
    BasicTestCase,
)

if __name__ == "__main__":
    example_dir = os.path.realpath(os.path.dirname(__file__)) + "/example/"
    ag = Autograder(
        "Test Autograder",
        example_dir + "submission/",
        example_dir + "tests/",
        required_files=["palindrome.c"],
        verbose_rubric=True,
        build_command="gcc -o palindrome palindrome.c",
        compile_points=1,
        arm=False,
    )

    def test_num_lines(result: CustomTestResult):
        line_count = 0
        with open("./palindrome.c", "r") as fp:
            line_count = len(fp.readlines())

        if line_count > 20:
            result.passed = False
            result.output = "You wrote too much code!"
            result.score = 0
        else:
            result.passed = True
            result.output = "Line number within limit."
            result.score = 4

    custom_test = CustomTestCase(test_num_lines, "Custom Test Case 1", point_value=4)

    ag.add_test(custom_test)

    basic_test = BasicTestCase(
        'echo "Hello World"',
        name="Hello world!",
        point_value=5,
        arm=False,
    )

    ag.add_test(basic_test)

    ag.io_tests_bulk_loader(
        prefix="Unit Tests - ",
        default_timeout=5,
        commands_prefix="cmd",
        test_input_prefix="test",
        expected_stderr_prefix="err",
        expected_stdout_prefix="out",
    ).add(
        "1",
        2,
        timeout=2,
        prefix="Public - ",
    ).add_list(
        [
            ("2", 4),
            ("3", 4),
            ("4", 4),
            ("5", 6),
            ("6", 6),
            ("7", 6),
        ],
        prefix="Hidden - ",
        hidden=True,
    )

    ag.execute()

    formatter = GradescopeResultsFormatter(
        src=ag,
        message="tritongrader test",
        hidden_tests_setting="after_published",
        html_diff=True,
    )

    pprint.pprint(formatter.execute())
