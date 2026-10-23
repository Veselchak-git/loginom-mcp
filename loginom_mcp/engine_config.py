"""Engine settings for filter / calculator / sorting / ordered outliers / join / import.

Encodings match real Loginom 7.4 packages (e.g. Desktop Zadanie1_Audit.lgp,
join_sample Unit_0.bin for TBGJoinDataEngine Links).
"""
from __future__ import annotations

import re
import struct
import sys
import uuid
from html import escape
from typing import Any
from xml.sax.saxutils import quoteattr

from .paths import VENDOR

if str(VENDOR) not in sys.path:
    sys.path.insert(0, str(VENDOR))

from bgb_import_node import (  # type: ignore  # noqa: E402
    empty_list,
    field_bool,
    field_char,
    field_guid,
    field_int32,
    field_str,
    list_of_items,
    s,
)
from bgb_transform_nodes import field_enum16  # type: ignore  # noqa: E402
from .loginom_ident import resolve_column_names

# ConcatenationType
CT_AND = 0
CT_OR = 1
CT = {"ctAnd": CT_AND, "ctOr": CT_OR, "and": CT_AND, "or": CT_OR}

# RelationType — order matches Loginom FilterRelationType enum (loginom.exe)
FRT_LESS = 0
FRT_LESS_OR_EQUAL = 1
FRT_GREATER = 2
FRT_GREATER_OR_EQUAL = 3
FRT_EQUAL = 4
FRT_NOT_EQUAL = 5
FRT_IS_NULL = 6
FRT_IS_NOT_NULL = 7
FRT_BETWEEN = 8
FRT_NOT_BETWEEN = 9
FRT_IN = 10
FRT_NOT_IN = 11
FRT_LIKE = 12
FRT_NOT_LIKE = 13
FRT_STARTING_WITH = 14
FRT_NOT_STARTING_WITH = 15
FRT_ENDING_WITH = 16
FRT_NOT_ENDING_WITH = 17
FRT_FIRST_PERIOD = 18
FRT_NOT_FIRST_PERIOD = 19
FRT_LAST_PERIOD = 20
FRT_NOT_LAST_PERIOD = 21
FRT_IS_TRUE = 22
FRT_IS_FALSE = 23

FRT_NAMES = {
    FRT_LESS: "frtLess",
    FRT_LESS_OR_EQUAL: "frtLessOrEqual",
    FRT_GREATER: "frtGreater",
    FRT_GREATER_OR_EQUAL: "frtGreaterOrEqual",
    FRT_EQUAL: "frtEqual",
    FRT_NOT_EQUAL: "frtNotEqual",
    FRT_IS_NULL: "frtIsNull",
    FRT_IS_NOT_NULL: "frtIsNotNull",
    FRT_BETWEEN: "frtBetween",
    FRT_NOT_BETWEEN: "frtNotBetween",
    FRT_IN: "frtIn",
    FRT_NOT_IN: "frtNotIn",
    FRT_LIKE: "frtLike",
    FRT_NOT_LIKE: "frtNotLike",
    FRT_STARTING_WITH: "frtStartingWith",
    FRT_NOT_STARTING_WITH: "frtNotStartingWith",
    FRT_ENDING_WITH: "frtEndingWith",
    FRT_NOT_ENDING_WITH: "frtNotEndingWith",
    FRT_FIRST_PERIOD: "frtFirstPeriod",
    FRT_NOT_FIRST_PERIOD: "frtNotFirstPeriod",
    FRT_LAST_PERIOD: "frtLastPeriod",
    FRT_NOT_LAST_PERIOD: "frtNotLastPeriod",
    FRT_IS_TRUE: "frtIsTrue",
    FRT_IS_FALSE: "frtIsFalse",
}

# Canonical + UI/alias keys (RU labels from Loginom filter dropdown)
FRT: dict[str, int] = {
    **{name: code for code, name in FRT_NAMES.items()},
    # comparisons
    "equal": FRT_EQUAL,
    "=": FRT_EQUAL,
    "not_equal": FRT_NOT_EQUAL,
    "ne": FRT_NOT_EQUAL,
    "<>": FRT_NOT_EQUAL,
    "!=": FRT_NOT_EQUAL,
    "less": FRT_LESS,
    "lt": FRT_LESS,
    "<": FRT_LESS,
    "less_or_equal": FRT_LESS_OR_EQUAL,
    "le": FRT_LESS_OR_EQUAL,
    "<=": FRT_LESS_OR_EQUAL,
    "greater": FRT_GREATER,
    "gt": FRT_GREATER,
    ">": FRT_GREATER,
    "greater_or_equal": FRT_GREATER_OR_EQUAL,
    "ge": FRT_GREATER_OR_EQUAL,
    ">=": FRT_GREATER_OR_EQUAL,
    # null / empty
    "is_null": FRT_IS_NULL,
    "null": FRT_IS_NULL,
    "empty": FRT_IS_NULL,
    "пустой": FRT_IS_NULL,
    "is_not_null": FRT_IS_NOT_NULL,
    "not_null": FRT_IS_NOT_NULL,
    "not_empty": FRT_IS_NOT_NULL,
    "не пустой": FRT_IS_NOT_NULL,
    "непустой": FRT_IS_NOT_NULL,
    # range
    "between": FRT_BETWEEN,
    "in_range": FRT_BETWEEN,
    "в интервале": FRT_BETWEEN,
    "not_between": FRT_NOT_BETWEEN,
    "out_of_range": FRT_NOT_BETWEEN,
    "вне интервала": FRT_NOT_BETWEEN,
    # list
    "in": FRT_IN,
    "in_list": FRT_IN,
    "в списке": FRT_IN,
    "not_in": FRT_NOT_IN,
    "out_of_list": FRT_NOT_IN,
    "вне списка": FRT_NOT_IN,
    # text
    "like": FRT_LIKE,
    "contains": FRT_LIKE,
    "содержит": FRT_LIKE,
    "not_like": FRT_NOT_LIKE,
    "not_contains": FRT_NOT_LIKE,
    "не содержит": FRT_NOT_LIKE,
    "starts_with": FRT_STARTING_WITH,
    "starting_with": FRT_STARTING_WITH,
    "начинается с": FRT_STARTING_WITH,
    "not_starts_with": FRT_NOT_STARTING_WITH,
    "not_starting_with": FRT_NOT_STARTING_WITH,
    "не начинается с": FRT_NOT_STARTING_WITH,
    "ends_with": FRT_ENDING_WITH,
    "ending_with": FRT_ENDING_WITH,
    "заканчивается на": FRT_ENDING_WITH,
    "not_ends_with": FRT_NOT_ENDING_WITH,
    "not_ending_with": FRT_NOT_ENDING_WITH,
    "не заканчивается на": FRT_NOT_ENDING_WITH,
    # boolean / period
    "is_true": FRT_IS_TRUE,
    "true": FRT_IS_TRUE,
    "is_false": FRT_IS_FALSE,
    "false": FRT_IS_FALSE,
}

