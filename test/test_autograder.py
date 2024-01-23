import sys
import os

# This is fairly janky, but it works.
sys.path.append(os.path.realpath(os.path.realpath(os.path.dirname(__file__)) + "/../src"))

from tritongrader.autograder import Autograder

if __name__ == "__main__":
    example_dir = os.path.realpath(os.path.dirname(__file__)) + "/example/"
    ag = Autograder(
        "Test Autograder",
        example_dir + "submission/",
        example_dir + "tests/",
    )
