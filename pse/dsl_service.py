from dataclasses import dataclass
from functools import lru_cache
from typing import Any

from textx import metamodel_from_file
from textx.exceptions import TextXSemanticError, TextXSyntaxError

from pse.language import GRAMMAR_PATH
from pse.validation import DslValidationError, ValidationProblem, validate_model


@dataclass(frozen=True)
class DiagnosticPosition:
    line: int
    character: int


@dataclass(frozen=True)
class DiagnosticRange:
    start: DiagnosticPosition
    end: DiagnosticPosition


@dataclass(frozen=True)
class DslDiagnostic:
    message: str
    range: DiagnosticRange
    severity: str = "error"
    source: str = "pse"

    def to_lsp(self):
        return {
            "range": {
                "start": {
                    "line": self.range.start.line,
                    "character": self.range.start.character,
                },
                "end": {
                    "line": self.range.end.line,
                    "character": self.range.end.character,
                },
            },
            "severity": 1 if self.severity == "error" else 2,
            "source": self.source,
            "message": self.message,
        }


@dataclass(frozen=True)
class DslDocument:
    model: Any = None
    diagnostics: tuple[DslDiagnostic, ...] = ()

    @property
    def is_valid(self):
        return not self.diagnostics


@lru_cache(maxsize=1)
def load_metamodel():
    return metamodel_from_file(GRAMMAR_PATH)


def parse_document(source_text: str, file_name: str = "<memory>"):
    model, diagnostics = parse_and_validate(source_text, file_name)
    return DslDocument(model=model, diagnostics=tuple(diagnostics))


def validate_document(source_text: str, file_name: str = "<memory>"):
    _, diagnostics = parse_and_validate(source_text, file_name)
    return diagnostics


def parse_and_validate(source_text: str, file_name: str = "<memory>"):
    try:
        model = load_metamodel().model_from_str(source_text, file_name=file_name)
        validate_model(model, source_text)
    except (TextXSyntaxError, TextXSemanticError) as error:
        return None, [diagnostic_from_textx_error(error, source_text)]
    except DslValidationError as error:
        return None, diagnostics_from_validation_error(error, source_text)

    return model, []


def diagnostic_from_textx_error(error, source_text: str):
    message = getattr(error, "message", None) or str(error)
    return DslDiagnostic(
        message=message,
        range=range_from_location(
            getattr(error, "line", None),
            getattr(error, "col", None),
            source_text,
        ),
    )


def diagnostics_from_validation_error(error: DslValidationError, source_text: str):
    return [
        diagnostic_from_validation_problem(problem, source_text)
        for problem in error.problems
    ]


def diagnostic_from_validation_problem(problem: ValidationProblem, source_text: str):
    return DslDiagnostic(
        message=problem.message,
        range=range_from_location(problem.line, problem.column, source_text),
    )


def range_from_location(line, column, source_text: str):
    start_line = max(int(line) - 1, 0) if line else 0
    start_character = max(int(column) - 1, 0) if column else 0
    end_character = start_character + 1

    lines = source_text.splitlines() or [""]
    if start_line < len(lines):
        line_length = len(lines[start_line])
        if start_character < line_length:
            end_character = min(start_character + 1, line_length)

    return DiagnosticRange(
        start=DiagnosticPosition(start_line, start_character),
        end=DiagnosticPosition(start_line, end_character),
    )