FRT_NULLARY = {
    FRT_IS_NULL,
    FRT_IS_NOT_NULL,
    FRT_FIRST_PERIOD,
    FRT_NOT_FIRST_PERIOD,
    FRT_LAST_PERIOD,
    FRT_NOT_LAST_PERIOD,
    FRT_IS_TRUE,
    FRT_IS_FALSE,
}
FRT_BETWEEN_SET = {FRT_BETWEEN, FRT_NOT_BETWEEN}
FRT_LIST_SET = {FRT_IN, FRT_NOT_IN}

# Column DataType enum (Filter Item / Expression); same ordinals as import
# ColumnDefs, so a calculator can declare every type an import can produce.
DT_BOOLEAN = 1
DT_DATETIME = 2
DT_FLOAT = 3
DT_INTEGER = 4
DT_STRING = 5
DT_VARIANT = 6
DT = {
    "dtBoolean": DT_BOOLEAN,
    "dtDateTime": DT_DATETIME,
    "dtFloat": DT_FLOAT,
    "dtInteger": DT_INTEGER,
    "dtString": DT_STRING,
    "dtVariant": DT_VARIANT,
    "boolean": DT_BOOLEAN,
    "datetime": DT_DATETIME,
    "float": DT_FLOAT,
    "integer": DT_INTEGER,
    "int": DT_INTEGER,
    "string": DT_STRING,
}

# CompareValue VarType
VRT_DOUBLE = 5
VRT_INT64 = 13
VRT_STRING = 15

# Windows VARIANT type codes used after empty-name payload header
VT_R8 = 5
VT_I8 = 20


def _enum(mapping: dict[str, int], value: str | int, default: int | None = None) -> int:
    if isinstance(value, int):
        return value
    key = str(value)
    if key in mapping:
        return mapping[key]
    low = key.lower()
    for k, v in mapping.items():
        if k.lower() == low:
            return v
    if default is not None:
        return default
    raise ValueError(f"unknown enum value {value!r}; expected {list(mapping)}")


def _variant_fields(
    *,
    var_type: int,
    double: float | None = None,
    string: str | None = None,
    int64: int | None = None,
) -> bytes:
    """VarType + variant payload (two attrs) for CompareValue / bounds / list items."""
    body = field_enum16("VarType", var_type)
    if double is not None:
        body += b"\x00\x00" + struct.pack("<H", VT_R8) + struct.pack("<d", float(double))
    elif int64 is not None:
        body += b"\x00\x00" + struct.pack("<H", VT_I8) + struct.pack("<q", int(int64))
    elif string is not None:
        body += b"\x00\x00\x00\x01" + s(string)
    else:
        raise ValueError("variant needs double, string, or int64")
    return body


def _value_as_variant(
    value: Any,
    *,
    data_type: int,
    var_type_hint: str | None = None,
) -> tuple[int, bytes]:
    """Pick VarType + fields body for a Python value."""
    if var_type_hint == "vrtDouble" or (
        data_type == DT_FLOAT and not isinstance(value, str)
    ):
        return VRT_DOUBLE, _variant_fields(var_type=VRT_DOUBLE, double=float(value))
    if var_type_hint == "vrtInt64" or (
        isinstance(value, int)
        and not isinstance(value, bool)
        and data_type != DT_STRING
    ):
        return VRT_INT64, _variant_fields(var_type=VRT_INT64, int64=int(value))
    if data_type == DT_FLOAT and isinstance(value, str):
        try:
            return VRT_DOUBLE, _variant_fields(var_type=VRT_DOUBLE, double=float(value))
        except ValueError:
            pass
    return VRT_STRING, _variant_fields(var_type=VRT_STRING, string=str(value))


def _compare_value_blob(
    *,
    var_type: int,
    double: float | None = None,
    string: str | None = None,
    int64: int | None = None,
) -> bytes:
    """Named CompareValue object: VarType + variant payload, 0 children."""
    return (
        s("CompareValue")
        + b"\x00\x02"
        + _variant_fields(var_type=var_type, double=double, string=string, int64=int64)
        + b"\x00"
    )


def _bound_blob(name: str, value: Any, *, data_type: int, var_type_hint: str | None) -> bytes:
    _, fields = _value_as_variant(value, data_type=data_type, var_type_hint=var_type_hint)
    return s(name) + b"\x00\x02" + fields + b"\x00"


def _compare_value_list_blob(
    values: list[Any],
    *,
    data_type: int,
    var_type_hint: str | None,
) -> bytes:
    if len(values) > 255:
        raise ValueError("too many list values (max 255)")
    children = b""
    for v in values:
        _, fields = _value_as_variant(v, data_type=data_type, var_type_hint=var_type_hint)
        children += s("I") + b"\x00\x02" + fields + b"\x00"
    n = len(values)
    return (
        s("CompareValueList")
        + b"\x00\x01"
        + s("Count")
        + b"\x04"
        + bytes([n])
        + bytes([n])
        + children
    )


