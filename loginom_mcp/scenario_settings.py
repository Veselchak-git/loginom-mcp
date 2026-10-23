"""Settings taken from course scenarios (elbow, clustering, regression, ROC).

Encodings are the ones Loginom 7 writes *before* training. Trained centers,
coefficients and coarse-class boundaries are not reproduced: Loginom fills
those when the node runs.
"""
from __future__ import annotations

import re
import struct
import sys
import uuid
from typing import Any
from xml.sax.saxutils import escape, quoteattr

from .paths import VENDOR

if str(VENDOR) not in sys.path:
    sys.path.insert(0, str(VENDOR))

from bgb_import_node import (  # type: ignore  # noqa: E402
    empty_list,
    field_bool,
    field_float64,
    field_guid,
    field_int32,
    field_str,
    list_of_items,
    s,
)

# DataType enum8, same ordinals as Loginom column defs.
DT8 = {
    "dtBoolean": 1,
    "dtDateTime": 2,
    "dtFloat": 3,
    "dtInteger": 4,
    "dtString": 5,
    "boolean": 1,
    "datetime": 2,
    "float": 3,
    "integer": 4,
    "string": 5,
}

# Verified against lokotDZ / kursovaya Unit.bin.
HISTOGRAM_SCALE = {"hsSizeScale": 0}
# Ordinals read from lokotDZ (cpitMin) and klaster.lgp (cpitClusterCenter).
INDICATOR = {"cpitMin": 2, "cpitClusterCenter": 11}
LIN_METHOD = {"linregEnter": 0, "enter": 0}
HIDDEN_LAYERS = {"nhlNoHiddenLayers": 0, "none": 0}
SORT_ORDER = {"rsoIndex": 0}
SORT_DIRECTION = {"sdAsc": 0, "sdDesc": 1}
# CorrTypes is a 16-bit set. Only Pearson was present in the scenarios.
CORR_BITS = {"caPirson": 1, "pearson": 1}

ROC_CHARTS = (
    ("rvcROC", (True,)),
    ("rvcPrecisionRecall", (True,)),
    ("rvcOverallRates", (True, True, True, False)),
    ("rvcPrecision", (True, True, False, True)),
    ("rvcBreakEven", (True, True)),
    ("rvcEvent", (True,)),
    ("rvcLift", (True,)),
    ("rvcResponse", (True,)),
    ("rvcGain", (True,)),
    ("rvcEventCum", (True,)),
    ("rvcLiftCum", (True,)),
    ("rvcResponseCum", (True,)),
)

def encode_varint(value: int) -> bytes:
    """Loginom integer type 0x04: 7-bit groups, high bit means more bytes."""
    if value < 0:
        raise ValueError(f"varint must be >= 0, got {value}")
    out = bytearray()
    while True:
        byte = value & 0x7F
        value >>= 7
        if value:
            out.append(byte | 0x80)
        else:
            out.append(byte)
            return bytes(out)


def field_varint(name: str, value: int) -> bytes:
    return s(name) + b"\x04" + encode_varint(value)


def field_enum8(name: str, value: int) -> bytes:
    if not 0 <= int(value) <= 255:
        raise ValueError(f"enum out of range: {value}")
    return s(name) + b"\x09" + bytes([int(value)])


def _named(mapping: dict[str, int], value: str | int, label: str) -> tuple[int, str]:
    if isinstance(value, int):
        for name, ordinal in mapping.items():
            if ordinal == value:
                return value, name
        return value, str(value)
    key = str(value)
    for name, ordinal in mapping.items():
        if name.lower() == key.lower():
            return ordinal, name
    raise ValueError(
        f"unknown {label} {value!r}; verified names: {list(mapping)} or an integer"
    )


def _skip_varint(raw: bytes, i: int) -> int:
    while True:
        byte = raw[i]
        i += 1
        if byte < 128:
            return i


def _replace_rand_seed(blob: bytes, xml: str, seed: int) -> tuple[bytes, str]:
    marker = b"\x06Random\x00\x01\x08RandSeed\x04"
    start = blob.find(marker)
    if start < 0:
        raise ValueError("Random/RandSeed block not found")
    end = _skip_varint(blob, start + len(marker))
    if blob[end] != 0:
        raise ValueError("RandSeed child count is not 0")
    new = marker + encode_varint(int(seed)) + b"\x00"
    blob = blob[:start] + new + blob[end + 1 :]
    xml2, n = re.subn(
        r'(<Random\s+RandSeed=")[^"]*(")',
        rf"\g<1>{int(seed)}\2",
        xml,
        count=1,
    )
    if n != 1:
        raise ValueError("Random RandSeed attribute not found in XML")
    return blob, xml2


