# Tests

## `web_pages/`

Saved copies of NM OCD **Well Details** HTML (same layout as the live site). Filenames are the well API, e.g. `30-015-25325.html`. Use them to manually check the parser or extend tests.

Repo layout:

```text
web_pages/          ← HTML fixtures (sibling of tests/, not inside tests/)
tests/              ← this folder
```

## Run tests

From the **repository root** (where `pyproject.toml` is):

```bash
# Install once
pip install -e ".[dev]"

# All tests
pytest tests/ -q

# Parser tests only (use content.html + models)
pytest tests/test_parse.py -q

# Repository / SQLite helpers
pytest tests/test_repository.py -q
```

If you use a virtual environment, activate it first, then run the same `pytest` commands.

If `pytest` cannot import `synmax_takehome`, install from the repo root: `pip install -e .` (or set `PYTHONPATH` to the `src` folder).

On Windows, activate `.venv` with `venv_shell.bat` (new window) or `call venv_here.bat` (current prompt); see repo root `README.md`.

## Try the parser on a `web_pages/` file

From the repo root, after `pip install -e .`, start Python and run:

```python
from pathlib import Path
from synmax_takehome.scraping.parse import parse_well_html

p = Path("web_pages/30-015-25325.html")
row = parse_well_html(p.read_text(encoding="utf-8"), fallback_api=p.stem)
print(row["API"], row["Status"])
```

Or open the `.html` files in a browser to compare with printed fields.