def _relation_children_blob(
    relation: int,
    item: dict[str, Any],
    *,
    data_type: int,
) -> bytes:
    hint = item.get("var_type")
    if relation in FRT_NULLARY:
        return b""
    if relation in FRT_BETWEEN_SET:
        lower = item.get("lower", item.get("CompareValueLowerBound"))
        upper = item.get("upper", item.get("CompareValueUpperBound"))
        if lower is None or upper is None:
            raw = item.get("value", item.get("CompareValue"))
            if isinstance(raw, (list, tuple)) and len(raw) >= 2:
                lower, upper = raw[0], raw[1]
        if lower is None or upper is None:
            raise ValueError("between/not_between needs lower+upper (or value=[lo, hi])")
        return (
            _bound_blob("CompareValueLowerBound", lower, data_type=data_type, var_type_hint=hint)
            + _bound_blob("CompareValueUpperBound", upper, data_type=data_type, var_type_hint=hint)
        )
    if relation in FRT_LIST_SET:
        values = item.get("values", item.get("CompareValueList"))
        if values is None:
            raw = item.get("value", item.get("CompareValue"))
            if isinstance(raw, (list, tuple)):
                values = list(raw)
            elif raw is None or raw == "":
                values = []
            else:
                values = [raw]
        if not isinstance(values, list):
            raise ValueError("in/not_in needs values=[...]")
        return _compare_value_list_blob(values, data_type=data_type, var_type_hint=hint)

    value = item.get("value", item.get("CompareValue", ""))
    _, fields = _value_as_variant(value, data_type=data_type, var_type_hint=hint)
    return s("CompareValue") + b"\x00\x02" + fields + b"\x00"


def _filter_item_blob(item: dict[str, Any]) -> bytes:
    label = item["name"]
    name, display = resolve_column_names(label)
    if item.get("display_name") or item.get("displayName"):
        display = item.get("display_name") or item.get("displayName")
    if display is None:
        display = label

    concat = _enum(CT, item.get("concat") or item.get("ConcatenationType") or "ctAnd")
    data_type = _enum(DT, item.get("data_type") or item.get("DataType") or "dtString")
    relation = _enum(FRT, item.get("relation") or item.get("RelationType") or "frtEqual")
    guid = uuid.UUID(item["guid"]) if item.get("guid") else uuid.uuid4()

    children = _relation_children_blob(relation, item, data_type=data_type)
    child_count = 0 if not children else (2 if relation in FRT_BETWEEN_SET else 1)

    attrs = (
        field_guid("Guid", guid)
        + field_str("Name", name)
        + field_str("DisplayName", display)
        + field_enum16("ConcatenationType", concat)
        + field_enum16("DataType", data_type)
        + field_enum16("RelationType", relation)
    )
    return b"\x00\x06" + attrs + bytes([child_count]) + children


def build_filter_obj_blob(
    items: list[dict[str, Any]],
    *,
    case_sensitive: bool = False,
) -> bytes:
    """Filter object (child of TBGFilterDataEngine), not including Engine wrapper."""
    if len(items) > 255:
        raise ValueError("too many filter items")
    children = b"".join(s("Item") + _filter_item_blob(it) for it in items)
    return (
        s("Filter")
        + b"\x00\x01"
        + field_bool("UseGlobalCaseSensitive", case_sensitive)
        + bytes([len(items)])
        + children
    )


_VIRGIN_FILTER_OBJ = (
    s("Filter")
    + b"\x00\x01"
    + field_bool("UseGlobalCaseSensitive", False)
    + b"\x00"
)


def inject_filter_blob(node_blob: bytes, items: list[dict[str, Any]]) -> bytes:
    filled = build_filter_obj_blob(items)
    if _VIRGIN_FILTER_OBJ not in node_blob:
        raise ValueError("virgin Filter object not found in node blob")
    return node_blob.replace(_VIRGIN_FILTER_OBJ, filled, 1)


def _xml_var_type_and_text(
    value: Any,
    *,
    data_type: str,
    var_type_hint: str | None,
) -> tuple[str, str]:
    if var_type_hint == "vrtDouble" or (
        data_type == "dtFloat" and not isinstance(value, str)
    ):
        return "vrtDouble", str(value)
    if var_type_hint == "vrtInt64" or (
        isinstance(value, int) and not isinstance(value, bool) and data_type != "dtString"
    ):
        return "vrtInt64", str(value)
    if data_type == "dtFloat" and isinstance(value, str):
        try:
            float(value)
            return "vrtDouble", value
        except ValueError:
            pass
    return "vrtString", str(value)


def _xml_relation_name(relation: str | int) -> str:
    if isinstance(relation, int):
        return FRT_NAMES.get(relation, "frtEqual")
    code = _enum(FRT, relation)
    return FRT_NAMES[code]


def _xml_relation_children(
    relation_code: int,
    item: dict[str, Any],
    *,
    data_type: str,
) -> str:
    hint = item.get("var_type")
    if relation_code in FRT_NULLARY:
        return ""
    if relation_code in FRT_BETWEEN_SET:
        lower = item.get("lower", item.get("CompareValueLowerBound"))
        upper = item.get("upper", item.get("CompareValueUpperBound"))
        if lower is None or upper is None:
            raw = item.get("value", item.get("CompareValue"))
            if isinstance(raw, (list, tuple)) and len(raw) >= 2:
                lower, upper = raw[0], raw[1]
        if lower is None or upper is None:
            raise ValueError("between/not_between needs lower+upper (or value=[lo, hi])")
        vt_l, t_l = _xml_var_type_and_text(lower, data_type=data_type, var_type_hint=hint)
        vt_u, t_u = _xml_var_type_and_text(upper, data_type=data_type, var_type_hint=hint)
        return (
            f'<CompareValueLowerBound VarType="{vt_l}">{escape(t_l)}</CompareValueLowerBound>'
            f'<CompareValueUpperBound VarType="{vt_u}">{escape(t_u)}</CompareValueUpperBound>'
        )
    if relation_code in FRT_LIST_SET:
        values = item.get("values", item.get("CompareValueList"))
        if values is None:
            raw = item.get("value", item.get("CompareValue"))
            if isinstance(raw, (list, tuple)):
                values = list(raw)
            elif raw is None or raw == "":
                values = []
            else:
                values = [raw]
        parts = ["<CompareValueList>"]
        for v in values:
            vt, text = _xml_var_type_and_text(v, data_type=data_type, var_type_hint=hint)
            parts.append(f'<I VarType="{vt}">{escape(text)}</I>')
        parts.append("</CompareValueList>")
        return "".join(parts)

    value = item.get("value", item.get("CompareValue", ""))
    vt, text = _xml_var_type_and_text(value, data_type=data_type, var_type_hint=hint)
    return f'<CompareValue VarType="{vt}">{escape(text)}</CompareValue>'


