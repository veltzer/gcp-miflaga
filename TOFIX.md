# TOFIX

Findings from a code scan on 2026-10-04.

## Medium

- `Dockerfile:10` - only `pyproject.toml` is copied and dependencies are installed with `uv pip install -r pyproject.toml`, which resolves the newest releases at build time and ignores `uv.lock`, so the deployed image never runs the versions the tests ran against; copy `uv.lock` too and install with `uv sync --frozen --no-dev` (or `uv export --frozen | uv pip install -r -`).
- `pyproject.toml:10` - `webtest` is a test-only library (used only by `tests/app_test.py`) but sits in `[project].dependencies`, so it is installed into the production Cloud Run image; move it to the `dev` dependency group next to `types-WebTest`.

## Low

- `src/main.py:29` - `build_info.json` is opened relative to the current working directory, while the word bank is resolved from `HERE` (line 37); it only works because the Docker `WORKDIR` and the test `os.chdir` happen to be the repo root - resolve it from `HERE` (`os.path.join(HERE, "..", "build_info.json")`) like the other data file.
- `pyproject.toml:26` - `mypy_path = "src:python:scripts"` names `python` and `scripts` directories that do not exist; reduce to `src`.
- `doc/TODO.txt` - `doc/TODO.txt` and `doc/DONE.txt` are tracked empty files; delete them or put content in them.
