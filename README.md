# CloNIX

Multi-operating system cloning tool based on NixOS

## Usage

### Developing

#### NixOS

To access the development shell to run the project without building, run:

```bash
nix develop
```

#### Other Linux

Create a virtual environment, activate it, and install the dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r ./requirements.txt
```

### Building

Ensure you're within the development environment.

On NixOS:

```bash
nix build
```

This will create an iso as well, so keep that in mind.


