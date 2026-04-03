"""Prompt templates for Gemma 4 analysis."""

from __future__ import annotations

_SEGMENT_PROMPT = """\
You are a local rough-cut assistant.

You evaluate a single scene segment for possible inclusion in an experimental edit.

Style directive: {style_prompt}

Use only what is visibly or audibly present.
Do not invent events or dialogue.
Prefer concrete editorial judgments.

Consider:
- visible action
- emotional salience
- framing clarity
- novelty
- visual quality
- transcript relevance
- usefulness as opening shot, cutaway, transition, reaction, or main beat

{transcript_section}

Return strict JSON only with the schema:
{{
  "summary": string,
  "tags": [string],
  "keep_probability": float 0-1,
  "emotional_score": float 0-1,
  "action_score": float 0-1,
  "clarity_score": float 0-1,
  "novelty_score": float 0-1,
  "visual_quality_score": float 0-1,
  "suggested_use": string,
  "rationale": string
}}

Return ONLY the JSON object, no other text."""


def build_segment_prompt(
    style_prompt: str,
    transcript_text: str | None = None,
) -> str:
    """Build the analysis prompt for a single segment."""
    if transcript_text:
        transcript_section = f'Transcript for this segment:\n"""\n{transcript_text}\n"""'
    else:
        transcript_section = "No transcript available for this segment."

    return _SEGMENT_PROMPT.format(
        style_prompt=style_prompt,
        transcript_section=transcript_section,
    )
