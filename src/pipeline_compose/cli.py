from pathlib import Path
from typing import Annotated

import typer
from local_first_common.tracking import register_tool
from rich.console import Console

from .core import PipelineError, run_pipeline
from .system import ConfigError, load_pipelines, shell_runner

TOOL_NAME = "pipeline-compose"
_TOOL = register_tool(TOOL_NAME)

console = Console(stderr=True)
app = typer.Typer(
    help="Chains local-first tool CLIs into named pipelines defined in YAML, "
    "piping each step's captured output into the next step's command."
)

_CONFIG_OPTION = typer.Option("--config", help="Path to pipelines.yaml")
DEFAULT_CONFIG = Path("pipelines.yaml")


@app.command("list")
def list_pipelines(config: Annotated[Path, _CONFIG_OPTION] = DEFAULT_CONFIG) -> None:
    """List the pipelines defined in the config file."""
    try:
        pipelines = load_pipelines(config)
    except ConfigError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1) from e

    for name, pipeline in pipelines.items():
        console.print(f"[bold]{name}[/bold] ({len(pipeline.steps)} steps) -- {pipeline.description}")


@app.command()
def run(
    name: Annotated[str, typer.Argument(help="Pipeline name from the config file")],
    config: Annotated[Path, _CONFIG_OPTION] = DEFAULT_CONFIG,
    dry_run: Annotated[
        bool, typer.Option("--dry-run", "-n", help="Print resolved commands without executing them")
    ] = False,
) -> None:
    """Run a named pipeline, feeding each step's stdout into the next step's stdin."""
    try:
        pipelines = load_pipelines(config)
    except ConfigError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1) from e

    if name not in pipelines:
        console.print(f"[red]No pipeline named {name!r} in {config}[/red]")
        raise typer.Exit(1)

    try:
        results = run_pipeline(pipelines[name], shell_runner, dry_run=dry_run)
    except PipelineError as e:
        console.print(f"[red]FAILED[/red] at step {e.step.name!r}: {e.step.command}")
        console.print(e.step.stderr)
        raise typer.Exit(1) from e

    for r in results:
        prefix = "[yellow]DRY-RUN[/yellow]" if dry_run else "[green]OK[/green]"
        console.print(f"{prefix} {r.name}: {r.command}")


if __name__ == "__main__":
    app()
