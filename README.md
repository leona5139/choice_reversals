# Choice reversals

Run from the repository folder:

```sh
uv sync
```

Add your API key to `.env` (see `.env.example`). In `main.py`, set the model,
prompt version, run name, and number of players per treatment.

```sh
uv run python main.py
uv run python -m analysis.run_analysis.pilot
```

For analysis settings and outputs, see [analysis/README.md](analysis/README.md).
