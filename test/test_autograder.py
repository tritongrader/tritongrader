import sys
import os

from datetime import datetime, timedelta

# This is fairly janky, but it works.
sys.path.append(
    os.path.realpath(os.path.realpath(os.path.dirname(__file__)) + "/../src")
)

from tritongrader.autograder import Autograder

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

    ag.add_public_tests(
        [
            ("1", 1),
            ("2", 2),
        ],
        prefix="Public Tests"
    )

    ag.add_private_tests(
        [
            ("3", 4),
            ("4", 4),
        ],
        prefix="Hidden Tests",
        unhide_time=datetime.now() + timedelta(days=1)
    )

    r = ag.execute()

    import pprint

    pprint.pprint(r)
