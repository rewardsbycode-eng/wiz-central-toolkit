"""Entry point for wiz dispatch."""
import sys
from .lib.cli import main

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
