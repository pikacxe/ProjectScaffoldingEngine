import os

TEMPLATE_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "templates", "dotnet")
)


def render_template(name: str, values: dict):
    path = os.path.join(TEMPLATE_ROOT, name)

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    for key, value in values.items():
        placeholder = "{{" + key + "}}"
        content = content.replace(placeholder, value)

    return content
