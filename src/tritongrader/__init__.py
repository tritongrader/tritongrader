import platform
import logging

import logging.config

logging.basicConfig(
    format="[%(asctime)s] %(message)s", 
    level=logging.DEBUG
)

logging.info(platform.uname())
