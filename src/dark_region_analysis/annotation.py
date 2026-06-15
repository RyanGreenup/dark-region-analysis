"""Draw rectangle and dark-region annotations."""

from __future__ import annotations

import math

from PIL import Image, ImageDraw, ImageFont

from dark_region_analysis.models import BoundingBox, DarkRegion

BOX_COLOR = (220, 30, 30)
REGION_COLOR = (0, 200, 255)
CENTER_COLOR = (255, 0, 200)
LINE_COLOR = (255, 210, 0)
MARKER_INFLATE = 1.3


def annotate_rectangle(image: Image.Image, box: BoundingBox) -> Image.Image:
    """Draw the detected rectangle on a copy of the image."""
    output = image.convert("RGB")
    draw = ImageDraw.Draw(output)
    thickness = max(2, math.floor(max(output.size) * 0.004))
    _draw_rectangle_outline(draw, box, thickness)
    return output


def annotate_regions(
    image: Image.Image,
    box: BoundingBox,
    regions: list[DarkRegion],
) -> Image.Image:
    """Draw the rectangle, center marker, dark regions, labels, and center lines."""
    output = annotate_rectangle(image, box)
    draw = ImageDraw.Draw(output)
    scale = max(output.size)
    thickness = max(2, scale // 350)
    font = _load_font(max(14, scale // 45))
    center_x, center_y = box.center

    for region in regions:
        draw.line(
            [(center_x, center_y), (region.cx, region.cy)],
            fill=LINE_COLOR,
            width=max(2, thickness),
        )

    for region in regions:
        _draw_region_marker(draw, region, thickness, font)

    _draw_center_marker(draw, box, scale, thickness)
    return output


def _draw_rectangle_outline(
    draw: ImageDraw.ImageDraw,
    box: BoundingBox,
    thickness: int,
) -> None:
    """Draw a rectangle outline with deterministic inward thickness."""
    for offset in range(thickness):
        draw.rectangle(
            [box.x1 + offset, box.y1 + offset, box.x2 - 1 - offset, box.y2 - 1 - offset],
            outline=BOX_COLOR,
            width=1,
        )


def _draw_region_marker(
    draw: ImageDraw.ImageDraw,
    region: DarkRegion,
    thickness: int,
    font: ImageFont.ImageFont,
) -> None:
    """Draw one dark-region ring and label."""
    radius = region.radius * MARKER_INFLATE
    draw.ellipse(
        [region.cx - radius, region.cy - radius, region.cx + radius, region.cy + radius],
        outline=REGION_COLOR,
        width=thickness,
    )
    label = str(region.index)
    text_box = draw.textbbox((0, 0), label, font=font)
    text_width = text_box[2] - text_box[0]
    text_height = text_box[3] - text_box[1]
    label_x = region.cx + radius + 2
    label_y = region.cy - radius - text_height - 2
    draw.rectangle(
        [label_x - 2, label_y - 2, label_x + text_width + 2, label_y + text_height + 2],
        fill=(0, 0, 0),
    )
    draw.text((label_x, label_y), label, fill=REGION_COLOR, font=font)


def _draw_center_marker(
    draw: ImageDraw.ImageDraw,
    box: BoundingBox,
    scale: int,
    thickness: int,
) -> None:
    """Draw a crosshair and dot at the rectangle center."""
    center_x, center_y = box.center
    radius = max(6, scale // 90)
    draw.line(
        [(center_x - radius, center_y), (center_x + radius, center_y)],
        fill=CENTER_COLOR,
        width=thickness,
    )
    draw.line(
        [(center_x, center_y - radius), (center_x, center_y + radius)],
        fill=CENTER_COLOR,
        width=thickness,
    )
    draw.ellipse(
        [
            center_x - radius // 2,
            center_y - radius // 2,
            center_x + radius // 2,
            center_y + radius // 2,
        ],
        fill=CENTER_COLOR,
    )


def _load_font(size: int) -> ImageFont.ImageFont:
    """Load Pillow's default font with a size when the installed version supports it."""
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()
