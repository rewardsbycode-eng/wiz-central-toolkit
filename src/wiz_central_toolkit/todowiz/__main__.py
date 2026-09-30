"""Entry point for wiz dispatch."""
import sys
from .lib import cli as internal_cli
from .lib.todo_wizard import TodoWizard  # noqa: F401 (re-exported for tests)

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
__all__ = ['main', 'TodoWizard']

if __name__ == "__main__":
    sys.exit(main())
