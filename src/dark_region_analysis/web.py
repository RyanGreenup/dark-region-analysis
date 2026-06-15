"""Flask web UI for dark-region analysis."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Final

import numpy as np
from flask import (
    Flask,
    Response,
    abort,
    current_app,
    render_template,
    request,
    send_from_directory,
)
from PIL import Image, UnidentifiedImageError
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from dark_region_analysis.annotation import annotate_regions
from dark_region_analysis.detection import detect_dark_regions, detect_white_rectangle
from dark_region_analysis.reporting import ReportFormat, render_report

ALLOWED_EXTENSIONS: Final[set[str]] = {"jpg", "jpeg", "png", "webp", "bmp", "tif", "tiff"}
DEFAULT_MAX_CONTENT_LENGTH: Final[int] = 32 * 1024 * 1024


@dataclass(frozen=True)
class WebResult:
    """Store the generated asset URLs for one analysis run."""

    image_url: str
    csv_url: str
    csv_text: str


def create_app() -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=_secret_key(),
        MAX_CONTENT_LENGTH=DEFAULT_MAX_CONTENT_LENGTH,
        JOB_FOLDER=Path(app.instance_path) / "jobs",
    )
    _ensure_job_folder(app)

    @app.get("/")
    def index() -> str:
        """Render the upload form."""
        return render_template("index.html", result=None, error=None)

    @app.post("/analyze")
    def analyze() -> str:
        """Analyze an uploaded image and render result links."""
        upload = request.files.get("image")
        if upload is None or upload.filename is None or upload.filename == "":
            return render_template("index.html", result=None, error="Choose an image first."), 400
        if not _allowed_file(upload.filename):
            return render_template(
                "index.html",
                result=None,
                error="Use jpg, jpeg, png, webp, bmp, tif, or tiff.",
            ), 400

        try:
            result = _process_upload(upload)
        except (ValueError, UnidentifiedImageError) as exc:
            return render_template("index.html", result=None, error=str(exc)), 400

        return render_template("index.html", result=result, error=None)

    @app.get("/jobs/<job_id>/<filename>")
    def job_file(job_id: str, filename: str) -> Response:
        """Return a generated job file for viewing or download."""
        if not _safe_job_id(job_id):
            abort(404)
        job_dir = _job_folder() / job_id
        if not job_dir.exists():
            abort(404)
        return send_from_directory(job_dir, filename)

    return app


def main() -> None:
    """Run the Flask development server."""
    app = create_app()
    app.run(host="0.0.0.0", port=8000)


def _process_upload(upload: FileStorage) -> WebResult:
    """Save an upload, analyze it, and write generated assets."""
    job_id = uuid.uuid4().hex
    job_dir = _job_folder() / job_id
    job_dir.mkdir(parents=True, exist_ok=False)

    original_name = secure_filename(upload.filename or "upload")
    input_path = job_dir / f"input-{original_name}"
    output_path = job_dir / "annotated.png"
    csv_path = job_dir / "measurements.csv"
    upload.save(input_path)

    with Image.open(input_path) as image:
        rgb = image.convert("RGB")
        array = np.array(rgb)
        box = detect_white_rectangle(array)
        regions = detect_dark_regions(array, box)
        annotated = annotate_regions(rgb, box, regions)
        annotated.save(output_path)
        csv_text = render_report(regions, box, ReportFormat.CSV)
        csv_path.write_text(csv_text + "\n", encoding="utf-8")

    return WebResult(
        image_url=f"/jobs/{job_id}/{output_path.name}",
        csv_url=f"/jobs/{job_id}/{csv_path.name}",
        csv_text=csv_text,
    )


def _allowed_file(filename: str) -> bool:
    """Return true when a filename has an accepted image extension."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def _safe_job_id(job_id: str) -> bool:
    """Return true when a job id only contains lowercase hex characters."""
    return len(job_id) == 32 and all(char in "0123456789abcdef" for char in job_id)


def _job_folder() -> Path:
    """Return the configured job storage directory."""
    folder = current_app.config["JOB_FOLDER"]
    if isinstance(folder, Path):
        return folder
    return Path(str(folder))


def _ensure_job_folder(app: Flask) -> None:
    """Create the configured job storage directory."""
    folder = app.config["JOB_FOLDER"]
    Path(folder).mkdir(parents=True, exist_ok=True)


def _secret_key() -> str:
    """Return the Flask secret key from the environment or a local default."""
    import os

    return os.environ.get("FLASK_SECRET_KEY", "dev-only-change-me")


app = create_app()


if __name__ == "__main__":
    main()
