"""Regenerate the API reference files from the bundled ``utils`` package.

Run from anywhere:

    python scripts/dev/generate_references.py

The generated files live in ``references/api/`` and are intentionally
checked in so the skill works without running this script.
"""

from __future__ import annotations

import ast
import re
import textwrap
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[2]
SOURCE_DIR = SKILL_ROOT / "scripts" / "utils"
OUTPUT_DIR = SKILL_ROOT / "references" / "api"

MODULES = [
    ("preprocessing", "Preprocessing", "Data inspection, cleaning, imputation, outlier handling, scaling, and encoding."),
    ("feature_selection", "Feature selection", "Correlation analysis, categorical association tests, VIF, and univariate importance."),
    ("statistics", "Statistics", "Descriptive statistics for numerical, categorical, and date columns plus distribution typing."),
    ("visualization", "Visualization", "Notebook-friendly distribution, count, relationship, and correlation plots."),
    ("classification_evals_and_tuning", "Classification", "Binary classification evaluation, model comparison, and hyperparameter tuning."),
    ("regression_evals_and_tuning", "Regression", "Regression evaluation, model comparison, and hyperparameter tuning."),
    ("ab_testing", "A/B testing", "Sample sizing, assumption checks, hypothesis tests, and end-to-end experiment analysis."),
    ("time_series", "Time series", "Decomposition, stationarity, feature engineering, splitting, diagnostics, and forecast metrics."),
    ("text_preprocessing", "Text processing", "Text cleaning, tokenization, lemmatization, stemming, word clouds, and frequency analysis."),
    ("translation_utils", "Translation", "Language detection, row filtering, and batched translation helpers."),
    ("eda_report", "EDA report", "Self-contained HTML exploratory data analysis reports."),
]

OUTPUT_NAMES = {
    "classification_evals_and_tuning": "classification.md",
    "regression_evals_and_tuning": "regression.md",
    "text_preprocessing": "text.md",
    "translation_utils": "translation.md",
    "eda_report": "eda-report.md",
    "feature_selection": "feature-selection.md",
    "time_series": "time-series.md",
    "ab_testing": "ab-testing.md",
}

HEADER = """# {title} API

Source: `scripts/utils/{module}.py`

> Auto-generated from the bundled source. Re-run
> `python scripts/dev/generate_references.py` after changing the package.

"""


def clean_docstring(doc: str | None) -> str:
    text = textwrap.dedent(doc or "").strip()
    text = re.sub(
        r"(?m)^(Parameters|Returns|Raises|Examples|Example|Notes|Attributes|Yields):\n-+\s*$",
        r"**\1**",
        text,
    )
    text = re.sub(r"(?m)^(SCALING METHOD GUIDE):\n-+\s*$", r"**\1**", text)
    return text


def summary_from_doc(doc: str | None) -> str:
    paragraph: list[str] = []
    for line in clean_docstring(doc).splitlines():
        stripped = line.strip()
        if not stripped:
            if paragraph:
                break
            continue
        if stripped.startswith(("**", "#", "```", "|")):
            continue
        paragraph.append(stripped)
    return " ".join(paragraph).rstrip(".")


def format_args(args: ast.arguments, *, drop_self: bool = False) -> str:
    if drop_self:
        if args.posonlyargs:
            args = ast.arguments(
                posonlyargs=args.posonlyargs[1:],
                args=args.args,
                vararg=args.vararg,
                kwonlyargs=args.kwonlyargs,
                kw_defaults=args.kw_defaults,
                kwarg=args.kwarg,
                defaults=args.defaults,
            )
        elif args.args:
            args = ast.arguments(
                posonlyargs=args.posonlyargs,
                args=args.args[1:],
                vararg=args.vararg,
                kwonlyargs=args.kwonlyargs,
                kw_defaults=args.kw_defaults,
                kwarg=args.kwarg,
                defaults=args.defaults,
            )
    return ast.unparse(args)


def render_function(node: ast.FunctionDef | ast.AsyncFunctionDef, *, owner: str | None = None) -> str:
    name = f"{owner}.{node.name}" if owner else node.name
    doc = clean_docstring(ast.get_docstring(node))
    returns = f" -> {ast.unparse(node.returns)}" if node.returns else ""
    signature = f"{node.name}({format_args(node.args, drop_self=owner is not None)}){returns}"
    body = f"### `{name}`\n\n```python\ndef {signature}\n```\n"
    if doc:
        body += f"\n{doc}\n"
    return body


def render_class(node: ast.ClassDef) -> str:
    init = next(
        (
            child
            for child in node.body
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
            and child.name == "__init__"
        ),
        None,
    )
    ctor = f"{node.name}({format_args(init.args, drop_self=True)})" if init else f"{node.name}()"

    doc = clean_docstring(ast.get_docstring(node))
    section = f"## class `{node.name}`\n\n```python\n{ctor}\n```\n"
    if doc:
        section += f"\n{doc}\n"

    for child in node.body:
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) and not child.name.startswith("_"):
            section += "\n" + render_function(child, owner=node.name)

    return section


def parse_module(module_name: str) -> list[dict[str, str]]:
    path = SOURCE_DIR / f"{module_name}.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    entries: list[dict[str, str]] = []

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and not node.name.startswith("_"):
            entries.append(
                {
                    "name": node.name,
                    "summary": summary_from_doc(ast.get_docstring(node)),
                    "markdown": render_function(node),
                }
            )
        elif isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
            entries.append(
                {
                    "name": node.name,
                    "summary": summary_from_doc(ast.get_docstring(node)) or "Class",
                    "markdown": render_class(node),
                }
            )

    return entries


def build() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    index_parts = [
        "# API index\n",
        "Every public function and class in the bundled `utils` package, grouped by module.\n",
        "The internal modules `_ml_common.py` and `_plotting.py` are implementation details "
        "and are not part of the public API.\n",
    ]

    for module_name, title, description in MODULES:
        entries = parse_module(module_name)
        filename = OUTPUT_NAMES.get(module_name, f"{module_name.replace('_', '-')}.md")
        lines = [HEADER.format(title=title, module=module_name), f"{description}\n", "## Quick index\n"]
        lines.append("| Name | Summary |")
        lines.append("| --- | --- |")
        for entry in entries:
            lines.append(f"| `{entry['name']}` | {entry['summary'].replace('|', '\\|')} |")
        lines.append("")

        for entry in entries:
            lines.append(entry["markdown"].rstrip())
            lines.append("")

        output_path = OUTPUT_DIR / filename
        output_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")

        index_parts.append(f"\n## {title}\n")
        index_parts.append(f"{description} See [`api/{filename}`](api/{filename}).\n")
        for entry in entries:
            index_parts.append(f"- [`{entry['name']}`](api/{filename}) — {entry['summary']}")

        print(f"wrote {output_path.relative_to(SKILL_ROOT)} ({len(entries)} entries)")

    (SKILL_ROOT / "references" / "api-index.md").write_text(
        "\n".join(index_parts).rstrip() + "\n", encoding="utf-8"
    )
    print("wrote references/api-index.md")


if __name__ == "__main__":
    build()