def _apply_cluster(blob: bytes, xml: str, settings: dict[str, Any]) -> tuple[bytes, str]:
    if "n_clusters" not in settings:
        raise ValueError("cluster engine_settings requires n_clusters")
    n_clusters = int(settings["n_clusters"])
    if n_clusters < 1:
        raise ValueError("n_clusters must be >= 1")
    auto = bool(settings.get("auto_select", False))
    params = (
        s("Params")
        + b"\x00\x02"
        + field_bool("NClustersAutoSelect", auto)
        + field_int32("NClusters", n_clusters)
        + b"\x00"
    )
    engine_at = blob.find(s("TBGClusterizationEngine"))
    if engine_at < 0:
        raise ValueError("TBGClusterizationEngine not found")
    old_params = s("Params") + b"\x00\x00\x00"
    abs_at = blob.find(old_params, engine_at)
    if abs_at < 0:
        raise ValueError("empty cluster Params not found (already configured?)")
    blob = blob[:abs_at] + params + blob[abs_at + len(old_params) :]
    seed = settings.get("rand_seed")
    if seed is not None:
        blob, xml = _replace_rand_seed(blob, xml, int(seed))
    flag = "true" if auto else "false"
    xml2, n = re.subn(
        r"<Params\s*/>",
        f'<Params NClustersAutoSelect="{flag}" NClusters="{n_clusters}"/>',
        xml,
        count=1,
    )
    if n != 1:
        raise ValueError("empty <Params/> not found in cluster XML")
    return blob, xml2


def _apply_corr(blob: bytes, xml: str, settings: dict[str, Any]) -> tuple[bytes, str]:
    raw = settings.get("corr_types", "caPirson")
    bits, name = _named(CORR_BITS, raw, "corr_types")
    if not 0 <= bits <= 0xFFFF:
        raise ValueError("corr_types bitmask must fit in 16 bits")
    marker = s("CorrTypes") + b"\x0a"
    start = blob.find(marker)
    if start < 0:
        raise ValueError("CorrTypes field not found")
    blob = blob[: start + len(marker)] + struct.pack("<H", bits) + blob[start + len(marker) + 2 :]
    xml2, n = re.subn(
        r'CorrTypes="[^"]*"',
        f'CorrTypes="{escape(name)}"',
        xml,
        count=1,
    )
    if n != 1:
        raise ValueError("CorrTypes attribute not found in XML")
    return blob, xml2


def _apply_lin(blob: bytes, xml: str, settings: dict[str, Any]) -> tuple[bytes, str]:
    if settings.get("rand_seed") is not None:
        blob, xml = _replace_rand_seed(blob, xml, int(settings["rand_seed"]))
    if "method" not in settings:
        return blob, xml
    ordinal, name = _named(LIN_METHOD, settings["method"], "method")
    marker = s("RegressionParams") + b"\x00\x00\x04"
    start = blob.find(marker)
    if start < 0:
        raise ValueError("virgin RegressionParams not found")
    filled = (
        s("RegressionParams")
        + b"\x00\x01"
        + field_enum8("LinRegressionMethod", ordinal)
        + b"\x04"
    )
    blob = blob[:start] + filled + blob[start + len(marker) :]
    xml2, n = re.subn(
        r"<RegressionParams>",
        f'<RegressionParams LinRegressionMethod="{escape(name)}">',
        xml,
        count=1,
    )
    if n != 1:
        raise ValueError("<RegressionParams> not found in XML")
    return blob, xml2


