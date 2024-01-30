import os
import logging
import subprocess

from typing import List


class BuildRule:
    """
    This class defines the build rule for an autograder.
    """

    BUILD_PENDING = 0
    BUILD_SUCCESS = 1
    BUILD_FAILED = 2

    def __init__(
        self, dirpath: str = "", required_files: List[str] = [], build_command: str = ""
    ):
        self.dirptah = dirpath
        self.required_files = required_files
        self.build_command = build_command
        self.build_status: int = BuildRule.BUILD_PENDING
        self.build_stdout: str = None
        self.build_stderr: str = None

    def build(self) -> int:
        if self.build_status == BuildRule.BUILD_SUCCESS:
            return self.build_status

        os.chdir(self.dirpath)

        buildproc = subprocess.run(
            self.build_command,
            shell=True,
            capture_output=True,
            text=True,
        )

        self.build_stdout = buildproc.stdout
        self.build_stderr = buildproc.stderr

        if buildproc.returncode == 0:
            self.build_status = BuildRule.BUILD_SUCCESS
            logging.info("Submission build success.")
        else:
            self.build_status = BuildRule.BUILD_FAILED
            logging.info(
                "Submission build failed. "
                + f"(returncode={buildproc.returncode})\n{buildproc.stderr}"
            )
