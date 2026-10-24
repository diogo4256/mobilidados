"""``python -m mobilidados`` is the same as the ``mobilidados`` command."""

import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
