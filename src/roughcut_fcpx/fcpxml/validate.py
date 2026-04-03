"""FCPXML validation checks."""

from __future__ import annotations

import logging
from pathlib import Path

from lxml import etree

logger = logging.getLogger(__name__)


def validate_fcpxml_doc(root: etree._Element) -> list[str]:
    """Run structural validation on an in-memory FCPXML tree.

    Returns a list of human-readable issue strings (empty = valid).
    """
    issues: list[str] = []

    # 1. Root element
    if root.tag != "fcpxml":
        issues.append(f"Root element is <{root.tag}>, expected <fcpxml>")
        return issues

    version = root.get("version")
    if version is None:
        issues.append("Missing version attribute on <fcpxml>")

    # 2. Resources
    resources = root.find("resources")
    if resources is None:
        issues.append("Missing <resources> element")
        return issues

    asset_ids = set()
    for asset in resources.findall("asset"):
        aid = asset.get("id")
        if aid is None:
            issues.append("Found <asset> without id attribute")
        elif aid in asset_ids:
            issues.append(f"Duplicate asset id: {aid}")
        else:
            asset_ids.add(aid)

        src = asset.get("src", "")
        if src.startswith("file://"):
            file_path = src.removeprefix("file://")
            if not Path(file_path).exists():
                issues.append(f"Media file not found: {file_path} (ref {aid})")

        dur = asset.get("duration", "")
        if dur and not dur.endswith("s"):
            issues.append(f"Asset {aid} duration not in rational time format: {dur}")

    # 3. Spine clips reference valid assets
    for clip in root.iter("asset-clip"):
        ref = clip.get("ref")
        if ref and ref not in asset_ids:
            issues.append(f"asset-clip ref={ref} does not match any asset id")

        for attr in ("offset", "duration", "start"):
            val = clip.get(attr, "")
            if val and not val.endswith("s"):
                issues.append(f"asset-clip {attr}={val} not in rational time format")

    # 4. At least one clip on the spine
    spine = root.find(".//spine")
    if spine is not None and len(spine) == 0:
        issues.append("Spine is empty – no clips")

    return issues


def validate_fcpxml_file(path: str) -> list[str]:
    """Validate an FCPXML file on disk."""
    issues: list[str] = []
    try:
        tree = etree.parse(path)
    except etree.XMLSyntaxError as exc:
        return [f"XML syntax error: {exc}"]

    return validate_fcpxml_doc(tree.getroot())