def build_filter_xml(
    items: list[dict[str, Any]],
    *,
    case_sensitive: bool = False,
) -> str:
    cs = "true" if case_sensitive else "false"
    parts = [f'<Filter UseGlobalCaseSensitive="{cs}">']
    for it in items:
        label = it["name"]
        name, display = resolve_column_names(label)
        if it.get("display_name") or it.get("displayName"):
            display = it.get("display_name") or it.get("displayName")
        if display is None:
            display = label
        concat = it.get("concat") or it.get("ConcatenationType") or "ctAnd"
        if isinstance(concat, int):
            concat = {0: "ctAnd", 1: "ctOr"}.get(concat, "ctAnd")
        data_type = it.get("data_type") or it.get("DataType") or "dtString"
        if isinstance(data_type, int):
            data_type = {3: "dtFloat", 5: "dtString"}.get(data_type, "dtString")
        relation_raw = it.get("relation") or it.get("RelationType") or "frtEqual"
        relation = _xml_relation_name(relation_raw)
        relation_code = _enum(FRT, relation_raw)
        guid = it.get("guid") or str(uuid.uuid4())
        children = _xml_relation_children(relation_code, it, data_type=str(data_type))
        open_tag = (
            f'<Item Guid="{guid}" Name="{escape(name)}" '
            f'DisplayName={quoteattr(display)} ConcatenationType="{concat}" '
            f'DataType="{data_type}" RelationType="{relation}"'
        )
        if children:
            parts.append(open_tag + ">" + children + "</Item>")
        else:
            parts.append(open_tag + "/>")
    parts.append("</Filter>")
    return "".join(parts)


def inject_filter_xml(node_xml: str, items: list[dict[str, Any]]) -> str:
    filled = build_filter_xml(items)
    patterns = [
        r'<Filter UseGlobalCaseSensitive="false"\s*/>',
        r'<Filter UseGlobalCaseSensitive="false"></Filter>',
        r"<Filter/>",
        r"<Filter></Filter>",
    ]
    for pat in patterns:
        new_xml, n = re.subn(pat, lambda _m: filled, node_xml, count=1)
        if n:
            return new_xml
    raise ValueError("empty Filter element not found in node XML")


def _expression_item_blob(expr: dict[str, Any]) -> bytes:
    name = expr["name"]
    # keep Latin Name as-is when already valid
    name, _ = resolve_column_names(name) if not name.isascii() or " " in name else (name, None)
    data_type = _enum(DT, expr.get("data_type") or expr.get("DataType") or "dtFloat")
    expression = expr["expression"] if "expression" in expr else expr["Expression"]
    display = expr.get("display_name") or expr.get("displayName")
    attrs = field_str("Name", name)
    n_attrs = 3
    if display:
        attrs += field_str("DisplayName", display)
        n_attrs = 4
    attrs += field_enum16("DataType", data_type) + field_str("Expression", expression)
    return b"\x00" + bytes([n_attrs]) + attrs + b"\x00"


def build_expressions_blob(expressions: list[dict[str, Any]]) -> bytes:
    items = [_expression_item_blob(e) for e in expressions]
    return list_of_items("Expressions", items)


_VIRGIN_EXPRESSIONS = empty_list("Expressions")


def inject_expressions_blob(node_blob: bytes, expressions: list[dict[str, Any]]) -> bytes:
    filled = build_expressions_blob(expressions)
    if _VIRGIN_EXPRESSIONS not in node_blob:
        raise ValueError("virgin Expressions list not found in node blob")
    return node_blob.replace(_VIRGIN_EXPRESSIONS, filled, 1)


def build_expressions_xml(expressions: list[dict[str, Any]]) -> str:
    parts = ["<Expressions>"]
    for e in expressions:
        name = e["name"]
        if not name.isascii() or " " in name:
            name, _ = resolve_column_names(name)
        data_type = e.get("data_type") or e.get("DataType") or "dtFloat"
        if isinstance(data_type, int):
            data_type = {3: "dtFloat", 5: "dtString"}.get(data_type, "dtFloat")
        expression = e["expression"] if "expression" in e else e["Expression"]
        display = e.get("display_name") or e.get("displayName")
        attrs = f'Name="{escape(name)}" DataType="{data_type}" Expression={quoteattr(expression)}'
        if display:
            attrs = (
                f'Name="{escape(name)}" DisplayName={quoteattr(display)} '
                f'DataType="{data_type}" Expression={quoteattr(expression)}'
            )
        parts.append(f"<Item {attrs}/>")
    parts.append("</Expressions>")
    return "".join(parts)


def inject_expressions_xml(node_xml: str, expressions: list[dict[str, Any]]) -> str:
    filled = build_expressions_xml(expressions)
    for pat in (r"<Expressions\s*/>", r"<Expressions></Expressions>"):
        new_xml, n = re.subn(pat, lambda _m: filled, node_xml, count=1)
        if n:
            return new_xml
    raise ValueError("empty Expressions element not found in node XML")


def build_sorting_columns_blob(columns: list[str | dict[str, Any]]) -> bytes:
    items: list[bytes] = []
    for col in columns:
        if isinstance(col, str):
            name = col
            direction = None
        else:
            name = col["name"]
            direction = col.get("direction") or col.get("SortDirection")
        name, _ = resolve_column_names(name) if not name.isascii() else (name, None)
        if direction is None:
            items.append(b"\x00\x01" + field_str("Name", name) + b"\x00")
        else:
            d = 0 if str(direction).lower() in ("0", "asc", "sdasc", "sd_asc") else 1
            items.append(
                b"\x00\x02"
                + field_str("Name", name)
                + field_enum16("SortDirection", d)
                + b"\x00"
            )
    return list_of_items("SortingColumns", items)


_VIRGIN_SORTING = empty_list("SortingColumns")


def inject_sorting_blob(node_blob: bytes, columns: list[str | dict[str, Any]]) -> bytes:
    filled = build_sorting_columns_blob(columns)
    if _VIRGIN_SORTING not in node_blob:
        raise ValueError("virgin SortingColumns list not found in node blob")
    return node_blob.replace(_VIRGIN_SORTING, filled, 1)


def build_sorting_xml(columns: list[str | dict[str, Any]]) -> str:
    parts = ["<SortingColumns>"]
    for col in columns:
        if isinstance(col, str):
            name = col
            direction = None
        else:
            name = col["name"]
            direction = col.get("direction") or col.get("SortDirection")
        name, _ = resolve_column_names(name) if not name.isascii() else (name, None)
        if direction is None:
            parts.append(f'<Item Name="{escape(name)}"/>')
        else:
            d = "sdAsc" if str(direction).lower() in ("0", "asc", "sdasc", "sd_asc") else "sdDesc"
            parts.append(f'<Item Name="{escape(name)}" SortDirection="{d}"/>')
    parts.append("</SortingColumns>")
    return "".join(parts)


