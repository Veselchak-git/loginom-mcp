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
import struct
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
    field_int32,
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

DT = {
    "dtBoolean": 1,
    "dtDateTime": 2,
    "dtFloat": 3,
    "dtInteger": 4,
    "dtString": 5,
}
LK_X, LK_Y, LK_LABELS = 1, 2, 6
SERIES_KIND = {"ctArea": 1, "ctSpline": 2, "ctColumns": 3}
AP_LEFT, AP_RIGHT = 1, 2
SORT_DIR = {"sdAsc": 0, "asc": 0, "sdDesc": 1, "desc": 1}
DIM_AXIS = {"cdtCols": 0, "cols": 0, "cdtRows": 1, "rows": 1, "cdtFree": 2, "free": 2}
AXIS_XML = {0: "cdtCols", 1: "cdtRows", 2: "cdtFree"}
# View CompareValue VarType (enum8) and the OLE VT that follows the empty-name header.
VRT_BYTE, VRT_DOUBLE, VRT_INT64, VRT_STRING = 10, 5, 13, 15
VRT_XML = {VRT_BYTE: "vrtByte", VRT_DOUBLE: "vrtDouble", VRT_INT64: "vrtInt64", VRT_STRING: "vrtString"}
VT_I4, VT_R8, VT_BSTR, VT_UI1, VT_I8 = 3, 5, 8, 17, 20
ROW_NUMBER = 1  # rnRowNumber
CUBE_FN = {"sum": 0, "count": 1, "cfSum": 0, "cfCount": 1}
SERIES_POS = {"ccspCols": 0, "cols": 0, "ccspRows": 1, "rows": 1}
ROUND_MODE = {"rmoNearestMath": 4}
# Indicator panels copied from a configured TBGStatView (lab package).
STAT_INFO_IDS = (7, 1, 3)
STAT_INDICATOR_HIDDEN = {6, 7, 8, 9, 10, 11, 12, 13, 15}
STAT_HISTOGRAM_HIDDEN = {1}
_FRT = {
    "frtLess": 0, "<": 0, "lt": 0,
    "frtLessOrEqual": 1, "<=": 1, "le": 1,
    "frtGreater": 2, ">": 2, "gt": 2,
    "frtGreaterOrEqual": 3, ">=": 3, "ge": 3,
    "frtEqual": 4, "=": 4, "eq": 4, "equal": 4,
    "frtNotEqual": 5, "!=": 5, "<>": 5, "ne": 5,
    "frtIsNull": 6, "is_null": 6, "null": 6,
    "frtIsNotNull": 7, "is_not_null": 7,
    "frtBetween": 8, "between": 8,
    "frtNotBetween": 9,
    "frtIsTrue": 22, "is_true": 22, "true": 22,
    "frtIsFalse": 23, "is_false": 23, "false": 23,
}
_FRT_XML = {
    0: "frtLess", 1: "frtLessOrEqual", 2: "frtGreater", 3: "frtGreaterOrEqual",
    4: "frtEqual", 5: "frtNotEqual", 6: "frtIsNull", 7: "frtIsNotNull",
    8: "frtBetween", 9: "frtNotBetween", 22: "frtIsTrue", 23: "frtIsFalse",
}
_FRT_NULLARY = {6, 7, 22, 23}
_NUMERIC_DT = {"dtFloat", "dtInteger", "dtDateTime"}

Col = tuple[str, str, str]  # (Name, DisplayName, DataType)
SortCol = tuple[str, str]  # (Name, sdAsc|sdDesc)

# Same four columns the Duplicates node appends to its output.
DUPLICATE_FLAGS: list[Col] = [
    ("Duplicate", "Дубликат", "dtBoolean"),
    ("DuplicateGroup", "Группа дубликата", "dtInteger"),
    ("Contradiction", "Противоречие", "dtBoolean"),
    ("ContradictionGroup", "Группа противоречия", "dtInteger"),
]

