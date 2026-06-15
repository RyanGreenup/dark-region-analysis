"""Detect a smooth white rectangle and dark enclosed regions."""

from __future__ import annotations

from typing import TypeAlias

import numpy as np
import numpy.typing as npt
from scipy.ndimage import binary_fill_holes, binary_opening, uniform_filter
from skimage.filters import gaussian
from skimage.measure import label, regionprops

from dark_region_analysis.models import BoundingBox, DarkRegion

ImageArray: TypeAlias = npt.NDArray[np.uint8]
BoolMask: TypeAlias = npt.NDArray[np.bool_]
FloatArray: TypeAlias = npt.NDArray[np.float64]


def validate_rgb_image(image: npt.NDArray[np.generic]) -> ImageArray:
    """Return the image as RGB uint8 data or raise a value error."""
    if image.ndim != 3 or image.shape[2] != 3:
        raise ValueError("Expected an RGB image array with shape (height, width, 3)")
    if image.dtype != np.uint8:
        raise ValueError("Expected an RGB image array with dtype uint8")
    return image


def smooth_white_components(image: npt.NDArray[np.generic]) -> tuple[BoolMask, BoolMask]:
    """Return the largest smooth-white mask and the same mask with holes filled."""
    rgb = validate_rgb_image(image)
    height, width = rgb.shape[:2]
    normalized = rgb.astype(np.float32) / 255.0
    max_channel = normalized.max(axis=2)
    min_channel = normalized.min(axis=2)
    value = max_channel
    saturation = (max_channel - min_channel) / np.maximum(max_channel, 1e-6)
    gray = normalized.mean(axis=2)

    window = max(7, int(round(min(width, height) * 0.017)))
    mean = uniform_filter(gray, window)
    local_variance = uniform_filter(gray * gray, window) - mean * mean
    local_std = np.sqrt(np.maximum(local_variance, 0.0))

    mask = (value > 0.85) & (saturation < 0.08) & (local_std < 0.05)
    opened = binary_opening(mask, structure=np.ones((7, 7)))
    largest = _largest_component(np.asarray(opened, dtype=bool))
    filled = np.asarray(binary_fill_holes(largest), dtype=bool)
    return largest, filled


def smooth_white_mask(image: npt.NDArray[np.generic]) -> BoolMask:
    """Return the solid smooth-white rectangle mask."""
    _, filled = smooth_white_components(image)
    return filled


def detect_white_rectangle(image: npt.NDArray[np.generic]) -> BoundingBox:
    """Detect the smooth white rectangle from row and column coverage."""
    rgb = validate_rgb_image(image)
    height, width = rgb.shape[:2]
    mask = smooth_white_mask(rgb)

    sigma = max(2.0, min(width, height) * 0.003)
    row_coverage = np.asarray(gaussian(mask.mean(axis=1), sigma=sigma))
    col_coverage = np.asarray(gaussian(mask.mean(axis=0), sigma=sigma))

    left_edge, right_edge = _coverage_edges(col_coverage)
    top_edge, bottom_edge = _coverage_edges(row_coverage)
    _validate_box_edges(left_edge, top_edge, right_edge, bottom_edge, width, height)

    interior = float(mask[top_edge:bottom_edge, left_edge:right_edge].mean())
    edge_sharpness = _mean_edge_sharpness(
        row_coverage,
        col_coverage,
        top_edge,
        bottom_edge,
        left_edge,
        right_edge,
    )
    confidence = max(0.0, min(1.0, 0.7 * interior + 0.3 * min(1.0, edge_sharpness * 4.0)))
    return BoundingBox(
        x1=left_edge,
        y1=top_edge,
        x2=right_edge,
        y2=bottom_edge,
        confidence=confidence,
    )


