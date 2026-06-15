"""Basic smoke tests for dark-region-analysis."""

from typer.testing import CliRunner

from dark_region_analysis.cli import app

runner = CliRunner()


def test_greet_command() -> None:
    """Verify the exemplar Typer command runs."""
    result = runner.invoke(app, ["greet", "Ada"])

    assert result.exit_code == 0
    assert "Hello, Ada!" in result.output
