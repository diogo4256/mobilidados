"""``python -m streetfit`` is the same as the ``streetfit`` command."""

import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
