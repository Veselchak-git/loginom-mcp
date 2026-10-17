"""Additional palette nodes: ungroup, preprocess, import XML (G1–G5)."""
from __future__ import annotations

import importlib.util
import uuid
from pathlib import Path

_VENDOR = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location(
    "imp", _VENDOR / "bgb_import_node.py"
)
imp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(imp)

_spec2 = importlib.util.spec_from_file_location(
    "tr", _VENDOR / "bgb_transform_nodes.py"
)
tr = importlib.util.module_from_spec(_spec2)
_spec2.loader.exec_module(tr)

s = imp.s
field_guid = imp.field_guid
field_str = imp.field_str
field_bool = imp.field_bool
field_float64 = imp.field_float64
empty_list = imp.empty_list
list_of_items = imp.list_of_items
port_item = imp.port_item
field_enum16 = tr.field_enum16

PORT_DS_IN = tr.PORT_DS_IN
PORT_DS_OUT = tr.PORT_DS_OUT
PORT_CONTROL_VARS = imp.PORT_CONTROL_VARS
PORT_SYNC_IN = imp.PORT_SYNC_IN
PORT_SYNC_OUT = imp.PORT_SYNC_OUT
PORT_COMPONENT = imp.PORT_COMPONENT
PORT_DEPENDENT = imp.PORT_DEPENDENT
PORT_CONNECTION = imp.PORT_CONNECTION
PORT_DATASET = imp.PORT_DATASET

PORT_SUPPORT = uuid.UUID("7957ead3-e5a4-3fdc-a6f6-257da214aec9")
PORT_UNGROUP_OUT = uuid.UUID("b1b9a7d7-acab-3f13-a8cc-e93ad801d966")
PORT_UNGROUP_STATS = uuid.UUID("c1517ce9-666e-3c4d-b6dc-de107adf927a")
PORT_RANGES_IN = uuid.UUID("8ae3195f-164d-3b58-8868-6b02979f28d1")
PORT_RANGES_OUT = uuid.UUID("26d376d8-9a60-3baa-b210-be00b095e5aa")
PORT_OUT_DATA = uuid.UUID("87ef0491-b8e1-3fe2-aad7-3d3f6ca39174")
PORT_OUT_OUTLIERS = uuid.UUID("d4871709-2ee7-3c6a-bd72-d65885a82746")
PORT_OUT_EXTR = uuid.UUID("b635a828-1df5-35c7-a5bd-e27f652fcc4a")
PORT_PART_COMMON = uuid.UUID("289668ce-a35b-36f7-a4c7-7e9819fb3fc8")
PORT_PART_TEACH = uuid.UUID("51c20538-def7-374c-851c-a318298b9c80")
PORT_PART_TEST = uuid.UUID("0b3d620f-18d5-38da-8d37-7159844f74d8")
PORT_XSD = uuid.UUID("fd34ec8d-296a-3c2c-8eb3-efab884ae3cd")
PORT_CLASS_PARAMS = uuid.UUID("114f9a7f-dfa1-3fdd-ac79-86d7e23d8310")
PORT_BINNING_PARAMS = uuid.UUID("6ae2fc3e-b405-386e-9c97-7f04bc23d3ee")

VENDOR_UNGROUP = uuid.UUID("e7a4849d-3f92-4636-8efc-cae078129e65")
VENDOR_IMPUTATION = uuid.UUID("77ecdc2c-735e-4f23-a95e-c510320308b3")
VENDOR_SMOOTHING = uuid.UUID("73aad18e-9b22-4667-9feb-94ee1cae948e")
VENDOR_QUANTIZE = uuid.UUID("a0c05046-e72b-4d8f-8689-1385fa7f14d6")
VENDOR_OUTLIERS = uuid.UUID("6c638720-bbff-4d42-8c18-eb14f3e3cca6")
VENDOR_PARTITION = uuid.UUID("b2161dca-d25a-440e-8833-813d4af7c5f6")
# Palette «Конечные классы» in preprocess maps to the trainable model node
VENDOR_FINAL_CLASSES = uuid.UUID("5c25727f-f53f-44b3-89cc-9570afe0f294")
VENDOR_IMPORT_XML = uuid.UUID("f678ea95-0484-46a4-ab42-e03739a40cc6")
VENDOR_SLIDING = uuid.UUID("4b7b4a8c-0c25-4496-94aa-216fc9e252de")
VENDOR_REPLACE_VARS = uuid.UUID("f2c44372-4b7c-41ae-99f5-a3d52d418d90")
VENDOR_IMPORT_DB = uuid.UUID("e8491d9e-c797-4acf-beb2-220bd39331e7")
VENDOR_IMPORT_1C = uuid.UUID("0eea96bc-66b8-475f-a7bb-6fc572577392")
VENDOR_IMPORT_DW = uuid.UUID("e9c33e31-d53c-43d6-9ea6-568a830a02d4")
VENDOR_EXPORT_XML = uuid.UUID("5036451c-e1fc-4bb5-aa32-bf9302af7c7d")
VENDOR_EXPORT_NATIVE = uuid.UUID("70fd0efe-6caa-4151-95e0-1868586e32c9")
VENDOR_EXPORT_DB = uuid.UUID("44bdaed5-66f9-4fe6-b7db-b93febb77b3a")
VENDOR_EXPORT_DW = uuid.UUID("e6358791-8f62-4de2-b6e3-5da388597806")
PORT_RESULT_STATUS = uuid.UUID("078588da-9edb-35aa-9cff-3f8a5b66b073")
PORT_VARS_IN = tr.PORT_VARS_IN
PORT_VARS_OUT = uuid.UUID("b671426b-642b-3e7c-b9a9-9653573f3199")


