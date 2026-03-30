# CloNIX

Multi-operating system cloning tool based on NixOS

## Dependencies

- Python 3 (I use 3.13 but anything current will work)
- Urwid
- Httpx (Alternative to requests)
- Nuitka

All python requirements are present in the `requirements.txt` file.

## Usage

### Developing

#### NixOS

To access the development shell to run the project without building, run:

```bash
nix develop
```

Note: the development shell automatically will regenerate the `requirements.txt` file. This is to ensure that
every environment is *exactly* the same, including non-NixOS systems' environments.

#### Other Linux

Create a virtual environment, activate it, and install the dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate  # or activate.fish/activate.zsh depending on your shell
pip install -r ./requirements.txt
```

Within the development shell you can run the python program as any other python program:

```bash
python3 ./main.py
```

### Building

Ensure you're within the development environment.

To build the entire project, including the ISO:

```bash
nix build
```

If you don't want it to build everything, you can instead run:

```bash
nix build .#clonix-bin
```

This will only build the binary by using nuitka.

If you aren't on NixOS:

```bash
python3 -m nuitka --onefile ./main.py
```

This is the same command that gets run inside the build hook.

## ISOs

Creating an ISO requires the use of the Nix package system, as the tool is built into the package
manager.

