"""
Módulo que contiene la configuración del sistema.
"""

import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    BASE_URL = os.getenv("BOOKING_BASE_URL")
    USER_AGENT = os.getenv("USER_AGENT")
    TIMEOUT = 10
    MAX_RETRIES = 3
    BACKOFF_FACTOR = 2
    BATCH_SIZE = 20