def _svc_in() -> bytes:
    return list_of_items(
        "ServiceInputPorts",
        [
            port_item(PORT_SYNC_IN, "SynchronizationInputPort", "Порядок выполнения"),
            port_item(PORT_CONTROL_VARS, "ControlVariables", "Управляющие переменные"),
        ],
    )


def _svc_out() -> bytes:
    return list_of_items(
        "ServiceOutputPorts",
        [
            port_item(PORT_SYNC_OUT, "SynchronizationOutputPort", "Порядок выполнения"),
            port_item(PORT_COMPONENT, "ComponentOutputPort", "Компонент"),
            port_item(PORT_DEPENDENT, "DependentNodeOutputPort", "Зависимые узлы"),
        ],
    )


def _layout(left: float, top: float) -> bytes:
    # Loginom 7.4 saves Position (not Layout); Layout breaks some DB nodes on open.
    return (
        s("Position")
        + b"\x00\x02"
        + field_float64("Left", left)
        + field_float64("Top", top)
        + b"\x00"
    )


def _node_header(node_guid: uuid.UUID, display_name: str, vendor: uuid.UUID) -> bytes:
    return (
        b"\x00\x03"
        + field_guid("Guid", node_guid)
        + field_str("DisplayName", display_name)
        + field_guid("VendorGuid", vendor)
        + b"\x06"
    )


def build_ungroup_node(
    node_guid: uuid.UUID,
    display_name: str,
    left: float = 160.0,
    top: float = 100.0,
) -> bytes:
    input_ports = list_of_items(
        "InputPorts",
        [
            port_item(PORT_DS_IN, "DataSource", "Разгруппируемые данные"),
            port_item(PORT_SUPPORT, "SupportInputDataSource", "Данные для расчета долей"),
        ],
    )
    output_ports = list_of_items(
        "OutputPorts",
        [
            port_item(PORT_UNGROUP_OUT, "UngroupOutput", "Выход разгруппировки"),
            port_item(
                PORT_UNGROUP_STATS,
                "UngroupStatsDataSource",
                "Показатели качества модели и сезонные индексы",
            ),
        ],
    )
    main = tr._ds_in_socket_item(PORT_DS_IN, "DataSource", "Разгруппируемые данные")
    support = tr._ds_in_socket_item(
        PORT_SUPPORT, "SupportInputDataSource", "Данные для расчета долей"
    )
    ctrl = tr._ctrl_vars_socket_item()
    out1 = tr._ds_out_socket_item(PORT_UNGROUP_OUT, "UngroupOutput", "Выход разгруппировки")
    out2 = tr._ds_out_socket_item(
        PORT_UNGROUP_STATS,
        "UngroupStatsDataSource",
        "Показатели качества модели и сезонные индексы",
    )
    input_sockets = (
        s("InputSockets")
        + b"\x00\x00\x03"
        + s("Item")
        + main
        + s("Item")
        + support
        + s("Item")
        + ctrl
    )
    output_sockets = (
        s("OutputSockets")
        + b"\x00\x00\x02"
        + s("Item")
        + out1
        + s("Item")
        + out2
    )
    # Defaults from ungrouping-demo sample
    engine = (
        s("Engine")
        + s("TBGUngroupDataEngine")
        + b"\x03"
        + field_enum16("UngroupMethod", 0)  # umQuotaIsGiven
        + field_enum16("RoundFormat", 2)  # rfDecimalPlaces
        + field_float64("MaxDepthPeriodFraction", 0.0)
        + b"\x01"
        + empty_list("Links")
    )
    component = (
        s("Component") + b"\x00\x00\x03" + input_sockets + output_sockets + engine
    )
    return (
        _node_header(node_guid, display_name, VENDOR_UNGROUP)
        + input_ports
        + output_ports
        + _svc_in()
        + _svc_out()
        + component
        + _layout(left, top)
    )


