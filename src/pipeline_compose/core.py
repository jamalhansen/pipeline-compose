"""Pure pipeline orchestration -- no subprocess/YAML I/O here.

The local-first toolkit's own STANDARDS.md already establishes a Unix-style
stdin/stdout convention across tools (`-`/`--pipe` reads stdin, `--json`
writes machine-readable stdout). This module just chains that convention:
each step's captured stdout becomes the next step's stdin, unless the step's
command contains a `{prev}` placeholder, in which case the previous output is
substituted inline instead (for tools that take a value as an argument rather
than reading it from stdin).

Subprocess execution is injected as `runner` so this stays testable without
shelling out; system.py provides the real one.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

RunnerResult = tuple[str, str, int]  # (stdout, stderr, returncode)
Runner = Callable[[str, str | None], RunnerResult]


@dataclass
class Step:
    name: str
    command: str


@dataclass
class Pipeline:
    name: str
    steps: list[Step]
    description: str = ""


@dataclass
class StepResult:
    name: str
    command: str
    stdout: str
    stderr: str
    returncode: int


class PipelineError(Exception):
    """Raised when a step in a pipeline exits non-zero."""

    def __init__(self, step: StepResult):
        self.step = step
        super().__init__(f"step {step.name!r} exited {step.returncode}: {step.stderr.strip()}")


def resolve_command(command: str, prev_output: str | None) -> tuple[str, str | None]:
    """Return (command_to_run, stdin_to_feed).

    If the command references {prev}, the previous step's output is
    substituted inline and nothing is piped via stdin. Otherwise the
    previous output (if any) is piped as stdin, Unix-pipe style.
    """
    if "{prev}" in command:
        return command.format(prev=(prev_output or "").strip()), None
    return command, prev_output


def run_pipeline(pipeline: Pipeline, runner: Runner, dry_run: bool = False) -> list[StepResult]:
    """Run every step in order, feeding each step's stdout to the next.

    Stops and raises PipelineError on the first non-zero exit -- a partial
    pipeline result is still returned via the exception's .step attribute
    for the caller to report, matching how a shell pipeline with `set -e`
    would behave.
    """
    results: list[StepResult] = []
    prev_output: str | None = None

    for step in pipeline.steps:
        command, stdin = resolve_command(step.command, prev_output)

        if dry_run:
            results.append(StepResult(name=step.name, command=command, stdout="", stderr="", returncode=0))
            prev_output = ""
            continue

        stdout, stderr, returncode = runner(command, stdin)
        result = StepResult(name=step.name, command=command, stdout=stdout, stderr=stderr, returncode=returncode)
        results.append(result)
        if returncode != 0:
            raise PipelineError(result)
        prev_output = stdout

    return results
