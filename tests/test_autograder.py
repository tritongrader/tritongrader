# This is fairly janky, but it works.
import os
import sys
sys.path.append(
    os.path.realpath(os.path.realpath(os.path.dirname(__file__)) + "/../src")
)

#
# The following is how a grading script using the tritongrader 
# library might look. This test file is constantly updated as
# the library evolves.
#

import pprint

from tritongrader.autograder import Autograder  # noqa
from tritongrader.rubric import GradescopeRubricFormatter  # noqa
from tritongrader.visibility import GradescopeVisibility  # noqa

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

    ag.create_public_io_tests(
        [
            ("1", 1),
            ("2", 2),
        ],
        prefix="Public Tests",
    )

    ag.create_private_io_tests(
        [
            ("3", 4),
            ("4", 4),
        ],
        prefix="Hidden Tests",
    )

    formatter = GradescopeRubricFormatter(
        ag.execute(),
        message="tritongrader -- test",
        hidden_tests_setting=GradescopeVisibility.AFTER_PUBLISHED,
    )

    pprint.pprint(formatter.as_dict())
    formatter.export(f"{example_dir}/results.json")
