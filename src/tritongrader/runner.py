import os
import subprocess
import time
import logging

from tempfile import NamedTemporaryFile
from typing import TextIO, Optional, BinaryIO

logger = logging.getLogger("tritongrader.runner")


class CommandRunner:
    DEFAULT_TIMEOUT = 1.0
    QEMU_ARM = "qemu-arm-static -L /usr/arm-linux-gnueabihf/ "

    def __init__(
        self,
        command: str,
        capture_output: bool = False,
        print_command: bool = False,
        print_output: bool = False,
        timeout: float = DEFAULT_TIMEOUT,
        text: bool = True,
        arm: bool = False,
    ):
        """
        - timeout: timeout in seconds.
        """
        if arm:
            self.command = CommandRunner.QEMU_ARM + command
        else:
            self.command = command

        self.capture_output = capture_output or print_output
        self.print_command = print_command
        self.print_output = print_output
        self.timeout = timeout
        self.text = text
        self.arm = arm
        self.stdout_tf: Optional[str] = None
        self.stderr_tf: Optional[str] = None
        self.running_time: float = 0
        self.exit_status = None

    def __del__(self):
        if self.stdout_tf:
            os.remove(self.stdout_tf)
        if self.stderr_tf:
            os.remove(self.stderr_tf)

    def print_text_file(self, fp: TextIO, heading=""):
        if heading:
            print(heading)
        while True:
            line = fp.readline()
            if not line:
                break
            print(line, end="")

    @property
    def read_mode(self):
        return "r" if self.text else "rb"

    @property
    def write_mode(self):
        return "w" if self.text else "wb"

    def compare(self, file_a: str, file_b: str) -> bool:
        with open(file_a, "rb") as a, open(file_b, "rb") as b:
            return a.read() == b.read()

    def check_stdout(self, expected_stdout: str) -> bool:
        assert self.stdout_tf is not None
        return self.compare(self.stdout_tf, expected_stdout)

    def check_stderr(self, expected_stderr: str) -> bool:
        assert self.stderr_tf is not None
        return self.compare(self.stderr_tf, expected_stderr)

    @property
    def stdout(self):
        if not self.capture_output:
            raise Exception("stdout was not captured")
        with open(self.stdout_tf, self.read_mode) as fp:
            try:
                if os.path.getsize(
                    self.stdout_tf
                ) > 20000000:  #hard coded big number, maybe parametrize this
                    msg = "stdout is too large to read, you may have an infinite loop in your code. " \
                           "Here are the first 4096 bytes of stdout:\n"
                    pos = 0
                    while (pos < 4096):
                        msg += fp.readline(4096 - pos)
                        pos = fp.tell()
                    fp.close()
                    return msg
                else:
                    msg = fp.read()
                    fp.close()
                    return msg
            except UnicodeDecodeError as e:
                return f"tritongrader: error decoding stdout as UTF-8: {e}"

    @property
    def stderr(self):
        if not self.capture_output:
            raise Exception("stderr was not captured")
        with open(self.stderr_tf, self.read_mode) as fp:
            try:
                if os.path.getsize(
                    self.stderr_tf
                ) > 20000000:  #hard coded big number, maybe parametrize this
                    msg = "stderr is too large to read, you may have an infinite loop in your code. " \
                           "Here are the first 4096 bytes of stderr:\n"
                    pos = 0
                    while (pos < 4096):
                        msg += fp.readline(4096 - pos)
                        pos = fp.tell()
                    fp.close()
                    return msg
                else:
                    msg = fp.read()
                    fp.close()
                    return msg
            except UnicodeDecodeError as e:
                return f"tritongrader: error decoding stderr as UTF-8: {e}"

    def run(self):
        if self.capture_output:
            self.stdout_tf = NamedTemporaryFile(
                "w+" if self.text else "w+b", delete=False
            ).name
            self.stderr_tf = NamedTemporaryFile(
                "w+" if self.text else "w+b", delete=False
            ).name
            outfp = open(self.stdout_tf, self.write_mode)
            errfp = open(self.stderr_tf, self.write_mode)

        if self.print_command:
            print(f"Current working directory: {os.getcwd()}")
            print(f"Files: {[f for f in os.listdir('.')]}")
            print(f"$ {self.command}")

        start_ts = time.time()
        sp = subprocess.run(
            self.command,
            shell=True,
            stdout=outfp if self.capture_output else None,
            stderr=errfp if self.capture_output else None,
            text=self.text,
            timeout=self.timeout,
        )
        end_ts = time.time()
        self.running_time = end_ts - start_ts
        self.exit_status: int = sp.returncode
