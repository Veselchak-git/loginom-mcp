"""Loginom visualizers (ModelViews) registry and virgin XML/BGB builders.

Visualizer types attach to a workflow node's output port via ModelViews Links.
Tabular components (e.g. Sliding Window) expose the five «Табличное представление»
visualizers: chart, quality, cube, statistics, table.

Builders here produce VIRGIN engines only. Configuring Series / Dimensions /
ViewColumns after save is documented in VISUALIZERS.md (MCP resource
loginom://docs/visualizers). There is no configure_visualizer API yet.
"""
from __future__ import annotations

import struct
import uuid
from dataclasses import dataclass
from xml.sax.saxutils import escape

import importlib.util
from pathlib import Path

from .paths import VENDOR

_spec = importlib.util.spec_from_file_location(
    "imp", VENDOR / "bgb_import_node.py"
)
imp = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(imp)

s = imp.s
field_guid = imp.field_guid
field_str = imp.field_str
field_bool = imp.field_bool
empty_list = imp.empty_list
list_of_items = imp.list_of_items
port_item = imp.port_item
build_link_item = imp.build_link_item

PORT_DS_IN = uuid.UUID("9dc72a3f-56bf-3bfc-84ec-f979daf4da6b")  # visualizer input
PORT_SYNC_IN = imp.PORT_SYNC_IN
PORT_SYNC_OUT = imp.PORT_SYNC_OUT
PORT_COMPONENT = imp.PORT_COMPONENT
PORT_DEPENDENT = imp.PORT_DEPENDENT

# Well-known service ComponentOutputPort on workflow nodes (Loginom uses this
# for TBGDuplicatesView ModelViews links — not the DataSource dataset port).
COMPONENT_PORT_GUID = str(PORT_COMPONENT)

def field_enum8(name: str, value: int) -> bytes:
    """BGB enum attribute (type 0x09) as a single-byte ordinal."""
    if not 0 <= value <= 255:
        raise ValueError(f"enum out of range: {value}")
    return s(name) + b"\x09" + bytes([value])


@dataclass(frozen=True)
class VisualizerInfo:
    key: str
    title: str
    vendor: str
    engine: str
    group: str  # tabular | special
    # components that expose this visualizer beyond the default tabular set
    extra_for: tuple[str, ...] = ()
    # dataset = DataSource socket; model = Component socket (regression reports)
    socket_kind: str = "dataset"
    input_guid: str = "9dc72a3f-56bf-3bfc-84ec-f979daf4da6b"
    input_name: str = "DataSource"
    input_title: str = "Набор данных"


