import pytest

from pipeline_compose.system import ConfigError, load_pipelines, shell_runner


def test_load_pipelines_parses_steps(tmp_path):
    config = tmp_path / "pipelines.yaml"
    config.write_text(
        """
pipelines:
  demo:
    description: a test pipeline
    steps:
      - name: one
        command: echo hi
      - name: two
        command: cat
"""
    )
    pipelines = load_pipelines(config)
    assert set(pipelines) == {"demo"}
    demo = pipelines["demo"]
    assert demo.description == "a test pipeline"
    assert [s.name for s in demo.steps] == ["one", "two"]
    assert [s.command for s in demo.steps] == ["echo hi", "cat"]


def test_load_pipelines_missing_file_raises(tmp_path):
    with pytest.raises(ConfigError):
        load_pipelines(tmp_path / "nope.yaml")


def test_load_pipelines_no_pipelines_key_raises(tmp_path):
    config = tmp_path / "pipelines.yaml"
    config.write_text("not_pipelines: {}\n")
    with pytest.raises(ConfigError):
        load_pipelines(config)


def test_load_pipelines_empty_steps_raises(tmp_path):
    config = tmp_path / "pipelines.yaml"
    config.write_text("pipelines:\n  demo:\n    steps: []\n")
    with pytest.raises(ConfigError):
        load_pipelines(config)


def test_shell_runner_executes_real_command_and_pipes_stdin():
    stdout, _stderr, returncode = shell_runner("tr a-z A-Z", "hello")
    assert stdout == "HELLO"
    assert returncode == 0


def test_shell_runner_reports_nonzero_exit():
    _stdout, _stderr, returncode = shell_runner("exit 3", None)
    assert returncode == 3
