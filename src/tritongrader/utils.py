import os
import json
import subprocess


def get_countable_unit_string(count: int, unit: str):
    ret = f"{count} {unit}"
    if count != 1:
        ret += "s"
    return ret


def output_score(total_score):
    if os.path.isdir("/autograder/results"):
        resultsjson = open("/autograder/results/results.json", "w")
        resultsjson.write(json.dumps(total_score))
        resultsjson.close()
    else:
        print("local test")
        print(json.dumps(total_score, indent=4, sort_keys=True))


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
        command = "qemu-arm -L /usr/arm-linux-gnueabihf/ " + command
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
