import argparse

from bootstrap import run_pse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run PSE against a DSL file.")
    parser.add_argument("input", nargs="?", default="sample.pse", help="Path to the DSL file")
    parser.add_argument("-o", "--output", default="./sample_output", help="Output directory")
    args = parser.parse_args()

    run_pse(args.input, args.output)