# Package VendorGuids = first GUID of each Invoker pair (iface GUID is +72 bytes).
VISUALIZERS: dict[str, VisualizerInfo] = {
    "table": VisualizerInfo(
        "table", "Таблица", "e6ed8484-b292-4534-a136-fd82df5cc01c", "TBGBrowseView", "tabular"
    ),
    "chart": VisualizerInfo(
        "chart", "Диаграмма", "423d2c8c-4334-43f2-aad5-2f01e8bf0f87", "TBGChartView", "tabular"
    ),
    "cube": VisualizerInfo(
        "cube", "Куб", "85236173-223c-4772-833f-7841c84a7ddf", "TBGCubeView", "tabular"
    ),
    "statistics": VisualizerInfo(
        "statistics",
        "Статистика",
        "121165f9-07d1-4507-9ff4-d64f6333b4ca",
        "TBGStatView",
        "tabular",
    ),
    "quality": VisualizerInfo(
        "quality",
        "Качество данных",
        "85cb32b2-4a6d-4dca-9b7f-9548585095c1",
        "TBGQualityView",
        "tabular",
    ),
    "duplicates_view": VisualizerInfo(
        "duplicates_view",
        "Дубликаты и противоречия",
        "c9865e25-9c19-452a-9f80-583df20308f7",
        "TBGDuplicatesView",
        "special",
        extra_for=("duplicates",),
    ),
    "cluster_profiles": VisualizerInfo(
        "cluster_profiles",
        "Профили кластеров",
        "a62082df-ef2c-49d1-a716-de861006deaf",
        "TBGClusterProfilesView",
        "special",
        extra_for=("cluster", "em_cluster", "sonn", "clope"),
    ),
    "roc": VisualizerInfo(
        "roc",
        "ROC-анализ",
        "3092a5ee-820e-4a4c-b266-daddfafd2848",
        "TBGROCView",
        "special",
        extra_for=(
            "log_regression",
            "nn_classify",
            "lin_regression",
            "nn_regress",
        ),
    ),
    "coarse_classes": VisualizerInfo(
        "coarse_classes",
        "Конечные классы",
        "d7361376-312d-484d-b2c4-11b371685f67",
        "TBGCoarseClassesView",
        "special",
        extra_for=("final_classes",),
    ),
    "lin_regress_report": VisualizerInfo(
        "lin_regress_report",
        "Отчет по регрессии",
        "3f113f5e-420c-431f-ad16-43ee015f2af9",
        "TBGLinRegressReport",
        "special",
        extra_for=("lin_regression",),
        socket_kind="model",
        input_guid="ff1a6c68-78bc-3733-8212-65348b401a95",
        input_name="Component",
        input_title="Компонент",
    ),
    "log_regress_report": VisualizerInfo(
        "log_regress_report",
        "Отчет по регрессии",
        "fc5bc69a-713e-4267-be4a-fc50954a857c",
        "TBGLogRegressReport",
        "special",
        extra_for=("log_regression",),
        socket_kind="model",
        input_guid="ff1a6c68-78bc-3733-8212-65348b401a95",
        input_name="Component",
        input_title="Компонент",
    ),
    "data_tree": VisualizerInfo(
        "data_tree",
        "Дерево",
        "3cf2c74a-9b3d-49bc-9894-eec8a37a7ae5",
        "TBGDataTreeView",
        "special",
        extra_for=(
            "table_to_tree",
            "json_to_tree",
            "calc_tree",
            "union_tree",
            "join_tree",
            "tree_to_table",
            "tree_to_json",
        ),
    ),
}

# Components whose primary output is a dataset → get the full tabular visualizer set.
_TABULAR_COMPONENTS = {
    "import_native",
    "import_text",
    "import_excel",
    "import_xml",
    "import_db",
    "import_1c",
    "import_warehouse",
    "sorting",
    "reform_columns",
    "calculator",
    "datetime",
    "grouping",
    "replace",
    "filter",
    "union",
    "join",
    "enrich",
    "colunion",
    "collapse_columns",
    "crosstab",
    "sampling",
    "ungroup",
    "sliding_window",
    "imputation",
    "quantize",
    "final_classes",
    "partition",
    "outliers",
    "smoothing",
    "vars_to_table",
    "autocorr",
    "duplicates",
    "corr_analysis",
    "factor_analysis",
    "assoc_rules",
    "cluster",
    "clope",
    "lin_regression",
    "log_regression",
    "nn_classify",
    "nn_regress",
    "sonn",
    "arimax",
    "em_cluster",
    "tree_to_table",
    "sql_script",
    "rest_client",
}


def list_visualizers(component: str | None = None) -> list[dict]:
    """List visualizer types; if component given, only those available for it."""
    if component is None:
        items = list(VISUALIZERS.values())
    else:
        items = []
        if component in _TABULAR_COMPONENTS:
            items.extend(v for v in VISUALIZERS.values() if v.group == "tabular")
        for v in VISUALIZERS.values():
            if component in v.extra_for and v not in items:
                items.append(v)
    return [
        {
            "key": v.key,
            "title": v.title,
            "engine": v.engine,
            "vendor": v.vendor,
            "group": v.group,
            "preferred_port": preferred_source_port(v.key),
        }
        for v in items
    ]


def preferred_source_port(visualizer: str) -> str:
    """Logical port name on the workflow node to attach this visualizer to.

    ``duplicates_view`` must link to the node's Component service port
    (``e98be5ba-…``), not DataSource — matching Loginom 7.4 ModelViews.
    """
    info = VISUALIZERS[visualizer]
    if visualizer == "duplicates_view" or info.socket_kind == "model":
        return "component"
    return "data"