def _apply_nn(blob: bytes, xml: str, settings: dict[str, Any]) -> tuple[bytes, str]:
    if settings.get("rand_seed") is not None:
        blob, xml = _replace_rand_seed(blob, xml, int(settings["rand_seed"]))
    hidden, hidden_name = _named(
        HIDDEN_LAYERS, settings.get("hidden_layers", "nhlNoHiddenLayers"), "hidden_layers"
    )
    decay = float(settings.get("decay", 1.2589254117941661e-6))
    epochs = int(settings.get("max_epochs", 1000))
    flags = {
        "structure_autofit": "StructureAutofit",
        "use_initial_structure": "UseInitialStructure",
        "decay_autofit": "DecayAutofit",
        "use_initial_decay": "UseInitialDecay",
    }
    bools = {xml_name: bool(settings.get(key, True)) for key, xml_name in flags.items()}

    def _swap(old: bytes, new: bytes, label: str) -> None:
        nonlocal blob
        at = blob.find(old)
        if at < 0:
            raise ValueError(f"virgin {label} not found")
        blob = blob[:at] + new + blob[at + len(old) :]

    _swap(
        s("StructureParams") + b"\x00\x00\x00",
        s("StructureParams") + b"\x00\x01" + field_enum8("HiddenLayers", hidden) + b"\x00",
        "StructureParams",
    )
    _swap(
        s("TrainingParams") + b"\x00\x00\x00",
        s("TrainingParams") + b"\x00\x01" + field_float64("Decay", decay) + b"\x00",
        "TrainingParams",
    )
    _swap(
        s("StoppingCriteria") + b"\x00\x00\x00",
        s("StoppingCriteria") + b"\x00\x01" + field_int32("MaxEpochs", epochs) + b"\x00",
        "StoppingCriteria",
    )
    autofit_attrs = b"".join(field_bool(name, value) for name, value in bools.items())
    _swap(
        s("AutofitParams") + s("TBGNeuralNetworkAutofitParams") + b"\x00\x00",
        s("AutofitParams") + s("TBGNeuralNetworkAutofitParams") + b"\x04" + autofit_attrs + b"\x00",
        "AutofitParams",
    )
    flag_xml = " ".join(
        f'{name}="{"true" if value else "false"}"' for name, value in bools.items()
    )
    xml2 = xml
    xml2, n = re.subn(
        r"<StructureParams\s*/>",
        f'<StructureParams HiddenLayers="{escape(hidden_name)}"/>',
        xml2,
        count=1,
    )
    xml2, n2 = re.subn(
        r"<TrainingParams\s*/>",
        f'<TrainingParams Decay="{decay}"/>',
        xml2,
        count=1,
    )
    xml2, n3 = re.subn(
        r"<StoppingCriteria\s*/>",
        f'<StoppingCriteria MaxEpochs="{epochs}"/>',
        xml2,
        count=1,
    )
    xml2, n4 = re.subn(
        r'<AutofitParams xsi:type="TBGNeuralNetworkAutofitParams"\s*/>',
        f'<AutofitParams xsi:type="TBGNeuralNetworkAutofitParams" {flag_xml}/>',
        xml2,
        count=1,
    )
    if (n, n2, n3, n4) != (1, 1, 1, 1):
        raise ValueError("neural-net XML placeholders not found")
    return blob, xml2


def apply_model_settings(
    blob: bytes,
    xml: str,
    component: str,
    settings: dict[str, Any],
) -> tuple[bytes, str]:
    """Patch a virgin data-mining node. ``settings`` keys depend on ``component``."""
    if component == "cluster":
        return _apply_cluster(blob, xml, settings)
    if component == "corr_analysis":
        return _apply_corr(blob, xml, settings)
    if component == "lin_regression":
        return _apply_lin(blob, xml, settings)
    if component in ("nn_regress", "nn_classify"):
        return _apply_nn(blob, xml, settings)
    if component in ("log_regression",) and settings.get("rand_seed") is not None:
        return _replace_rand_seed(blob, xml, int(settings["rand_seed"]))
    raise ValueError(
        "engine_settings is implemented for cluster, corr_analysis, "
        "lin_regression, log_regression (rand_seed), nn_regress, nn_classify"
    )


def _var_expr_item(expr: dict[str, Any]) -> bytes:
    name = expr["name"]
    display = expr.get("display_name") or expr.get("displayName") or name
    data_type = expr.get("data_type") or expr.get("DataType") or "dtFloat"
    if isinstance(data_type, int):
        ordinal = data_type
    else:
        if data_type not in DT8:
            raise ValueError(f"unknown data_type {data_type!r}")
        ordinal = DT8[data_type]
    description = expr.get("description") or ""
    expression = expr["expression"] if "expression" in expr else expr["Expression"]
    attrs = (
        field_str("Name", name)
        + field_str("DisplayName", display)
        + field_enum8("DataType", ordinal)
        + field_str("Description", description)
        + field_str("Expression", expression)
    )
    return b"\x00\x05" + attrs + b"\x00"


