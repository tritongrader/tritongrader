import os
import json
import subprocess
import pprint
from datetime import datetime

LOGGING = True

pretty_printer = pprint.PrettyPrinter(indent=2)


def get_countable_unit_string(count: int, unit: str):
    ret = f"{count} {unit}"
    if count != 1:
        ret += "s"
    return ret


def get_jdk11_path(partial_paths):
    for path in partial_paths:
        if os.path.isdir(path):
            return path
    return "../../../"


def replaceStringInFile(path, filename, stringToReplace, stringReplacement):
    studentFile = open(path).read()

    # Replace string
    studentFileUpdated = studentFile.replace(stringToReplace, stringReplacement)

    # Write the file out again
    with open(path, "w") as file:
        file.write(studentFileUpdated)

    # return the name of the file if it contains print statements
    if stringToReplace in studentFile:
        return filename + ", "
    return ""


def output_score(total_score):
    if os.path.isdir("/autograder/results"):
        resultsjson = open("/autograder/results/results.json", "w")
        resultsjson.write(json.dumps(total_score))
        resultsjson.close()
    else:
        print("local test")
        print(json.dumps(total_score, indent=4, sort_keys=True))


def format_for_subprocess_call(executable_name, raw_arg_string):
    return [executable_name] + raw_arg_string.split()


def run(
    command,
    capture_output=False,
    print_command=False,
    print_output=False,
    timeout=None,
    text=True,
    arm=False,
):
    if arm:
        command = "qemu-arm -L /usr/arm-linux-gnueabi/ " + command
    sp = subprocess.run(
        command,
        shell=True,
        capture_output=capture_output or print_output,
        text=text or print_output,
        timeout=timeout,
    )
    if print_command:
        print(f"$ {command}")
    if print_output:
        print(str(sp.stdout))
        print(str(sp.stderr))
    return sp


def log(message):
    if LOGGING:
        print(f"[{datetime.now()}] " + str(message))


def prettyprint(body):
    pretty_printer.pprint(body)
