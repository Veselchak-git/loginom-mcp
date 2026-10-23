# -*- coding: utf-8 -*-
"""Check ModelViews in a saved .lgp: virgin engines and columns that do not match the scenario."""
from __future__ import annotations

import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

FLAG_NAMES = (
    "Duplicate",
    "DuplicateGroup",
    "Contradiction",
    "ContradictionGroup",
)

_ENGINE_OK = {
    "TBGBrowseView": "columns",
    "TBGDuplicatesView": "duplicates",
    "TBGChartView": "chart",
    "TBGQualityView": "quality",
    "TBGCubeView": "cube",
    "TBGStatView": "statistics",
}


def _local(tag: str) -> str:
    return tag.split("}")[-1]


def _xtype(el: ET.Element) -> str:
    for key, value in el.attrib.items():
        if key.endswith("type"):
            return value
    return ""


def _load_unit(path: Path) -> ET.Element:
    with zipfile.ZipFile(path) as zf:
        text = zf.read("Unit_0/Unit.xml").decode("utf-8")
    text = re.sub(r'\sxmlns(:\w+)?="[^"]*"', "", text)
    text = text.replace("xsi:type", "type")
    return ET.fromstring(text)


def _col_names(node: ET.Element) -> set[str]:
    names: set[str] = set()
    for el in node.iter():
        if _local(el.tag) != "Item":
            continue
        name = el.get("Name")
        if name and el.get("DataType"):
            names.add(name)
    for el in node.iter():
        if _local(el.tag) == "Item" and el.get("Expression") and el.get("Name"):
            names.add(el.get("Name") or "")
    return {n for n in names if n}


def _col_labels(node: ET.Element) -> set[str]:
    """DisplayNames of declared columns (view columns are stored by label)."""
    labels: set[str] = set()
    for el in node.iter():
        if _local(el.tag) != "Item" or not el.get("DataType"):
            continue
        display = el.get("DisplayName")
        if display:
            labels.add(display)
    return labels