def build_imputation_node(
    node_guid: uuid.UUID,
    display_name: str,
    left: float = 160.0,
    top: float = 100.0,
) -> bytes:
    engine = (
        s("Engine")
        + s("TBGDataRecoveryEngine")
        + b"\x01"
        + field_float64("MaxNullsPercent", 50.0)
        + b"\x00"
    )
    return tr._transform_shell(
        node_guid, display_name, VENDOR_IMPUTATION, engine, left, top
    )


def build_smoothing_node(
    node_guid: uuid.UUID,
    display_name: str,
    left: float = 160.0,
    top: float = 100.0,
) -> bytes:
    engine = s("Engine") + s("TBGCustomModelComponentEngine") + b"\x00\x00"
    return tr._transform_shell(
        node_guid, display_name, VENDOR_SMOOTHING, engine, left, top
    )


def build_final_classes_node(
    node_guid: uuid.UUID,
    display_name: str,
    left: float = 160.0,
    top: float = 100.0,
) -> bytes:
    """Конечные классы (модель) — TBGCoarseClassesEngine, virgin empty Mappers/Builders."""
    input_ports = list_of_items(
        "InputPorts",
        [port_item(PORT_DS_IN, "DataSource", "Входной источник данных")],
    )
    output_ports = list_of_items(
        "OutputPorts",
        [
            port_item(PORT_DS_OUT, "DataSource", "Выходной набор данных"),
            port_item(PORT_CLASS_PARAMS, "ClassParams", "Параметры классов"),
            port_item(PORT_BINNING_PARAMS, "BinningParams", "Значимости столбцов"),
        ],
    )
    ds_in = tr._ds_in_socket_item(PORT_DS_IN, "DataSource", "Входной источник данных")
    ctrl = tr._ctrl_vars_socket_item()
    o1 = tr._ds_out_socket_item(PORT_DS_OUT, "DataSource", "Выходной набор данных")
    o2 = tr._ds_out_socket_item(PORT_CLASS_PARAMS, "ClassParams", "Параметры классов")
    o3 = tr._ds_out_socket_item(
        PORT_BINNING_PARAMS, "BinningParams", "Значимости столбцов"
    )
    input_sockets = (
        s("InputSockets") + b"\x00\x00\x02" + s("Item") + ds_in + s("Item") + ctrl
    )
    output_sockets = (
        s("OutputSockets")
        + b"\x00\x00\x03"
        + s("Item")
        + o1
        + s("Item")
        + o2
        + s("Item")
        + o3
    )
    engine = (
        s("Engine")
        + s("TBGCoarseClassesEngine")
        + b"\x00\x02"
        + empty_list("Mappers")
        + empty_list("Builders")
    )
    component = (
        s("Component") + b"\x00\x00\x03" + input_sockets + output_sockets + engine
    )
    return (
        _node_header(node_guid, display_name, VENDOR_FINAL_CLASSES)
        + input_ports
        + output_ports
        + _svc_in()
        + _svc_out()
        + component
        + _layout(left, top)
    )


