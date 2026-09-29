"""tmuxwiz — sovereign tmux session manager."""
import sys

from .tmux_wizard import main as _main


def main(argv=None) -> int:
    return _main(sys.argv[1:] if argv is None else list(argv))


if __name__ == "__main__":
    sys.exit(main())
