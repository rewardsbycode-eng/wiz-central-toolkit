"""Entry point for tmuxwiz dispatch."""
import sys
from .lib import cli as internal_cli

def main(argv=None):
    old_argv = sys.argv
    if argv is not None:
        sys.argv = [sys.argv[0]] + list(argv)
    try:
        return internal_cli.main()
    finally:
        sys.argv = old_argv

if __name__ == "__main__":
    sys.exit(main())