def build_quantize_node(
    node_guid: uuid.UUID,
    display_name: str,
    left: float = 160.0,
    top: float = 100.0,
) -> bytes:
    input_ports = list_of_items(
        "InputPorts",
        [
            port_item(PORT_DS_IN, "DataSource", "Входной источник данных"),
            port_item(PORT_RANGES_IN, "Ranges", "Внешние диапазоны квантования"),
        ],
    )
    output_ports = list_of_items(
        "OutputPorts",
        [
            port_item(PORT_DS_OUT, "DataSource", "Выходной набор данных"),
            port_item(PORT_RANGES_OUT, "Ranges", "Диапазоны для квантования"),
        ],
    )
    ds_in = tr._ds_in_socket_item(PORT_DS_IN, "DataSource", "Входной источник данных")
    ranges_in = tr._ds_in_socket_item(
        PORT_RANGES_IN, "Ranges", "Внешние диапазоны квантования"
    )
    ctrl = tr._ctrl_vars_socket_item()
    ds_out = tr._ds_out_socket_item(PORT_DS_OUT, "DataSource", "Выходной набор данных")
    ranges_out = tr._ds_out_socket_item(
        PORT_RANGES_OUT, "Ranges", "Диапазоны для квантования"
    )
    input_sockets = (
        s("InputSockets")
        + b"\x00\x00\x03"
        + s("Item")
        + ds_in
        + s("Item")
        + ranges_in
        + s("Item")
        + ctrl
    )
    output_sockets = (
        s("OutputSockets")
        + b"\x00\x00\x02"
        + s("Item")
        + ds_out
        + s("Item")
        + ranges_out
    )
    engine = s("Engine") + s("TBGBinningEngine") + b"\x00\x00"
    component = (
        s("Component") + b"\x00\x00\x03" + input_sockets + output_sockets + engine
    )
    return (
        _node_header(node_guid, display_name, VENDOR_QUANTIZE)
        + input_ports
        + output_ports
        + _svc_in()
        + _svc_out()
        + component
        + _layout(left, top)
    )


def build_outliers_node(
    node_guid: uuid.UUID,
    display_name: str,
    left: float = 160.0,
    top: float = 100.0,
) -> bytes:
    input_ports = list_of_items(
        "InputPorts",
        [port_item(PORT_DS_IN, "DataSource", "Входной источник данных")],
    )
    output_ports = list_of_items(
        "OutputPorts",
        [
            port_item(PORT_OUT_DATA, "OutData", "Выходной набор"),
            port_item(PORT_OUT_OUTLIERS, "OutDataOut", "Выбросы"),
            port_item(PORT_OUT_EXTR, "OutDataExtr", "Экстремальные значения"),
        ],
    )
    ds_in = tr._ds_in_socket_item(PORT_DS_IN, "DataSource", "Входной источник данных")
    ctrl = tr._ctrl_vars_socket_item()
    o1 = tr._ds_out_socket_item(PORT_OUT_DATA, "OutData", "Выходной набор")
    o2 = tr._ds_out_socket_item(PORT_OUT_OUTLIERS, "OutDataOut", "Выбросы")
    o3 = tr._ds_out_socket_item(PORT_OUT_EXTR, "OutDataExtr", "Экстремальные значения")
    input_sockets = (
        s("InputSockets") + b"\x00\x00\x02" + s("Item") + ds_in + s("Item") + ctrl
    )
    output_sockets = (
        s("OutputSockets")
        + b"\x00\x00\x03"
        + s("Item")
        + o1
        + s("Item")
        + o2
        + s("Item")
        + o3
    )
    engine = s("Engine") + s("TBGElimOutlierEngine") + b"\x00\x00"
    component = (
        s("Component") + b"\x00\x00\x03" + input_sockets + output_sockets + engine
    )
    return (
        _node_header(node_guid, display_name, VENDOR_OUTLIERS)
        + input_ports
        + output_ports
        + _svc_in()
        + _svc_out()
        + component
        + _layout(left, top)
    )


def build_partition_node(
    node_guid: uuid.UUID,
    display_name: str,
    left: float = 160.0,
    top: float = 100.0,
) -> bytes:
    input_ports = list_of_items(
        "InputPorts",
        [port_item(PORT_DS_IN, "DataSource", "Входной источник данных")],
    )
    output_ports = list_of_items(
        "OutputPorts",
        [
            port_item(PORT_PART_COMMON, "OutDataSetCommon", "Общий выходной набор"),
            port_item(PORT_PART_TEACH, "OutDataSetTeach", "Обучающий выходной набор"),
            port_item(PORT_PART_TEST, "OutDataSetTest", "Тестовый выходной набор"),
        ],
    )
    ds_in = tr._ds_in_socket_item(PORT_DS_IN, "DataSource", "Входной источник данных")
    ctrl = tr._ctrl_vars_socket_item()
    o1 = tr._ds_out_socket_item(
        PORT_PART_COMMON, "OutDataSetCommon", "Общий выходной набор"
    )
    o2 = tr._ds_out_socket_item(
        PORT_PART_TEACH, "OutDataSetTeach", "Обучающий выходной набор"
    )
    o3 = tr._ds_out_socket_item(
        PORT_PART_TEST, "OutDataSetTest", "Тестовый выходной набор"
    )
    input_sockets = (
        s("InputSockets") + b"\x00\x00\x02" + s("Item") + ds_in + s("Item") + ctrl
    )
    output_sockets = (
        s("OutputSockets")
        + b"\x00\x00\x03"
        + s("Item")
        + o1
        + s("Item")
        + o2
        + s("Item")
        + o3
    )
    # Exact engine body from working sample Unit.bin (through empty SamplingRecordCount)
    engine = s("Engine") + s("TBGPartitionEngine") + bytes.fromhex(
        "00020652616e646f6d00010852616e645365656404ac87e0a3030009506172746974696f6e"
        "00030c546573745072696f7269747901000f506172746974696f6e4d6574686f640902"
        "08526f77436f756e7404e4ea00020c53616d706c696e6754797065000000"
        "1353616d706c696e675265636f7264436f756e74000000"
    )
    component = (
        s("Component") + b"\x00\x00\x03" + input_sockets + output_sockets + engine
    )
    return (
        _node_header(node_guid, display_name, VENDOR_PARTITION)
        + input_ports
        + output_ports
        + _svc_in()
        + _svc_out()
        + component
        + _layout(left, top)
    )


