import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile

from pse.language import pse_language


KEYWORD_COMPLETIONS = [
    "Project",
    "target",
    "Archetype",
    "Capabilities",
    "Capability",
    "Context",
    "Entity",
    "ValueObject",
    "Aggregate",
    "root",
    "children",
    "Infrastructure",
    "Database",
    "Cache",
    "MessageBroker",
    "Deployment",
]

PRIMITIVE_TYPE_COMPLETIONS = [
    "Guid",
    "DateTime",
    "String",
    "Int",
    "Long",
    "Bool",
    "Boolean",
    "Decimal",
    "Double",
    "Float",
]

VALUE_COMPLETIONS = [
    "dotnet",
    "java",
    "WebApi",
    "CleanArchitecture",
    "ModularMonolith",
    "Microservices",
    "PostgreSQL",
    "Redis",
    "RabbitMQ",
    "Docker",
]


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


def completion_extension_js():
    keywords = json.dumps(KEYWORD_COMPLETIONS, indent=2)
    primitive_types = json.dumps(PRIMITIVE_TYPE_COMPLETIONS, indent=2)
    values = json.dumps(VALUE_COMPLETIONS, indent=2)

    return f"""const vscode = require('vscode');

const KEYWORDS = {keywords};
const PRIMITIVE_TYPES = {primitive_types};
const VALUES = {values};

function item(label, kind, detail) {{
  const completion = new vscode.CompletionItem(label, kind);
  completion.detail = detail;
  return completion;
}}

function items(labels, kind, detail) {{
  return labels.map((label) => item(label, kind, detail));
}}

function provideCompletionItems(document, position) {{
  const linePrefix = document.lineAt(position).text.slice(0, position.character);

  if (/\\btarget\\s*=\\s*$/.test(linePrefix)) {{
    return items(['dotnet', 'java'], vscode.CompletionItemKind.Value, 'PSE target');
  }}

  if (/^\\s*(Archetype|Database|Cache|MessageBroker|Deployment|Capability)\\s+$/.test(linePrefix)) {{
    return items(VALUES, vscode.CompletionItemKind.Value, 'PSE value');
  }}

  return [
    ...items(KEYWORDS, vscode.CompletionItemKind.Keyword, 'PSE keyword'),
    ...items(PRIMITIVE_TYPES, vscode.CompletionItemKind.TypeParameter, 'PSE primitive type'),
    ...items(VALUES, vscode.CompletionItemKind.Value, 'PSE value'),
  ];
}}

function formatPseText(text) {{
  const newline = text.includes('\\r\\n') ? '\\r\\n' : '\\n';
  const normalized = text.replace(/\\r\\n/g, '\\n').replace(/\\r/g, '\\n');
  const hadFinalNewline = normalized.endsWith('\\n');
  const lines = normalized.split('\\n');
  if (hadFinalNewline) {{
    lines.pop();
  }}

  const formatted = [];
  let indent = 0;
  let previousWasBlank = false;

  for (const rawLine of lines) {{
    const trimmed = rawLine.trim();

    if (trimmed.length === 0) {{
      if (!previousWasBlank) {{
        formatted.push('');
      }}
      previousWasBlank = true;
      continue;
    }}

    previousWasBlank = false;
    const startsWithClose = trimmed.startsWith('}}');
    if (startsWithClose) {{
      indent = Math.max(indent - 1, 0);
    }}

    formatted.push(`${{' '.repeat(indent * 4)}}${{trimmed}}`);

    const openCount = (trimmed.match(/\\{{/g) || []).length;
    const closeCount = (trimmed.match(/\\}}/g) || []).length;
    indent = Math.max(indent + openCount - closeCount + (startsWithClose ? 1 : 0), 0);
  }}

  return formatted.join(newline) + (hadFinalNewline ? newline : '');
}}

function provideDocumentFormattingEdits(document) {{
  const text = document.getText();
  const formatted = formatPseText(text);

  if (formatted === text) {{
    return [];
  }}

  const fullRange = new vscode.Range(document.positionAt(0), document.positionAt(text.length));
  return [vscode.TextEdit.replace(fullRange, formatted)];
}}

/**
 * @param {{vscode.ExtensionContext}} context
 */
function activate(context) {{
  const textxExtension = vscode.extensions.getExtension('textX.textX');
  if (textxExtension && !textxExtension.isActive) {{
    textxExtension.activate();
  }}

  context.subscriptions.push(
    vscode.languages.registerCompletionItemProvider(
      'pse',
      {{ provideCompletionItems }},
      ' ',
      '=',
      '\\t'
    )
  );

  context.subscriptions.push(
    vscode.languages.registerDocumentFormattingEditProvider(
      'pse',
      {{ provideDocumentFormattingEdits }}
    )
  );
}}

function deactivate() {{}}

module.exports = {{
  activate,
  deactivate,
}};
"""


def normalize_vsix_package(output_path: str):
    with zipfile.ZipFile(output_path) as archive:
        entries = {name: archive.read(name) for name in archive.namelist()}

    package = json.loads(entries["extension/package.json"].decode("utf-8"))
    for language in package.get("contributes", {}).get("languages", []):
        language.setdefault("aliases", ["PSE", "pse"])
        language["extensions"] = [
            extension if extension.startswith(".") else f".{extension}"
            for extension in language.get("extensions", [])
        ]
        language.setdefault("filenamePatterns", ["*.pse"])

    entries["extension/package.json"] = (
        json.dumps(package, indent=2, ensure_ascii=True) + "\n"
    ).encode("utf-8")
    entries["extension/extension.js"] = completion_extension_js().encode("utf-8")

    output_dir = os.path.dirname(os.path.abspath(output_path))
    fd, temp_path = tempfile.mkstemp(suffix=".vsix", dir=output_dir)
    os.close(fd)
    try:
        with zipfile.ZipFile(temp_path, "w", zipfile.ZIP_DEFLATED) as archive:
            for name, content in entries.items():
                archive.writestr(name, content)
        os.replace(temp_path, output_path)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def generate_vscode_extension(output_path: str, overwrite: bool = True):
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    command = build_command(output_path, overwrite=overwrite)

    result = subprocess.run(
        command,
        text=True,
        capture_output=True,
    )

    if result.returncode == 0:
        normalize_vsix_package(output_path)
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
