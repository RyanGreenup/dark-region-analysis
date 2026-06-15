"""Command-line interface for dark-region-analysis."""

from __future__ import annotations

from typing import Annotated

import typer

app = typer.Typer(help="Analysis of dark regions on a white rectangle", no_args_is_help=True)

NameArgument = Annotated[str, typer.Argument(help="Name to greet.")]


@app.callback()
def callback() -> None:
    """Analysis of dark regions on a white rectangle."""


@app.command()
def greet(name: NameArgument = "World") -> None:
    """Print a friendly greeting."""
    typer.echo(f"Hello, {name}!")


def main() -> None:
    """Run the CLI application."""
    app()

if __name__ == "__main__":
    # NOTE: MUST call main() (to call `app()`) for the cli to work as the entry point
     main()
