import json
import os
import shutil
import uuid
from datetime import datetime

from textx import metamodel_from_file

from generators.dotnet.generator import generate_dotnet
from generators.dotnet.mapper import map_model_to_architecture
from heuristics.loader import load_all_heuristics
from heuristics.resolver import resolve_capabilities
from heuristics.dependency_builder import build_dependency_graph
from model.generation_context import GenerationContext

BASE_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.dirname(BASE_DIR)
GRAMMAR_PATH = os.path.join(BASE_DIR, "grammar", "pse.tx")

def run_pse(input_file: str, output_dir: str):
    run_id = None
    try:
        print("PSE bootstrap starting...\n")

        print("Validating environment...\n")
        validate_environment()

        print("Creating output directory...\n")
        os.makedirs(output_dir, exist_ok=True)

        print("Loading metamodel...\n")
        mm = load_metamodel()

        print("Loading model...\n")
        model, input_path = load_model(mm, input_file)

        print("Loading heuristics...\n")
        heuristics = load_all_heuristics()

        print("Mapping model to architecture...\n")
        arch = map_model_to_architecture(model)

        print("Creating generation context...\n")
        ctx = GenerationContext(
            architecture=arch,
            output_dir=output_dir,
            presets=heuristics["presets"],
            packages=heuristics["packages"],
            versions=heuristics["versions"]
        )

        # NEW: capability system
        print("Resolving capabilities and dependencies...\n")
        cap_graph = resolve_capabilities(ctx)
        print("Building dependency graph...\n")
        dep_graph = build_dependency_graph(cap_graph)

        ctx.capabilities = cap_graph
        ctx.dependency_graph = dep_graph
        print("Capabilities resolved and dependency graph built.\n")
        print(f"Capabilities: {list(cap_graph.capabilities.keys())}\n")
        print(f"Dependency graph: {dep_graph}\n")

        dsl_text = read_dsl_input(input_path)
        run_id = write_run_manifest(output_dir, input_path, dsl_text, cap_graph)

        print("Dispatching generator...\n")
        dispatch_generator(ctx)
        update_run_status(output_dir, run_id, "completed")

    except Exception as e:
        if run_id:
            update_run_status(output_dir, run_id, "failed")
        print(f"\nError during PSE bootstrap: {e}")


def validate_environment():
    if not os.path.exists(GRAMMAR_PATH):
        raise FileNotFoundError(f"Grammar file not found: {GRAMMAR_PATH}")

    if not shutil.which("dotnet"):
        raise EnvironmentError("dotnet is required but was not found on PATH")


def load_metamodel():
    return metamodel_from_file(GRAMMAR_PATH)


def load_model(mm, input_file: str):
    resolved = resolve_input_path(input_file)
    return mm.model_from_file(resolved), resolved


def resolve_input_path(input_file: str):
    resolved = input_file

    if not os.path.isabs(resolved) and not os.path.exists(resolved):
        candidate = os.path.join(PROJECT_ROOT, input_file)
        if os.path.exists(candidate):
            resolved = candidate

    if not os.path.exists(resolved):
        raise FileNotFoundError(f"Input file not found: {input_file}")

    return resolved


def read_dsl_input(input_path: str):
    with open(input_path, "r", encoding="utf-8") as f:
        return f.read()


def write_run_manifest(output_dir: str, input_path: str, dsl_text: str, cap_graph):
    manifest_path = os.path.join(output_dir, "pse.manifest.json")
    run_id = str(uuid.uuid4())
    timestamp = datetime.utcnow().isoformat(timespec="seconds") + "Z"

    run_entry = {
        "id": run_id,
        "timestamp": timestamp,
        "input_file": os.path.abspath(input_path),
        "capabilities": [
            {
                "name": name,
                "value": cap.value,
                "source": cap.source
            }
            for name, cap in sorted(cap_graph.capabilities.items())
        ],
        "dsl": dsl_text,
        "status": "started"
    }

    data = {"runs": []}

    if os.path.exists(manifest_path):
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError:
            data = {"runs": []}

    data.setdefault("runs", []).append(run_entry)

    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=True)

    return run_id


def update_run_status(output_dir: str, run_id: str, status: str):
    if not run_id:
        return

    manifest_path = os.path.join(output_dir, "pse.manifest.json")
    if not os.path.exists(manifest_path):
        return

    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError:
        return

    for run in data.get("runs", []):
        if run.get("id") == run_id:
            run["status"] = status
            break

    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=True)


def dispatch_generator(ctx: GenerationContext):
    target = (ctx.architecture.project.target or "dotnet").lower()

    if target == "dotnet":
        generate_dotnet(ctx)
        return

    raise ValueError(f"Unsupported target: {target}")