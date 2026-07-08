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

### Packages (for custom instances of Clonix)

wip

## Modules

This system is broken out into modules.

### `deploy` - Deployment of Operating Systems

The `deploy` module is what actually does the cloning of the operating system target.

### `freeze` - Creating OS Images

### `test` - Testing Clonix

## How to use

### Presets

Presets allow for automated installs, given a target drive selected on boot.

#### Standard deploy

Uses the base image marked as `standard`. Follows the format of the standard install template.
