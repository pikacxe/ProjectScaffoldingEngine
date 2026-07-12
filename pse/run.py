import argparse
import os
import sys

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from pse.bootstrap import run_pse


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run PSE against a DSL file.")
    parser.add_argument("input", nargs="?", default="sample.pse", help="Path to the DSL file")
    parser.add_argument("-o", "--output", default="./sample_output", help="Output directory")
    parser.add_argument(
        "--no-overwrite",
        action="store_true",
        help="Preserve modified generated files and only refresh unchanged owned files.",
    )
    args = parser.parse_args(argv)

    return 0 if run_pse(args.input, args.output, overwrite=not args.no_overwrite) else 1


if __name__ == "__main__":
    sys.exit(main())
