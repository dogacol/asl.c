"""Tests for FCPXML validation."""

from __future__ import annotations

from lxml import etree

from roughcut_fcpx.config import AppConfig
from roughcut_fcpx.fcpxml.validate import validate_fcpxml_doc
from roughcut_fcpx.fcpxml.writer import generate_fcpxml
from roughcut_fcpx.models.schemas import EditDecision, MediaAsset


def _make_asset(**kwargs) -> MediaAsset:
    defaults = dict(
        id="abc123",
        path="/tmp/clip.mp4",
        filename="clip.mp4",
        duration_sec=10.0,
        fps=30.0,
        width=1920,
        height=1080,
        has_audio=True,
    )
    defaults.update(kwargs)
    return MediaAsset(**defaults)


def _make_decision(**kwargs) -> EditDecision:
    defaults = dict(
        sequence_index=0,
        asset_id="abc123",
        source_in_sec=0.0,
        source_out_sec=5.0,
        dest_in_sec=0.0,
    )
    defaults.update(kwargs)
    return EditDecision(**defaults)


def test_valid_doc_passes():
    cfg = AppConfig()
    root = generate_fcpxml([_make_asset()], [_make_decision()], cfg)
    # Media file won't exist in CI, so filter out that specific issue
    issues = [i for i in validate_fcpxml_doc(root) if "not found" not in i]
    assert issues == []


def test_missing_resources():
    root = etree.Element("fcpxml", version="1.11")
    issues = validate_fcpxml_doc(root)
    assert any("resources" in i.lower() for i in issues)


def test_wrong_root_tag():
    root = etree.Element("notfcpxml")
    issues = validate_fcpxml_doc(root)
    assert any("fcpxml" in i.lower() for i in issues)


def test_duplicate_asset_ids():
    root = etree.Element("fcpxml", version="1.11")
    res = etree.SubElement(root, "resources")
    etree.SubElement(res, "asset", id="a1", src="file:///x.mp4", duration="10/1s")
    etree.SubElement(res, "asset", id="a1", src="file:///y.mp4", duration="10/1s")

    issues = validate_fcpxml_doc(root)
    assert any("duplicate" in i.lower() for i in issues)


def test_bad_asset_clip_ref():
    root = etree.Element("fcpxml", version="1.11")
    res = etree.SubElement(root, "resources")
    etree.SubElement(res, "asset", id="a1", src="file:///x.mp4", duration="10/1s")
    lib = etree.SubElement(root, "library")
    ev = etree.SubElement(lib, "event")
    proj = etree.SubElement(ev, "project")
    seq = etree.SubElement(proj, "sequence")
    spine = etree.SubElement(seq, "spine")
    etree.SubElement(spine, "asset-clip", ref="MISSING", offset="0/1s", duration="5/1s", start="0/1s")

    issues = validate_fcpxml_doc(root)
    assert any("MISSING" in i for i in issues)
