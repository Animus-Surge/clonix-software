"""
Clonix: util/crypt.py

Cryptography functions
"""

import base64
import os



from . import api, constants

obfusc_value = ""

server_pub = ""

def init_crypt():
    global obfusc_value
    global server_pub

    # Generate obfuscation salt
    obfusc_value = os.urandom(128)

    # Create API request for server public key
    server_pub = api.api_get_server_pub_key()

    # Verify server public key
    

    # Generate local public/private key pair
    

    # Create API request to send client public key to server

    # Done.
    

# Encrypt to send
def encrypt(value):
    pass

# Decrypt from receive
def decrypt(value):
    pass

# Moved from util
def obfuscate_text(value):
    pass

def deobfuscate_text(value):
    pass
