# Choice reversals

Run from the repository folder:

```sh
uv sync
```

Add your API key to `.env` (see `.env.example`). In `main.py`, set the model,
prompt version, run name, and number of players per treatment.

```sh
uv run python main.py  ## run simulation
uv run python -m analysis.run_analysis.pilot_1 ## run analysis
```

Preview one treatment with `uv run python -m simulation.run 2A2P_4AR`.

If you are not using uv for package management, remove `uv run` and call `python` directly.

For analysis settings and outputs, see [analysis/README.md](analysis/README.md).