def build_import_xml_node(
    node_guid: uuid.UUID,
    display_name: str,
    left: float = 160.0,
    top: float = 100.0,
    file_name: str = "data.xml",
) -> bytes:
    """Virgin XML import (TBGImportXML) — Connection + XSDConnection + ControlVariables."""
    input_ports = list_of_items(
        "InputPorts",
        [
            port_item(PORT_CONNECTION, "Connection", "Подключение"),
            port_item(PORT_CONTROL_VARS, "ControlVariables", "Управляющие переменные"),
            port_item(PORT_XSD, "XSDConnection", "Подключение к источнику XSD-схемы"),
        ],
    )
    output_ports = list_of_items(
        "OutputPorts",
        [port_item(PORT_DATASET, "DataSet", "Набор данных")],
    )
    service_in = list_of_items(
        "ServiceInputPorts",
        [port_item(PORT_SYNC_IN, "SynchronizationInputPort", "Порядок выполнения")],
    )
    conn_socket = (
        s("Socket") + s("TBGConnectionInputSocket") + b"\x01" + field_bool("Virgin", True) + b"\x01" + empty_list("Constraints")
    )
    conn_item = (
        b"\x00\x03"
        + field_guid("Guid", PORT_CONNECTION)
        + field_str("Name", "Connection")
        + field_str("DisplayName", "Подключение")
        + b"\x01"
        + conn_socket
    )
    xsd_socket = (
        s("Socket") + s("TBGConnectionInputSocket") + b"\x01" + field_bool("Virgin", True) + b"\x01" + empty_list("Constraints")
    )
    xsd_item = (
        b"\x00\x03"
        + field_guid("Guid", PORT_XSD)
        + field_str("Name", "XSDConnection")
        + field_str("DisplayName", "Подключение к источнику XSD-схемы")
        + b"\x01"
        + xsd_socket
    )
    ctrl = tr._ctrl_vars_socket_item()
    out_ds = (
        b"\x00\x03"
        + field_guid("Guid", PORT_DATASET)
        + field_str("Name", "DataSet")
        + field_str("DisplayName", "Набор данных")
        + b"\x01"
        + (
            s("Socket")
            + s("TBGDataSetOutputSocket")
            + b"\x00\x01"
            + (
                s("DataSource")
                + b"\x00\x01"
                + field_bool("SyncThroughColumns", True)
                + b"\x01"
                + empty_list("ColumnDefs")
            )
        )
    )
    input_sockets = (
        s("InputSockets")
        + b"\x00\x00\x03"
        + s("Item")
        + conn_item
        + s("Item")
        + ctrl
        + s("Item")
        + xsd_item
    )
    output_sockets = s("OutputSockets") + b"\x00\x00\x01" + s("Item") + out_ds
    engine = (
        s("Engine")
        + s("TBGImportXML")
        + b"\x02"
        + field_str("FileName", file_name)
        + field_str("CompositeDisplayNameSeparator", "|")
        + b"\x00"
    )
    component = (
        s("Component") + b"\x00\x00\x03" + input_sockets + output_sockets + engine
    )
    return (
        _node_header(node_guid, display_name, VENDOR_IMPORT_XML)
        + input_ports
        + output_ports
        + service_in
        + _svc_out()
        + component
        + _layout(left, top)
    )


def _conn_item(guid: uuid.UUID, name: str, display: str) -> bytes:
    sock = (
        s("Socket")
        + s("TBGConnectionInputSocket")
        + b"\x01"
        + field_bool("Virgin", True)
        + b"\x01"
        + empty_list("Constraints")
    )
    return (
        b"\x00\x03"
        + field_guid("Guid", guid)
        + field_str("Name", name)
        + field_str("DisplayName", display)
        + b"\x01"
        + sock
    )


