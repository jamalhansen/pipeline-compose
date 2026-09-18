# pipeline-compose

Chains local-first tool CLIs into named pipelines defined in YAML, piping each step's captured output into the next step's command.

## Quickstart

```bash
uv run pipeline-compose
```

## Status

Scaffolded via `local-first-common/scripts/new_tool.py` -- replace `core.run()`
and the CLI options in `cli.py` with the tool's real logic.