def variable_expressions_blob(expressions: list[dict[str, Any]]) -> bytes:
    return list_of_items("Expressions", [_var_expr_item(e) for e in expressions])


def variable_expressions_xml(expressions: list[dict[str, Any]]) -> str:
    parts = ["<Expressions>"]
    for expr in expressions:
        name = expr["name"]
        display = expr.get("display_name") or expr.get("displayName") or name
        data_type = expr.get("data_type") or expr.get("DataType") or "dtFloat"
        if isinstance(data_type, int):
            data_type = {v: k for k, v in DT8.items() if k.startswith("dt")}.get(
                data_type, "dtFloat"
            )
        description = expr.get("description") or ""
        expression = expr["expression"] if "expression" in expr else expr["Expression"]
        parts.append(
            "<Item "
            f'Name="{escape(name)}" DisplayName={quoteattr(display)} '
            f'DataType="{escape(str(data_type))}" Description={quoteattr(description)} '
            f'Expression={quoteattr(expression)}/>'
        )
    parts.append("</Expressions>")
    return "".join(parts)


def inject_variable_expressions(blob: bytes, xml: str, expressions: list[dict[str, Any]]) -> tuple[bytes, str]:
    filled = variable_expressions_blob(expressions)
    virgin = empty_list("Expressions")
    if virgin not in blob:
        raise ValueError("virgin Expressions list not found")
    blob = blob.replace(virgin, filled, 1)
    xml_filled = variable_expressions_xml(expressions)
    xml2, n = re.subn(r"<Expressions\s*/>", lambda _m: xml_filled, xml, count=1)
    if n != 1:
        xml2, n = re.subn(r"<Expressions></Expressions>", lambda _m: xml_filled, xml, count=1)
    if n != 1:
        raise ValueError("empty Expressions element not found")
    return blob, xml2


def _empty_obj(name: str) -> bytes:
    return s(name) + b"\x00\x00\x00"


def _serie(visible: bool) -> bytes:
    return s("SerieVisible") + b"\x00\x01\x00\x01" + bytes([1 if visible else 0]) + b"\x00"


def _roc_chart(tag: str, ordinal: int, series: tuple[bool, ...]) -> bytes:
    return (
        s(tag)
        + b"\x00\x01"
        + field_enum8("ROCChartType", ordinal)
        + bytes([len(series)])
        + b"".join(_serie(flag) for flag in series)
    )


def roc_engine_blob(charts: list[tuple[str, tuple[bool, ...]]] | None = None) -> bytes:
    spec = list(charts) if charts is not None else [(name, flags) for name, flags in ROC_CHARTS]
    body = _empty_obj("DataSets")
    for ordinal, (name, flags) in enumerate(spec):
        body += _roc_chart("TrainChart", ordinal, tuple(flags))
    for ordinal, (name, flags) in enumerate(spec):
        body += _roc_chart("TestChart", ordinal, tuple(flags))
    body += _empty_obj("VisualOptions")
    count = 2 + 2 * len(spec)
    if count > 255:
        raise ValueError("too many ROC charts")
    return s("Engine") + s("TBGROCView") + b"\x00" + bytes([count]) + body


def roc_engine_xml(charts: list[tuple[str, tuple[bool, ...]]] | None = None) -> str:
    spec = list(charts) if charts is not None else [(name, flags) for name, flags in ROC_CHARTS]
    parts = ['<Engine xsi:type="TBGROCView">', "<DataSets/>"]
    for tag in ("TrainChart", "TestChart"):
        for name, flags in spec:
            series = "".join(
                f"<SerieVisible>{'true' if flag else 'false'}</SerieVisible>" for flag in flags
            )
            parts.append(f'<{tag} ROCChartType="{escape(name)}">{series}</{tag}>')
    parts.append("<VisualOptions/>")
    parts.append("</Engine>")
    return "".join(parts)


