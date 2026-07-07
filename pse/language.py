import os

from textx import language, metamodel_from_file
from textx.exceptions import TextXSemanticError

from pse.validation import DslValidationError, validate_model


BASE_DIR = os.path.dirname(__file__)
GRAMMAR_PATH = os.path.join(BASE_DIR, "grammar", "pse.tx")


@language("pse", "*.pse")
def pse_language():
    """Project Scaffolding Engine DSL."""
    metamodel = metamodel_from_file(GRAMMAR_PATH)
    metamodel.register_model_processor(validate_pse_model)
    return metamodel


def validate_pse_model(model, metamodel):
    source_text = ""
    input_file = getattr(model, "_tx_filename", None)
    if input_file and os.path.exists(input_file):
        with open(input_file, "r", encoding="utf-8") as f:
            source_text = f.read()

    try:
        validate_model(model, source_text)
    except DslValidationError as error:
        problem = error.problems[0]
        raise TextXSemanticError(
            problem.message,
            line=problem.line,
            col=problem.column,
            filename=input_file,
        ) from error
