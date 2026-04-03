"""Top-level FCPXML document generation."""

from __future__ import annotations

from lxml import etree

from roughcut_fcpx.config import AppConfig
from roughcut_fcpx.fcpxml.resources import build_resources
from roughcut_fcpx.fcpxml.sequence import build_sequence
from roughcut_fcpx.models.schemas import EditDecision, MediaAsset


def generate_fcpxml(
    assets: list[MediaAsset],
    decisions: list[EditDecision],
    cfg: AppConfig,
) -> etree._Element:
    """Build a complete FCPXML document tree."""
    root = etree.Element("fcpxml", version=cfg.fcpxml_version)

    asset_ref_map = build_resources(root, assets)
    build_sequence(root, assets, decisions, asset_ref_map, cfg)

    return root


def serialize_fcpxml(root: etree._Element) -> bytes:
    """Serialize the FCPXML tree to a UTF-8 XML bytestring with declaration."""
    return etree.tostring(
        root,
        xml_declaration=True,
        encoding="UTF-8",
        pretty_print=True,
    )
