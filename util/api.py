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
        case "DELETE":
            pass
        case "UPDATE":
            pass

        case _:
            return
    pass


# Key-pair exchange
def api_get_server_pub_key():
    pass

def api_send_client_pub_key():
    pass


# Encryption keys
def api_get_client_encryption_key():
    pass

def api_send_client_master_volume_key():
    pass


# Configuration management
def api_get_client_deployment_config():
    pass


# Device management
def api_create_device():
    pass
