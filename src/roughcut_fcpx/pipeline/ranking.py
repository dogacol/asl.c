"""Segment ranking, selection, and ordering."""

from __future__ import annotations

import logging
from collections import defaultdict

from roughcut_fcpx.config import AppConfig
from roughcut_fcpx.models.schemas import SceneSegment

logger = logging.getLogger(__name__)


def weighted_score(seg: SceneSegment, cfg: AppConfig) -> float:
    """Compute a final composite score for a segment."""
    return (
        cfg.weight_keep_probability * seg.keep_probability
        + cfg.weight_clarity * seg.clarity_score
        + cfg.weight_visual_quality * seg.visual_quality_score
        + cfg.weight_emotional * seg.emotional_score
        + cfg.weight_action * seg.action_score
        + cfg.weight_novelty * seg.novelty_score
    )


def select_segments(all_segments: list[SceneSegment], cfg: AppConfig) -> list[SceneSegment]:
    """Filter, rank, and trim segments to fit the target duration."""
    # 1. Drop very short segments unless highly ranked
    filtered = [
        s
        for s in all_segments
        if s.duration_sec >= cfg.min_segment_duration_sec or s.keep_probability > 0.9
    ]

    # 2. Sort by final score descending
    ranked = sorted(filtered, key=lambda s: s.final_score, reverse=True)

    # 3. Enforce per-clip cap
    ranked = _enforce_per_clip_cap(ranked, cfg.max_segments_per_clip)

    # 4. Ensure diversity – at least one segment per asset if possible
    ranked = _enforce_diversity(ranked, all_segments)

    # 5. Trim to target duration
    return _trim_to_duration(ranked, cfg.target_duration_sec)


def order_segments(selected: list[SceneSegment], cfg: AppConfig) -> list[SceneSegment]:
    """Order selected segments according to the style strategy."""
    style = cfg.style_prompt.lower()

    if "dialogue" in style:
        return _order_dialogue_first(selected)
    if "trailer" in style:
        return _order_trailer_like(selected)
    if "experimental" in style or "associative" in style:
        return _order_associative(selected)
    if "action" in style:
        return _order_action_first(selected)
    # Default: chronological
    return _order_chronologically(selected)


# ── internal helpers ──────────────────────────────────────────────


def _enforce_per_clip_cap(
    ranked: list[SceneSegment], max_per_clip: int
) -> list[SceneSegment]:
    counts: dict[str, int] = defaultdict(int)
    result: list[SceneSegment] = []
    for seg in ranked:
        if counts[seg.asset_id] < max_per_clip:
            result.append(seg)
            counts[seg.asset_id] += 1
    return result


def _enforce_diversity(
    ranked: list[SceneSegment], all_segments: list[SceneSegment]
) -> list[SceneSegment]:
    """Ensure at least one segment from each asset that has a reasonable score."""
    present_assets = {s.asset_id for s in ranked}
    all_assets = {s.asset_id for s in all_segments}
    missing = all_assets - present_assets

    for asset_id in missing:
        best = max(
            (s for s in all_segments if s.asset_id == asset_id),
            key=lambda s: s.final_score,
            default=None,
        )
        if best is not None and best.final_score > 0.1:
            ranked.append(best)

    return ranked


def _trim_to_duration(
    ranked: list[SceneSegment], target_sec: float
) -> list[SceneSegment]:
    selected: list[SceneSegment] = []
    total = 0.0
    for seg in ranked:
        if total + seg.duration_sec > target_sec and selected:
            break
        selected.append(seg)
        total += seg.duration_sec
    return selected


# ── ordering strategies ───────────────────────────────────────────


def _order_chronologically(segments: list[SceneSegment]) -> list[SceneSegment]:
    return sorted(segments, key=lambda s: (s.asset_id, s.start_sec))


def _order_dialogue_first(segments: list[SceneSegment]) -> list[SceneSegment]:
    with_text = [s for s in segments if s.transcript_text]
    without_text = [s for s in segments if not s.transcript_text]
    return (
        sorted(with_text, key=lambda s: s.start_sec)
        + sorted(without_text, key=lambda s: s.final_score, reverse=True)
    )


def _order_trailer_like(segments: list[SceneSegment]) -> list[SceneSegment]:
    # Start slow, build to a peak
    by_action = sorted(segments, key=lambda s: s.action_score)
    return by_action


def _order_action_first(segments: list[SceneSegment]) -> list[SceneSegment]:
    return sorted(segments, key=lambda s: s.action_score, reverse=True)


def _order_associative(segments: list[SceneSegment]) -> list[SceneSegment]:
    # Alternate between high-emotional and low-emotional for contrast
    by_emotion = sorted(segments, key=lambda s: s.emotional_score, reverse=True)
    result: list[SceneSegment] = []
    lo, hi = 0, len(by_emotion) - 1
    toggle = True
    while lo <= hi:
        if toggle:
            result.append(by_emotion[lo])
            lo += 1
        else:
            result.append(by_emotion[hi])
            hi -= 1
        toggle = not toggle
    return result
