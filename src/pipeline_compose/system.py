"""YAML config loading and real subprocess execution for pipeline-compose."""
from __future__ import annotations

import subprocess
from pathlib import Path

import yaml

from .core import Pipeline, RunnerResult, Step


class ConfigError(Exception):
    """Raised when pipelines.yaml is missing or malformed."""


def load_pipelines(path: Path) -> dict[str, Pipeline]:
    if not path.exists():
        raise ConfigError(f"no pipeline config at {path}")

    raw = yaml.safe_load(path.read_text()) or {}
    pipelines_raw = raw.get("pipelines")
    if not pipelines_raw:
        raise ConfigError(f"{path} has no top-level 'pipelines' key")

    pipelines: dict[str, Pipeline] = {}
    for name, spec in pipelines_raw.items():
        steps_raw = spec.get("steps") or []
        if not steps_raw:
            raise ConfigError(f"pipeline {name!r} has no steps")
        steps = [Step(name=s["name"], command=s["command"]) for s in steps_raw]
        pipelines[name] = Pipeline(name=name, steps=steps, description=spec.get("description", ""))
    return pipelines


def shell_runner(command: str, stdin: str | None) -> RunnerResult:
    """Real runner: executes `command` via the shell, piping stdin if given."""
    result = subprocess.run(
        ["/bin/sh", "-c", command],
        input=stdin,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout, result.stderr, result.returncode
