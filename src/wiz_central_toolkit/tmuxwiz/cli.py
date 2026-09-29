"""cli.py - entry module for tmuxwiz (contains main())."""
import sys

from .tmux_wizard import main

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))