def _dataset_out_item() -> bytes:
    return (
        b"\x00\x03"
        + field_guid("Guid", PORT_DATASET)
        + field_str("Name", "DataSet")
        + field_str("DisplayName", "Набор данных")
        + b"\x01"
        + (
            s("Socket")
            + s("TBGDataSetOutputSocket")
            + b"\x01"
            + field_bool("Virgin", True)
            + b"\x01"
            + (
                s("DataSource")
                + b"\x00\x01"
                + field_bool("SyncThroughColumns", True)
                + b"\x01"
                + empty_list("ColumnDefs")
            )
        )
    )


def _result_status_out_item() -> bytes:
    return (
        b"\x00\x03"
        + field_guid("Guid", PORT_RESULT_STATUS)
        + field_str("Name", "ResultStatus")
        + field_str("DisplayName", "Статус выполнения")
        + b"\x01"
        + (
            s("Socket")
            + s("TBGDerivedVariablesOutputSocket")
            + b"\x01"
            + field_bool("Virgin", True)
            + b"\x01"
            + (
                s("Variables")
                + b"\x00\x01"
                + field_bool("SyncThroughVariables", True)
                + b"\x01"
                + empty_list("Elements")
            )
        )
    )


def _sync_only_service_in() -> bytes:
    return list_of_items(
        "ServiceInputPorts",
        [port_item(PORT_SYNC_IN, "SynchronizationInputPort", "Порядок выполнения")],
    )


def build_sliding_window_node(
    node_guid: uuid.UUID,
    display_name: str,
    left: float = 160.0,
    top: float = 100.0,
) -> bytes:
    engine = s("Engine") + s("TBGSlidingWindowEngine") + b"\x00\x00"
    return tr._transform_shell(
        node_guid, display_name, VENDOR_SLIDING, engine, left, top
    )


def build_replace_variables_node(
    node_guid: uuid.UUID,
    display_name: str,
    left: float = 160.0,
    top: float = 100.0,
) -> bytes:
    input_ports = list_of_items(
        "InputPorts",
        [port_item(PORT_VARS_IN, "Variables", "Входные переменные")],
    )
    output_ports = list_of_items(
        "OutputPorts",
        [port_item(PORT_VARS_OUT, "Variables", "Выходные переменные")],
    )
    # Match Cursor_G2 sample: Variables in without Virgin; out with Virgin
    vars_in = tr._vars_socket_item(
        PORT_VARS_IN, "Variables", "Входные переменные", virgin=False
    )
    ctrl = tr._ctrl_vars_socket_item()
    vars_out = (
        b"\x00\x03"
        + field_guid("Guid", PORT_VARS_OUT)
        + field_str("Name", "Variables")
        + field_str("DisplayName", "Выходные переменные")
        + b"\x01"
        + (
            s("Socket")
            + s("TBGDerivedVariablesOutputSocket")
            + b"\x01"
            + field_bool("Virgin", True)
            + b"\x01"
            + (
                s("Variables")
                + b"\x00\x01"
                + field_bool("SyncThroughVariables", True)
                + b"\x01"
                + empty_list("Elements")
            )
        )
    )
    input_sockets = (
        s("InputSockets") + b"\x00\x00\x02" + s("Item") + vars_in + s("Item") + ctrl
    )
    output_sockets = s("OutputSockets") + b"\x00\x00\x01" + s("Item") + vars_out
    engine = s("Engine") + s("TBGCustomModelComponentEngine") + b"\x00\x00"
    component = (
        s("Component") + b"\x00\x00\x03" + input_sockets + output_sockets + engine
    )
    return (
        _node_header(node_guid, display_name, VENDOR_REPLACE_VARS)
        + input_ports
        + output_ports
        + _svc_in()
        + _svc_out()
        + component
        + _layout(left, top)
    )