def _engine_xml(info: VisualizerInfo) -> str:
    if info.key == "table":
        return (
            '<Engine xsi:type="TBGBrowseView">'
            "<ViewColumns/><Filtering/><Grouping/><Sorting/><Options/>"
            "</Engine>"
        )
    if info.key == "chart":
        # Loginom 7.x axis keys are apAbscissa/apLeftOrdinate/apRightOrdinate
        # (Russian «Нижняя»/«Левая» names are legacy 6.x display labels).
        return (
            '<Engine xsi:type="TBGChartView">'
            '<Parameters Rationing="false">'
            "<BackgroundColor/>"
            "<Links>"
            '<Item Name="lkXData" LinkKind="lkXData"/>'
            '<Item Name="lkLabels" LinkKind="lkLabels"/>'
            "</Links>"
            "<Series/>"
            "<Axes>"
            '<Item Name="apAbscissa"/>'
            '<Item Name="apLeftOrdinate" Position="apLeftOrdinate"/>'
            '<Item Name="apRightOrdinate" Position="apRightOrdinate"/>'
            "</Axes>"
            "</Parameters>"
            "</Engine>"
        )
    if info.key == "cube":
        # Loginom 7.3+ replaced singular Chart with Charts list.
        return (
            '<Engine xsi:type="TBGCubeView">'
            "<Dimensions><Dimensions/></Dimensions>"
            "<Summaries><Cases/></Summaries>"
            "<Charts/>"
            "</Engine>"
        )
    if info.key == "statistics":
        return (
            '<Engine xsi:type="TBGStatView">'
            "<StatViewColumns/>"
            "<StatIndicatorColumnConfig/>"
            "<ColumnInfosConfig/>"
            "<StatIndicatorsConfig/>"
            "<HistogramColumnsConfig/>"
            "</Engine>"
        )
    if info.key == "quality":
        # Loginom 7.x TBGQualityView required children (RTTI order).
        return (
            '<Engine xsi:type="TBGQualityView">'
            "<CommonConfigs/>"
            "<ColumnsStats/>"
            "<CalculationSettings/>"
            "<PreviewDetailing/>"
            "<CommonColumnConfigs/>"
            "<IndicatorColumnConfigs/>"
            "<OverviewColumnConfigs/>"
            "<HistogramManager/>"
            "</Engine>"
        )
    if info.key == "duplicates_view":
        # Same browse-grid children as TBGBrowseView (Filtering required by RTTI).
        return (
            '<Engine xsi:type="TBGDuplicatesView">'
            "<ViewColumns/><Filtering/><Grouping/><Sorting/><Options/>"
            "</Engine>"
        )
    if info.key == "cluster_profiles":
        return '<Engine xsi:type="TBGClusterProfilesView"></Engine>'
    if info.key == "roc":
        return '<Engine xsi:type="TBGROCView"></Engine>'
    if info.key in ("lin_regress_report", "log_regress_report"):
        from .scenario_settings import regress_report_engine_xml

        return regress_report_engine_xml(info.engine)
    if info.key == "coarse_classes":
        return '<Engine xsi:type="TBGCoarseClassesView"/>'
    if info.key == "data_tree":
        return '<Engine xsi:type="TBGDataTreeView"/>'
    raise KeyError(info.key)


def visualizer_xml(
    visualizer: str,
    view_guid: uuid.UUID,
    display_name: str | None = None,
) -> str:
    info = VISUALIZERS[visualizer]
    dn = escape(display_name or info.title)
    eng = _engine_xml(info)
    if info.socket_kind == "model":
        socket_xml = (
            '<Socket xsi:type="TBGModelInputSocket">'
            "<Constraints/>"
            "</Socket>"
        )
    else:
        socket_xml = (
            '<Socket xsi:type="TBGTuneDataSourceSocket">'
            "<Constraints/>"
            '<DataSource SyncThroughColumns="true"><ColumnDefs/></DataSource>'
            "</Socket>"
        )
    return f"""\t\t\t<Item Guid="{view_guid}" DisplayName="{dn}" VendorGuid="{info.vendor}">
\t\t\t\t<InputPorts>
\t\t\t\t\t<Item Guid="{info.input_guid}" Name="{info.input_name}" DisplayName="{escape(info.input_title)}"/>
\t\t\t\t</InputPorts>
\t\t\t\t<OutputPorts/>
\t\t\t\t<ServiceInputPorts>
\t\t\t\t\t<Item Guid="{PORT_SYNC_IN}" Name="SynchronizationInputPort" DisplayName="Порядок выполнения"/>
\t\t\t\t</ServiceInputPorts>
\t\t\t\t<ServiceOutputPorts>
\t\t\t\t\t<Item Guid="{PORT_SYNC_OUT}" Name="SynchronizationOutputPort" DisplayName="Порядок выполнения"/>
\t\t\t\t\t<Item Guid="{PORT_COMPONENT}" Name="ComponentOutputPort" DisplayName="Компонент"/>
\t\t\t\t\t<Item Guid="{PORT_DEPENDENT}" Name="DependentNodeOutputPort" DisplayName="Зависимые узлы"/>
\t\t\t\t</ServiceOutputPorts>
\t\t\t\t<Component>
\t\t\t\t\t<InputSockets>
\t\t\t\t\t\t<Item Guid="{info.input_guid}" Name="{info.input_name}" DisplayName="{escape(info.input_title)}">
\t\t\t\t\t\t\t{socket_xml}
\t\t\t\t\t\t</Item>
\t\t\t\t\t</InputSockets>
\t\t\t\t\t{eng}
\t\t\t\t</Component>
\t\t\t</Item>"""