def _cluster_profile_fields(settings: dict[str, Any] | None) -> list[tuple[str, bytes]]:
    """Attribute order matches the saved cluster-profile views."""
    settings = dict(settings or {})
    fields: list[tuple[str, bytes]] = []
    if "indicator" in settings:
        ordinal, name = _named(INDICATOR, settings["indicator"], "indicator")
        fields.append((f'Indicator="{escape(name)}"', field_enum8("Indicator", ordinal)))
    raw = settings.get("histogram_scaling", "hsSizeScale")
    ordinal, name = _named(HISTOGRAM_SCALE, raw, "histogram_scaling")
    fields.append(
        (f'HistogramScaling="{escape(name)}"', field_enum8("HistogramScaling", ordinal))
    )
    bools = (
        ("importance_heat_map", "ImportanceHeatMap"),
        ("filter_cluster", "FilterClusterEnabled"),
        ("filter_column", "FilterColumnEnabled"),
        ("filter_cell", "FilterCellEnabled"),
        ("show_total_histogram", "ShowTotalHistogram"),
        ("show_comparison", "ShowComparison"),
    )
    for key, xml_name in bools:
        if key not in settings:
            continue
        flag = bool(settings[key])
        fields.append(
            (
                f'{xml_name}="{"true" if flag else "false"}"',
                field_bool(xml_name, flag),
            )
        )
    return fields


def cluster_profiles_engine_blob(settings: dict[str, Any] | None) -> bytes:
    fields = _cluster_profile_fields(settings)
    attrs = b"".join(blob for _, blob in fields)
    return s("Engine") + s("TBGClusterProfilesView") + bytes([len(fields)]) + attrs + b"\x00"


def cluster_profiles_engine_xml(settings: dict[str, Any] | None) -> str:
    bits = " ".join(xml for xml, _ in _cluster_profile_fields(settings))
    return f'<Engine xsi:type="TBGClusterProfilesView" {bits}></Engine>'


def regress_report_engine_blob(engine: str, sort_order: str | int = "rsoIndex", direction: str | int = "sdAsc") -> bytes:
    order, _ = _named(SORT_ORDER, sort_order, "sort_order")
    direct, _ = _named(SORT_DIRECTION, direction, "sort_direction")
    return (
        s("Engine")
        + s(engine)
        + b"\x02"
        + field_enum8("SortOrder", order)
        + field_enum8("SortDirection", direct)
        + b"\x00"
    )


LOOP_KIND = {"lkRepeat": 1, "repeat": 1}


def nest_workflow(
    blob: bytes,
    xml: str,
    nodes: list[bytes],
    node_xmls: list[str],
    links: list[bytes],
    link_xmls: list[str],
) -> tuple[bytes, str]:
    """Insert nodes and links into a virgin submodel WorkFlow.

    The submodel template stores an empty Nodes list and an empty Links list.
    That pair is the same encoding as the root workflow (``list_of_items``).
    """
    old = empty_list("Nodes") + empty_list("Links")
    new = list_of_items("Nodes", nodes) + (
        list_of_items("Links", links) if links else empty_list("Links")
    )
    at = blob.find(old)
    if at < 0:
        raise ValueError("submodel has no empty WorkFlow Nodes/Links list")
    blob = blob[:at] + new + blob[at + len(old) :]
    xml2, n = re.subn(
        r"<Nodes\s*/>",
        lambda _m: "<Nodes>\n" + "\n".join(node_xmls) + "\n</Nodes>",
        xml,
        count=1,
    )
    if n != 1:
        raise ValueError("submodel XML has no empty <Nodes />")
    xml = xml2
    if link_xmls:
        xml, n = re.subn(
            r"<Links\s*/>",
            lambda _m: "<Links>\n" + "\n".join(link_xmls) + "\n</Links>",
            xml,
            count=1,
        )
        if n != 1:
            raise ValueError("submodel XML has no empty <Links />")
    return blob, xml


def _side_blob(tag: str, name: str, socket: str) -> bytes:
    return (
        s(tag)
        + b"\x00\x02"
        + field_str("Name", name)
        + field_guid("SocketGuid", uuid.UUID(socket))
        + b"\x00"
    )


def _mapping_body(item: dict[str, Any]) -> bytes:
    guid = item.get("guid") or str(uuid.uuid4())
    left = _side_blob("Left", item["left"], item["left_socket"])
    right = _side_blob("Right", item["right"], item["right_socket"])
    return b"\x00\x01" + field_guid("Guid", uuid.UUID(str(guid))) + b"\x02" + left + right


