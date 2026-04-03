"""Build the FCPXML sequence and spine elements."""

from __future__ import annotations

from lxml import etree

from roughcut_fcpx.config import AppConfig
from roughcut_fcpx.fcpxml.timecode import sec_to_fcpx_time
from roughcut_fcpx.models.schemas import EditDecision, MediaAsset


def build_sequence(
    parent: etree._Element,
    assets: list[MediaAsset],
    decisions: list[EditDecision],
    asset_ref_map: dict[str, str],
    cfg: AppConfig,
) -> etree._Element:
    """Create the <library>/<event>/<project>/<sequence>/<spine> tree.

    Returns the <spine> element for caller convenience.
    """
    # Determine dominant fps
    if assets:
        fps = assets[0].fps
    else:
        fps = 30.0

    total_dur = sum(max(0, d.source_out_sec - d.source_in_sec) for d in decisions)

    library = etree.SubElement(parent, "library")
    event = etree.SubElement(library, "event", name="Rough Cut Event")
    project = etree.SubElement(event, "project", name=cfg.project_title)

    sequence = etree.SubElement(project, "sequence")
    sequence.set("duration", sec_to_fcpx_time(total_dur, fps))
    sequence.set("format", "r1")  # reference first format
    sequence.set("tcStart", "0/1s")
    sequence.set("tcFormat", "NDF")

    spine = etree.SubElement(sequence, "spine")

    asset_map = {a.id: a for a in assets}
    for d in decisions:
        asset = asset_map.get(d.asset_id)
        if asset is None:
            continue
        ref = asset_ref_map.get(d.asset_id)
        if ref is None:
            continue

        clip_dur = max(0.0, d.source_out_sec - d.source_in_sec)
        clip = etree.SubElement(spine, "asset-clip")
        clip.set("ref", ref)
        clip.set("name", asset.filename)
        clip.set("offset", sec_to_fcpx_time(d.dest_in_sec, asset.fps))
        clip.set("duration", sec_to_fcpx_time(clip_dur, asset.fps))
        clip.set("start", sec_to_fcpx_time(d.source_in_sec, asset.fps))
        clip.set("tcFormat", "NDF")

    return spine