def build_import_db_node(
    node_guid: uuid.UUID,
    display_name: str,
    left: float = 160.0,
    top: float = 100.0,
) -> bytes:
    engine = s("Engine") + s("TBGDBImport") + bytes.fromhex(
        "020b436f6d6d616e645479706509000b436f6d6d616e64546578740700010646696c746572000000"
    )
    # rebuild with left/top
    input_ports = list_of_items(
        "InputPorts",
        [
            port_item(PORT_CONNECTION, "Connection", "Подключение"),
            port_item(PORT_CONTROL_VARS, "ControlVariables", "Управляющие переменные"),
        ],
    )
    output_ports = list_of_items(
        "OutputPorts",
        [
            port_item(PORT_DATASET, "DataSet", "Набор данных"),
            port_item(PORT_RESULT_STATUS, "ResultStatus", "Статус выполнения"),
        ],
    )
    conn = _conn_item(PORT_CONNECTION, "Connection", "Подключение")
    ctrl = tr._ctrl_vars_socket_item()
    input_sockets = (
        s("InputSockets") + b"\x00\x00\x02" + s("Item") + conn + s("Item") + ctrl
    )
    output_sockets = (
        s("OutputSockets")
        + b"\x00\x00\x02"
        + s("Item")
        + _dataset_out_item()
        + s("Item")
        + _result_status_out_item()
    )
    component = (
        s("Component") + b"\x00\x00\x03" + input_sockets + output_sockets + engine
    )
    return (
        _node_header(node_guid, display_name, VENDOR_IMPORT_DB)
        + input_ports
        + output_ports
        + _sync_only_service_in()
        + _svc_out()
        + component
        + _layout(left, top)
    )


def build_import_1c_node(
    node_guid: uuid.UUID,
    display_name: str,
    left: float = 160.0,
    top: float = 100.0,
) -> bytes:
    engine = s("Engine") + s("TBG1Cv8QueryImport") + bytes.fromhex(
        "0109517565727954657874070000"
    )
    input_ports = list_of_items(
        "InputPorts",
        [
            port_item(PORT_CONNECTION, "Connection", "Подключение"),
            port_item(PORT_CONTROL_VARS, "ControlVariables", "Управляющие переменные"),
        ],
    )
    output_ports = list_of_items(
        "OutputPorts",
        [port_item(PORT_DATASET, "DataSet", "Набор данных")],
    )
    conn = _conn_item(PORT_CONNECTION, "Connection", "Подключение")
    ctrl = tr._ctrl_vars_socket_item()
    input_sockets = (
        s("InputSockets") + b"\x00\x00\x02" + s("Item") + conn + s("Item") + ctrl
    )
    output_sockets = s("OutputSockets") + b"\x00\x00\x01" + s("Item") + _dataset_out_item()
    component = (
        s("Component") + b"\x00\x00\x03" + input_sockets + output_sockets + engine
    )
    return (
        _node_header(node_guid, display_name, VENDOR_IMPORT_1C)
        + input_ports
        + output_ports
        + _sync_only_service_in()
        + _svc_out()
        + component
        + _layout(left, top)
    )


def build_import_warehouse_node(
    node_guid: uuid.UUID,
    display_name: str,
    left: float = 160.0,
    top: float = 100.0,
) -> bytes:
    engine = s("Engine") + s("TBGDWExtract") + bytes.fromhex(
        "030c44574f626a6563745479706509000c44574f626a6563744e616d650700"
        "1344574f626a656374446973706c61794e616d650700010d53656c656374696f6e54726565"
        "0000010753656c4f626a73000000"
    )
    input_ports = list_of_items(
        "InputPorts",
        [
            port_item(PORT_CONNECTION, "Connection", "Подключение"),
            port_item(PORT_CONTROL_VARS, "ControlVariables", "Управляющие переменные"),
        ],
    )
    output_ports = list_of_items(
        "OutputPorts",
        [port_item(PORT_DATASET, "DataSet", "Набор данных")],
    )
    conn = _conn_item(PORT_CONNECTION, "Connection", "Подключение")
    ctrl = tr._ctrl_vars_socket_item()
    input_sockets = (
        s("InputSockets") + b"\x00\x00\x02" + s("Item") + conn + s("Item") + ctrl
    )
    output_sockets = s("OutputSockets") + b"\x00\x00\x01" + s("Item") + _dataset_out_item()
    component = (
        s("Component") + b"\x00\x00\x03" + input_sockets + output_sockets + engine
    )
    return (
        _node_header(node_guid, display_name, VENDOR_IMPORT_DW)
        + input_ports
        + output_ports
        + _sync_only_service_in()
        + _svc_out()
        + component
        + _layout(left, top)
    )


