import json
import os
import shutil
import tempfile
import uuid
from datetime import datetime, timezone

from textx import metamodel_from_file

from pse.generators.dotnet.generator import generate_dotnet
from pse.generators.dotnet.mapper import map_model_to_architecture
from pse.heuristics.loader import load_all_heuristics
from pse.heuristics.resolver import resolve_capabilities
from pse.heuristics.dependency_builder import build_dependency_graph
from pse.model.generation_context import GenerationContext
from pse.validation import format_user_error, validate_model

BASE_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.dirname(BASE_DIR)
GRAMMAR_PATH = os.path.join(BASE_DIR, "grammar", "pse.tx")

def run_pse(input_file: str, output_dir: str, overwrite: bool = True):
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
        dsl_text = read_dsl_input(input_path)

        run_id = write_run_manifest(output_dir, input_path, dsl_text)

        print("Validating model...\n")
        validate_model(model, dsl_text)

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
            versions=heuristics["versions"],
            options={"overwrite": overwrite},
        )

        # NEW: capability system
        print("Resolving capabilities and dependencies...\n")
        cap_graph = resolve_capabilities(ctx)
        print("Building dependency graph...\n")
        dep_graph = build_dependency_graph(cap_graph)

        update_run_manifest(output_dir, run_id, status="started", cap_graph=cap_graph)

        ctx.capabilities = cap_graph
        ctx.dependency_graph = dep_graph
        print("Capabilities resolved and dependency graph built.\n")
        print(f"Capabilities: {list(cap_graph.capabilities.keys())}\n")
        print(f"Dependency graph: {dep_graph}\n")

        print("Dispatching generator...\n")
        dispatch_generator(ctx)
        update_run_status(output_dir, run_id, "completed")
        return True

    except Exception as e:
        if run_id:
            update_run_status(output_dir, run_id, "failed", error=format_user_error(e))
        print(f"\nError during PSE bootstrap:\n{format_user_error(e)}")
        return False


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


def write_run_manifest(output_dir: str, input_path: str, dsl_text: str, cap_graph=None):
    manifest_path = os.path.join(output_dir, "pse.manifest.json")
    run_id = str(uuid.uuid4())
    timestamp = utc_timestamp()

    run_entry = {
        "id": run_id,
        "timestamp": timestamp,
        "input_file": os.path.abspath(input_path),
        "capabilities": serialize_capabilities(cap_graph),
        "dsl": dsl_text,
        "status": "started",
        "error": None,
        "finished_at": None,
    }

    data = {"runs": []}

    if os.path.exists(manifest_path):
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as error:
            raise ValueError(f"Run manifest is not valid JSON: {manifest_path}") from error

    data.setdefault("runs", []).append(run_entry)

    write_json_atomic(manifest_path, data)

    return run_id


def update_run_status(output_dir: str, run_id: str, status: str, error: str = None, cap_graph=None):
    if not run_id:
        return

    manifest_path = os.path.join(output_dir, "pse.manifest.json")
    if not os.path.exists(manifest_path):
        return

    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as error:
        raise ValueError(f"Run manifest is not valid JSON: {manifest_path}") from error

    for run in data.get("runs", []):
        if run.get("id") == run_id:
            run["status"] = status
            if error is not None:
                run["error"] = error
            if cap_graph is not None:
                run["capabilities"] = serialize_capabilities(cap_graph)
            run["finished_at"] = utc_timestamp()
            break

    write_json_atomic(manifest_path, data)


def update_run_manifest(output_dir: str, run_id: str, status: str = None, error: str = None, cap_graph=None):
    if not run_id:
        return

    manifest_path = os.path.join(output_dir, "pse.manifest.json")
    if not os.path.exists(manifest_path):
        return

    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as error:
        raise ValueError(f"Run manifest is not valid JSON: {manifest_path}") from error

    for run in data.get("runs", []):
        if run.get("id") == run_id:
            if status is not None:
                run["status"] = status
            if error is not None:
                run["error"] = error
            if cap_graph is not None:
                run["capabilities"] = serialize_capabilities(cap_graph)
            break

    write_json_atomic(manifest_path, data)


def utc_timestamp():
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def write_json_atomic(path, data):
    directory = os.path.dirname(os.path.abspath(path))
    fd, temporary_path = tempfile.mkstemp(prefix=".pse-manifest-", dir=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2, ensure_ascii=True)
            handle.write("\n")
        os.replace(temporary_path, path)
    finally:
        if os.path.exists(temporary_path):
            os.remove(temporary_path)


def serialize_capabilities(cap_graph):
    if not cap_graph:
        return []

    return [
        {
            "name": name,
            "value": cap.value,
            "source": cap.source
        }
        for name, cap in sorted(cap_graph.capabilities.items())
    ]


def dispatch_generator(ctx: GenerationContext):
    target = (ctx.architecture.project.target or "dotnet").lower()

    if target == "dotnet":
        generate_dotnet(ctx)
        return

    raise ValueError(f"Unsupported target: {target}")
