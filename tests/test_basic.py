"""Basic smoke tests for dark-region-analysis."""

from typer.testing import CliRunner

from dark_region_analysis.cli import app
from dark_region_analysis.reporting import ReportFormat

runner = CliRunner()


def test_help_lists_analysis_commands() -> None:
    """Verify the CLI exposes the analysis commands."""
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "detect" in result.output
    assert "regions" in result.output


def test_report_format_values_are_stable() -> None:
    """Verify report format values remain script friendly."""
    assert [item.value for item in ReportFormat] == ["plain", "json", "csv"]
