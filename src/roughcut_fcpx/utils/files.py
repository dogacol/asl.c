"""File and directory helpers."""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path

from lxml import etree

from roughcut_fcpx.config import AppConfig
from roughcut_fcpx.models.schemas import MediaAsset, ProjectPlan, SceneSegment

logger = logging.getLogger(__name__)


def build_segments(
    asset: MediaAsset,
    boundaries: list[tuple[float, float]],
    transcript: dict | None,
) -> list[SceneSegment]:
    """Create SceneSegment objects from scene boundaries and optional transcript."""
    from roughcut_fcpx.pipeline.transcript import align_transcript_to_segment

    segments: list[SceneSegment] = []
    for i, (start, end) in enumerate(boundaries):
        seg_id = f"{asset.id}_s{i:03d}"
        text = align_transcript_to_segment(transcript, start, end)
        segments.append(
            SceneSegment(
                id=seg_id,
                asset_id=asset.id,
                start_sec=start,
                end_sec=end,
                duration_sec=max(0.0, end - start),
                transcript_text=text,
            )
        )
    return segments


def write_outputs(
    fcpxml_root: etree._Element,
    plan: ProjectPlan,
    cfg: AppConfig,
) -> None:
    """Write all output files: FCPXML, edit_decisions.json, report.md."""
    out = Path(cfg.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    # FCPXML
    from roughcut_fcpx.fcpxml.writer import serialize_fcpxml

    fcpxml_path = out / "project.fcpxml"
    fcpxml_path.write_bytes(serialize_fcpxml(fcpxml_root))
    logger.info("Wrote %s", fcpxml_path)

    # edit_decisions.json
    decisions_path = out / "edit_decisions.json"
    decisions_path.write_text(
        json.dumps(
            {
                "title": plan.title,
                "theme_prompt": plan.theme_prompt,
                "target_duration_sec": plan.target_duration_sec,
                "strategy_name": plan.strategy_name,
                "edit_decisions": [d.model_dump() for d in plan.edit_decisions],
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    logger.info("Wrote %s", decisions_path)

    # report.md
    report_path = out / "report.md"
    report_path.write_text(_build_report(plan), encoding="utf-8")
    logger.info("Wrote %s", report_path)


def _build_report(plan: ProjectPlan) -> str:
    """Generate a human-readable Markdown report."""
    lines = [
        f"# {plan.title}",
        "",
        f"**Style:** {plan.theme_prompt}",
        f"**Strategy:** {plan.strategy_name}",
        f"**Target duration:** {plan.target_duration_sec}s",
        f"**Assets:** {len(plan.assets)}",
        f"**Selected segments:** {len(plan.selected_segments)}",
        f"**Edit decisions:** {len(plan.edit_decisions)}",
        "",
        "## Timeline",
        "",
        "| # | Asset | In | Out | Duration | Role | Rationale |",
        "|---|---|---|---|---|---|---|",
    ]

    for d in plan.edit_decisions:
        dur = max(0, d.source_out_sec - d.source_in_sec)
        asset_name = d.asset_id[:8]
        for a in plan.assets:
            if a.id == d.asset_id:
                asset_name = a.filename
                break
        lines.append(
            f"| {d.sequence_index} | {asset_name} | {d.source_in_sec:.2f}s | "
            f"{d.source_out_sec:.2f}s | {dur:.2f}s | {d.role} | {d.rationale[:60]} |"
        )

    lines.append("")
    lines.append("## Segment scores")
    lines.append("")
    lines.append("| Segment | Score | Keep | Clarity | Visual | Emotional | Tags |")
    lines.append("|---|---|---|---|---|---|---|")
    for s in plan.selected_segments:
        tags = ", ".join(s.gemma_tags[:4])
        lines.append(
            f"| {s.id} | {s.final_score:.2f} | {s.keep_probability:.2f} | "
            f"{s.clarity_score:.2f} | {s.visual_quality_score:.2f} | "
            f"{s.emotional_score:.2f} | {tags} |"
        )

    return "\n".join(lines) + "\n"