def inject_sorting_xml(node_xml: str, columns: list[str | dict[str, Any]]) -> str:
    filled = build_sorting_xml(columns)
    for pat in (r"<SortingColumns\s*/>", r"<SortingColumns></SortingColumns>"):
        new_xml, n = re.subn(pat, lambda _m: filled, node_xml, count=1)
        if n:
            return new_xml
    raise ValueError("empty SortingColumns element not found in node XML")


_VIRGIN_OUTLIER_ENGINE = s("Engine") + s("TBGElimOutlierEngine") + b"\x00\x00"
_ORDERED_OUTLIER_ENGINE = (
    s("Engine")
    + s("TBGElimOutlierEngine")
    + b"\x01"
    + field_bool("OrderedSample", True)
    + b"\x00"
)


def inject_ordered_sample_blob(node_blob: bytes, ordered: bool = True) -> bytes:
    if not ordered:
        return node_blob
    if _VIRGIN_OUTLIER_ENGINE not in node_blob:
        raise ValueError("virgin TBGElimOutlierEngine not found in node blob")
    return node_blob.replace(_VIRGIN_OUTLIER_ENGINE, _ORDERED_OUTLIER_ENGINE, 1)


def inject_ordered_sample_xml(node_xml: str, ordered: bool = True) -> str:
    if not ordered:
        return node_xml
    filled = '<Engine xsi:type="TBGElimOutlierEngine" OrderedSample="true"/>'
    patterns = [
        r'<Engine xsi:type="TBGElimOutlierEngine"\s*/>',
        r'<Engine xsi:type="TBGElimOutlierEngine"></Engine>',
    ]
    for pat in patterns:
        new_xml, n = re.subn(pat, lambda _m: filled, node_xml, count=1)
        if n:
            return new_xml
    raise ValueError("TBGElimOutlierEngine element not found in node XML")


# JoinType ordinals (docs + jtFullJoin=3 in join_sample)
JT_INNER = 0
JT_LEFT = 1
JT_RIGHT = 2
JT_FULL = 3
JT_DIFF = 4
JOIN_TYPE = {
    "jtInnerJoin": JT_INNER,
    "inner": JT_INNER,
    "внутреннее": JT_INNER,
    "jtLeftJoin": JT_LEFT,
    "left": JT_LEFT,
    "левое": JT_LEFT,
    "jtRightJoin": JT_RIGHT,
    "right": JT_RIGHT,
    "правое": JT_RIGHT,
    "jtFullJoin": JT_FULL,
    "full": JT_FULL,
    "полное": JT_FULL,
    "jtDifference": JT_DIFF,
    "diff": JT_DIFF,
    "difference": JT_DIFF,
    "разность": JT_DIFF,
}
JOIN_TYPE_XML = {
    JT_INNER: "jtInnerJoin",
    JT_LEFT: "jtLeftJoin",
    JT_RIGHT: "jtRightJoin",
    JT_FULL: "jtFullJoin",
    JT_DIFF: "jtDifference",
}
JOIN_TYPE_DISPLAY = {
    JT_INNER: "Внутреннее",
    JT_LEFT: "Левое",
    JT_RIGHT: "Правое",
    JT_FULL: "Полное",
    JT_DIFF: "Разность",
}

_VIRGIN_JOIN_ENGINE = (
    s("Engine")
    + s("TBGJoinDataEngine")
    + b"\x01"
    + field_str("DisplayNamePrefix", "Соединение")
    + b"\x01"
    + empty_list("Links")
)


def resolve_join_type(value: str | int) -> int:
    if isinstance(value, int):
        if value not in JOIN_TYPE_XML:
            raise ValueError(f"unknown JoinType ordinal {value}")
        return value
    key = str(value).strip()
    if key in JOIN_TYPE:
        return JOIN_TYPE[key]
    low = key.lower()
    for k, v in JOIN_TYPE.items():
        if k.lower() == low:
            return v
    raise ValueError(f"unknown JoinType {value!r}; expected {list(JOIN_TYPE)}")


def _join_side_blob(tag: str, column: str) -> bytes:
    name, _ = resolve_column_names(column)
    return s(tag) + b"\x00\x01" + field_str("Name", name) + b"\x00"


def _join_link_item_blob(left: str, right: str) -> bytes:
    return (
        b"\x00\x01"
        + field_guid("Guid", uuid.uuid4())
        + b"\x02"
        + _join_side_blob("Left", left)
        + _join_side_blob("Right", right)
    )


def build_join_engine_blob(
    join_type: str | int,
    keys: list[dict[str, Any] | list[str] | tuple[str, str]],
) -> bytes:
    jt = resolve_join_type(join_type)
    link_items: list[bytes] = []
    for key in keys:
        if isinstance(key, (list, tuple)) and len(key) == 2:
            left, right = key[0], key[1]
        elif isinstance(key, dict):
            left = key.get("left") or key.get("main") or key.get("Left")
            right = key.get("right") or key.get("joined") or key.get("Right")
            if left is None or right is None:
                raise ValueError(f"join key needs left/right: {key!r}")
        else:
            raise ValueError(f"bad join key: {key!r}")
        link_items.append(_join_link_item_blob(str(left), str(right)))
    links = list_of_items("Links", link_items) if link_items else empty_list("Links")
    return (
        s("Engine")
        + s("TBGJoinDataEngine")
        + b"\x02"
        + field_enum16("JoinType", jt)
        + field_str("DisplayNamePrefix", "Соединение")
        + b"\x01"
        + links
    )


