"""Entry point for wiz dispatch."""
import sys
from .lib import cli as internal_cli

# Wrap main() to accept argv (wiz dispatcher calls main(args))
def main(argv=None):
    # Save original sys.argv
    old_argv = sys.argv
    # Replace with provided argv (or empty list)
    if argv is not None:
        sys.argv = [sys.argv[0]] + list(argv)
    try:
        return internal_cli.main()
    finally:
        sys.argv = old_argv

# Also expose for module-level access
__all__ = ['main']

if __name__ == "__main__":
    sys.exit(main())
