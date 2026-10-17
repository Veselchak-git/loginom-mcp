"""ColumnDefs builders for Loginom node input ports (BGB + XML).

Used by configure_node to set UsageType / grouping aggregates so nodes are
not left virgin («Не указаны столбцы для обработки»).
"""
from __future__ import annotations

import re
import struct
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from xml.sax.saxutils import escape

import importlib.util

from loginom_ident import loginom_ident, resolve_column_names
from paths import VENDOR

_spec = importlib.util.spec_from_file_location(
    "imp", VENDOR / "bgb_import_node.py"
)
imp = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(imp)

s = imp.s
field_str = imp.field_str
field_guid = imp.field_guid
list_of_items = imp.list_of_items
empty_list = imp.empty_list


def field_enum8(name: str, value: int) -> bytes:
    if not 0 <= value <= 255:
        raise ValueError(value)
    return s(name) + b"\x09" + bytes([value])


def field_int32(name: str, value: int) -> bytes:
    return s(name) + b"\x05" + struct.pack("<i", value)


def field_group_functions(mask: int) -> bytes:
    """Encode GroupFunctions set (type 0x0A). Low masks are 1 byte; high bits use 0x80|low, high."""
    if mask < 0:
        raise ValueError(mask)
    if mask <= 0x7F:
        return s("GroupFunctions") + b"\x0a" + bytes([mask])
    return s("GroupFunctions") + b"\x0a" + bytes([0x80 | (mask & 0x7F), (mask >> 8) & 0xFF])


# UsageType ordinals (from configured packages)
UT = {
    "utUnspecified": 0,
    "utActive": 3,
    "utPredicted": 4,
    "utGroup": 6,
    "utValue": 7,
}

# DataType ordinals
DT = {
    "dtBoolean": 1,
    "dtDateTime": 2,
    "dtFloat": 3,
    "dtInteger": 4,
    "dtString": 5,
    "dtVariant": 6,
}

# DataKind ordinals
DK = {
    "dkUndefined": 0,
    "dkContinuous": 1,
    "dkDiscrete": 2,
}

# GroupFunctions bit masks (TBGGroupDataColumnDefExtension)
GF = {
    "gdSum": 1 << 0,
    "gdCount": 1 << 1,
    "gdMin": 1 << 2,
    "gdMax": 1 << 3,
    "gdAvg": 1 << 4,
    "gdMedian": 1 << 5,
    "gdMode": 1 << 6,
    "gdStdDev": 1 << 7,
    "gdUniqueCount": 1 << 9,
    "gdNullCount": 1 << 10,
    "gdFirst": 1 << 11,
    "gdLast": 1 << 12,
}

GROUP_EXT_GUID = uuid.UUID("4e016f37-9d38-4f5f-a107-5590464316e2")
OUTLIER_EXT_GUID = uuid.UUID("4e016f37-9d38-4f5f-a107-5590464316e2")  # placeholder if needed


@dataclass
class ColumnSpec:
    name: str
    usage: str  # utActive / utPredicted / utGroup / utValue / ...
    display_name: str | None = None
    data_type: str = "dtString"
    data_kind: str = "dkDiscrete"
    input_column: str | None = None
    origin_custom: bool = False
    group_functions: list[str] = field(default_factory=list)
    group_order: int | None = None
    extension: str | None = None  # group | outlier | None


def guess_type(name: str) -> tuple[str, str]:
    n = name.lower()
    if any(k in n for k in ("дата", "date", "time", "period")):
        return "dtDateTime", "dkContinuous"
    if any(
        k in n
        for k in (
            "сумма",
            "прибыл",
            "себестоим",
            "количеств",
            "скидк",
            "цена",
            "amount",
            "qty",
            "sum",
            "price",
            "cost",
            "count",
        )
    ):
        return "dtFloat", "dkContinuous"
    if re.search(r"(^id$|_id$|key$|код)", n):
        return "dtString", "dkDiscrete"
    return "dtString", "dkDiscrete"


def read_text_header(path: Path, max_cols: int = 500) -> list[str]:
    """Read column names from first line of a delimited text file."""
    raw = path.read_bytes()
    # strip BOM
    if raw.startswith(b"\xef\xbb\xbf"):
        raw = raw[3:]
    text = raw.decode("utf-8", errors="replace")
    first = text.splitlines()[0] if text else ""
    if "\t" in first:
        cols = first.split("\t")
    elif ";" in first:
        cols = first.split(";")
    elif "," in first:
        cols = first.split(",")
    else:
        cols = [first]
    cols = [c.strip().strip('"') for c in cols if c.strip()]
    if len(cols) > max_cols:
        raise ValueError(f"too many columns: {len(cols)}")
    for c in cols:
        if len(c.encode("utf-8")) >= 16384:
            raise ValueError(f"column name too long for BGB: {c!r}")
    return cols



