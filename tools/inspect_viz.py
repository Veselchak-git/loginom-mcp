# -*- coding: utf-8 -*-
"""Summarize ModelViews visualizers in a Loginom .lgp (configured vs virgin).

Usage:
  python tools/inspect_viz.py path/to/package.lgp
"""
from __future__ import annotations

import argparse
import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


def _local(tag: str) -> str:
    return tag.split("}")[-1]


def summarize(lgp: Path) -> int:
    print("====", lgp.name, "====")
    with zipfile.ZipFile(lgp) as z:
        xml = z.read("Unit_0/Unit.xml").decode("utf-8")
        raw = z.read("Unit_0/Unit.bin")

    root = ET.fromstring(xml)
    mv = next((c for c in root if _local(c.tag) == "ModelViews"), None)
    if mv is None:
        print("  no ModelViews")
        return 1

    nodes = mv.find("Nodes")
    if nodes is None:
        print("  empty Nodes")
        return 1

    virgin = 0
    configured = 0
    for item in nodes.findall("Item"):
        dn = (item.get("DisplayName") or "").replace("\r\n", " / ")
        eng = next((e for e in item.iter() if _local(e.tag) == "Engine"), None)
        if eng is None:
            continue
        et = next((v for k, v in eng.attrib.items() if "type" in k), "?")
        vc = eng.find("ViewColumns")
        cols = [it.get("Name") for it in vc.findall("Item")] if vc is not None else []
        fields = [el.get("FieldName") for el in eng.iter() if el.get("FieldName")]
        series = eng.find("Parameters/Series") if et == "TBGChartView" else None
        empty_series = series is not None and len(list(series)) == 0
        empty_vc = vc is not None and len(cols) == 0
        status = "ok"
        if et in ("TBGBrowseView", "TBGDuplicatesView") and (
            vc is None or empty_vc
        ):
            status = "VIRGIN"
            virgin += 1
        elif et == "TBGChartView" and (empty_series or not fields):
            status = "VIRGIN"
            virgin += 1
        elif et == "TBGQualityView" and "IndicatorColumnConfigs" not in ET.tostring(
            eng, encoding="unicode"
        ):
            status = "VIRGIN?"
            virgin += 1
        else:
            configured += 1
        print(f"  [{status}] {dn}: {et}")
        if cols:
            print(f"         cols={cols}")
        if fields:
            print(f"         chart_fields={fields}")

    # quick BIN presence for common markers
    markers = [b"FieldName", b"ViewColumns", b"Qty0"]
    bin_hits = [m.decode() for m in markers if m in raw]
    print(f"  summary: configured={configured} virgin={virgin} bin_hits={bin_hits}")
    # also flag virgin Series in raw XML text
    if "<Series/>" in xml:
        print("  WARN: virgin <Series/> still in XML")
    if re.search(r"<ViewColumns\s*/>", xml):
        print("  WARN: empty <ViewColumns/> still in XML")
    return 0 if virgin == 0 else 2


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("lgp", type=Path, help="Path to .lgp package")
    args = ap.parse_args(argv)
    if not args.lgp.is_file():
        print("not found:", args.lgp, file=sys.stderr)
        return 1
    return summarize(args.lgp)


if __name__ == "__main__":
    raise SystemExit(main())
