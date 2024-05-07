import logging

import logging.config
from tritongrader.autograder import Autograder  # noqa

logging.basicConfig(format="[%(asctime)s] %(message)s", level=logging.DEBUG)
