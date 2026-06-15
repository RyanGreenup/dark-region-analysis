"""Data models for rectangle and dark-region measurements."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class BoundingBox:
    """Store an axis-aligned rectangle in image coordinates."""

    x1: int
    y1: int
    x2: int
    y2: int
    confidence: float

    @property
    def width(self) -> int:
        """Return the rectangle width in pixels."""
        return self.x2 - self.x1

    @property
    def height(self) -> int:
        """Return the rectangle height in pixels."""
        return self.y2 - self.y1

    @property
    def area(self) -> int:
        """Return the rectangle area in pixels."""
        return self.width * self.height

    @property
    def center(self) -> tuple[float, float]:
        """Return the rectangle center in image coordinates."""
        return ((self.x1 + self.x2) / 2.0, (self.y1 + self.y2) / 2.0)


@dataclass(frozen=True)
class DarkRegion:
    """Store one accepted dark region measurement."""

    index: int
    cx: float
    cy: float
    radius: float
    area: int
    mean_value: float

    def relative_to(self, box: BoundingBox) -> tuple[float, float]:
        """Return the center measured from the rectangle top-left origin."""
        return (self.cx - box.x1, self.cy - box.y1)

    def distance_to_center(self, box: BoundingBox) -> float:
        """Return the distance from this region center to the rectangle center."""
        mx, my = box.center
        return float(np.hypot(self.cx - mx, self.cy - my))


@dataclass(frozen=True)
class RegionReportRow:
    """Store one script-friendly report row for a dark region."""

    n: int
    cx_img: float
    cy_img: float
    cx_rel: float
    cy_rel: float
    radius: float
    area: int
    dist_center: float
    mean_value: float
