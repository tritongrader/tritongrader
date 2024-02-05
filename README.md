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

The library currently supports two types of test cases:
I/O-based tests (`IOTestCase`) and custom tests (`CustomTestCase`).

#### I/O-based tests

`IOTestCase` runs a command read from a _command file_, and (optionally)
feeds the program some input via `stdin` read from a _test input file_.
The output of the program/command (both `stdout` and `stderr`) are then
compared against the desired output, which is read from an _expected stdout file_
and an _expected stderr file_.

Additionally, each test case is configured with a name (`name`), a point value
(`point_value`), an execution timeout (`timeout`), a visibility setting to
indicate if the test case should be hidden from the student (`hidden`).

Additionally, `binary_io` sets if the test cases produces binary output (i.e.,
output that cannot be interpreted as text.)

Lastly, for the time being, an `arm` flag is provided to specify if the test
should be run in an emulated ARM environment. **This flag will soon be deprecated.**


#### Custom tests

Custom tests are created with a custom function defined by the library user.
A `CustomTestCase` is still created with `name`, `point_value`, `timeout`,
`hidden` just like the `IOTestCase`, but it first requires a `func` parameter
that defines the body of the test case -- what it is supposed to do.

The test function `func` takes only a single parameter: a `CustomTestCaseResult`
object. This will be supplied by the test case runner (_i.e._, the `Autograder`
object). It is the library user's responsibility to fill in the fields of this
object in the test function. Specifically, the following fields will **not**
be filled in by the test runner:

- `output`: a message displayed in the test result rubric.
- `passed`: a boolean value to indicate if the test passed or not.
- `score`: how many points are granted for this test case.

#### Bulk Loading

We provide a bulk-loading interface for `IOTestCase` objects, because these test
cases usually come in a fairly large number. 

A bulk loader object can be created and configured from the `Autograder` object
by calling the `io_tests_bulk_loader` with the desired parameters, which will
create an `IOTestCaseBulkLoader` object. This object supports two methods:
`add()`, which creates a single test case, and
`add_list()`, which creates a list of test cases. The test case objects created
are then added to the autograder.

Example:

```python
    ag = Autograder(...)  # parameters omitted
    ag.io_tests_bulk_loader(
        prefix="Unit Tests - ",
        default_timeout_ms=5000,
        commands_prefix="cmd",
        test_input_prefix="test",
        expected_stderr_prefix="err",
        expected_stdout_prefix="out",
    ).add(
        "1",
        2,
        timeout_ms=20000,
        prefix="Public - ",
    ).add_list(
        [
            ("2", 4),
            ("3", 4),
            ("4", 4),
        ],
        prefix="Hidden - ",
        hidden=True,
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