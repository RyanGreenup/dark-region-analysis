"""Command-line interface for dark-region-analysis."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import numpy as np
import typer
from PIL import Image, UnidentifiedImageError

from dark_region_analysis.annotation import annotate_rectangle, annotate_regions
from dark_region_analysis.detection import (
    detect_dark_regions,
    detect_white_rectangle,
    format_box,
)
from dark_region_analysis.reporting import ReportFormat, render_report

app = typer.Typer(help="Analysis of dark regions on a white rectangle", no_args_is_help=True)

InputImage = Annotated[Path, typer.Argument(exists=True, readable=True, help="Source image.")]
OutputImage = Annotated[Path, typer.Argument(help="Annotated output image path.")]
DarkValue = Annotated[
    float,
    typer.Option(
        min=0.0,
        max=1.0,
        help="Maximum normalized brightness for a dark region.",
    ),
]
MinAreaFrac = Annotated[
    float,
    typer.Option(min=0.0, help="Minimum dark-region area as a fraction of rectangle area."),
]
MaxAspect = Annotated[
    float,
    typer.Option(min=1.0, help="Maximum bounding-box aspect ratio for accepted regions."),
]
ReportFormatOption = Annotated[
    ReportFormat,
    typer.Option(help="Report output format."),
]


@app.callback()
def callback() -> None:
    """Run dark-region analysis commands."""


@app.command()
def detect(input_image: InputImage, output_image: OutputImage) -> None:
    """Detect the white rectangle and save a bounding-box annotation."""
    try:
        image = _load_rgb_image(input_image)
        box = detect_white_rectangle(np.array(image))
        _save_image(annotate_rectangle(image, box), output_image)
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc
    except UnidentifiedImageError as exc:
        raise typer.BadParameter(f"'{input_image}' is not a valid image file") from exc

    typer.echo(f"white_rectangle_bbox: {format_box(box)}")
    typer.echo(f"Saved annotated image to {output_image}")


@app.command()
def regions(
    input_image: InputImage,
    output_image: OutputImage,
    dark_value: DarkValue = 0.85,
    min_area_frac: MinAreaFrac = 2.0e-4,
    max_aspect: MaxAspect = 3.0,
    report_format: ReportFormatOption = ReportFormat.PLAIN,
) -> None:
    """Detect dark regions, print measurements, and save an annotation."""
    try:
        image = _load_rgb_image(input_image)
        array = np.array(image)
        box = detect_white_rectangle(array)
        found = detect_dark_regions(
            array,
            box,
            dark_value=dark_value,
            min_area_frac=min_area_frac,
            max_aspect=max_aspect,
        )
        report = render_report(found, box, report_format)
        _save_image(annotate_regions(image, box, found), output_image)
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc
    except UnidentifiedImageError as exc:
        raise typer.BadParameter(f"'{input_image}' is not a valid image file") from exc

    typer.echo(report)
    typer.echo(f"Saved annotated image to {output_image}")


def main() -> None:
    """Run the CLI application."""
    app()


def _load_rgb_image(path: Path) -> Image.Image:
    """Load an image from disk and convert it to RGB."""
    with Image.open(path) as image:
        return image.convert("RGB")


def _save_image(image: Image.Image, path: Path) -> None:
    """Create the parent directory and save an image."""
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)

if __name__ == "__main__":
    main()