def _export_conn_ds_shell(
    node_guid: uuid.UUID,
    display_name: str,
    vendor: uuid.UUID,
    engine: bytes,
    left: float,
    top: float,
    *,
    with_ctrl: bool = True,
    with_xsd: bool = False,
    with_result_status: bool = False,
    conn_display: str = "Подключение",
) -> bytes:
    ports = [
        port_item(PORT_CONNECTION, "Connection", conn_display),
        port_item(PORT_DS_IN, "DataSource", "Источник данных"),
    ]
    socks = [
        _conn_item(PORT_CONNECTION, "Connection", conn_display),
        tr._ds_in_socket_item(PORT_DS_IN, "DataSource", "Источник данных", virgin=True),
    ]
    if with_ctrl:
        ports.append(
            port_item(PORT_CONTROL_VARS, "ControlVariables", "Управляющие переменные")
        )
        socks.append(tr._ctrl_vars_socket_item())
    if with_xsd:
        ports.append(
            port_item(PORT_XSD, "XSDConnection", "Подключение к источнику XSD-схемы")
        )
        socks.append(
            _conn_item(PORT_XSD, "XSDConnection", "Подключение к источнику XSD-схемы")
        )
    input_ports = list_of_items("InputPorts", ports)
    if with_result_status:
        output_ports = list_of_items(
            "OutputPorts",
            [port_item(PORT_RESULT_STATUS, "ResultStatus", "Статус выполнения")],
        )
        output_sockets = (
            s("OutputSockets") + b"\x00\x00\x01" + s("Item") + _result_status_out_item()
        )
    else:
        output_ports = empty_list("OutputPorts")
        output_sockets = empty_list("OutputSockets")
    input_sockets = (
        s("InputSockets")
        + b"\x00\x00"
        + bytes([len(socks)])
        + b"".join(s("Item") + it for it in socks)
    )
    component = (
        s("Component") + b"\x00\x00\x03" + input_sockets + output_sockets + engine
    )
    return (
        _node_header(node_guid, display_name, vendor)
        + input_ports
        + output_ports
        + _sync_only_service_in()
        + _svc_out()
        + component
        + _layout(left, top)
    )


def build_export_xml_node(
    node_guid: uuid.UUID,
    display_name: str,
    left: float = 160.0,
    top: float = 100.0,
    file_name: str = "export.xml",
) -> bytes:
    engine = (
        s("Engine")
        + s("TBGExportXML")
        + b"\x01"
        + field_str("FileName", file_name)
        + b"\x02"
        + empty_list("RequestProcessor")
        + empty_list("InputColumnsMapping")
    )
    return _export_conn_ds_shell(
        node_guid,
        display_name,
        VENDOR_EXPORT_XML,
        engine,
        left,
        top,
        with_ctrl=True,
        with_xsd=True,
        conn_display="Подключение к файловому хранилищу",
    )


def build_export_native_node(
    node_guid: uuid.UUID,
    display_name: str,
    left: float = 160.0,
    top: float = 100.0,
    file_name: str = "export.lgd",
) -> bytes:
    engine = (
        s("Engine")
        + s("TBGExportNative")
        + b"\x02"
        + field_str("FileName", file_name)
        + s("Compression")
        + b"\x09"
        + bytes([2])  # dcLZ4, 1-byte enum
        + b"\x00"
    )
    return _export_conn_ds_shell(
        node_guid, display_name, VENDOR_EXPORT_NATIVE, engine, left, top
    )


def build_export_db_node(
    node_guid: uuid.UUID,
    display_name: str,
    left: float = 160.0,
    top: float = 100.0,
    table_name: str = "",
) -> bytes:
    # ExportType is a 1-byte enum (not uint16); trailing \x01 starts nested ExportColumns.
    engine = (
        s("Engine")
        + s("TBGDBExport")
        + b"\x02"
        + field_str("TableName", table_name)
        + s("ExportType")
        + b"\x09"
        + bytes([0])  # etAppend
        + b"\x01"
        + empty_list("ExportColumns")
    )
    return _export_conn_ds_shell(
        node_guid,
        display_name,
        VENDOR_EXPORT_DB,
        engine,
        left,
        top,
        with_result_status=True,
    )


def build_export_warehouse_node(
    node_guid: uuid.UUID,
    display_name: str,
    left: float = 160.0,
    top: float = 100.0,
) -> bytes:
    # Exact virgin blob from Cursor_G5 sample
    engine = s("Engine") + s("TBGDWLoad") + bytes.fromhex(
        "030c44574f626a6563745479706509000c44574f626a6563744e616d650700"
        "1344574f626a656374446973706c61794e616d650700010d53656c656374696f6e54726565"
        "00021243726561746550726f636573735461626c6501000b52656275696c64437562650100"
        "010753656c4f626a73000000"
    )
    return _export_conn_ds_shell(
        node_guid,
        display_name,
        VENDOR_EXPORT_DW,
        engine,
        left,
        top,
        with_ctrl=False,
    )
