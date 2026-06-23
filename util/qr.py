"""
Clonix: util/qr.py

QR code generation
"""

import io

import qrcode

def generate_copy_qr(text):
    return generate_qr(f"clipboard:{text}")

def generate_qr(content):
    qr = qrcode.QRCode()
    qr.add_data(content)

    f = io.StringIO()
    qr.print_ascii(out=f)
    f.seek(0)

    return f.read()
