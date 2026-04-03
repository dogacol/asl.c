"""CLI entry-point for roughcut-fcpx."""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import click

from roughcut_fcpx.config import AppConfig, ensure_directories, load_config
from roughcut_fcpx.logging_utils import setup_logging

logger = logging.getLogger(__name__)


@click.group()
@click.version_option(package_name="roughcut-fcpx")
def main() -> None:
    """roughcut-fcpx – local rough-cut generator for Final Cut Pro."""


@main.command()
@click.option("--input", "input_dir", type=click.Path(exists=True), help="Folder of raw clips")
@click.option("--output", "output_dir", type=click.Path(), help="Output folder")
@click.option("--style", "style_prompt", type=str, help="Editorial style prompt")
@click.option("--duration", "target_duration_sec", type=float, help="Target duration in seconds")
@click.option("--model", "model_name", type=str, help="MLX model name")
@click.option("--config", "config_path", type=click.Path(), default=None, help="Path to config YAML")
def run(
    input_dir: str | None,
    output_dir: str | None,
    style_prompt: str | None,
    target_duration_sec: float | None,
    model_name: str | None,
    config_path: str | None,
) -> None:
    """Analyse clips and generate a rough-cut FCPXML."""
    cfg = load_config(
        config_path=config_path,
        overrides={
            "input_dir": input_dir,
            "output_dir": output_dir,
            "style_prompt": style_prompt,
            "target_duration_sec": target_duration_sec,
            "model_name": model_name,
        },
    )
    setup_logging(cfg.log_level, log_dir=Path(cfg.work_dir) / "logs")
    ensure_directories(cfg)
    logger.info("Starting pipeline with style=%r, duration=%ss", cfg.style_prompt, cfg.target_duration_sec)

    from roughcut_fcpx.pipeline import run_pipeline

    plan = run_pipeline(cfg)

    logger.info(
        "Pipeline complete – %d decisions written to %s/project.fcpxml",
        len(plan.edit_decisions),
        cfg.output_dir,
    )


@main.command()
@click.option("--input", "input_dir", type=click.Path(exists=True), required=True)
@click.option("--style", "style_prompt", type=str, default="poetic observational montage")
@click.option("--config", "config_path", type=click.Path(), default=None)
def watch(input_dir: str, style_prompt: str, config_path: str | None) -> None:
    """Watch an input folder and regenerate on new media."""
    cfg = load_config(config_path=config_path, overrides={"input_dir": input_dir, "style_prompt": style_prompt, "watch_mode": True})
    setup_logging(cfg.log_level, log_dir=Path(cfg.work_dir) / "logs")
    ensure_directories(cfg)

    from roughcut_fcpx.pipeline import run_pipeline

    try:
        from watchdog.events import FileSystemEventHandler
        from watchdog.observers import Observer
    except ImportError:
        click.echo("watchdog is required for watch mode: pip install watchdog", err=True)
        sys.exit(1)

    class _Handler(FileSystemEventHandler):
        def on_created(self, event):  # noqa: ANN001
            if not event.is_directory:
                logger.info("Detected new file: %s – re-running pipeline", event.src_path)
                try:
                    run_pipeline(cfg)
                except Exception:
                    logger.exception("Pipeline failed")

    observer = Observer()
    observer.schedule(_Handler(), cfg.input_dir, recursive=False)
    observer.start()
    click.echo(f"Watching {cfg.input_dir} – press Ctrl-C to stop")
    try:
        observer.join()
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


@main.command()
@click.argument("fcpxml_path", type=click.Path(exists=True))
def validate(fcpxml_path: str) -> None:
    """Validate an FCPXML file."""
    from roughcut_fcpx.fcpxml.validate import validate_fcpxml_file

    issues = validate_fcpxml_file(fcpxml_path)
    if issues:
        for issue in issues:
            click.echo(f"  ERROR: {issue}", err=True)
        sys.exit(1)
    click.echo("FCPXML is valid.")


@main.command()
@click.argument("fcpxml_path", type=click.Path(exists=True))
def inspect(fcpxml_path: str) -> None:
    """Print a human-readable summary of an FCPXML file."""
    from lxml import etree

    tree = etree.parse(fcpxml_path)
    root = tree.getroot()
    clips = root.findall(".//{*}asset-clip") or root.findall(".//asset-clip")
    click.echo(f"FCPXML version: {root.get('version', '?')}")
    click.echo(f"Asset-clips on spine: {len(clips)}")
    for i, clip in enumerate(clips):
        click.echo(f"  [{i}] ref={clip.get('ref')} offset={clip.get('offset')} duration={clip.get('duration')}")


@main.command()
@click.option("--input", "input_dir", type=click.Path(exists=True), required=True)
@click.option("--plan", "plan_path", type=click.Path(exists=True), required=True)
@click.option("--config", "config_path", type=click.Path(), default=None)
def preview(input_dir: str, plan_path: str, config_path: str | None) -> None:
    """Render a low-res preview MP4 from an edit-decisions JSON."""
    cfg = load_config(config_path=config_path, overrides={"input_dir": input_dir, "preview_render_enabled": True})
    setup_logging(cfg.log_level)
    ensure_directories(cfg)

    from roughcut_fcpx.models.schemas import EditDecision, MediaAsset
    from roughcut_fcpx.pipeline.ingest import ingest_media
    from roughcut_fcpx.pipeline.preview import render_preview

    with open(plan_path) as f:
        raw = json.load(f)

    decisions = [EditDecision(**d) for d in raw["edit_decisions"]]
    assets = ingest_media(cfg.input_dir)
    render_preview(decisions, assets, cfg)
    click.echo(f"Preview written to {cfg.output_dir}/preview.mp4")
