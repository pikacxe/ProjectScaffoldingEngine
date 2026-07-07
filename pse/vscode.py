import argparse
import os
import shutil
import subprocess
import sys

from pse.language import pse_language


def default_output_path():
    return os.path.join("dist", "pse-0.1.0.vsix")


def textx_executable():
    executable = shutil.which("textx")
    if executable:
        return executable

    candidate = os.path.join(os.path.dirname(sys.executable), "textx")
    if os.path.exists(candidate):
        return candidate

    return "textx"


def build_command(output_path: str, overwrite: bool = True):
    command = [
        textx_executable(),
        "generate",
        "--target",
        "vscode",
        "--project-name",
        "pse",
        "--output-path",
        output_path,
        "--description",
        "Project Scaffolding Engine DSL",
    ]

    if overwrite:
        command.append("--overwrite")

    return command


def generate_vscode_extension(output_path: str, overwrite: bool = True):
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    command = build_command(output_path, overwrite=overwrite)

    result = subprocess.run(
        command,
        text=True,
        capture_output=True,
    )

    if result.returncode == 0:
        print(f"Generated VS Code extension: {output_path}")
        return 0

    message = "\n".join(
        part.strip()
        for part in (result.stdout, result.stderr)
        if part and part.strip()
    )
    if "vscode" in message and "not registered" in message:
        message += "\nInstall editor tooling with: pip install -e .[editor]"

    print(message or "Failed to generate VS Code extension.", file=sys.stderr)
    return result.returncode or 1


def build_parser():
    parser = argparse.ArgumentParser(
        description="Generate a VS Code extension for the PSE textX language."
    )
    parser.add_argument(
        "-o",
        "--output",
        default=default_output_path(),
        help=f"Output .vsix path. Default: {default_output_path()}",
    )
    parser.add_argument(
        "--no-overwrite",
        action="store_true",
        help="Do not overwrite an existing .vsix file.",
    )
    return parser


def main(argv=None):
    # Importing the descriptor keeps a direct reference to the registered language
    # and makes this command fail early if language registration breaks.
    _ = pse_language
    args = build_parser().parse_args(argv)
    return generate_vscode_extension(args.output, overwrite=not args.no_overwrite)


if __name__ == "__main__":
    sys.exit(main())
