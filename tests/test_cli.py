from typer.testing import CliRunner

from pipeline_compose.cli import app

CONFIG = """
pipelines:
  demo:
    description: a test pipeline
    steps:
      - name: one
        command: printf hi
      - name: two
        command: tr a-z A-Z
"""


def _write_config(tmp_path):
    path = tmp_path / "pipelines.yaml"
    path.write_text(CONFIG)
    return path


def test_list_shows_pipeline_and_description(tmp_path):
    config = _write_config(tmp_path)
    result = CliRunner().invoke(app, ["list", "--config", str(config)])
    assert result.exit_code == 0
    assert "demo" in result.output
    assert "a test pipeline" in result.output


def test_list_missing_config_exits_nonzero(tmp_path):
    result = CliRunner().invoke(app, ["list", "--config", str(tmp_path / "nope.yaml")])
    assert result.exit_code == 1


def test_run_executes_real_pipeline_end_to_end(tmp_path):
    config = _write_config(tmp_path)
    result = CliRunner().invoke(app, ["run", "demo", "--config", str(config)])
    assert result.exit_code == 0
    assert "OK" in result.output


def test_run_unknown_pipeline_exits_nonzero(tmp_path):
    config = _write_config(tmp_path)
    result = CliRunner().invoke(app, ["run", "nonexistent", "--config", str(config)])
    assert result.exit_code == 1


def test_run_dry_run_reports_without_executing(tmp_path):
    config = _write_config(tmp_path)
    result = CliRunner().invoke(app, ["run", "demo", "--config", str(config), "--dry-run"])
    assert result.exit_code == 0
    assert "DRY-RUN" in result.output


def test_run_failing_step_exits_nonzero(tmp_path):
    config = tmp_path / "pipelines.yaml"
    config.write_text("pipelines:\n  bad:\n    steps:\n      - name: boom\n        command: exit 1\n")
    result = CliRunner().invoke(app, ["run", "bad", "--config", str(config)])
    assert result.exit_code == 1
    assert "FAILED" in result.output
