"""Build FCPXML <resources> block (formats and assets)."""

from __future__ import annotations

from lxml import etree

from roughcut_fcpx.fcpxml.timecode import sec_to_fcpx_time
from roughcut_fcpx.models.schemas import MediaAsset


def build_resources(
    parent: etree._Element,
    assets: list[MediaAsset],
) -> dict[str, str]:
    """Append <resources> children and return a mapping of asset_id -> ref id.

    Creates one <format> per unique resolution/fps combo and one <asset> per
    media file.
    """
    resources = etree.SubElement(parent, "resources")

    # Dedupe formats
    format_map: dict[tuple[int, int, float], str] = {}
    asset_ref_map: dict[str, str] = {}

    for i, asset in enumerate(assets):
        key = (asset.width, asset.height, asset.fps)
        if key not in format_map:
            fmt_id = f"r{len(format_map) + 1}"
            fmt = etree.SubElement(resources, "format", id=fmt_id)
            fmt.set("name", f"FFVideoFormat{asset.height}p{int(asset.fps) if asset.fps == int(asset.fps) else asset.fps}")
            fmt.set("frameDuration", sec_to_fcpx_time(1.0 / asset.fps, asset.fps))
            fmt.set("width", str(asset.width))
            fmt.set("height", str(asset.height))
            format_map[key] = fmt_id

        ref_id = f"a{i + 1}"
        fmt_id = format_map[key]

        asset_el = etree.SubElement(resources, "asset", id=ref_id)
        asset_el.set("name", asset.filename)
        asset_el.set("src", f"file://{asset.path}")
        asset_el.set("start", "0/1s")
        asset_el.set("duration", sec_to_fcpx_time(asset.duration_sec, asset.fps))
        asset_el.set("format", fmt_id)
        asset_el.set("hasVideo", "1")
        asset_el.set("hasAudio", "1" if asset.has_audio else "0")

        asset_ref_map[asset.id] = ref_id

    return asset_ref_map
