# -*- coding: utf-8 -*-
"""Configure virgin Loginom visualizers in an existing .lgp (XML + BIN).

``add_visualizer`` in the MCP creates empty Series / ViewColumns. This module
builds configured Engine XML+BGB and patches ``Unit_0/Unit.xml`` + ``Unit.bin``.

Do not call ``save_package`` from an MCP session after patching — it would
overwrite configured views with virgin ones again.

See VISUALIZERS.md / loginom://docs/visualizers.
"""
from __future__ import annotations

import re
import sys
import uuid
import zipfile
from pathlib import Path

_VENDOR = Path(__file__).resolve().parent
if str(_VENDOR) not in sys.path:
    sys.path.insert(0, str(_VENDOR))

from bgb_import_node import (  # noqa: E402
    empty_list,
    field_bool,
    field_guid,
    field_str,
    list_of_items,
    s,
)


def field_enum8(name: str, value: int) -> bytes:
    if not 0 <= value <= 255:
        raise ValueError(f"enum out of range: {value}")
    return s(name) + b"\x09" + bytes([value])


def _empty_obj(name: str) -> bytes:
    return s(name) + b"\x00\x00\x00"

DT = {"dtDateTime": 2, "dtFloat": 3, "dtInteger": 4, "dtString": 5}
LK_X, LK_Y, LK_LABELS = 1, 2, 6
CT_COLUMNS = 3
AP_LEFT, AP_RIGHT = 1, 2

Col = tuple[str, str, str]  # (Name, DisplayName, DataType)

QUALITY_ENGINE_XML = (
    '<Engine xsi:type="TBGQualityView">'
    "<CommonConfigs/><CalculationSettings/>"
    "<CommonColumnConfigs>"
    '<Item ID="0"/><Item ID="1"/><Item ID="2"/><Item ID="3"/><Item ID="4"/>'
    "</CommonColumnConfigs>"
    "<IndicatorColumnConfigs>"
    + "".join(f'<Item ID="{i}"/>' for i in range(15))
    + "".join(f'<Item ID="{i}" Visible="false"/>' for i in range(15, 20))
    + '<Item ID="20"/><Item ID="21"/>'
    "</IndicatorColumnConfigs>"
    "<OverviewColumnConfigs>"
    '<Item ID="0"/><Item ID="1"/>'
    "</OverviewColumnConfigs>"
    "<HistogramManager><ColumnConfigs>"
    '<Item ID="0"/><Item ID="1"/><Item ID="2"/><Item ID="3"/><Item ID="4"/>'
    "</ColumnConfigs></HistogramManager>"
    "</Engine>"
)


def _attr_item(
    attrs: bytes, n: int, children: bytes = b"", child_n: int = 0
) -> bytes:
    return b"\x00" + bytes([n]) + attrs + bytes([child_n]) + children


def browse_xml(cols: list[Col], engine: str = "TBGBrowseView") -> str:
    body = "".join(
        f'<Item Name="{n}" DisplayName="{d}" DataType="{t}"/>' for n, d, t in cols
    )
    return (
        f'<Engine xsi:type="{engine}">'
        f"<ViewColumns>{body}</ViewColumns>"
        "<Filtering/><Grouping/><Sorting/><Options/>"
        "</Engine>"
    )


def browse_blob(cols: list[Col], engine: str = "TBGBrowseView") -> bytes:
    items = []
    for n, d, t in cols:
        attrs = (
            field_str("Name", n)
            + field_str("DisplayName", d)
            + field_enum8("DataType", DT[t])
        )
        items.append(_attr_item(attrs, 3))
    return (
        s("Engine")
        + s(engine)
        + b"\x00\x05"
        + list_of_items("ViewColumns", items)
        + empty_list("Filtering")
        + empty_list("Grouping")
        + empty_list("Sorting")
        + _empty_obj("Options")
    )


def quality_xml() -> str:
    return QUALITY_ENGINE_XML


