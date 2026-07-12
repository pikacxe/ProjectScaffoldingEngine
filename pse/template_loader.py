import os
import re


TEMPLATE_ROOT = os.path.join(os.path.dirname(__file__), "templates")


def render_template(relative_path: str, values=None):
    path = os.path.join(TEMPLATE_ROOT, relative_path)
    with open(path, "r", encoding="utf-8") as handle:
        content = handle.read()

    for key, value in (values or {}).items():
        content = content.replace("{{" + key + "}}", str(value))

    unresolved = sorted(set(re.findall(r"\{\{([A-Za-z][A-Za-z0-9_]*)\}\}", content)))
    if unresolved:
        names = ", ".join(unresolved)
        raise ValueError(f"Template '{relative_path}' has unresolved placeholders: {names}")

    return content
