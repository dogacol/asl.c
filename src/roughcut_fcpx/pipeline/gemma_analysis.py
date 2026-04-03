"""Gemma 4 multimodal analysis of scene segments."""

from __future__ import annotations

import json
import logging

from roughcut_fcpx.config import AppConfig
from roughcut_fcpx.models.schemas import GemmaAnalysisResult, SceneSegment
from roughcut_fcpx.utils.prompts import build_segment_prompt

logger = logging.getLogger(__name__)


def analyze_segment(
    segment: SceneSegment,
    cfg: AppConfig,
    model_name: str | None = None,
) -> GemmaAnalysisResult:
    """Run Gemma 4 inference on a single segment and return structured scores."""
    model = model_name or cfg.model_name
    prompt = build_segment_prompt(
        style_prompt=cfg.style_prompt,
        transcript_text=segment.transcript_text,
    )

    raw_text = _run_vlm_inference(
        model_name=model,
        image_path=segment.keyframe_path,
        video_path=segment.snippet_path,
        prompt=prompt,
    )

    return _parse_analysis(raw_text)


def safe_analyze_segment(
    segment: SceneSegment,
    cfg: AppConfig,
) -> GemmaAnalysisResult | None:
    """Analyse a segment with automatic retry and fallback on failure."""
    # Check cache
    from pathlib import Path

    cache_path = Path(cfg.work_dir) / "analysis" / f"{segment.id}.json"
    if cache_path.exists():
        with open(cache_path) as f:
            data = json.load(f)
        return GemmaAnalysisResult(**data)

    try:
        result = analyze_segment(segment, cfg)
    except (json.JSONDecodeError, ValueError):
        logger.warning("Malformed JSON from model for segment %s – retrying", segment.id)
        try:
            result = analyze_segment(segment, cfg)
        except Exception:
            logger.exception("Retry failed for segment %s – trying fallback model", segment.id)
            try:
                result = analyze_segment(segment, cfg, model_name=cfg.fallback_model_name)
            except Exception:
                logger.exception("Fallback also failed for segment %s", segment.id)
                return None
    except MemoryError:
        logger.warning("OOM for segment %s – retrying with fallback model", segment.id)
        try:
            result = analyze_segment(segment, cfg, model_name=cfg.fallback_model_name)
        except Exception:
            logger.exception("Fallback also OOM for segment %s", segment.id)
            return None
    except Exception:
        logger.exception("Analysis failed for segment %s", segment.id)
        return None

    # Cache result
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    with open(cache_path, "w") as f:
        json.dump(result.model_dump(), f, ensure_ascii=False)

    return result


def _run_vlm_inference(
    model_name: str,
    image_path: str | None,
    video_path: str | None,
    prompt: str,
) -> str:
    """Invoke mlx-vlm for multimodal inference. Returns raw text output."""
    try:
        from mlx_vlm import load, generate
    except ImportError:
        raise RuntimeError(
            "mlx-vlm is required for Gemma analysis. Install with: pip install mlx-vlm"
        )

    model, processor = load(model_name)

    # Build the message for the model
    images = []
    if image_path:
        images.append(image_path)

    output = generate(
        model,
        processor,
        prompt,
        images=images if images else None,
        max_tokens=512,
        temp=0.1,
    )

    return output


def _parse_analysis(raw: str) -> GemmaAnalysisResult:
    """Extract and validate JSON from raw model output."""
    # The model may wrap JSON in markdown fences
    text = raw.strip()
    if "```json" in text:
        text = text.split("```json", 1)[1]
        text = text.split("```", 1)[0]
    elif "```" in text:
        text = text.split("```", 1)[1]
        text = text.split("```", 1)[0]

    # Find the JSON object boundaries
    start = text.find("{")
    end = text.rfind("}") + 1
    if start == -1 or end == 0:
        raise ValueError(f"No JSON object found in model output: {raw[:200]}")

    data = json.loads(text[start:end])
    return GemmaAnalysisResult(**data)