def build_join_engine_xml(
    join_type: str | int,
    keys: list[dict[str, Any] | list[str] | tuple[str, str]],
) -> str:
    jt = resolve_join_type(join_type)
    jt_name = JOIN_TYPE_XML[jt]
    parts = [
        f'<Engine xsi:type="TBGJoinDataEngine" JoinType="{jt_name}" '
        f'DisplayNamePrefix="Соединение">'
    ]
    if not keys:
        parts.append("<Links/>")
    else:
        parts.append("<Links>")
        for key in keys:
            if isinstance(key, (list, tuple)) and len(key) == 2:
                left, right = str(key[0]), str(key[1])
            else:
                assert isinstance(key, dict)
                left = str(key.get("left") or key.get("main") or key.get("Left"))
                right = str(key.get("right") or key.get("joined") or key.get("Right"))
            left_name, _ = resolve_column_names(left)
            right_name, _ = resolve_column_names(right)
            gid = str(uuid.uuid4())
            parts.append(
                f'<Item Guid="{gid}">'
                f'<Left Name="{escape(left_name)}"/>'
                f'<Right Name="{escape(right_name)}"/>'
                f"</Item>"
            )
        parts.append("</Links>")
    parts.append("</Engine>")
    return "".join(parts)


def inject_join_blob(
    node_blob: bytes,
    join_type: str | int,
    keys: list[dict[str, Any] | list[str] | tuple[str, str]],
) -> bytes:
    filled = build_join_engine_blob(join_type, keys)
    if _VIRGIN_JOIN_ENGINE not in node_blob:
        # already configured or unexpected layout — replace by engine classname span
        start = node_blob.find(s("TBGJoinDataEngine"))
        if start < 0:
            raise ValueError("TBGJoinDataEngine not found in node blob")
        # walk back to Engine tag
        eng = node_blob.rfind(s("Engine"), 0, start)
        if eng < 0:
            raise ValueError("Engine wrapper not found before TBGJoinDataEngine")
        # naive: replace from Engine through virgin-like empty Links if present
        raise ValueError("virgin Join engine not found in node blob; recreate join node")
    return node_blob.replace(_VIRGIN_JOIN_ENGINE, filled, 1)


def inject_join_xml(
    node_xml: str,
    join_type: str | int,
    keys: list[dict[str, Any] | list[str] | tuple[str, str]],
) -> str:
    filled = build_join_engine_xml(join_type, keys)
    patterns = [
        r'<Engine xsi:type="TBGJoinDataEngine" DisplayNamePrefix="Соединение"><Links/></Engine>',
        r'<Engine xsi:type="TBGJoinDataEngine" DisplayNamePrefix="Соединение"/>',
        r'<Engine xsi:type="TBGJoinDataEngine" DisplayNamePrefix="Соединение"></Engine>',
    ]
    for pat in patterns:
        new_xml, n = re.subn(pat, lambda _m: filled, node_xml, count=1)
        if n:
            return new_xml
    # already has JoinType — replace whole engine element
    new_xml, n = re.subn(
        r'<Engine xsi:type="TBGJoinDataEngine"[^>]*>.*?</Engine>',
        lambda _m: filled,
        node_xml,
        count=1,
        flags=re.DOTALL,
    )
    if n:
        return new_xml
    raise ValueError("TBGJoinDataEngine element not found in node XML")


# --- Import text / Excel engine settings ------------------------------------
# Quote and skip-rows are not stored on TBGImportTextFile.
# DelimiterChar is stored when it is not the Loginom default (the practice
# packages keep ";"). FileName, CodePage, decimal/date separators, SheetNumber
# and ColumnDefs are stored as well.

CODE_PAGES: dict[str, int] = {
    "utf-8": 65001,
    "utf8": 65001,
    "cp65001": 65001,
    "65001": 65001,
    "windows-1251": 1251,
    "cp1251": 1251,
    "1251": 1251,
    "windows-1252": 1252,
    "cp1252": 1252,
    "1252": 1252,
    "ascii": 20127,
    "cp866": 866,
    "866": 866,
}

# Import ColumnDefs DataType / DataKind / UsageType (same ordinals as column_config)
_IMP_DT = {
    "dtBoolean": 1,
    "dtDateTime": 2,
    "dtFloat": 3,
    "dtInteger": 4,
    "dtString": 5,
    "dtVariant": 6,
    "boolean": 1,
    "datetime": 2,
    "float": 3,
    "integer": 4,
    "int": 4,
    "string": 5,
}
_IMP_DK = {
    "dkUndefined": 0,
    "dkContinuous": 1,
    "dkDiscrete": 2,
    "continuous": 1,
    "discrete": 2,
}
_IMP_UT = {
    "utUnspecified": 0,
    "utActive": 3,
    "utPredicted": 4,
    "active": 3,
}


def resolve_code_page(value: str | int | None, default: int = 65001) -> int:
    if value is None:
        return default
    if isinstance(value, int):
        return value
    key = str(value).strip()
    if key.isdigit():
        return int(key)
    low = key.lower().replace("_", "-")
    if low in CODE_PAGES:
        return CODE_PAGES[low]
    raise ValueError(f"unknown code_page/encoding {value!r}; try 1251, 65001, utf-8, windows-1251")


def _guess_import_kind(data_type: str) -> str:
    if data_type in ("dtString", "dtBoolean", "string", "boolean"):
        return "dkDiscrete"
    return "dkContinuous"


def _import_column_item_blob(col: dict[str, Any]) -> bytes:
    """Engine ColumnDefs Item as in hand-saved Loginom imports (enum type 0x09)."""
    label = col["name"]
    name, display = resolve_column_names(label)
    if col.get("display_name") or col.get("displayName"):
        display = col.get("display_name") or col.get("displayName")
    dt_raw = col.get("data_type") or col.get("DataType") or "dtString"
    if isinstance(dt_raw, int):
        dt = dt_raw
        dt_name = {v: k for k, v in _IMP_DT.items() if k.startswith("dt")}.get(dt, "dtString")
    else:
        dt = _enum(_IMP_DT, dt_raw)
        dt_name = str(dt_raw) if str(dt_raw).startswith("dt") else {
            1: "dtBoolean", 2: "dtDateTime", 3: "dtFloat", 4: "dtInteger", 5: "dtString",
        }.get(dt, "dtString")
    dk_raw = col.get("data_kind") or col.get("DataKind") or _guess_import_kind(dt_name)
    dk = dk_raw if isinstance(dk_raw, int) else _enum(_IMP_DK, dk_raw)
    ut_raw = col.get("usage") or col.get("UsageType") or "utActive"
    ut = ut_raw if isinstance(ut_raw, int) else _enum(_IMP_UT, ut_raw)

    attrs = field_str("Name", name)
    n_attr = 1
    if display is not None:
        attrs += field_str("DisplayName", display)
        n_attr += 1
    attrs += (
        field_enum16("DataType", dt)
        + field_enum16("DataKind", dk)
        + field_enum16("UsageType", ut)
    )
    n_attr += 3
    return b"\x00" + bytes([n_attr]) + attrs + b"\x00"


