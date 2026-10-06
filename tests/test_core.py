import pytest

from pipeline_compose.core import (
    Pipeline,
    PipelineError,
    Step,
    resolve_command,
    run_pipeline,
)


class TestResolveCommand:
    def test_no_placeholder_pipes_prev_as_stdin(self):
        command, stdin = resolve_command("tr a-z A-Z", "hello")
        assert command == "tr a-z A-Z"
        assert stdin == "hello"

    def test_placeholder_substitutes_and_drops_stdin(self):
        command, stdin = resolve_command("echo {prev}-suffix", "hello\n")
        assert command == "echo hello-suffix"
        assert stdin is None

    def test_first_step_has_no_prev(self):
        command, stdin = resolve_command("echo start", None)
        assert command == "echo start"
        assert stdin is None


class TestRunPipeline:
    def _pipeline(self, *steps):
        return Pipeline(name="p", steps=[Step(name=n, command=c) for n, c in steps])

    def test_chains_stdout_to_next_stdin(self):
        calls = []

        def runner(command, stdin):
            calls.append((command, stdin))
            return (f"out-of-{command}", "", 0)

        pipeline = self._pipeline(("a", "step-a"), ("b", "step-b"))
        results = run_pipeline(pipeline, runner)

        assert calls == [("step-a", None), ("step-b", "out-of-step-a")]
        assert [r.stdout for r in results] == ["out-of-step-a", "out-of-step-b"]

    def test_stops_and_raises_on_first_failure(self):
        def runner(command, stdin):
            if command == "boom":
                return ("", "it broke", 1)
            return ("ok", "", 0)

        pipeline = self._pipeline(("first", "fine"), ("second", "boom"), ("third", "never runs"))

        with pytest.raises(PipelineError) as exc_info:
            run_pipeline(pipeline, runner)

        assert exc_info.value.step.name == "second"
        assert "it broke" in str(exc_info.value)

    def test_dry_run_never_calls_runner(self):
        calls = []

        def runner(command: str, stdin: str | None) -> tuple[str, str, int]:
            calls.append(1)
            return "", "", 0

        pipeline = self._pipeline(("a", "echo {prev}"), ("b", "cat"))
        results = run_pipeline(pipeline, runner, dry_run=True)
        assert calls == []
        assert len(results) == 2
        assert all(r.returncode == 0 for r in results)
