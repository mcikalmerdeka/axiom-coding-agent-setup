---
name: running-notebooks
description: Use when a task requires building, rebuilding, or executing a Jupyter notebook end-to-end — especially long-running training notebooks, nbconvert runs, notebooks that must produce a model or data artifact, or notebooks whose executed outputs and findings must be verified.
---

# Running Notebooks End-to-End

## Overview

A notebook is code, narrative, and **executed outputs**. The deliverable is a
notebook that runs top-to-bottom from a clean kernel and a verified artifact —
not a draft with plausible-looking cells. Build it programmatically, execute it
headlessly, and prove the outputs with the same checks you would run on code.

## When to Use

Use when:

- Rebuilding or revamping an existing notebook.
- A training notebook must produce a model, CSV, or other artifact.
- Tuning or EDA makes the notebook slow enough that a failed cell costs minutes.
- Cell outputs, plots, or markdown findings must match the final code.
- The notebook and an app must share one cleaning/encoding contract.

Do not use for quick scratch notebooks or a single exploratory cell.

## Workflow

1. **Read the context first.** Inspect the existing notebook cells, the shared
   `utils/` or library modules, the reference project, the data, and the
   dependency file. Identify the artifact the notebook must produce and where
   it is written.
2. **Separate reusable logic from narrative.** Put cleaning, encoding, schema,
   and artifact-contract code in a small importable package used by both the
   notebook and the app. The notebook imports it; it does not duplicate it.
   This prevents training/serving drift.
3. **Build the notebook with a throwaway builder.** Use `nbformat` in a temp
   directory, not hand-edited JSON. A minimal builder:

   ```python
   import nbformat as nbf

   cells = []
   def md(text): cells.append(nbf.v4.new_markdown_cell(text))
   def code(text): cells.append(nbf.v4.new_code_cell(text))

   # append cells in order
   md("# Title")
   code("import pandas as pd")

   nb = nbf.v4.new_notebook(cells=cells)
   nb.metadata["kernelspec"] = {
       "display_name": "Python 3", "language": "python", "name": "python3"
   }
   nbf.write(nb, "notebook.ipynb")
   ```

   Keep the builder outside the repo. The notebook is the deliverable.
4. **Set up and verify the environment.** `uv sync` (or the project's install
   command), then confirm `ipykernel`, `nbconvert`, and `nbclient` are present.
5. **Execute headlessly.**

   ```powershell
   uv run jupyter nbconvert --to notebook --execute --inplace notebook.ipynb --ExecutePreprocessor.timeout=1800
   ```

   `[NbConvertApp] Writing ... bytes to notebook.ipynb` means success.
6. **Background long runs; check once, do not poll.** A tuning notebook can take
   minutes. Run it in the background, then check the output tail and the kernel's
   CPU time once when asked. Rising CPU means it is working; a flat CPU with no
   output usually means a hung kernel or an interactive prompt.
7. **On failure, fix the builder and rebuild.** Read the exact cell traceback.
   Patch the builder source, regenerate the notebook, re-execute. Do not patch
   only the `.ipynb` JSON and leave the builder stale. If the failure is a
   library/API mismatch, inspect the real return value before indexing it.
8. **After success, update findings in place.** If only markdown changed, use
   `nbformat.read` / `nbf.write` to replace markdown cells without losing the
   executed outputs. Re-run only when code changed.
9. **Verify the artifact, not just the notebook.** Reload the artifact, score a
   raw sample row, run the project tests, check for PII, and confirm the
   notebook's final markdown quotes the real numbers. Submit the app's primary
   form through `AppTest`, not just a render check — a render-only test misses
   input-type crashes. Then repeat the test suite from a fresh clone to prove
   every import is tracked.

## Common Mistakes

| Mistake | Reality |
|---|---|
| Hand-editing notebook JSON | Cell IDs, outputs, and metadata break. Use `nbformat`. |
| Importing `get_model_pipeline`, `compare_cv_metrics`, or `tune_pipelines` unsuffixed from `utils` | Those are the **regression** aliases. Import the classification helpers from `utils.classification_evals_and_tuning`. |
| Assuming column names | `compare_cv_metrics` returns `Model`, not `MODEL`. Inspect the actual DataFrame before indexing. |
| Replacing real inputs with medians for demo profiles | A tree that learned only age-at-hire gives every median-date profile the same score. Score the exact profiles the app will show. |
| Re-running the whole notebook to change markdown | Expensive and pointless. Update markdown cells in place with `nbformat`. |
| Trusting a green notebook | The notebook can run and still write a broken artifact. Reload it and score a row. |
| Only rendering the app in `AppTest` | A render-only smoke test misses input-type crashes. Submit the primary form and assert the result. |
| Trusting local imports | An untracked `utils/` or local package passes in your worktree and fails in a clean clone. Track/vendor it and run the clone test. |
| Validating only the happy-path artifact | Check every key the app reads, including nested metrics, summary, predictions, and examples. |
| Formatting a raw probability as a percentage | `0.60` with `%.1f%%` renders as `0.6%`. Add a display-only `×100` column and keep raw values for download. |
| Blanket `.str.strip()` on object columns | `datetime.date` objects and mixed numeric cells break or become `NaN`. Strip only values that are actually strings. |
| Polling a long run repeatedly | Check process CPU and the output tail once. Rising CPU = working; no CPU + no output = investigate. |
| Leaving the builder in the repo | The notebook is the source of truth after execution. Keep the builder in temp. |

## Quick Reference

| Action | Command |
|---|---|
| Build notebook | `uv run python C:\...\temp\build_notebook.py` |
| Execute | `uv run jupyter nbconvert --to notebook --execute --inplace notebook.ipynb --ExecutePreprocessor.timeout=1800` |
| Missing kernel | `uv run python -m ipykernel install --user --name python3` once |
| Check a run | Read the output tail, then `Get-Process -Id <pid>` for CPU |
| Update markdown only | `nbformat.read` → replace `cell.source` → `nbf.write` |
| Reload artifact | `load_artifact("models/<name>.joblib")`, score one raw row |

## Checklist

- [ ] Builder script is outside the repo (or clearly marked throwaway).
- [ ] Dependencies installed and imports verified.
- [ ] Notebook runs top-to-bottom from a clean kernel with no errors.
- [ ] Outputs are real; no placeholder findings remain.
- [ ] Artifact reloads and scores a raw row end-to-end.
- [ ] Asking the artifact for every key the app reads succeeds; nested metrics/examples are validated.
- [ ] The app's primary form is submitted through `AppTest` and renders a result (not just a render check).
- [ ] Display values (e.g. percentages) are separate from raw values used in downloads.
- [ ] Project tests pass after the notebook run.
- [ ] A fresh clone + install + test run passes; every imported local package is tracked or vendored.
- [ ] No PII appears in the artifact, previews, or UI.
- [ ] Final markdown quotes the actual metrics/gains, not guesses.
