"""
Clonix: util/api.py

API functions
"""

import httpx
from loguru import logger

from util import constants

def _make_api_request(method, path, data={}):
    full_uri = f"{constants.CLONIX_API_URL}{path}"

    match method:
        case "GET":
            pass
        case "POST":
            pass
        case "UPDATE":
            pass

        case _:
            return
    pass

def retrieve_autoprovision_config(): # Authenticates this cloner instance
    pass
