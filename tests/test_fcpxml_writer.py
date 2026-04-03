"""Tests for FCPXML generation."""

from __future__ import annotations

from lxml import etree

from roughcut_fcpx.config import AppConfig
from roughcut_fcpx.fcpxml.writer import generate_fcpxml, serialize_fcpxml
from roughcut_fcpx.models.schemas import EditDecision, MediaAsset


def _make_asset(id: str = "abc123", path: str = "/tmp/clip.mp4") -> MediaAsset:
    return MediaAsset(
        id=id,
        path=path,
        filename="clip.mp4",
        duration_sec=10.0,
        fps=30.0,
        width=1920,
        height=1080,
        has_audio=True,
    )


def _make_decision(asset_id: str = "abc123") -> EditDecision:
    return EditDecision(
        sequence_index=0,
        asset_id=asset_id,
        source_in_sec=0.0,
        source_out_sec=5.0,
        dest_in_sec=0.0,
    )


def test_generate_basic_fcpxml():
    cfg = AppConfig()
    asset = _make_asset()
    decision = _make_decision()

    root = generate_fcpxml([asset], [decision], cfg)

    assert root.tag == "fcpxml"
    assert root.get("version") == "1.11"
    assert root.find("resources") is not None
    assert root.find(".//spine") is not None


def test_fcpxml_has_asset_clip():
    cfg = AppConfig()
    asset = _make_asset()
    decision = _make_decision()

    root = generate_fcpxml([asset], [decision], cfg)
    clips = root.findall(".//asset-clip")
    assert len(clips) == 1
    assert clips[0].get("ref") is not None


def test_serialize_fcpxml_is_valid_xml():
    cfg = AppConfig()
    asset = _make_asset()
    decision = _make_decision()

    root = generate_fcpxml([asset], [decision], cfg)
    xml_bytes = serialize_fcpxml(root)

    # Should be parseable XML
    parsed = etree.fromstring(xml_bytes)
    assert parsed.tag == "fcpxml"


def test_empty_decisions():
    cfg = AppConfig()
    asset = _make_asset()
    root = generate_fcpxml([asset], [], cfg)

    spine = root.find(".//spine")
    assert spine is not None
    assert len(spine) == 0


def test_multiple_assets():
    cfg = AppConfig()
    a1 = _make_asset(id="a1", path="/tmp/a.mp4")
    a2 = _make_asset(id="a2", path="/tmp/b.mp4")
    d1 = _make_decision(asset_id="a1")
    d2 = EditDecision(
        sequence_index=1,
        asset_id="a2",
        source_in_sec=0.0,
        source_out_sec=3.0,
        dest_in_sec=5.0,
    )

    root = generate_fcpxml([a1, a2], [d1, d2], cfg)
    clips = root.findall(".//asset-clip")
    assert len(clips) == 2