def audit_package(path: str | Path) -> dict:
    """Return per-view status and a flat issue list. ``ok`` is true when issues is empty."""
    lgp = Path(path)
    if not lgp.is_file():
        raise FileNotFoundError(path)
    root = _load_unit(lgp)
    wf = next((c for c in root if _local(c.tag) == "WorkFlow"), None)
    mv = next((c for c in root if _local(c.tag) == "ModelViews"), None)
    if mv is None:
        return {"ok": False, "path": str(lgp), "views": [], "issues": [
            {"code": "no_model_views", "view": "", "detail": "ModelViews missing"}
        ]}

    nodes_by_guid: dict[str, ET.Element] = {}
    if wf is not None:
        nodes = next((c for c in wf if _local(c.tag) == "Nodes"), None)
        if nodes is not None:
            for item in nodes.findall("Item"):
                guid = item.get("Guid")
                if guid:
                    nodes_by_guid[guid] = item

    # Downstream input schema, used when the source itself stores no ColumnDefs
    # (native import). Keyed by source workflow guid.
    downstream: dict[str, set[str]] = {}
    downstream_labels: dict[str, set[str]] = {}
    if wf is not None:
        links = next((c for c in wf if _local(c.tag) == "Links"), None)
        if links is not None:
            for link in links.findall("Item"):
                src = link.find("SourcePort")
                tgt = link.find("TargetPort")
                if src is None or tgt is None:
                    continue
                src_guid = src.get("NodeGuid")
                tgt_guid = tgt.get("NodeGuid")
                if not src_guid or not tgt_guid or tgt_guid not in nodes_by_guid:
                    continue
                cols = _col_names(nodes_by_guid[tgt_guid])
                if cols:
                    downstream.setdefault(src_guid, set()).update(cols)
                    downstream_labels.setdefault(src_guid, set()).update(
                        _col_labels(nodes_by_guid[tgt_guid])
                    )

    view_nodes = next((c for c in mv if _local(c.tag) == "Nodes"), None)
    view_links = next((c for c in mv if _local(c.tag) == "Links"), None)
    attached: dict[str, str] = {}
    if view_links is not None:
        for link in view_links.findall("Item"):
            src = link.find("SourcePort")
            tgt = link.find("TargetPort")
            if src is None or tgt is None:
                continue
            if src.get("NodeGuid") and tgt.get("NodeGuid"):
                attached[tgt.get("NodeGuid") or ""] = src.get("NodeGuid") or ""

    views: list[dict] = []
    issues: list[dict] = []
    if view_nodes is None:
        issues.append({"code": "no_views", "view": "", "detail": "ModelViews/Nodes empty"})
        return {"ok": False, "path": str(lgp), "views": [], "issues": issues}

    for item in view_nodes.findall("Item"):
        guid = item.get("Guid") or ""
        title = (item.get("DisplayName") or "").replace("\r\n", " / ")
        eng = next((e for e in item.iter() if _local(e.tag) == "Engine"), None)
        engine = _xtype(eng) if eng is not None else ""
        cols = []
        fields = []
        if eng is not None:
            vc = eng.find("ViewColumns")
            if vc is not None:
                cols = [it.get("Name") or "" for it in vc.findall("Item")]
            fields = [el.get("FieldName") for el in eng.iter() if el.get("FieldName")]
        src_guid = attached.get(guid, "")
        src_node = nodes_by_guid.get(src_guid)
        src_name = ""
        schema: set[str] = set()
        labels: set[str] = set()
        if src_node is not None:
            src_name = (src_node.get("DisplayName") or "").replace("\r\n", " / ")
            schema = _col_names(src_node)
            labels = _col_labels(src_node)
            if len(schema) < 8:
                wider = downstream.get(src_guid, set())
                if len(wider) >= 8:
                    schema = wider
                    labels = downstream_labels.get(src_guid, set())
            if len(schema) < 8:
                schema = set()
                labels = set()
        entry = {
            "guid": guid,
            "display_name": title,
            "engine": engine,
            "attached_to": src_name,
            "columns": cols,
            "chart_fields": fields,
        }
        views.append(entry)
        label = title or guid[:8]

        if engine == "TBGQualityView":
            raw = ET.tostring(eng, encoding="unicode") if eng is not None else ""
            if "IndicatorColumnConfigs" not in raw or "<IndicatorColumnConfigs/>" in raw:
                issues.append({
                    "code": "quality_virgin",
                    "view": label,
                    "guid": guid,
                    "detail": "quality view has no indicator columns",
                })
            elif "ColumnsStats" not in raw or "PreviewDetailing" not in raw:
                issues.append({
                    "code": "quality_shape",
                    "view": label,
                    "guid": guid,
                    "detail": "quality engine is missing ColumnsStats/PreviewDetailing",
                })
            continue

        if engine in ("TBGBrowseView", "TBGDuplicatesView"):
            if not cols:
                issues.append({
                    "code": "empty_columns",
                    "view": label,
                    "guid": guid,
                    "detail": f"{engine} ViewColumns is empty",
                })
            if engine == "TBGDuplicatesView":
                missing = [n for n in FLAG_NAMES if n not in cols]
                if missing:
                    issues.append({
                        "code": "missing_duplicate_flags",
                        "view": label,
                        "guid": guid,
                        "detail": "missing " + ", ".join(missing),
                    })
            if schema:
                unknown = [
                    n for n in cols
                    if n and n not in schema and n not in labels and n not in FLAG_NAMES
                ]
                if unknown:
                    issues.append({
                        "code": "unknown_column",
                        "view": label,
                        "guid": guid,
                        "detail": "not on the source node: " + ", ".join(unknown),
                    })
            continue

        if engine == "TBGChartView":
            series = eng.find("Parameters/Series") if eng is not None else None
            empty = series is None or len(list(series)) == 0
            if empty or not fields:
                issues.append({
                    "code": "empty_series",
                    "view": label,
                    "guid": guid,
                    "detail": "chart has no labels FieldName or Series",
                })
            elif schema:
                unknown = [
                    n for n in fields if n not in schema and n not in labels
                ]
                if unknown:
                    issues.append({
                        "code": "unknown_column",
                        "view": label,
                        "guid": guid,
                        "detail": "chart fields not on the source node: " + ", ".join(unknown),
                    })
            continue

        if engine == "TBGStatView" and eng is not None:
            cols = eng.find("StatViewColumns")
            if cols is None or len(list(cols)) == 0:
                issues.append({
                    "code": "empty_statistics",
                    "view": label,
                    "guid": guid,
                    "detail": "statistics view has no StatViewColumns",
                })
            continue

        if engine == "TBGCubeView" and eng is not None:
            dims = eng.find("Dimensions/Dimensions")
            if dims is None or len(list(dims)) == 0:
                issues.append({
                    "code": "empty_cube",
                    "view": label,
                    "guid": guid,
                    "detail": "cube has no dimensions",
                })
            continue

        if engine not in _ENGINE_OK and engine:
            issues.append({
                "code": "unchecked_engine",
                "view": label,
                "guid": guid,
                "detail": engine,
            })

    return {
        "ok": not issues,
        "path": str(lgp.resolve()),
        "view_count": len(views),
        "views": views,
        "issues": issues,
    }
