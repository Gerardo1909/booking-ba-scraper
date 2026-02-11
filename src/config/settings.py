"""
Módulo que contiene la configuración del sistema.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


class Settings:
    DATA_DIR = Path(__file__).parent.parent.parent / "data"
    USER_AGENT = os.getenv("USER_AGENT")
    TIMEOUT = 20
    MAX_RETRIES = 5
    BACKOFF_FACTOR = 4
    BATCH_SIZE = 20


settings = Settings()