def detect_dark_regions(
    image: npt.NDArray[np.generic],
    box: BoundingBox,
    dark_value: float = 0.85,
    min_area_frac: float = 2.0e-4,
    max_aspect: float = 3.0,
) -> list[DarkRegion]:
    """Find dark regions enclosed by the smooth white rectangle."""
    rgb = validate_rgb_image(image)
    value = rgb.astype(np.float32).max(axis=2) / 255.0
    prefill, filled = smooth_white_components(rgb)
    holes = filled & ~prefill & (value < dark_value)
    opened = binary_opening(holes, structure=np.ones((5, 5)))

    min_area = max(120.0, min_area_frac * box.area)
    labels = np.asarray(label(opened))
    raw: list[tuple[float, float, float, int, float]] = []
    for prop in regionprops(labels):
        if prop.area < min_area:
            continue
        region_height = prop.bbox[2] - prop.bbox[0]
        region_width = prop.bbox[3] - prop.bbox[1]
        aspect = max(region_height, region_width) / max(1, min(region_height, region_width))
        if aspect > max_aspect:
            continue
        cy, cx = prop.centroid
        area = int(prop.area)
        radius = float(np.sqrt(area / np.pi))
        mean_value = float(value[labels == prop.label].mean())
        raw.append((float(cx), float(cy), radius, area, mean_value))

    raw.sort(key=lambda item: (item[1], item[0]))
    return [
        DarkRegion(index=index, cx=cx, cy=cy, radius=radius, area=area, mean_value=mean)
        for index, (cx, cy, radius, area, mean) in enumerate(raw, start=1)
    ]


def format_box(box: BoundingBox) -> str:
    """Format a rectangle for human-readable CLI output."""
    return (
        f"x1={box.x1}, y1={box.y1}, x2={box.x2}, y2={box.y2}, "
        f"confidence={box.confidence:.2f}"
    )


def _largest_component(mask: BoolMask) -> BoolMask:
    """Return the largest foreground component in a boolean mask."""
    labels = np.asarray(label(mask))
    counts = np.bincount(labels.ravel())
    if counts.size <= 1:
        return mask
    counts[0] = 0
    return labels == int(counts.argmax())


def _coverage_edges(coverage: npt.NDArray[np.floating]) -> tuple[int, int]:
    """Return the first and last indices above an adaptive coverage threshold."""
    threshold = max(0.5, 0.55 * float(coverage.max()))
    above = np.where(coverage > threshold)[0]
    if len(above) == 0:
        raise ValueError("No smooth white rectangle found in the image")
    return int(above[0]), int(above[-1]) + 1


def _validate_box_edges(
    left_edge: int,
    top_edge: int,
    right_edge: int,
    bottom_edge: int,
    image_width: int,
    image_height: int,
) -> None:
    """Raise a value error when detected rectangle edges are invalid."""
    if top_edge >= bottom_edge or left_edge >= right_edge:
        raise ValueError("Failed to detect valid rectangle boundaries")
    rectangle_area = (right_edge - left_edge) * (bottom_edge - top_edge)
    if rectangle_area < 0.01 * image_width * image_height:
        raise ValueError("Detected rectangle region too small")


def _coverage_drop(coverage: npt.NDArray[np.floating], index: int, size: int) -> float:
    """Return the coverage drop from inside an edge to outside it."""
    inside = coverage[max(0, min(index, size - 1))]
    outside = coverage[index - 1] if index - 1 >= 0 else 0.0
    return float(max(0.0, inside - outside))


def _mean_edge_sharpness(
    row_coverage: npt.NDArray[np.floating],
    col_coverage: npt.NDArray[np.floating],
    top_edge: int,
    bottom_edge: int,
    left_edge: int,
    right_edge: int,
) -> float:
    """Return the mean coverage drop across the four detected edges."""
    height = len(row_coverage)
    width = len(col_coverage)
    drops = [
        _coverage_drop(row_coverage, top_edge, height),
        _coverage_drop(row_coverage, bottom_edge - 1, height),
        _coverage_drop(col_coverage, left_edge, width),
        _coverage_drop(col_coverage, right_edge - 1, width),
    ]
    return float(np.mean(drops))
