"""Pipeline orchestration."""

from __future__ import annotations

import logging
from pathlib import Path

from roughcut_fcpx.config import AppConfig
from roughcut_fcpx.models.schemas import ProjectPlan

logger = logging.getLogger(__name__)


def run_pipeline(cfg: AppConfig) -> ProjectPlan:
    """Execute the full rough-cut pipeline and write outputs."""
    from roughcut_fcpx.fcpxml.validate import validate_fcpxml_doc
    from roughcut_fcpx.fcpxml.writer import generate_fcpxml
    from roughcut_fcpx.pipeline.edit_plan import build_edit_decisions
    from roughcut_fcpx.pipeline.gemma_analysis import safe_analyze_segment
    from roughcut_fcpx.pipeline.ingest import ingest_media
    from roughcut_fcpx.pipeline.keyframes import extract_keyframe, extract_snippet
    from roughcut_fcpx.pipeline.preprocess import preprocess_assets
    from roughcut_fcpx.pipeline.preview import render_preview
    from roughcut_fcpx.pipeline.ranking import select_segments, weighted_score
    from roughcut_fcpx.pipeline.scene_detect import detect_scenes
    from roughcut_fcpx.pipeline.transcript import transcribe_asset
    from roughcut_fcpx.utils.files import build_segments, write_outputs

    # 1. Ingest
    assets = ingest_media(cfg.input_dir)
    logger.info("Ingested %d media assets", len(assets))

    # 2. Pre-process (proxies, audio extraction)
    assets = preprocess_assets(assets, cfg)

    # 3. Per-asset analysis
    all_segments = []
    for asset in assets:
        video_path = asset.proxy_path or asset.path
        boundaries = detect_scenes(video_path, cfg.scene_threshold)
        transcript = transcribe_asset(asset, cfg) if cfg.transcript_enabled else None
        segments = build_segments(asset, boundaries, transcript)

        for seg in segments:
            seg.keyframe_path = extract_keyframe(video_path, seg, cfg)
            seg.snippet_path = extract_snippet(video_path, seg, cfg)

            analysis = safe_analyze_segment(seg, cfg)
            if analysis is not None:
                seg.gemma_summary = analysis.summary
                seg.gemma_tags = analysis.tags
                seg.keep_probability = analysis.keep_probability
                seg.emotional_score = analysis.emotional_score
                seg.action_score = analysis.action_score
                seg.clarity_score = analysis.clarity_score
                seg.novelty_score = analysis.novelty_score
                seg.visual_quality_score = analysis.visual_quality_score

            seg.final_score = weighted_score(seg, cfg)

        all_segments.extend(segments)

    logger.info("Total segments: %d", len(all_segments))

    # 4. Rank and select
    selected = select_segments(all_segments, cfg)
    logger.info("Selected %d segments for edit", len(selected))

    # 5. Build edit decisions
    decisions = build_edit_decisions(selected, cfg)

    # 6. Determine strategy name
    style = cfg.style_prompt.lower()
    if "dialogue" in style:
        strategy = "dialogue_first"
    elif "trailer" in style:
        strategy = "trailer_like"
    elif "experimental" in style:
        strategy = "experimental_associative"
    elif "action" in style:
        strategy = "action_first"
    elif "mood" in style:
        strategy = "mood_piece"
    else:
        strategy = "chronological_montage"

    plan = ProjectPlan(
        title=cfg.project_title,
        theme_prompt=cfg.style_prompt,
        target_duration_sec=cfg.target_duration_sec,
        strategy_name=strategy,
        assets=assets,
        selected_segments=selected,
        edit_decisions=decisions,
    )

    # 7. Generate FCPXML
    fcpxml_doc = generate_fcpxml(assets, decisions, cfg)
    issues = validate_fcpxml_doc(fcpxml_doc)
    if issues:
        for issue in issues:
            logger.warning("FCPXML validation: %s", issue)

    # 8. Write outputs
    write_outputs(fcpxml_doc, plan, cfg)

    # 9. Optional preview
    if cfg.preview_render_enabled:
        render_preview(decisions, assets, cfg)

    return plan
