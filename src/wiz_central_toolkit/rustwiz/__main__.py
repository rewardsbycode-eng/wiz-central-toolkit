"""Entry point for wiz dispatch."""
import sys
from .lib.cli import main
from .lib.rust_wizard import RustWizard  # noqa: F401 (re-exported for tests)

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
