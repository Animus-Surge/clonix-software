# Clonix

Multi-operating system cloning tool based on NixOS

## How it works

## Dependencies

### Python
- Python 3 (I use 3.13 but anything current will work)
- Urwid
- Httpx (Alternative to requests)
- Nuitka
- QRCode (for QR code generation)
- Loguru
- PyTest and FusePY for testing

All python requirements are present in the `requirements.txt` file.


## Notes

- `systemctl reboot --firmware-setup`
- `fwupdmgr` for modifying bios variables
  - `echo "MyNewStrongPassword123" | sudo tee /sys/class/firmware-attributes/dell-wmi-sysman/authentication/bios-admin/new_password` for updating dell passwords


