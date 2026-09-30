"""Entry point for writewiz."""
import sys
from .cli import main

# Expose main() at module level
main = main

if __name__ == "__main__":
    sys.exit(main())
