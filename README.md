# tritongrader 

A lightweight Python library for handling basic I/O-based grading for
programming assignments. Originally developed for UCSD lower-division 
CSE courses.

## Installation

For now, the project is not hosted on PyPI. To install the library,
use `pip install` directly from this repository.

```bash
pip install git+https://github.com/jyu283/tritongrader.git
```

See more detailed instructions for installation via `pip` [here][1].

[1]: https://www.geeksforgeeks.org/how-to-install-a-python-package-from-a-github-repository/

## Getting Started

The general workflow for this library can be broken down into the
following steps:

1. Initialize autograder
1. Create test cases
1. Execute autograder
1. Export results

### Initializing `tritongrader.autograder.Autograder`

The `Autograder` class defines one autograder instance that works on
one submission or parts of a submission that share common source files
and build procedure (e.g. Makefiles).

Sometimes, an assignment may need to be tested under different build
rules, in wihch case, multiple `Autograder` instances should be defined.

An autograder can be initialized like so:

```python
from tritongrader.autograder import Autograder

ag = Autograder(
    "Test Autograder",
    submission_path="/autogarder/submission/",
    tests_path="/autograder/hw2/tests/",
    required_files=["palindrome.c"],
    build_command="gcc -o palindrome palindrome.c",
    compile_points=5,
)
```

### Creating Test Cases

TODO

```python
ag.create_public_tests(
    [
        ("1", 1),
        ("2", 2),
    ],
    prefix="Public Tests",
)

ag.create_private_tests(
    [
        ("3", 4),
        ("4", 4),
    ],
    prefix="Hidden Tests",
)
```

### Executing and Exporting Results

The following code snippet executes the autograder and exports
the results in the Gradescope JSON format:

```python
rubric = ag.execute()

formatter = GradescopeRubricFormatter(
    rubric,
    message="tritongrader -- test",
    hidden_tests_setting=GradescopeVisibility.AFTER_PUBLISHED,
)

formatter.export("./results.json")
```