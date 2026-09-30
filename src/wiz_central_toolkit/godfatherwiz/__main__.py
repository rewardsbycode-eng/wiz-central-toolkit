"""Entry point for godfatherwiz dispatch."""
import sys
from .lib import cli as internal_cli

def main(argv=None):
    old_argv = sys.argv
    if argv is None:
        sys.argv = [sys.argv[0]]
    else:
        sys.argv = [sys.argv[0]] + list(argv)
    try:
        return internal_cli.main()
    finally:
        sys.argv = old_argv

# Expose main at module level for tools_registry.py
__all__ = ['main']

if __name__ == "__main__":
    sys.exit(main())
