import os

import yaml


HEURISTICS_DIR = os.path.dirname(__file__)


def load_yaml(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_all_heuristics():
    return {
        "presets": load_yaml(os.path.join(HEURISTICS_DIR, "presets.yaml")),
        "packages": load_yaml(os.path.join(HEURISTICS_DIR, "packages.yaml")),
        "versions": load_yaml(os.path.join(HEURISTICS_DIR, "versions.yaml")),
    }