def _group_extension_blob(order: int | None, functions: list[str]) -> bytes:
    mask = 0
    for f in functions:
        if f not in GF:
            raise KeyError(f"unknown group function {f!r}; have {sorted(GF)}")
        mask |= GF[f]
    attrs = b""
    n = 0
    if mask:
        attrs += field_group_functions(mask)
        n += 1
    if order is not None:
        attrs += field_int32("Order", order)
        n += 1
    return (
        s("Extension")
        + s("TBGGroupDataColumnDefExtension")
        + bytes([n])
        + attrs
        + b"\x00"
    )


def _needs_group_extension(col: ColumnSpec) -> bool:
    return bool(
        col.group_functions
        or col.extension == "group"
        or col.usage in ("utGroup", "utValue")
        or col.group_order is not None
    )


def _column_item_blob(col: ColumnSpec) -> bytes:
    # Name must be a valid identifier; DisplayName may be Cyrillic (or omitted).
    display = col.display_name  # None → omit DisplayName (ASCII-only fields)
    inp = col.input_column or col.name
    ut = UT[col.usage]
    dt = DT[col.data_type]
    dk = DK[col.data_kind]
    # Emit OriginType only for iotCustom (never iotUnspecified).
    origin_custom = bool(col.origin_custom or col.usage == "utValue")
    attrs = field_str("Name", col.name)
    n_attr = 1
    if display is not None:
        attrs += field_str("DisplayName", display)
        n_attr += 1
    attrs += (
        field_enum8("DataType", dt)
        + field_enum8("DataKind", dk)
        + field_enum8("UsageType", ut)
    )
    n_attr += 3
    if origin_custom:
        attrs += field_enum8("OriginType", 1)  # iotCustom
        n_attr += 1
    attrs += field_str("InputColumnInfoName", inp)
    n_attr += 1

    children = b""
    child_count = 0
    if _needs_group_extension(col):
        order = col.group_order
        if order is None and col.usage == "utGroup":
            order = 0
        if order is None and col.group_functions:
            order = 0
        ext_body = _group_extension_blob(order, col.group_functions)
        ext_item = (
            b"\x00\x01"
            + field_guid("Guid", GROUP_EXT_GUID)
            + b"\x01"
            + ext_body
        )
        children = s("Extensions") + b"\x00\x00\x01" + s("Item") + ext_item
        child_count = 1

    return b"\x00" + bytes([n_attr]) + attrs + bytes([child_count]) + children

def build_column_defs_blob(columns: list[ColumnSpec]) -> bytes:
    if not columns:
        return empty_list("ColumnDefs")
    if len(columns) > 255:
        raise ValueError("too many columns for single-byte BGB list count")
    items = [_column_item_blob(c) for c in columns]
    return list_of_items("ColumnDefs", items)


def build_column_defs_xml(columns: list[ColumnSpec]) -> str:
    if not columns:
        return "<ColumnDefs/>"
    parts = ["<ColumnDefs>"]
    for col in columns:
        name = escape(col.name)
        inp = escape(col.input_column or col.name)
        origin_custom = bool(col.origin_custom or col.usage == "utValue")
        attrs = f'Name="{name}"'
        if col.display_name is not None:
            attrs += f' DisplayName="{escape(col.display_name)}"'
        attrs += (
            f' DataType="{col.data_type}" DataKind="{col.data_kind}" '
            f'UsageType="{col.usage}"'
        )
        if origin_custom:
            attrs += ' OriginType="iotCustom"'
        attrs += f' InputColumnInfoName="{inp}"'
        if not _needs_group_extension(col):
            parts.append(f"<Item {attrs}/>")
            continue
        order = col.group_order
        if order is None and (col.usage == "utGroup" or col.group_functions):
            order = 0
        ext_bits = []
        if col.group_functions:
            ext_bits.append(
                f'GroupFunctions="{" ".join(escape(f) for f in col.group_functions)}"'
            )
        if order is not None:
            ext_bits.append(f'Order="{order}"')
        ext_attrs = (" " + " ".join(ext_bits)) if ext_bits else ""
        parts.append(
            f"<Item {attrs}>"
            f"<Extensions>"
            f'<Item Guid="{GROUP_EXT_GUID}">'
            f'<Extension xsi:type="TBGGroupDataColumnDefExtension"{ext_attrs}/>'
            f"</Item></Extensions></Item>"
        )
    parts.append("</ColumnDefs>")
    return "".join(parts)