def apply_loop_settings(
    blob: bytes,
    xml: str,
    settings: dict[str, Any],
    reference_guid: str,
) -> tuple[bytes, str]:
    """Point a cycle at a submodel and store the repeat condition.

    ``InternalComponent`` is the derived copy Loginom keeps of that submodel.
    The scenarios store a full copy; a new package gets an empty derived shell
    with the same class name. Loginom rebuilds the copy when the package opens.
    """
    if "reference" not in settings and reference_guid is None:
        raise ValueError("loop engine_settings requires reference")
    kind, kind_name = _named(LOOP_KIND, settings.get("loop_kind", "lkRepeat"), "loop_kind")
    append = bool(settings.get("append_iteration_identifiers", True))
    condition = settings.get("condition") or {}
    if "name" not in condition or "socket" not in condition:
        raise ValueError("loop condition requires name and socket")
    value = int(condition.get("value", 0))
    mappings = list(settings.get("mappings") or [])

    internal = s("InternalComponent") + s("IBGModelComponent.DerivedSchemeType") + b"\x00\x00"
    cond = (
        s("ConditionVariable")
        + b"\x00\x02"
        + field_str("Name", condition["name"])
        + field_guid("SocketGuid", uuid.UUID(str(condition["socket"])))
        + b"\x00"
    )
    compare = (
        s("CompareValue")
        + b"\x00\x02"
        + field_enum8("VarType", 13)
        + b"\x00\x00"
        + struct.pack("<H", 20)
        + struct.pack("<q", value)
        + b"\x00"
    )
    mapped = list_of_items("MappedVariables", [_mapping_body(item) for item in mappings])
    component = (
        s("Component")
        + s("TBGLoopComponent")
        + b"\x03"
        + field_guid("ReferencedVendorGuid", uuid.UUID(str(reference_guid)))
        + field_enum8("LoopKind", kind)
        + field_bool("AppendIterationIdentifiers", append)
        + b"\x04"
        + internal
        + cond
        + compare
        + mapped
    )
    old = s("Component") + s("TBGLoopComponent") + b"\x00\x00"
    at = blob.find(old)
    if at < 0:
        raise ValueError("virgin TBGLoopComponent not found")
    blob = blob[:at] + component + blob[at + len(old) :]

    map_xml = []
    for item in mappings:
        guid = item.get("guid") or str(uuid.uuid4())
        map_xml.append(
            f'<Item Guid="{guid}">'
            f'<Left Name="{escape(item["left"])}" SocketGuid="{item["left_socket"]}"/>'
            f'<Right Name="{escape(item["right"])}" SocketGuid="{item["right_socket"]}"/>'
            "</Item>"
        )
    maps = "<MappedVariables>" + "".join(map_xml) + "</MappedVariables>"
    filled = (
        f'<Component xsi:type="TBGLoopComponent" ReferencedVendorGuid="{reference_guid}" '
        f'LoopKind="{escape(kind_name)}" '
        f'AppendIterationIdentifiers="{"true" if append else "false"}">'
        '<InternalComponent xsi:type="IBGModelComponent.DerivedSchemeType"/>'
        f'<ConditionVariable Name="{escape(condition["name"])}" SocketGuid="{condition["socket"]}"/>'
        f'<CompareValue VarType="vrtInt64">{value}</CompareValue>'
        f"{maps}"
        "</Component>"
    )
    xml2, n = re.subn(
        r'<Component xsi:type="TBGLoopComponent"\s*/>',
        lambda _m: filled,
        xml,
        count=1,
    )
    if n != 1:
        raise ValueError("virgin loop Component element not found")
    return blob, xml2


def regress_report_engine_xml(engine: str, sort_order: str | int = "rsoIndex", direction: str | int = "sdAsc") -> str:
    _, order_name = _named(SORT_ORDER, sort_order, "sort_order")
    _, direct_name = _named(SORT_DIRECTION, direction, "sort_direction")
    if isinstance(sort_order, int) and sort_order != 0:
        order_name = str(sort_order)
    if isinstance(direction, int) and direction not in (0, 1):
        direct_name = str(direction)
    return (
        f'<Engine xsi:type="{engine}" SortOrder="{escape(order_name)}" '
        f'SortDirection="{escape(direct_name)}"></Engine>'
    )
