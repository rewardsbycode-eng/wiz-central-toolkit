"""cli.py - entry module for tmuxwiz."""
import sys
from .tmux_wizard import main as tmux_main

def main():
    """CLI entry point - wraps tmux_main with sys.argv."""
    return tmux_main(sys.argv[1:])

if __name__ == "__main__":
    sys.exit(main())
