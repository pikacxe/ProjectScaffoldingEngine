import os

from textx import generator

from pse.generators.dotnet.generator import generate_dotnet
from pse.generators.dotnet.mapper import map_model_to_architecture
from pse.heuristics.dependency_builder import build_dependency_graph
from pse.heuristics.loader import load_all_heuristics
from pse.heuristics.resolver import resolve_capabilities
from pse.model.generation_context import GenerationContext
from pse.validation import validate_model


@generator("pse", "dotnet")
def pse_dotnet_generator(metamodel, model, output_path, overwrite, debug):
    """Generate a .NET solution from a PSE model."""
    input_file = getattr(model, "_tx_filename", None)
    source_text = ""
    if input_file and os.path.exists(input_file):
        with open(input_file, "r", encoding="utf-8") as f:
            source_text = f.read()

    validate_model(model, source_text)

    output_dir = output_path or os.getcwd()
    os.makedirs(output_dir, exist_ok=True)

    heuristics = load_all_heuristics()
    architecture = map_model_to_architecture(model)
    ctx = GenerationContext(
        architecture=architecture,
        output_dir=output_dir,
        presets=heuristics["presets"],
        packages=heuristics["packages"],
        versions=heuristics["versions"],
    )

    ctx.capabilities = resolve_capabilities(ctx)
    ctx.dependency_graph = build_dependency_graph(ctx.capabilities)

    generate_dotnet(ctx)
