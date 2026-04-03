"""Tests for edit plan generation."""

from __future__ import annotations

from roughcut_fcpx.config import AppConfig
from roughcut_fcpx.models.schemas import SceneSegment
from roughcut_fcpx.pipeline.edit_plan import build_edit_decisions, infer_role
from roughcut_fcpx.pipeline.ranking import weighted_score


def _seg(
    id: str = "s001",
    asset_id: str = "a1",
    start: float = 0.0,
    end: float = 5.0,
    transcript: str | None = None,
    keep: float = 0.5,
    tags: list[str] | None = None,
) -> SceneSegment:
    return SceneSegment(
        id=id,
        asset_id=asset_id,
        start_sec=start,
        end_sec=end,
        duration_sec=end - start,
        transcript_text=transcript,
        keep_probability=keep,
        gemma_tags=tags or [],
    )


def test_infer_role_dialogue():
    seg = _seg(transcript="Hello world")
    assert infer_role(seg) == "dialogue"


def test_infer_role_video():
    seg = _seg()
    assert infer_role(seg) == "video"


def test_infer_role_effects():
    seg = _seg(tags=["ambient", "nature"])
    assert infer_role(seg) == "effects"


def test_build_decisions_ordered():
    cfg = AppConfig(style_prompt="chronological montage")
    segments = [
        _seg(id="s1", start=5.0, end=10.0, keep=0.8),
        _seg(id="s2", start=0.0, end=5.0, keep=0.9),
    ]
    decisions = build_edit_decisions(segments, cfg)
    assert len(decisions) == 2
    # Cursor should advance
    assert decisions[1].dest_in_sec > 0


def test_weighted_score():
    cfg = AppConfig()
    seg = _seg(keep=0.8)
    seg.clarity_score = 0.9
    seg.visual_quality_score = 0.7
    seg.emotional_score = 0.6
    seg.action_score = 0.5
    seg.novelty_score = 0.4

    score = weighted_score(seg, cfg)
    expected = (
        0.30 * 0.8
        + 0.20 * 0.9
        + 0.15 * 0.7
        + 0.15 * 0.6
        + 0.10 * 0.5
        + 0.10 * 0.4
    )
    assert abs(score - expected) < 1e-6
