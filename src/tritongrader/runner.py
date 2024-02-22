import subprocess
import time

from tempfile import NamedTemporaryFile
from typing import IO, TextIO, Optional, BinaryIO

class CommandRunner:
    DEFAULT_TIMEOUT_MS = 5000.0
    QEMU_ARM = "qemu-arm -L /usr/arm-linux-gnueabihf/ "

    def __init__(
        self,
        command: str,
        capture_output: bool = False,
        print_command: bool = False,
        print_output: bool = False,
        timeout_ms: float = DEFAULT_TIMEOUT_MS,
        text: bool = True,
        arm: bool = False,
    ):
        if arm:
            self.command = CommandRunner.QEMU_ARM + self.command
        else:
            self.command = command
        
        self.capture_output = capture_output or print_output
        self.print_command = print_command
        self.print_output = print_output
        self.timeout_ms = timeout_ms
        self.text = text
        self.arm = arm
        self.outfp: Optional[IO] = None
        self.errfp: Optional[IO] = None
        self.running_time_ms: float = 0
        self.returncode = None
    
    def print_text_file(self, fp: TextIO, heading=""):
        if heading:
            print(heading)
        while True:
            line = fp.readline() 
            if not line:
                break
            print(line, end="")
    
    def compare_text_files(self, fp1: TextIO, fp2: TextIO) -> bool:
        while True:
            line1 = fp1.readline()
            line2 = fp2.readline()
            if line1 != line2:
                return False
            if not line1 or not line2:
                break
        return True

    def compare_binary_files(self, fp1: BinaryIO, fp2: BinaryIO) -> bool:
        # TODO: Handle binary stdout and stderr
        return True
    
    def check_stdout(self, expected_stdout: str) -> bool:
        with open(expected_stdout, "r" if self.text else "rb") as fp:
            if self.text:
                return self.compare_text_files(self.outfp, fp)
            else:
                return self.compare_binary_files(self.outfp, fp)
    
    def check_stderr(self, expected_stderr: str) -> bool:
        with open(expected_stderr, "r" if self.text else "rb") as fp:
            if self.text:
                return self.compare_text_files(self.errfp, fp)
            else:
                return self.compare_binary_files(self.errfp, fp)
    
    def run(self):
        if self.capture_output:
            self.outfp = NamedTemporaryFile("w+" if self.text else "w+b")
            self.errfp = NamedTemporaryFile("w+" if self.text else "w+b")
        
        if self.print_command:
            print(f"$ self.command")
        
        start_ts = time.time()
        sp = subprocess.run(
            self.command,
            shell=True,
            stdout=self.outfp if self.capture_output else None,
            stderr=self.errfp if self.capture_output else None,
            text=self.text,
            arm=self.arm,
            timeout=self.timeout_ms / 1000,
        )
        end_ts = time.time()
        self.running_time_ms = (end_ts - start_ts) * 1000

        if self.print_command:
            if not self.text:
                print("[binray output]")
            self.print_text_file(self.outfp, heading="=== STDOUT ===")
            self.print_text_file(self.errfp, heading="=== STDERR ===")
        
        self.outfp.close()
        self.errfp.close()