def quality_blob() -> bytes:
    def id_item(i: int, hidden: bool = False) -> bytes:
        attrs = s("ID") + b"\x05" + int(i).to_bytes(4, "little", signed=True)
        n = 1
        if hidden:
            attrs += field_bool("Visible", False)
            n = 2
        return _attr_item(attrs, n)

    return (
        s("Engine")
        + s("TBGQualityView")
        + b"\x00\x06"
        + _empty_obj("CommonConfigs")
        + _empty_obj("CalculationSettings")
        + list_of_items("CommonColumnConfigs", [id_item(i) for i in range(5)])
        + list_of_items(
            "IndicatorColumnConfigs",
            [id_item(i, 15 <= i <= 19) for i in range(22)],
        )
        + list_of_items("OverviewColumnConfigs", [id_item(i) for i in range(2)])
        + (
            s("HistogramManager")
            + b"\x00\x00\x01"
            + list_of_items("ColumnConfigs", [id_item(i) for i in range(5)])
        )
    )


def chart_xml(labels: Col, series: list[Col]) -> str:
    lab_name, _, lab_dt = labels
    ser_xml = []
    for name, display, dt in series:
        gid = str(uuid.uuid4())
        ser_xml.append(
            f'<Item Guid="{gid}" DisplayName="{display}" Series="ctColumns">'
            f"<Color/><Links>"
            f'<Item Name="lkYData" FieldType="{dt}" LinkKind="lkYData" '
            f'FieldName="{name}"/>'
            f"</Links></Item>"
        )
    return (
        '<Engine xsi:type="TBGChartView">'
        '<Parameters Rationing="false">'
        "<BackgroundColor/>"
        "<Links>"
        '<Item Name="lkXData" LinkKind="lkXData"/>'
        f'<Item Name="lkLabels" FieldType="{lab_dt}" LinkKind="lkLabels" '
        f'FieldName="{lab_name}"/>'
        "</Links>"
        f"<Series>{''.join(ser_xml)}</Series>"
        "<Axes>"
        '<Item Name="apAbscissa"/>'
        '<Item Name="apLeftOrdinate" Position="apLeftOrdinate"/>'
        '<Item Name="apRightOrdinate" Position="apRightOrdinate"/>'
        "</Axes>"
        "</Parameters>"
        "</Engine>"
    )


def chart_blob(labels: Col, series: list[Col]) -> bytes:
    lab_name, _, lab_dt = labels
    links = list_of_items(
        "Links",
        [
            _attr_item(
                field_str("Name", "lkXData") + field_enum8("LinkKind", LK_X), 2
            ),
            _attr_item(
                field_str("Name", "lkLabels")
                + field_enum8("FieldType", DT[lab_dt])
                + field_enum8("LinkKind", LK_LABELS)
                + field_str("FieldName", lab_name),
                4,
            ),
        ],
    )
    ser_items = []
    for name, display, dt in series:
        y_link = list_of_items(
            "Links",
            [
                _attr_item(
                    field_str("Name", "lkYData")
                    + field_enum8("FieldType", DT[dt])
                    + field_enum8("LinkKind", LK_Y)
                    + field_str("FieldName", name),
                    4,
                )
            ],
        )
        ser_items.append(
            _attr_item(
                field_guid("Guid", uuid.uuid4())
                + field_str("DisplayName", display)
                + field_enum8("Series", CT_COLUMNS),
                3,
                _empty_obj("Color") + y_link,
                2,
            )
        )
    params = (
        s("Parameters")
        + b"\x00\x01"
        + s("Rationing")
        + b"\x01\x00"
        + b"\x04"
        + _empty_obj("BackgroundColor")
        + links
        + list_of_items("Series", ser_items)
        + list_of_items(
            "Axes",
            [
                _attr_item(field_str("Name", "apAbscissa"), 1),
                _attr_item(
                    field_str("Name", "apLeftOrdinate")
                    + field_enum8("Position", AP_LEFT),
                    2,
                ),
                _attr_item(
                    field_str("Name", "apRightOrdinate")
                    + field_enum8("Position", AP_RIGHT),
                    2,
                ),
            ],
        )
    )
    return s("Engine") + s("TBGChartView") + b"\x00\x01" + params


def skip_bgb_str(raw: bytes, p: int) -> int:
    n = raw[p]
    if n < 64:
        return p + 1 + n
    n = (n & 0x7F) | (raw[p + 1] << 7)
    return p + 2 + n


