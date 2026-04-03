"""Build edit decisions from ordered segments."""

from __future__ import annotations

import logging

from roughcut_fcpx.config import AppConfig
from roughcut_fcpx.models.schemas import EditDecision, SceneSegment
from roughcut_fcpx.pipeline.ranking import order_segments

logger = logging.getLogger(__name__)


def infer_role(seg: SceneSegment) -> str:
    """Heuristic role assignment based on segment content."""
    if seg.transcript_text:
        return "dialogue"
    tags = [t.lower() for t in seg.gemma_tags]
    if any(t in tags for t in ("music", "ambient", "sfx")):
        return "effects"
    return "video"


def default_audio_gain(seg: SceneSegment) -> float:
    """Default audio gain. Quiet segments get a small boost."""
    if seg.transcript_text:
        return 0.0
    return -6.0  # pull down non-dialogue audio


def build_edit_decisions(
    selected_segments: list[SceneSegment],
    cfg: AppConfig,
) -> list[EditDecision]:
    """Order segments by style strategy and produce timeline placements."""
    ordered = order_segments(selected_segments, cfg)

    decisions: list[EditDecision] = []
    cursor = 0.0

    for idx, seg in enumerate(ordered):
        source_in = seg.start_sec
        source_out = seg.end_sec
        clip_dur = max(0.0, source_out - source_in)

        decisions.append(
            EditDecision(
                sequence_index=idx,
                asset_id=seg.asset_id,
                source_in_sec=source_in,
                source_out_sec=source_out,
                dest_in_sec=cursor,
                lane_type="primary_video",
                role=infer_role(seg),
                rationale=seg.gemma_summary or "",
                audio_gain_db=default_audio_gain(seg),
            )
        )
        cursor += clip_dur

    logger.info("Built %d edit decisions (total %.1fs)", len(decisions), cursor)
    return decisions
