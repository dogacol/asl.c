"""Pydantic data models for the roughcut-fcpx pipeline."""

from __future__ import annotations

from pydantic import BaseModel, Field


class MediaAsset(BaseModel):
    """A single ingested media file with its probed metadata."""

    id: str
    path: str
    filename: str
    duration_sec: float
    fps: float
    width: int
    height: int
    audio_channels: int | None = None
    has_audio: bool
    creation_time: str | None = None
    reel_name: str | None = None
    proxy_path: str | None = None


class SceneSegment(BaseModel):
    """A segment within a media asset identified by scene detection."""

    id: str
    asset_id: str
    start_sec: float
    end_sec: float
    duration_sec: float
    transcript_text: str | None = None
    keyframe_path: str | None = None
    snippet_path: str | None = None

    # Gemma analysis results
    gemma_summary: str | None = None
    gemma_tags: list[str] = Field(default_factory=list)
    keep_probability: float = 0.0
    emotional_score: float = 0.0
    action_score: float = 0.0
    clarity_score: float = 0.0
    novelty_score: float = 0.0
    visual_quality_score: float = 0.0
    final_score: float = 0.0


class GemmaAnalysisResult(BaseModel):
    """Strict JSON contract returned by Gemma 4 for a single segment."""

    summary: str
    tags: list[str] = Field(default_factory=list)
    keep_probability: float = Field(ge=0.0, le=1.0)
    emotional_score: float = Field(ge=0.0, le=1.0)
    action_score: float = Field(ge=0.0, le=1.0)
    clarity_score: float = Field(ge=0.0, le=1.0)
    novelty_score: float = Field(ge=0.0, le=1.0)
    visual_quality_score: float = Field(ge=0.0, le=1.0)
    suggested_use: str = ""
    rationale: str = ""


class EditDecision(BaseModel):
    """A single clip placement on the output timeline."""

    sequence_index: int
    asset_id: str
    source_in_sec: float
    source_out_sec: float
    dest_in_sec: float
    lane_type: str = "primary_video"
    role: str = "dialogue"
    rationale: str = ""
    audio_gain_db: float = 0.0
    transition_before: str | None = None
    transition_after: str | None = None


class ProjectPlan(BaseModel):
    """Complete plan describing an entire rough-cut project."""

    title: str
    theme_prompt: str
    target_duration_sec: float
    strategy_name: str
    assets: list[MediaAsset] = Field(default_factory=list)
    selected_segments: list[SceneSegment] = Field(default_factory=list)
    edit_decisions: list[EditDecision] = Field(default_factory=list)
