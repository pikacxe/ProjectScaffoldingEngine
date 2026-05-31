import yaml


def load_yaml(path):
    with open(path) as f:
        return yaml.safe_load(f)


def load_all_heuristics():
    return {
        "presets": load_yaml("heuristics/presets.yaml"),
        "packages": load_yaml("heuristics/packages.yaml"),
        "versions": load_yaml("heuristics/versions.yaml"),
    }