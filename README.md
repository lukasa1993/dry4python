# dry4python

`dry4python` finds repeated normalized token blocks in Python source. Identifiers, numeric literals, and string literals are normalized, so structurally equal code is detected even when names and constants differ.

## Install

```bash
pipx install git+https://github.com/lukasa1993/dry4python.git
```

## Run

```bash
dry4python --min-tokens 30 --fail
```

Use path fragments to limit the scan:

```bash
dry4python src/domain src/services
```

Use `--json` for machine-readable output. The command exits with status `2` when `--fail` is set and duplication is found.

## Development

```bash
python -m pip install -e . pytest
pytest -q
```
