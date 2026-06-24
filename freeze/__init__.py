"""
Clonix: freeze/__init__.py

Image freeze and metadata generation
"""

def start_freeze(source: str, target_filename: str, metadata: dict | None = None):
    # If metadata = None, we'll be prompting. TUI will provide this dictionary.
    # Alternatively: source is a filesystem path. We *could* have it read certain information
    # from it, like version and distribution.

    pass
