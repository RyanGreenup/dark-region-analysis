"""Build and render dark-region analysis reports."""

from __future__ import annotations

import csv
import io
import json
from enum import StrEnum

from dark_region_analysis.models import BoundingBox, DarkRegion, RegionReportRow


class ReportFormat(StrEnum):
    """List supported report output formats."""

    PLAIN = "plain"
    JSON = "json"
    CSV = "csv"


def build_rows(regions: list[DarkRegion], box: BoundingBox) -> list[RegionReportRow]:
    """Build rounded report rows from detected dark regions."""
    rows: list[RegionReportRow] = []
    for region in regions:
        rel_x, rel_y = region.relative_to(box)
        rows.append(
            RegionReportRow(
                n=region.index,
                cx_img=round(region.cx, 1),
                cy_img=round(region.cy, 1),
                cx_rel=round(rel_x, 1),
                cy_rel=round(rel_y, 1),
                radius=round(region.radius, 1),
                area=region.area,
                dist_center=round(region.distance_to_center(box), 1),
                mean_value=round(region.mean_value, 3),
            )
        )
    return rows


def render_report(
    regions: list[DarkRegion],
    box: BoundingBox,
    report_format: ReportFormat,
) -> str:
    """Render the rectangle and dark-region measurements."""
    rows = build_rows(regions, box)
    if report_format is ReportFormat.JSON:
        return _render_json(rows, box)
    if report_format is ReportFormat.CSV:
        return _render_csv(rows)
    return _render_plain(rows, box)


def _render_plain(rows: list[RegionReportRow], box: BoundingBox) -> str:
    """Render a human-readable report."""
    center_x, center_y = box.center
    lines = [
        "== Bounding box (relative to image) ==",
        (
            f"  x1={box.x1} y1={box.y1} x2={box.x2} y2={box.y2} "
            f"size={box.width}x{box.height} confidence={box.confidence:.2f}"
        ),
        "== Bounding-box center (image coords, marked on output) ==",
        f"  center=({center_x:.1f}, {center_y:.1f})",
        f"== Dark regions: {len(rows)} (coords relative to bbox origin) ==",
    ]
    if not rows:
        lines.append("  (none detected)")
        return "\n".join(lines)

    headers = [
        "n",
        "cx_img",
        "cy_img",
        "cx_rel",
        "cy_rel",
        "radius",
        "area",
        "dist_center",
        "mean_value",
    ]
    records = [_row_to_dict(row) for row in rows]
    widths = {header: max(len(header), *(len(str(row[header])) for row in records)) for header in headers}
    lines.append("  " + " | ".join(f"{header:>{widths[header]}}" for header in headers))
    lines.append("  " + "-+-".join("-" * widths[header] for header in headers))
    for record in records:
        lines.append("  " + " | ".join(f"{record[header]!s:>{widths[header]}}" for header in headers))
    return "\n".join(lines)


def _render_json(rows: list[RegionReportRow], box: BoundingBox) -> str:
    """Render a machine-readable JSON report."""
    center_x, center_y = box.center
    payload = {
        "bounding_box": {
            "x1": box.x1,
            "y1": box.y1,
            "x2": box.x2,
            "y2": box.y2,
            "width": box.width,
            "height": box.height,
            "confidence": round(box.confidence, 4),
            "center": {"x": round(center_x, 1), "y": round(center_y, 1)},
        },
        "dark_regions": [_row_to_dict(row) for row in rows],
    }
    return json.dumps(payload, indent=2, sort_keys=True)


def _render_csv(rows: list[RegionReportRow]) -> str:
    """Render dark-region rows as CSV."""
    output = io.StringIO()
    fieldnames = [
        "n",
        "cx_img",
        "cy_img",
        "cx_rel",
        "cy_rel",
        "radius",
        "area",
        "dist_center",
        "mean_value",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(_row_to_dict(row) for row in rows)
    return output.getvalue().rstrip()


def _row_to_dict(row: RegionReportRow) -> dict[str, int | float]:
    """Convert one report row to a dictionary."""
    return {
        "n": row.n,
        "cx_img": row.cx_img,
        "cy_img": row.cy_img,
        "cx_rel": row.cx_rel,
        "cy_rel": row.cy_rel,
        "radius": row.radius,
        "area": row.area,
        "dist_center": row.dist_center,
        "mean_value": row.mean_value,
    }