def _clear_input_virgin_blob(node_blob: bytes) -> bytes:
    """Configured TuneDataSourceSocket must not keep Virgin=true (real packages omit it)."""
    # Prefer clearing the first Virgin=true (input DataSource socket).
    needle = s("Virgin") + b"\x01\x01"
    idx = node_blob.find(needle)
    if idx >= 0:
        return node_blob[: idx + len(s("Virgin")) + 1] + b"\x00" + node_blob[idx + len(needle) :]
    return node_blob


def _clear_input_virgin_xml(node_xml: str) -> str:
    # First Virgin="true" on an input tune socket.
    return node_xml.replace('Virgin="true"', 'Virgin="false"', 1)


def inject_column_defs_blob(node_blob: bytes, columns: list[ColumnSpec]) -> bytes:
    """Replace the first empty ColumnDefs list in a node BGB blob."""
    needle = empty_list("ColumnDefs")
    idx = node_blob.find(needle)
    if idx < 0:
        raise ValueError("empty ColumnDefs not found in node blob")
    replacement = build_column_defs_blob(columns)
    out = node_blob[:idx] + replacement + node_blob[idx + len(needle) :]
    return _clear_input_virgin_blob(out)


def inject_column_defs_xml(node_xml: str, columns: list[ColumnSpec]) -> str:
    """Replace first empty ColumnDefs in node XML (input DataSource)."""
    filled = build_column_defs_xml(columns)
    for empty in ("<ColumnDefs/>", "<ColumnDefs />", "<ColumnDefs></ColumnDefs>"):
        if empty in node_xml:
            return _clear_input_virgin_xml(node_xml.replace(empty, filled, 1))
    raise ValueError("empty ColumnDefs not found in node XML")

def _make_spec(
    label: str,
    usage: str,
    *,
    origin_custom: bool = False,
    extension: str | None = None,
    group_functions: list[str] | None = None,
    group_order: int | None = None,
    data_type: str | None = None,
    data_kind: str | None = None,
) -> ColumnSpec:
    """Build ColumnSpec with Loginom Name identifier + optional Cyrillic DisplayName."""
    ident, display = resolve_column_names(label)
    dt, dk = guess_type(display or label)
    return ColumnSpec(
        name=ident,
        display_name=display,
        usage=usage,
        data_type=data_type or dt,
        data_kind=data_kind or dk,
        input_column=ident,
        origin_custom=origin_custom,
        extension=extension,
        group_functions=list(group_functions or []),
        group_order=group_order,
    )


def specs_for_duplicates(
    names: list[str],
    *,
    inputs: list[str] | None = None,
    outputs: list[str] | None = None,
    all_as_input: bool = False,
) -> list[ColumnSpec]:
    """Duplicates: utActive = input fields, utPredicted = output fields.

    Labels may be Cyrillic headers or Latin identifiers; Name is always a
    valid identifier. Configured duplicates use OriginType=iotCustom.
    """
    if all_as_input:
        inputs = list(names)
        outputs = []
    inputs = inputs or []
    outputs = outputs or []
    # Match by identifier so either Cyrillic or Latin labels work.
    in_ids = {loginom_ident(x) for x in inputs}
    out_ids = {loginom_ident(x) for x in outputs}
    labels = list(dict.fromkeys(names + inputs + outputs))
    specs: list[ColumnSpec] = []
    for label in labels:
        ident = loginom_ident(label)
        if ident in in_ids:
            usage = "utActive"
        elif ident in out_ids:
            usage = "utPredicted"
        else:
            continue
        specs.append(_make_spec(label, usage, origin_custom=True))
    if not any(c.usage == "utActive" for c in specs):
        raise ValueError("duplicates requires at least one input (utActive) column")
    return specs


def specs_for_grouping(
    groups: list[str],
    values: list[str | dict] | None = None,
    *,
    default_agg: str = "gdSum",
) -> list[ColumnSpec]:
    """Grouping: utGroup keys + utValue measures with aggregate functions."""
    values = values or []
    specs: list[ColumnSpec] = []
    for i, label in enumerate(groups):
        specs.append(
            _make_spec(
                label,
                "utGroup",
                extension="group",
                group_order=i,
            )
        )
    for i, v in enumerate(values):
        if isinstance(v, str):
            label, aggs = v, [default_agg]
        else:
            label = v["name"]
            aggs = list(v.get("aggs") or v.get("functions") or [default_agg])
        specs.append(
            _make_spec(
                label,
                "utValue",
                origin_custom=True,
                extension="group",
                group_functions=aggs,
                group_order=i,
            )
        )
    if not groups:
        raise ValueError("grouping requires at least one group column")
    return specs


def specs_for_active(names: list[str]) -> list[ColumnSpec]:
    """Generic: mark columns as utActive (filter/outliers/etc.)."""
    specs = [_make_spec(label, "utActive") for label in names]
    if not specs:
        raise ValueError("no columns")
    return specs