def _empty_obj(name: str) -> bytes:
    """Named empty object child: name + object with 0 attrs + 0 children."""
    return s(name) + b"\x00\x00" + b"\x00"


def _attr_item(attrs: bytes, attr_count: int, children: bytes = b"", child_count: int = 0) -> bytes:
    """Anonymous list Item body: 00 attrCount attrs childCount [children]."""
    return b"\x00" + bytes([attr_count]) + attrs + bytes([child_count]) + children


def _chart_parameters_blob() -> bytes:
    """Virgin chart Parameters for Loginom 7.x (ap* axis keys, named link kinds)."""
    # LinkKind ordinals: 1=lkXData, 6=lkLabels
    links = list_of_items(
        "Links",
        [
            _attr_item(
                field_str("Name", "lkXData") + field_enum8("LinkKind", 1), 2
            ),
            _attr_item(
                field_str("Name", "lkLabels") + field_enum8("LinkKind", 6), 2
            ),
        ],
    )
    series = empty_list("Series")
    # Position ordinals: 1=apLeftOrdinate, 2=apRightOrdinate
    axes = list_of_items(
        "Axes",
        [
            _attr_item(field_str("Name", "apAbscissa"), 1),
            _attr_item(
                field_str("Name", "apLeftOrdinate") + field_enum8("Position", 1), 2
            ),
            _attr_item(
                field_str("Name", "apRightOrdinate") + field_enum8("Position", 2), 2
            ),
        ],
    )
    return (
        s("Parameters")
        + b"\x00\x01"
        + field_bool("Rationing", False)
        + b"\x04"
        + _empty_obj("BackgroundColor")
        + links
        + series
        + axes
    )


def _engine_blob(info: VisualizerInfo) -> bytes:
    """Typed Engine child. Format: name + classname + attrCount + attrs + childCount + children."""
    eng = s("Engine") + s(info.engine)
    if info.key == "table":
        return (
            eng
            + b"\x00"  # 0 attrs
            + b"\x05"
            + empty_list("ViewColumns")
            + empty_list("Filtering")
            + empty_list("Grouping")
            + empty_list("Sorting")
            + _empty_obj("Options")
        )
    if info.key == "chart":
        return eng + b"\x00" + b"\x01" + _chart_parameters_blob()
    if info.key == "cube":
        dims = s("Dimensions") + b"\x00\x00" + b"\x01" + empty_list("Dimensions")
        summaries = s("Summaries") + b"\x00\x00" + b"\x01" + empty_list("Cases")
        return eng + b"\x00" + b"\x03" + dims + summaries + empty_list("Charts")
    if info.key == "statistics":
        return (
            eng
            + b"\x00"
            + b"\x05"
            + empty_list("StatViewColumns")
            + _empty_obj("StatIndicatorColumnConfig")
            + empty_list("ColumnInfosConfig")
            + empty_list("StatIndicatorsConfig")
            + empty_list("HistogramColumnsConfig")
        )
    if info.key == "quality":
        return (
            eng
            + b"\x00"
            + b"\x08"
            + _empty_obj("CommonConfigs")
            + empty_list("ColumnsStats")
            + _empty_obj("CalculationSettings")
            + _empty_obj("PreviewDetailing")
            + empty_list("CommonColumnConfigs")
            + empty_list("IndicatorColumnConfigs")
            + empty_list("OverviewColumnConfigs")
            + _empty_obj("HistogramManager")
        )
    if info.key == "duplicates_view":
        return (
            eng
            + b"\x00"
            + b"\x05"
            + empty_list("ViewColumns")
            + empty_list("Filtering")
            + empty_list("Grouping")
            + empty_list("Sorting")
            + _empty_obj("Options")
        )
    if info.key in ("lin_regress_report", "log_regress_report"):
        from .scenario_settings import regress_report_engine_blob

        return regress_report_engine_blob(info.engine)
    # other specials: empty typed engine
    return eng + b"\x00" + b"\x00"


