class TestResultBase:
    def __init__(self):
        self.score: int = 0
        self.passed: bool = False
        self.timed_out: bool = False
        self.error: bool = False
        self.running_time_ms: float = None
        self.has_run: bool = False


class TestCaseBase:
    DEFAULT_TIMEOUT_MS = 100
    DEFAULT_TIMEOUT_SECS = DEFAULT_TIMEOUT_MS / 1000

    def __init__(
        self,
        name: str = "Test Case",
        point_value: float = 1,
        timeout: float = DEFAULT_TIMEOUT_MS,
        hidden: bool = False,
    ):
        self.name: str = name
        self.point_value: float = point_value
        self.timeout: float = timeout
        self.hidden: bool = hidden
        self.result: TestResultBase = None

    def execute(self) -> TestResultBase:
        raise NotImplementedError