QUALITY_ENGINE_XML = (
    '<Engine xsi:type="TBGQualityView">'
    "<CommonConfigs/>"
    "<ColumnsStats/>"
    "<CalculationSettings/>"
    "<PreviewDetailing/>"
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


def _xml_attr(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace('"', "&quot;")
        .replace("<", "&lt;")
    )


def _sort_xml(sort: list[SortCol] | None) -> str:
    if not sort:
        return "<Sorting/>"
    items = []
    for name, direction in sort:
        xml_dir, _ = _sort_pair(direction)
        items.append(
            f'<Item Name="{_xml_attr(name)}" SortDirection="{xml_dir}"/>'
        )
    return f"<Sorting><SortingColumns>{''.join(items)}</SortingColumns></Sorting>"


def _sort_pair(direction: str) -> tuple[str, int]:
    key = (direction or "sdAsc").strip()
    if key not in SORT_DIR:
        raise ValueError(f"sort direction {direction!r}; use sdAsc or sdDesc")
    xml_dir = "sdDesc" if SORT_DIR[key] else "sdAsc"
    return xml_dir, SORT_DIR[key]


def _sorting_blob(sort: list[SortCol] | None) -> bytes:
    if not sort:
        return empty_list("Sorting")
    items = []
    for name, direction in sort:
        _, enum = _sort_pair(direction)
        attrs = field_str("Name", name) + field_enum8("SortDirection", enum)
        items.append(_attr_item(attrs, 2))
    return s("Sorting") + b"\x00\x00\x01" + list_of_items("SortingColumns", items)


def _enum_map(mapping: dict[str, int], value: str | int, label: str) -> int:
    if isinstance(value, int):
        return value
    key = str(value).strip()
    if key not in mapping:
        raise ValueError(f"unknown {label} {value!r}; expected {sorted(set(mapping))}")
    return mapping[key]


def _frt(value: str | int) -> int:
    code = _enum_map(_FRT, value, "filter relation")
    if code not in _FRT_XML:
        raise ValueError(
            f"relation {value!r} is not in the captured view-filter layout "
            "(comparisons, null, between, is_true / is_false)"
        )
    return code


def _variant_of(value) -> tuple[int, int, bytes, str]:
    """Return VarType enum, OLE VT, payload, and XML text for a CompareValue."""
    if isinstance(value, bool):
        raise ValueError("boolean filters use relation is_true / is_false, not a compare value")
    if isinstance(value, int):
        if 0 <= value <= 255:
            return VRT_BYTE, VT_UI1, struct.pack("<i", value), str(value)
        return VRT_INT64, VT_I8, struct.pack("<q", value), str(value)
    if isinstance(value, float):
        return VRT_DOUBLE, VT_R8, struct.pack("<d", value), repr(value)
    return VRT_STRING, VT_BSTR, s(str(value)), str(value)


def _compare_object(name: str, value) -> tuple[str, bytes]:
    var_type, vt, payload, text = _variant_of(value)
    xml = (
        f'<{name} VarType="{VRT_XML[var_type]}">{_xml_attr(text)}</{name}>'
    )
    blob = (
        s(name)
        + b"\x00\x02"
        + field_enum8("VarType", var_type)
        + b"\x00\x00"
        + struct.pack("<H", vt)
        + payload
        + b"\x00"
    )
    return xml, blob


def _prepare_filter(item: dict, cols: list[Col]) -> dict:
    if not isinstance(item, dict):
        raise ValueError("filter item must be a dict")
    relation = item.get("relation") or item.get("RelationType") or "frtEqual"
    value = item.get("value", item.get("CompareValue"))
    if item.get("row_number") or item.get("row"):
        code = _frt(relation)
        if value is None:
            raise ValueError("row_number filter needs value")
        return {
            "row": True,
            "relation": code,
            "value": int(value),
            "guid": item.get("guid"),
        }
    name = item.get("name") or item.get("Name")
    if not name:
        raise ValueError("filter item needs name or row_number")
    known = {col[0]: col for col in cols}
    display = item.get("display_name") or item.get("displayName")
    data_type = item.get("data_type") or item.get("DataType")
    if name in known:
        display = display or known[name][1]
        data_type = data_type or known[name][2]
    if not data_type:
        raise ValueError(f"data_type required for filter {name!r}")
    if data_type not in DT:
        raise ValueError(f"unsupported DataType {data_type!r}")
    code = _frt(relation)
    if isinstance(value, bool) and code in (4, 22, 23):
        code = 22 if value else 23
        value = None
    lower = item.get("lower")
    upper = item.get("upper")
    if code in (8, 9):
        if lower is None or upper is None:
            raise ValueError("between filter needs lower and upper")
    elif code not in _FRT_NULLARY and value is None:
        raise ValueError(f"filter {name!r} needs value")
    return {
        "row": False,
        "name": name,
        "display": display or name,
        "data_type": data_type,
        "relation": code,
        "value": value,
        "lower": lower,
        "upper": upper,
        "guid": item.get("guid"),
    }


def _filter_children(prepared: dict) -> tuple[str, bytes]:
    code = prepared["relation"]
    if code in _FRT_NULLARY:
        return "", b""
    if code in (8, 9):
        xml_l, blob_l = _compare_object("CompareValueLowerBound", prepared["lower"])
        xml_u, blob_u = _compare_object("CompareValueUpperBound", prepared["upper"])
        return xml_l + xml_u, blob_l + blob_u
    xml, blob = _compare_object("CompareValue", prepared["value"])
    return xml, blob


def _filter_xml(filters: list[dict] | None, cols: list[Col]) -> str:
    if not filters:
        return "<Filtering/>"
    items = []
    for raw in filters:
        item = _prepare_filter(raw, cols)
        guid = item["guid"] or str(uuid.uuid4())
        inner, _ = _filter_children(item)
        rel = _FRT_XML[item["relation"]]
        if item["row"]:
            body = (
                f'<Item Guid="{guid}" ConcatenationType="ctAnd" '
                f'RowNumberer="rnRowNumber" RelationType="{rel}"'
            )
        else:
            body = (
                f'<Item Guid="{guid}" Name="{_xml_attr(item["name"])}" '
                f'DisplayName="{_xml_attr(item["display"])}" ConcatenationType="ctAnd" '
                f'DataType="{item["data_type"]}" RelationType="{rel}"'
            )
        items.append(body + "/>" if not inner else body + f">{inner}</Item>")
    return (
        '<Filtering Enabled="true"><FilterColumns UseGlobalCaseSensitive="false">'
        + "".join(items)
        + "</FilterColumns></Filtering>"
    )


def _filter_blob(filters: list[dict] | None, cols: list[Col]) -> bytes:
    if not filters:
        return empty_list("Filtering")
    bodies = []
    for raw in filters:
        item = _prepare_filter(raw, cols)
        guid = uuid.UUID(item["guid"]) if item["guid"] else uuid.uuid4()
        _, children = _filter_children(item)
        child_n = 0 if not children else (2 if item["relation"] in (8, 9) else 1)
        if item["row"]:
            attrs = (
                field_guid("Guid", guid)
                + field_enum8("ConcatenationType", 0)
                + field_enum8("RowNumberer", ROW_NUMBER)
                + field_enum8("RelationType", item["relation"])
            )
            bodies.append(s("Item") + _attr_item(attrs, 4, children, child_n))
        else:
            attrs = (
                field_guid("Guid", guid)
                + field_str("Name", item["name"])
                + field_str("DisplayName", item["display"])
                + field_enum8("ConcatenationType", 0)
                + field_enum8("DataType", DT[item["data_type"]])
                + field_enum8("RelationType", item["relation"])
            )
            bodies.append(s("Item") + _attr_item(attrs, 6, children, child_n))
    columns = (
        s("FilterColumns")
        + b"\x00\x01"
        + field_bool("UseGlobalCaseSensitive", False)
        + bytes([len(bodies)])
        + b"".join(bodies)
    )
    return (
        s("Filtering")
        + b"\x00\x01"
        + field_bool("Enabled", True)
        + b"\x01"
        + columns
    )


def browse_xml(
    cols: list[Col],
    engine: str = "TBGBrowseView",
    sort: list[SortCol] | None = None,
    filters: list[dict] | None = None,
) -> str:
    body = "".join(
        f'<Item Name="{_xml_attr(n)}" DisplayName="{_xml_attr(d)}" DataType="{t}"/>'
        for n, d, t in cols
    )
    return (
        f'<Engine xsi:type="{engine}">'
        f"<ViewColumns>{body}</ViewColumns>"
        f"{_filter_xml(filters, cols)}<Grouping/>{_sort_xml(sort)}<Options/>"
        "</Engine>"
    )


def browse_blob(
    cols: list[Col],
    engine: str = "TBGBrowseView",
    sort: list[SortCol] | None = None,
    filters: list[dict] | None = None,
) -> bytes:
    items = []
    for n, d, t in cols:
        if t not in DT:
            raise ValueError(f"unsupported DataType {t!r} for {n}")
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
        + _filter_blob(filters, cols)
        + empty_list("Grouping")
        + _sorting_blob(sort)
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
        + b"\x00\x08"
        + _empty_obj("CommonConfigs")
        + empty_list("ColumnsStats")
        + _empty_obj("CalculationSettings")
        + _empty_obj("PreviewDetailing")
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


def chart_xml(
    labels: Col,
    series: list[Col],
    series_guids: list[str] | None = None,
    series_type: str = "ctColumns",
) -> str:
    if series_type not in SERIES_KIND:
        raise ValueError(f"series type {series_type!r}")
    lab_name, _, lab_dt = labels
    guids = series_guids or [str(uuid.uuid4()) for _ in series]
    if len(guids) != len(series):
        raise ValueError("series_guids length must match series")
    ser_xml = []
    for gid, (name, display, dt) in zip(guids, series):
        ser_xml.append(
            f'<Item Guid="{gid}" DisplayName="{_xml_attr(display)}" '
            f'Series="{series_type}">'
            f"<Color/><Links>"
            f'<Item Name="lkYData" FieldType="{dt}" LinkKind="lkYData" '
            f'FieldName="{_xml_attr(name)}"/>'
            f"</Links></Item>"
        )
    return (
        '<Engine xsi:type="TBGChartView">'
        '<Parameters Rationing="false">'
        "<BackgroundColor/>"
        "<Links>"
        '<Item Name="lkXData" LinkKind="lkXData"/>'
        f'<Item Name="lkLabels" FieldType="{lab_dt}" LinkKind="lkLabels" '
        f'FieldName="{_xml_attr(lab_name)}"/>'
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


def chart_blob(
    labels: Col,
    series: list[Col],
    series_guids: list[str] | None = None,
    series_type: str = "ctColumns",
) -> bytes:
    if series_type not in SERIES_KIND:
        raise ValueError(f"series type {series_type!r}")
    lab_name, _, lab_dt = labels
    guids = series_guids or [str(uuid.uuid4()) for _ in series]
    if len(guids) != len(series):
        raise ValueError("series_guids length must match series")
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
    for gid, (name, display, dt) in zip(guids, series):
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
                field_guid("Guid", uuid.UUID(gid))
                + field_str("DisplayName", display)
                + field_enum8("Series", SERIES_KIND[series_type]),
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
    if tag == 0x04:
        while raw[p] >= 128:
            p += 1
        return p + 1
    if tag == 0x0A:
        return p + 2
    if tag == 0x0B:
        return p + 16
    if tag == 0x00:
        # Empty-name variant payload: OLE VT (uint16) + value.
        vt = struct.unpack_from("<H", raw, p)[0]
        p += 2
        if vt in (VT_UI1, VT_I4):
            return p + 4
        if vt in (VT_R8, VT_I8):
            return p + 8
        if vt == 11:
            return p + 2
        if vt == VT_BSTR:
            return skip_bgb_str(raw, p)
        raise RuntimeError(f"variant vt {vt}")
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
    attr_count = raw[p]
    p += 1
    for _ in range(attr_count):
        p = skip_bgb_attr(raw, p)
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


def _cube_function_slots(enabled: set[int]) -> tuple[str, bytes]:
    xml_parts: list[str] = []
    blob = b""
    for index in range(12):
        if index not in enabled:
            xml_parts.append("<Functions/>")
            blob += _empty_obj("Functions")
            continue
        subs = '<SubFunctions Usable="true" OrderNumber="0"/>' + "<SubFunctions/>" * 5
        xml_parts.append(f'<Functions OrderNumber="{index}">{subs}</Functions>')
        sub_blob = (
            s("SubFunctions")
            + b"\x00\x02"
            + field_bool("Usable", True)
            + field_int32("OrderNumber", 0)
            + b"\x00"
            + _empty_obj("SubFunctions") * 5
        )
        blob += (
            s("Functions")
            + b"\x00\x01"
            + field_int32("OrderNumber", index)
            + b"\x06"
            + sub_blob
        )
    return "".join(xml_parts), blob


def _enable_functions(spec: dict) -> set[int]:
    raw = spec.get("functions")
    if raw is None:
        return {0, 1}
    enabled: set[int] = set()
    for item in raw:
        if isinstance(item, int):
            enabled.add(item)
        else:
            enabled.add(_enum_map(CUBE_FN, item, "cube function"))
    if any(i < 0 or i > 11 for i in enabled):
        raise ValueError("cube function index must be 0..11")
    return enabled


def cube_xml(
    dimensions: list[dict],
    facts: list[dict],
    case_sort: dict | None = None,
    chart: dict | None = None,
) -> str:
    dim_xml, _, fact_xml, _, sort_xml, _, chart_xml, _ = _cube_parts(
        dimensions, facts, case_sort, chart
    )
    return (
        '<Engine xsi:type="TBGCubeView">'
        f"<Dimensions><Dimensions>{dim_xml}</Dimensions></Dimensions>"
        f"<Summaries><Cases>{fact_xml}</Cases></Summaries>"
        f"{sort_xml}{chart_xml}</Engine>"
    )


def cube_blob(
    dimensions: list[dict],
    facts: list[dict],
    case_sort: dict | None = None,
    chart: dict | None = None,
) -> bytes:
    _, dim_blob, _, fact_blob, _, sort_blob, _, chart_blob = _cube_parts(
        dimensions, facts, case_sort, chart
    )
    children = (
        (s("Dimensions") + b"\x00\x00\x01" + list_of_items("Dimensions", dim_blob))
        + (s("Summaries") + b"\x00\x00\x01" + list_of_items("Cases", fact_blob))
        + sort_blob
        + chart_blob
    )
    child_n = 4 if case_sort else 3
    return s("Engine") + s("TBGCubeView") + b"\x00" + bytes([child_n]) + children


def _cube_parts(
    dimensions: list[dict],
    facts: list[dict],
    case_sort: dict | None,
    chart: dict | None,
) -> tuple[str, list[bytes], str, list[bytes], str, bytes, str, bytes]:
    if not dimensions:
        raise ValueError("cube requires dimensions")
    if not facts:
        raise ValueError("cube requires facts")
    axis_n = {"rows": 0, "cols": 0, "free": 0}
    dim_xml: list[str] = []
    dim_blob: list[bytes] = []
    for spec in dimensions:
        name = spec["name"]
        display = spec.get("display_name") or spec.get("displayName") or name
        data_type = spec.get("data_type") or spec.get("DataType") or "dtString"
        if data_type not in DT:
            raise ValueError(f"unsupported DataType {data_type!r} for {name}")
        axis = _enum_map(DIM_AXIS, spec.get("axis") or spec.get("DimensionType") or "rows", "axis")
        axis_name = AXIS_XML[axis]
        key = {0: "cols", 1: "rows", 2: "free"}[axis]
        order = spec["order"] if "order" in spec else axis_n[key]
        axis_n[key] += 1
        dim_xml.append(
            f'<Item Name="{_xml_attr(name)}" DisplayName="{_xml_attr(display)}" '
            f'DataType="{data_type}" DimensionType="{axis_name}" OrderNumber="{order}">'
            '<Filter Usable="true"/></Item>'
        )
        attrs = (
            field_str("Name", name)
            + field_str("DisplayName", display)
            + field_enum8("DataType", DT[data_type])
            + field_enum8("DimensionType", axis)
            + field_int32("OrderNumber", int(order))
        )
        filt = s("Filter") + b"\x00\x01" + field_bool("Usable", True) + b"\x00"
        dim_blob.append(_attr_item(attrs, 5, filt, 1))

    fact_xml: list[str] = []
    fact_blob: list[bytes] = []
    for spec in facts:
        count_case = bool(spec.get("count_case") or spec.get("CountCase"))
        name = spec.get("name") or ("CountCase" if count_case else None)
        if not name:
            raise ValueError("fact needs name")
        display = spec.get("display_name") or spec.get("displayName") or name
        if count_case or name == "CountCase":
            fn_xml, fn_blob = _cube_function_slots(set())
            fact_xml.append(
                f'<Item Name="{_xml_attr(name)}" DisplayName="{_xml_attr(display)}" '
                f'CountCase="true">{fn_xml}</Item>'
            )
            attrs = (
                field_str("Name", name)
                + field_str("DisplayName", display)
                + field_bool("CountCase", True)
            )
            fact_blob.append(_attr_item(attrs, 3, fn_blob, 12))
            continue
        data_type = spec.get("data_type") or spec.get("DataType") or "dtFloat"
        if data_type not in DT:
            raise ValueError(f"unsupported DataType {data_type!r} for {name}")
        fn_xml, fn_blob = _cube_function_slots(_enable_functions(spec))
        fact_xml.append(
            f'<Item Name="{_xml_attr(name)}" DisplayName="{_xml_attr(display)}" '
            f'DataType="{data_type}">{fn_xml}</Item>'
        )
        attrs = (
            field_str("Name", name)
            + field_str("DisplayName", display)
            + field_enum8("DataType", DT[data_type])
        )
        fact_blob.append(_attr_item(attrs, 3, fn_blob, 12))

    if case_sort:
        name = case_sort["name"]
        data_type = case_sort.get("data_type") or case_sort.get("DataType") or "dtFloat"
        function = case_sort.get("function", 0)
        if not isinstance(function, int):
            function = _enum_map(CUBE_FN, function, "cube function")
        sort_xml = (
            "<CaseSortItems><Item><CompositeHeader "
            f'CaseName="{_xml_attr(name)}" CaseDataType="{data_type}" '
            f'CaseFunction="cfSum"/></Item></CaseSortItems>'
            if function == 0
            else (
                "<CaseSortItems><Item><CompositeHeader "
                f'CaseName="{_xml_attr(name)}" CaseDataType="{data_type}" '
                f'CaseFunction="{function}"/></Item></CaseSortItems>'
            )
        )
        header = (
            s("CompositeHeader")
            + b"\x00\x03"
            + field_str("CaseName", name)
            + field_enum8("CaseDataType", DT[data_type])
            + field_enum8("CaseFunction", function)
            + b"\x00"
        )
        sort_blob = list_of_items("CaseSortItems", [_attr_item(b"", 0, header, 1)])
    else:
        sort_xml, sort_blob = "", b""

    if chart:
        title = chart.get("title") or chart.get("Title") or ""
        source = chart.get("source") or chart.get("SourceName")
        if not source:
            raise ValueError("cube chart needs source fact name")
        width = int(chart.get("width") or chart.get("PanelWidth") or 300)
        position = _enum_map(
            SERIES_POS, chart.get("position") or chart.get("SeriesPosition") or "rows", "series position"
        )
        pos_xml = "ccspRows" if position == 1 else "ccspCols"
        guid = chart.get("guid") or str(uuid.uuid4())
        case_guid = chart.get("case_guid") or str(uuid.uuid4())
        chart_xml = (
            f'<Charts><Item Guid="{guid}" PanelWidth="{width}" '
            f'SeriesPosition="{pos_xml}" Title="{_xml_attr(title)}">'
            f'<CaseInfos><Item Guid="{case_guid}" SourceName="{_xml_attr(source)}"/>'
            "</CaseInfos></Item></Charts>"
        )
        case = _attr_item(field_guid("Guid", uuid.UUID(case_guid)) + field_str("SourceName", source), 2)
        attrs = (
            field_guid("Guid", uuid.UUID(guid))
            + field_int32("PanelWidth", width)
            + field_enum8("SeriesPosition", position)
            + field_str("Title", title)
        )
        infos = list_of_items("CaseInfos", [case])
        chart_blob = list_of_items("Charts", [_attr_item(attrs, 4, infos, 1)])
    else:
        chart_xml, chart_blob = "<Charts/>", empty_list("Charts")
    return (
        "".join(dim_xml),
        dim_blob,
        "".join(fact_xml),
        fact_blob,
        sort_xml,
        sort_blob,
        chart_xml,
        chart_blob,
    )


def _stat_column(spec: dict) -> tuple[str, bytes]:
    name = spec["name"]
    display = spec.get("display_name") or spec.get("displayName") or name
    data_type = spec.get("data_type") or spec.get("DataType") or "dtString"
    if data_type not in DT:
        raise ValueError(f"unsupported DataType {data_type!r} for {name}")
    if "decimals" in spec:
        decimals = spec["decimals"]
    elif data_type in _NUMERIC_DT:
        decimals = 3
    else:
        decimals = None
    if decimals is None:
        xml = (
            f'<Item Name="{_xml_attr(name)}" DisplayName="{_xml_attr(display)}" '
            f'DataType="{data_type}"><ColumnConfig/></Item>'
        )
        attrs = field_str("Name", name) + field_str("DisplayName", display) + field_enum8("DataType", DT[data_type])
        blob = _attr_item(attrs, 3, _empty_obj("ColumnConfig"), 1)
        return xml, blob
    mode = spec.get("round_mode") or spec.get("RoundMode") or "rmoNearestMath"
    mode_n = _enum_map(ROUND_MODE, mode, "round mode") if not isinstance(mode, int) else mode
    xml = (
        f'<Item Name="{_xml_attr(name)}" DisplayName="{_xml_attr(display)}" '
        f'DataType="{data_type}" RoundMode="rmoNearestMath" NumberOfDecimals="{int(decimals)}">'
        "<ColumnConfig/></Item>"
    )
    attrs = (
        field_str("Name", name)
        + field_str("DisplayName", display)
        + field_enum8("DataType", DT[data_type])
        + field_enum8("RoundMode", mode_n)
        + field_int32("NumberOfDecimals", int(decimals))
    )
    blob = _attr_item(attrs, 5, _empty_obj("ColumnConfig"), 1)
    return xml, blob


def _id_column(index: int, hidden: bool) -> tuple[str, bytes]:
    if hidden:
        xml = f'<Item ID="{index}"><ColumnConfig Visible="false"/></Item>'
        cfg = s("ColumnConfig") + b"\x00\x01" + field_bool("Visible", False) + b"\x00"
    else:
        xml = f'<Item ID="{index}"><ColumnConfig/></Item>'
        cfg = _empty_obj("ColumnConfig")
    blob = _attr_item(field_int32("ID", index), 1, cfg, 1)
    return xml, blob


def _stat_flags(settings: dict | None) -> tuple[str, bytes, int]:
    settings = settings or {}
    bits = []
    attrs = b""
    count = 0
    for key, xml_name in (
        ("show_histogram", "ShowHistogram"),
        ("statistics_in_rows", "StatisticsInRows"),
    ):
        if key not in settings:
            continue
        flag = bool(settings[key])
        bits.append(f'{xml_name}="{"true" if flag else "false"}"')
        attrs += field_bool(xml_name, flag)
        count += 1
    extra = (" " + " ".join(bits)) if bits else ""
    return extra, attrs, count


def statistics_xml(columns: list[dict], settings: dict | None = None) -> str:
    col_xml, info_xml, ind_xml, hist_xml = _stat_xml_parts(columns)
    extra, _, _ = _stat_flags(settings)
    return (
        f'<Engine xsi:type="TBGStatView"{extra}>'
        f"<StatViewColumns>{col_xml}</StatViewColumns>"
        "<StatIndicatorColumnConfig/>"
        f"<ColumnInfosConfig>{info_xml}</ColumnInfosConfig>"
        f"<StatIndicatorsConfig>{ind_xml}</StatIndicatorsConfig>"
        f"<HistogramColumnsConfig>{hist_xml}</HistogramColumnsConfig>"
        "</Engine>"
    )


def statistics_blob(columns: list[dict], settings: dict | None = None) -> bytes:
    cols = []
    for spec in columns:
        _, blob = _stat_column(spec)
        cols.append(blob)
    infos = [_id_column(i, False)[1] for i in STAT_INFO_IDS]
    indicators = [_id_column(i, i in STAT_INDICATOR_HIDDEN)[1] for i in range(17)]
    histograms = [_id_column(i, i in STAT_HISTOGRAM_HIDDEN)[1] for i in range(6)]
    _, attrs, count = _stat_flags(settings)
    return (
        s("Engine")
        + s("TBGStatView")
        + bytes([count])
        + attrs
        + b"\x05"
        + list_of_items("StatViewColumns", cols)
        + _empty_obj("StatIndicatorColumnConfig")
        + list_of_items("ColumnInfosConfig", infos)
        + list_of_items("StatIndicatorsConfig", indicators)
        + list_of_items("HistogramColumnsConfig", histograms)
    )


def _stat_xml_parts(columns: list[dict]) -> tuple[str, str, str, str]:
    cols = "".join(_stat_column(spec)[0] for spec in columns)
    infos = "".join(_id_column(i, False)[0] for i in STAT_INFO_IDS)
    indicators = "".join(_id_column(i, i in STAT_INDICATOR_HIDDEN)[0] for i in range(17))
    histograms = "".join(_id_column(i, i in STAT_HISTOGRAM_HIDDEN)[0] for i in range(6))
    return cols, infos, indicators, histograms


def _stamp_filter_guids(filters: list[dict] | None) -> list[dict] | None:
    if not filters:
        return filters
    stamped = []
    for item in filters:
        copy = dict(item)
        copy.setdefault("guid", str(uuid.uuid4()))
        stamped.append(copy)
    return stamped


def table_job(
    guid: str,
    cols: list[Col],
    sort: list[SortCol] | None = None,
    filters: list[dict] | None = None,
) -> Job:
    filters = _stamp_filter_guids(filters)
    return (
        guid,
        "TBGBrowseView",
        browse_xml(cols, sort=sort, filters=filters),
        browse_blob(cols, sort=sort, filters=filters),
    )


def duplicates_job(
    guid: str,
    cols: list[Col],
    sort: list[SortCol] | None = None,
    filters: list[dict] | None = None,
) -> Job:
    filters = _stamp_filter_guids(filters)
    return (
        guid,
        "TBGDuplicatesView",
        browse_xml(cols, "TBGDuplicatesView", sort=sort, filters=filters),
        browse_blob(cols, "TBGDuplicatesView", sort=sort, filters=filters),
    )


def cube_job(
    guid: str,
    dimensions: list[dict],
    facts: list[dict],
    case_sort: dict | None = None,
    chart: dict | None = None,
) -> Job:
    if chart is not None:
        chart = dict(chart)
        chart.setdefault("guid", str(uuid.uuid4()))
        chart.setdefault("case_guid", str(uuid.uuid4()))
    return (
        guid,
        "TBGCubeView",
        cube_xml(dimensions, facts, case_sort, chart),
        cube_blob(dimensions, facts, case_sort, chart),
    )


def statistics_job(guid: str, columns: list[dict], settings: dict | None = None) -> Job:
    return (
        guid,
        "TBGStatView",
        statistics_xml(columns, settings),
        statistics_blob(columns, settings),
    )


def quality_job(guid: str) -> Job:
    return (guid, "TBGQualityView", quality_xml(), quality_blob())


def chart_job(
    guid: str,
    labels: Col,
    series: list[Col],
    series_type: str = "ctColumns",
) -> Job:
    guids = [str(uuid.uuid4()) for _ in series]
    return (
        guid,
        "TBGChartView",
        chart_xml(labels, series, guids, series_type),
        chart_blob(labels, series, guids, series_type),
    )