def build_visualizer_node(
    visualizer: str,
    view_guid: uuid.UUID,
    display_name: str | None = None,
) -> bytes:
    """BGB Item body (without Item tag) for a virgin ModelViews node."""
    info = VISUALIZERS[visualizer]
    dn = display_name or info.title
    vendor = uuid.UUID(info.vendor)

    in_guid = uuid.UUID(info.input_guid)
    input_ports = list_of_items(
        "InputPorts",
        [port_item(in_guid, info.input_name, info.input_title)],
    )
    output_ports = empty_list("OutputPorts")
    service_in = list_of_items(
        "ServiceInputPorts",
        [port_item(PORT_SYNC_IN, "SynchronizationInputPort", "Порядок выполнения")],
    )
    service_out = list_of_items(
        "ServiceOutputPorts",
        [
            port_item(PORT_SYNC_OUT, "SynchronizationOutputPort", "Порядок выполнения"),
            port_item(PORT_COMPONENT, "ComponentOutputPort", "Компонент"),
            port_item(PORT_DEPENDENT, "DependentNodeOutputPort", "Зависимые узлы"),
        ],
    )

    if info.socket_kind == "model":
        ds_socket = (
            s("Socket")
            + s("TBGModelInputSocket")
            + b"\x00"
            + b"\x01"
            + empty_list("Constraints")
        )
    else:
        ds_inner = (
            s("DataSource")
            + b"\x00\x01"
            + field_bool("SyncThroughColumns", True)
            + b"\x01"
            + empty_list("ColumnDefs")
        )
        # Visualizer sockets are not Virgin (unlike workflow processors).
        ds_socket = (
            s("Socket")
            + s("TBGTuneDataSourceSocket")
            + b"\x00"  # 0 attrs
            + b"\x02"
            + empty_list("Constraints")
            + ds_inner
        )
    ds_item = (
        b"\x00\x03"
        + field_guid("Guid", in_guid)
        + field_str("Name", info.input_name)
        + field_str("DisplayName", info.input_title)
        + b"\x01"
        + ds_socket
    )
    input_sockets = s("InputSockets") + b"\x00\x00\x01" + s("Item") + ds_item

    component = (
        s("Component")
        + b"\x00\x00"
        + b"\x02"
        + input_sockets
        + _engine_blob(info)
    )

    # Loginom 7.x ModelViews nodes have no Layout/Position child (only 5 children).
    return (
        b"\x00\x03"
        + field_guid("Guid", view_guid)
        + field_str("DisplayName", dn)
        + field_guid("VendorGuid", vendor)
        + b"\x05"
        + input_ports
        + output_ports
        + service_in
        + service_out
        + component
    )


def model_views_xml(view_nodes_xml: list[str], view_links: list[dict]) -> str:
    nodes_body = "\n".join(view_nodes_xml) if view_nodes_xml else ""
    if view_links:
        items = []
        for lk in view_links:
            items.append(
                f"""\t\t\t<Item Guid="{lk['guid']}">
\t\t\t\t<SourcePort NodeGuid="{lk['source_node']}" PortGuid="{lk['source_port']}"/>
\t\t\t\t<TargetPort NodeGuid="{lk['target_node']}" PortGuid="{lk['target_port']}"/>
\t\t\t</Item>"""
            )
        links_xml = "\t\t<Links>\n" + "\n".join(items) + "\n\t\t</Links>"
    else:
        links_xml = "\t\t<Links/>"
    if view_nodes_xml:
        nodes_xml = f"\t\t<Nodes>\n{nodes_body}\n\t\t</Nodes>"
    else:
        nodes_xml = "\t\t<Nodes/>"
    return f"\t<ModelViews>\n{nodes_xml}\n{links_xml}\n\t</ModelViews>\n"