def _import_column_defs_blob(columns: list[dict[str, Any]] | None) -> bytes:
    if not columns:
        return empty_list("ColumnDefs")
    if len(columns) > 255:
        raise ValueError("too many import columns")
    items = [_import_column_item_blob(c) for c in columns]
    return list_of_items("ColumnDefs", items)


def _import_column_defs_xml(columns: list[dict[str, Any]] | None) -> str:
    if not columns:
        return "<ColumnDefs/>"
    parts = ["<ColumnDefs>"]
    for col in columns:
        label = col["name"]
        name, display = resolve_column_names(label)
        if col.get("display_name") or col.get("displayName"):
            display = col.get("display_name") or col.get("displayName")
        dt_raw = col.get("data_type") or col.get("DataType") or "dtString"
        if isinstance(dt_raw, int):
            dt = {1: "dtBoolean", 2: "dtDateTime", 3: "dtFloat", 4: "dtInteger", 5: "dtString"}.get(
                dt_raw, "dtString"
            )
        else:
            code = _enum(_IMP_DT, dt_raw)
            dt = {
                1: "dtBoolean", 2: "dtDateTime", 3: "dtFloat", 4: "dtInteger", 5: "dtString",
            }.get(code, "dtString")
            if str(dt_raw).startswith("dt"):
                dt = str(dt_raw)
        dk_raw = col.get("data_kind") or col.get("DataKind") or _guess_import_kind(dt)
        if isinstance(dk_raw, int):
            dk = {0: "dkUndefined", 1: "dkContinuous", 2: "dkDiscrete"}.get(dk_raw, "dkDiscrete")
        else:
            code = _enum(_IMP_DK, dk_raw)
            dk = {0: "dkUndefined", 1: "dkContinuous", 2: "dkDiscrete"}.get(code, "dkDiscrete")
            if str(dk_raw).startswith("dk"):
                dk = str(dk_raw)
        ut_raw = col.get("usage") or col.get("UsageType") or "utActive"
        if isinstance(ut_raw, int):
            ut = {3: "utActive", 4: "utPredicted"}.get(ut_raw, "utActive")
        else:
            ut = "utActive" if _enum(_IMP_UT, ut_raw) == 3 else str(ut_raw)
            if not str(ut).startswith("ut"):
                ut = "utActive"
        attrs = f'Name="{escape(name)}"'
        if display is not None:
            attrs += f" DisplayName={quoteattr(display)}"
        attrs += f' DataType="{dt}" DataKind="{dk}" UsageType="{ut}"'
        parts.append(f"<Item {attrs}/>")
    parts.append("</ColumnDefs>")
    return "".join(parts)


def _normalize_import_settings(settings: dict[str, Any]) -> dict[str, Any]:
    out = dict(settings)
    # aliases
    if "encoding" in out and "code_page" not in out:
        out["code_page"] = out["encoding"]
    if "codepage" in out and "code_page" not in out:
        out["code_page"] = out["codepage"]
    if "sheet" in out and "sheet_number" not in out:
        out["sheet_number"] = out["sheet"]
    if "delimiter_char" in out and "delimiter" not in out:
        out["delimiter"] = out["delimiter_char"]
    if "quote" in out or "skip_rows" in out:
        out.pop("quote", None)
        out.pop("skip_rows", None)
    return out


def build_import_text_engine_inner(
    *,
    file_name: str,
    code_page: str | int = 65001,
    decimal_separator: str = ".",
    date_format: str = "dd.MM.yyyy",
    date_separator: str = ".",
    delimiter: str | None = None,
    columns_required: bool | None = False,
    columns: list[dict[str, Any]] | None = None,
) -> bytes:
    """Inner object starting at TBGImportTextFile (no Engine wrapper)."""
    cp = resolve_code_page(code_page)
    attrs = field_str("FileName", file_name) + field_int32("CodePage", cp)
    n_attr = 2
    if delimiter is not None:
        attrs += field_char("DelimiterChar", delimiter)
        n_attr += 1
    attrs += (
        field_char("DecimalSeparator", decimal_separator)
        + field_str("DateFormat", date_format)
        + field_char("DateSeparator", date_separator)
    )
    n_attr += 3
    if columns_required is not None:
        attrs += field_bool("ColumnsRequired", bool(columns_required))
        n_attr += 1
    return (
        s("TBGImportTextFile")
        + bytes([n_attr])
        + attrs
        + b"\x01"
        + _import_column_defs_blob(columns)
    )


def build_import_excel_engine_inner(
    *,
    file_name: str,
    sheet_number: int = 1,
    columns: list[dict[str, Any]] | None = None,
) -> bytes:
    return (
        s("TBGImportExcelFileEngine")
        + b"\x02"
        + field_str("FileName", file_name)
        + field_int32("SheetNumber", int(sheet_number))
        + b"\x01"
        + _import_column_defs_blob(columns)
    )


def build_import_text_engine_xml(
    *,
    file_name: str,
    code_page: str | int = 65001,
    decimal_separator: str = ".",
    date_format: str = "dd.MM.yyyy",
    date_separator: str = ".",
    delimiter: str | None = None,
    columns_required: bool | None = False,
    columns: list[dict[str, Any]] | None = None,
) -> str:
    cp = resolve_code_page(code_page)
    attrs = (
        f'xsi:type="TBGImportTextFile" FileName={quoteattr(file_name)} '
        f'CodePage="{cp}"'
    )
    if delimiter is not None:
        attrs += f" DelimiterChar={quoteattr(delimiter)}"
    attrs += (
        f" DecimalSeparator={quoteattr(decimal_separator)} "
        f"DateFormat={quoteattr(date_format)} DateSeparator={quoteattr(date_separator)}"
    )
    if columns_required is not None:
        attrs += f' ColumnsRequired="{"true" if columns_required else "false"}"'
    return f"<Engine {attrs}>{_import_column_defs_xml(columns)}</Engine>"


