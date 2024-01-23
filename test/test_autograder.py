import sys
import os

# This is fairly janky, but it works.
sys.path.append(os.path.realpath(os.path.realpath(os.path.dirname(__file__)) + "/../src"))

print(sys.path)
from tritongrader.autograder import Autograder

if __name__ == "__main__":
    ag = Autograder("Test Autograder")