def skip_bgb_attr(raw: bytes, p: int) -> int:
    p = skip_bgb_str(raw, p)
    tag = raw[p]
    p += 1
    if tag == 0x01:
        return p + 1
    if tag == 0x03:
        return p + 8
    if tag == 0x05:
        return p + 4
    if tag == 0x07:
        return skip_bgb_str(raw, p)
    if tag == 0x08:
        return p + 1
    if tag == 0x09:
        return p + 1
    if tag == 0x0B:
        return p + 16
    raise RuntimeError(f"attr tag {tag:#x}")


def skip_bgb_object(raw: bytes, p: int) -> int:
    p = skip_bgb_str(raw, p)
    if raw[p] == 0:
        p += 1
    else:
        p = skip_bgb_str(raw, p)
    attr_count = raw[p]
    p += 1
    for _ in range(attr_count):
        p = skip_bgb_attr(raw, p)
    child_count = raw[p]
    p += 1
    for _ in range(child_count):
        p = skip_bgb_object(raw, p)
    return p


def find_engine_span(
    raw: bytes, view_guid: str, engine_class: str
) -> tuple[int, int]:
    pos = raw.find(uuid.UUID(view_guid).bytes_le)
    if pos < 0:
        raise RuntimeError(f"GUID missing: {view_guid}")
    needle = s("Engine") + s(engine_class)
    i = raw.find(needle, pos, pos + 12000)
    if i < 0:
        raise RuntimeError(f"Engine {engine_class} after {view_guid}")
    p = i + len(needle)
    if raw[p] != 0:
        raise RuntimeError(f"attr_count={raw[p]}")
    p += 1
    child_count = raw[p]
    p += 1
    for _ in range(child_count):
        p = skip_bgb_object(raw, p)
    return i, p


def patch_xml_engine(xml: str, guid: str, new_engine: str) -> str:
    pattern = (
        rf'(<Item Guid="{guid}"[^>]*>[\s\S]*?)'
        rf'(<Engine xsi:type="[^"]+"[\s\S]*?</Engine>)'
    )
    xml2, n = re.subn(pattern, lambda m: m.group(1) + new_engine, xml, count=1)
    if n != 1:
        raise RuntimeError(f"XML replace failed {guid} n={n}")
    return xml2


Job = tuple[str, str, str, bytes]  # guid, engine_class, engine_xml, engine_blob


def patch_package(lgp: Path | str, jobs: list[Job], *, quiet: bool = False) -> None:
    """Replace Engine blocks for listed visualizer GUIDs in XML and BIN."""
    lgp = Path(lgp)
    if not quiet:
        print("Patching", lgp.name)
    with zipfile.ZipFile(lgp, "r") as z:
        names = z.namelist()
        files = {n: z.read(n) for n in names}

    xml = files["Unit_0/Unit.xml"].decode("utf-8")
    raw = files["Unit_0/Unit.bin"]

    for guid, _cls, eng_xml, _ in jobs:
        xml = patch_xml_engine(xml, guid, eng_xml)

    spans: list[tuple[int, int, bytes]] = []
    for guid, cls, _, blob in jobs:
        start, end = find_engine_span(raw, guid, cls)
        if not quiet:
            print(f"  {guid[:8]} {cls}: {end - start} -> {len(blob)}")
        spans.append((start, end, blob))
    for start, end, blob in sorted(spans, reverse=True):
        raw = raw[:start] + blob + raw[end:]

    files["Unit_0/Unit.xml"] = xml.encode("utf-8")
    files["Unit_0/Unit.bin"] = raw
    tmp = lgp.with_suffix(".lgp.tmp")
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
        for n in names:
            z.writestr(n.replace("\\", "/"), files[n])
    tmp.replace(lgp)
    if not quiet:
        print("  OK", lgp.stat().st_size)


def table_job(guid: str, cols: list[Col]) -> Job:
    return (guid, "TBGBrowseView", browse_xml(cols), browse_blob(cols))


def duplicates_job(guid: str, cols: list[Col]) -> Job:
    return (
        guid,
        "TBGDuplicatesView",
        browse_xml(cols, "TBGDuplicatesView"),
        browse_blob(cols, "TBGDuplicatesView"),
    )


def quality_job(guid: str) -> Job:
    return (guid, "TBGQualityView", quality_xml(), quality_blob())


def chart_job(guid: str, labels: Col, series: list[Col]) -> Job:
    return (
        guid,
        "TBGChartView",
        chart_xml(labels, series),
        chart_blob(labels, series),
    )