def build_import_excel_engine_xml(
    *,
    file_name: str,
    sheet_number: int = 1,
    columns: list[dict[str, Any]] | None = None,
) -> str:
    return (
        f'<Engine xsi:type="TBGImportExcelFileEngine" FileName={quoteattr(file_name)} '
        f'SheetNumber="{int(sheet_number)}">'
        f"{_import_column_defs_xml(columns)}</Engine>"
    )


def _replace_typed_engine(blob: bytes, classname: bytes, filled_inner: bytes) -> bytes:
    """Replace virgin classname…empty ColumnDefs with filled_inner."""
    start = blob.find(classname)
    if start < 0:
        raise ValueError(f"{classname.decode()} not found in node blob")
    empty_cd = empty_list("ColumnDefs")
    cd = blob.find(empty_cd, start)
    if cd < 0:
        raise ValueError(
            "virgin import ColumnDefs not found — recreate the import node "
            "(re-inject into an already configured import is not supported)"
        )
    end = cd + len(empty_cd)
    return blob[:start] + filled_inner + blob[end:]


def inject_import_text_blob(node_blob: bytes, settings: dict[str, Any], *, file_name: str) -> bytes:
    sdict = _normalize_import_settings(settings)
    fn = sdict.get("file_name") or file_name
    inner = build_import_text_engine_inner(
        file_name=fn,
        code_page=sdict.get("code_page", 65001),
        decimal_separator=sdict.get("decimal_separator", "."),
        date_format=sdict.get("date_format", "dd.MM.yyyy"),
        date_separator=sdict.get("date_separator", "."),
        delimiter=sdict.get("delimiter"),
        columns_required=sdict.get("columns_required", False),
        columns=sdict.get("columns"),
    )
    return _replace_typed_engine(node_blob, b"TBGImportTextFile", inner)


def inject_import_excel_blob(node_blob: bytes, settings: dict[str, Any], *, file_name: str) -> bytes:
    sdict = _normalize_import_settings(settings)
    fn = sdict.get("file_name") or file_name
    inner = build_import_excel_engine_inner(
        file_name=fn,
        sheet_number=int(sdict.get("sheet_number", 1)),
        columns=sdict.get("columns"),
    )
    return _replace_typed_engine(node_blob, b"TBGImportExcelFileEngine", inner)


def inject_import_text_xml(node_xml: str, settings: dict[str, Any], *, file_name: str) -> str:
    sdict = _normalize_import_settings(settings)
    fn = sdict.get("file_name") or file_name
    filled = build_import_text_engine_xml(
        file_name=fn,
        code_page=sdict.get("code_page", 65001),
        decimal_separator=sdict.get("decimal_separator", "."),
        date_format=sdict.get("date_format", "dd.MM.yyyy"),
        date_separator=sdict.get("date_separator", "."),
        delimiter=sdict.get("delimiter"),
        columns_required=sdict.get("columns_required", False),
        columns=sdict.get("columns"),
    )
    new_xml, n = re.subn(
        r'<Engine xsi:type="TBGImportTextFile"[^>]*/>|'
        r'<Engine xsi:type="TBGImportTextFile"[^>]*>.*?</Engine>',
        lambda _m: filled,
        node_xml,
        count=1,
        flags=re.DOTALL,
    )
    if not n:
        raise ValueError("TBGImportTextFile Engine not found in node XML")
    return new_xml


def inject_import_excel_xml(node_xml: str, settings: dict[str, Any], *, file_name: str) -> str:
    sdict = _normalize_import_settings(settings)
    fn = sdict.get("file_name") or file_name
    filled = build_import_excel_engine_xml(
        file_name=fn,
        sheet_number=int(sdict.get("sheet_number", 1)),
        columns=sdict.get("columns"),
    )
    new_xml, n = re.subn(
        r'<Engine xsi:type="TBGImportExcelFileEngine"[^>]*/>|'
        r'<Engine xsi:type="TBGImportExcelFileEngine"[^>]*>.*?</Engine>',
        lambda _m: filled,
        node_xml,
        count=1,
        flags=re.DOTALL,
    )
    if not n:
        raise ValueError("TBGImportExcelFileEngine not found in node XML")
    return new_xml


def apply_engine_settings(
    blob: bytes,
    xml: str,
    *,
    filter_items: list[dict[str, Any]] | None = None,
    expressions: list[dict[str, Any]] | None = None,
    sort_columns: list[str | dict[str, Any]] | None = None,
    ordered_sample: bool | None = None,
    join_type: str | int | None = None,
    join_keys: list | None = None,
    import_settings: dict[str, Any] | None = None,
    import_component: str | None = None,
    file_name: str | None = None,
    component: str | None = None,
    engine_settings: dict[str, Any] | None = None,
) -> tuple[bytes, str]:
    if filter_items is not None:
        blob = inject_filter_blob(blob, filter_items)
        xml = inject_filter_xml(xml, filter_items)
    if expressions is not None:
        if component == "calc_variables":
            from .scenario_settings import inject_variable_expressions

            blob, xml = inject_variable_expressions(blob, xml, expressions)
        else:
            blob = inject_expressions_blob(blob, expressions)
            xml = inject_expressions_xml(xml, expressions)
    if sort_columns is not None:
        blob = inject_sorting_blob(blob, sort_columns)
        xml = inject_sorting_xml(xml, sort_columns)
    if ordered_sample is not None:
        blob = inject_ordered_sample_blob(blob, ordered_sample)
        xml = inject_ordered_sample_xml(xml, ordered_sample)
    if join_type is not None or join_keys is not None:
        jt = join_type if join_type is not None else "left"
        keys = list(join_keys or [])
        blob = inject_join_blob(blob, jt, keys)
        xml = inject_join_xml(xml, jt, keys)
    if import_settings is not None:
        fn = file_name or str(import_settings.get("file_name") or "data.csv")
        comp = import_component or "import_text"
        if comp == "import_text":
            blob = inject_import_text_blob(blob, import_settings, file_name=fn)
            xml = inject_import_text_xml(xml, import_settings, file_name=fn)
        elif comp == "import_excel":
            blob = inject_import_excel_blob(blob, import_settings, file_name=fn)
            xml = inject_import_excel_xml(xml, import_settings, file_name=fn)
        else:
            raise ValueError(f"import_settings not supported for {comp}")
    if engine_settings:
        from .scenario_settings import apply_model_settings

        if not component:
            raise ValueError("engine_settings requires component")
        blob, xml = apply_model_settings(blob, xml, component, engine_settings)
    return blob, xml
