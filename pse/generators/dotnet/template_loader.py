from pse.template_loader import render_template as render_project_template


def render_template(name: str, values: dict):
    return render_project_template(f"dotnet/{name}", values)
