# pipeline-compose

Chains local-first tool CLIs into named pipelines defined in YAML. Each
step's captured stdout is piped into the next step's stdin -- the same
convention `STANDARDS.md` already establishes across the toolkit
(`-`/`--pipe` reads stdin, `--json` writes machine-readable stdout) -- so
composing tools doesn't require a new abstraction, just a config file.

## Quickstart

```bash
cp pipelines.yaml.example pipelines.yaml
uv run pipeline-compose list
uv run pipeline-compose run demo --dry-run   # print resolved commands only
uv run pipeline-compose run demo             # actually run it
```

## Config format

```yaml
pipelines:
  my-pipeline:
    description: what this chain does
    steps:
      - name: step-one
        command: some-tool --json
      - name: step-two
        command: another-tool --pipe
```

Each step is run via the shell. By default, the previous step's stdout is
piped to the current step's stdin. If a step's command contains `{prev}`,
the previous step's (stripped) output is substituted inline instead, and
nothing is piped -- for tools that take a value as an argument rather than
reading it from stdin.

A pipeline stops at the first step that exits non-zero and reports which
step failed and its stderr, matching how a shell pipeline under `set -e`
would behave.

## Status

`pipelines.yaml.example` ships one verified demo pipeline (plain shell
commands) proving the chaining mechanism actually works, plus a commented
template for wiring in real local-first tools. Flags for real tools aren't
pre-filled -- check each tool's actual `--help` before wiring it in, rather
than trust a guessed flag name.
