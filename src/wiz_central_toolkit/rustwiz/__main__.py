"""rustwiz — honest Rust validator. Ported from wizard_central's rust-wizard."""
import sys
from .rust_wizard import RustWizard


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] in ("-h", "--help"):
        print("rustwiz - Rust project checker")
        print("usage: rustwiz check <file.rs|dir> ... | build <crate-dir>")
        return 0
    if not argv:
        print("out of scope - usage: rustwiz check <file.rs|dir> ... | build <crate-dir>")
        return 2
    cmd, args = argv[0], argv[1:]
    wz = RustWizard()
    if cmd == "check" and args:
        return wz.check(args)
    if cmd == "build" and args:
        return wz.build(args[0])
    print(f"out of scope - unknown or incomplete command: {' '.join(argv)}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
