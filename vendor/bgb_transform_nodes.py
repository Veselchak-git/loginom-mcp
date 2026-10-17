"""Transform nodes: Sorting, ReformColumns, Calculator, DateTime, Grouping."""
from __future__ import annotations

import struct
import uuid

# Reuse helpers from import module via import
import importlib.util
from pathlib import Path

_VENDOR = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location(
    "imp", _VENDOR / "bgb_import_node.py"
)
imp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(imp)

s = imp.s
field_guid = imp.field_guid
field_str = imp.field_str
field_bool = imp.field_bool
field_float64 = imp.field_float64
empty_list = imp.empty_list
list_of_items = imp.list_of_items
port_item = imp.port_item

PORT_DS_IN = uuid.UUID("9dc72a3f-56bf-3bfc-84ec-f979daf4da6b")
PORT_DS_OUT = uuid.UUID("4ba0e2c2-69ad-3a32-bbdc-75714efe7a51")
PORT_VARS_IN = uuid.UUID("d252e390-f72d-36c4-97fc-60d86186c3c6")
PORT_SYNC_IN = imp.PORT_SYNC_IN
PORT_SYNC_OUT = imp.PORT_SYNC_OUT
PORT_CONTROL_VARS = imp.PORT_CONTROL_VARS
PORT_COMPONENT = imp.PORT_COMPONENT
PORT_DEPENDENT = imp.PORT_DEPENDENT

VENDOR_SORTING = uuid.UUID("62a25d53-677f-45ef-abe7-537dfdc2ea4b")
VENDOR_REFORM_COLUMNS = uuid.UUID("dc279f34-55cf-4fee-8bb4-e10de32c88f2")
VENDOR_CALCULATOR = uuid.UUID("c7b69712-557f-4e51-bba5-db9cc2659e7a")
VENDOR_DATETIME = uuid.UUID("d21f2169-20c2-4ca3-85e3-5279e52aeebc")
VENDOR_GROUPING = uuid.UUID("4d4f2852-8a7d-4993-84f0-5b488029b1a7")
VENDOR_FILTER = uuid.UUID("a0e49d86-6fe3-43fc-8046-29d1ce92c03d")
VENDOR_REPLACE = uuid.UUID("5346793b-a4f9-40f2-ae49-b14c731bd0f2")
VENDOR_UNION = uuid.UUID("f5aa91d2-9fe5-439d-9f7f-1e17996da272")
VENDOR_JOIN = uuid.UUID("7197af14-a6cc-479c-acc6-9867bc970205")
VENDOR_ENRICH = uuid.UUID("0370e80a-78e1-4ede-b71b-930497994b44")
PORT_DS_ELSE = uuid.UUID("99559aff-aff4-3e08-8f1e-a290790bba03")
PORT_MAIN_DS = uuid.UUID("e028600d-9dca-3604-89ce-cd2fdadb4c1c")
PORT_JOINED_DS = uuid.UUID("54ae772d-7bcb-36bb-88ac-976dcae031bc")

# SortDirection enum
SD_ASC = 0
SD_DESC = 1


def field_enum16(name: str, value: int) -> bytes:
    """BGB type 0x09 is a 1-byte enum (not uint16). Extra byte desyncs the stream
    and Loginom reports empty schema names / phantom attributes.
    """
    return s(name) + b"\x09" + bytes([value & 0xFF])


def _transform_shell(
    node_guid: uuid.UUID,
    display_name: str,
    vendor: uuid.UUID,
    engine_blob: bytes,
    left: float,
    top: float,
) -> bytes:
    """Common 1-in/1-out dataset transform node shell."""
    input_ports = list_of_items(
        "InputPorts",
        [port_item(PORT_DS_IN, "DataSource", "Входной источник данных")],
    )
    output_ports = list_of_items(
        "OutputPorts",
        [port_item(PORT_DS_OUT, "DataSource", "Выходной набор данных")],
    )
    service_in = list_of_items(
        "ServiceInputPorts",
        [
            port_item(PORT_SYNC_IN, "SynchronizationInputPort", "Порядок выполнения"),
            port_item(PORT_CONTROL_VARS, "ControlVariables", "Управляющие переменные"),
        ],
    )
    service_out = list_of_items(
        "ServiceOutputPorts",
        [
            port_item(PORT_SYNC_OUT, "SynchronizationOutputPort", "Порядок выполнения"),
            port_item(PORT_COMPONENT, "ComponentOutputPort", "Компонент"),
            port_item(PORT_DEPENDENT, "DependentNodeOutputPort", "Зависимые узлы"),
        ],
    )

    ds_inner = (
        s("DataSource")
        + b"\x00\x01"
        + field_bool("SyncThroughColumns", True)
        + b"\x01"
        + empty_list("ColumnDefs")
    )
    ds_in_socket = (
        s("Socket")
        + s("TBGTuneDataSourceSocket")
        + b"\x00\x02"
        + empty_list("Constraints")
        + ds_inner
    )
    ds_in_item = (
        b"\x00\x03"
        + field_guid("Guid", PORT_DS_IN)
        + field_str("Name", "DataSource")
        + field_str("DisplayName", "Входной источник данных")
        + b"\x01"
        + ds_in_socket
    )

    vars_inner = (
        s("Variables")
        + b"\x00\x01"
        + field_bool("SyncThroughVariables", True)
        + b"\x01"
        + empty_list("Elements")
    )
    ctrl_socket = (
        s("Socket")
        + s("TBGTuneVariablesSocket")
        + b"\x01"
        + field_bool("Virgin", True)
        + b"\x02"
        + empty_list("Constraints")
        + vars_inner
    )
    ctrl_item = (
        b"\x00\x03"
        + field_guid("Guid", PORT_CONTROL_VARS)
        + field_str("Name", "ControlVariables")
        + field_str("DisplayName", "Управляющие переменные")
        + b"\x01"
        + ctrl_socket
    )

    out_ds_inner = (
        s("DataSource")
        + b"\x00\x01"
        + field_bool("SyncThroughColumns", True)
        + b"\x01"
        + empty_list("ColumnDefs")
    )
    ds_out_socket = (
        s("Socket") + s("TBGDerivedDataSourceOutputSocket") + b"\x00\x01" + out_ds_inner
    )
    ds_out_item = (
        b"\x00\x03"
        + field_guid("Guid", PORT_DS_OUT)
        + field_str("Name", "DataSource")
        + field_str("DisplayName", "Выходной набор данных")
        + b"\x01"
        + ds_out_socket
    )

    input_sockets = (
        s("InputSockets")
        + b"\x00\x00\x02"
        + s("Item")
        + ds_in_item
        + s("Item")
        + ctrl_item
    )
    output_sockets = s("OutputSockets") + b"\x00\x00\x01" + s("Item") + ds_out_item
    component = (
        s("Component") + b"\x00\x00\x03" + input_sockets + output_sockets + engine_blob
    )
    layout = (
        s("Position")
        + b"\x00\x02"
        + field_float64("Left", left)
        + field_float64("Top", top)
        + b"\x00"
    )

    node = b"\x00\x03"
    node += field_guid("Guid", node_guid)
    node += field_str("DisplayName", display_name)
    node += field_guid("VendorGuid", vendor)
    node += b"\x06"
    node += input_ports
    node += output_ports
    node += service_in
    node += service_out
    node += component
    node += layout
    return node


def build_sorting_node(
    node_guid: uuid.UUID,
    display_name: str,
    left: float = 160.0,
    top: float = 100.0,
    sort_columns: list[tuple[str, int]] | None = None,
) -> bytes:
    """Virgin/minimal TBGSortingEngine node. sort_columns: [(name, SD_ASC|SD_DESC), ...]"""
    sort_columns = sort_columns or []
    sort_items = []
    for col_name, direction in sort_columns:
        sort_items.append(
            b"\x00\x02"
            + field_str("Name", col_name)
            + field_enum16("SortDirection", direction)
            + b"\x00"
        )
    sorting_columns = (
        list_of_items("SortingColumns", sort_items)
        if sort_items
        else empty_list("SortingColumns")
    )
    engine = s("Engine") + s("TBGSortingEngine") + b"\x00\x01" + sorting_columns
    return _transform_shell(node_guid, display_name, VENDOR_SORTING, engine, left, top)


def build_reform_columns_node(
    node_guid: uuid.UUID,
    display_name: str,
    left: float = 160.0,
    top: float = 100.0,
) -> bytes:
    """Virgin TBGReformColumnsEngine (Параметры полей)."""
    engine = s("Engine") + s("TBGReformColumnsEngine") + b"\x00\x00"
    return _transform_shell(
        node_guid, display_name, VENDOR_REFORM_COLUMNS, engine, left, top
    )


def _vars_socket_item(port_guid: uuid.UUID, name: str, display: str, virgin: bool) -> bytes:
    vars_inner = (
        s("Variables")
        + b"\x00\x01"
        + field_bool("SyncThroughVariables", True)
        + b"\x01"
        + empty_list("Elements")
    )
    socket = s("Socket") + s("TBGTuneVariablesSocket")
    if virgin:
        socket += b"\x01" + field_bool("Virgin", True) + b"\x02"
    else:
        socket += b"\x00\x02"
    socket += empty_list("Constraints") + vars_inner
    return (
        b"\x00\x03"
        + field_guid("Guid", port_guid)
        + field_str("Name", name)
        + field_str("DisplayName", display)
        + b"\x01"
        + socket
    )


def build_calculator_node(
    node_guid: uuid.UUID,
    display_name: str,
    left: float = 160.0,
    top: float = 100.0,
) -> bytes:
    """Virgin TBGCalcData (Калькулятор) — DataSource + Variables in, empty Expressions."""
    input_ports = list_of_items(
        "InputPorts",
        [
            port_item(PORT_DS_IN, "DataSource", "Входной источник данных"),
            port_item(PORT_VARS_IN, "Variables", "Входные переменные"),
        ],
    )
    output_ports = list_of_items(
        "OutputPorts",
        [port_item(PORT_DS_OUT, "DataSource", "Выходной набор данных")],
    )
    service_in = list_of_items(
        "ServiceInputPorts",
        [
            port_item(PORT_SYNC_IN, "SynchronizationInputPort", "Порядок выполнения"),
            port_item(PORT_CONTROL_VARS, "ControlVariables", "Управляющие переменные"),
        ],
    )
    service_out = list_of_items(
        "ServiceOutputPorts",
        [
            port_item(PORT_SYNC_OUT, "SynchronizationOutputPort", "Порядок выполнения"),
            port_item(PORT_COMPONENT, "ComponentOutputPort", "Компонент"),
            port_item(PORT_DEPENDENT, "DependentNodeOutputPort", "Зависимые узлы"),
        ],
    )

    ds_inner = (
        s("DataSource")
        + b"\x00\x01"
        + field_bool("SyncThroughColumns", True)
        + b"\x01"
        + empty_list("ColumnDefs")
    )
    ds_in_item = (
        b"\x00\x03"
        + field_guid("Guid", PORT_DS_IN)
        + field_str("Name", "DataSource")
        + field_str("DisplayName", "Входной источник данных")
        + b"\x01"
        + (
            s("Socket")
            + s("TBGTuneDataSourceSocket")
            + b"\x00\x02"
            + empty_list("Constraints")
            + ds_inner
        )
    )
    ctrl_item = _vars_socket_item(
        PORT_CONTROL_VARS, "ControlVariables", "Управляющие переменные", virgin=True
    )
    vars_item = _vars_socket_item(
        PORT_VARS_IN, "Variables", "Входные переменные", virgin=True
    )
    out_ds_item = (
        b"\x00\x03"
        + field_guid("Guid", PORT_DS_OUT)
        + field_str("Name", "DataSource")
        + field_str("DisplayName", "Выходной набор данных")
        + b"\x01"
        + (
            s("Socket")
            + s("TBGDerivedDataSourceOutputSocket")
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
        + ds_in_item
        + s("Item")
        + ctrl_item
        + s("Item")
        + vars_item
    )
    output_sockets = s("OutputSockets") + b"\x00\x00\x01" + s("Item") + out_ds_item
    engine = s("Engine") + s("TBGCalcData") + b"\x00\x01" + empty_list("Expressions")
    component = (
        s("Component") + b"\x00\x00\x03" + input_sockets + output_sockets + engine
    )
    layout = (
        s("Position")
        + b"\x00\x02"
        + field_float64("Left", left)
        + field_float64("Top", top)
        + b"\x00"
    )
    node = b"\x00\x03"
    node += field_guid("Guid", node_guid)
    node += field_str("DisplayName", display_name)
    node += field_guid("VendorGuid", VENDOR_CALCULATOR)
    node += b"\x06"
    node += input_ports
    node += output_ports
    node += service_in
    node += service_out
    node += component
    node += layout
    return node


def build_datetime_node(
    node_guid: uuid.UUID,
    display_name: str,
    left: float = 160.0,
    top: float = 100.0,
) -> bytes:
    """Virgin Дата и время — Loginom 7.2+ uses TBGDateReformEngine (not CustomModel)."""
    engine = s("Engine") + s("TBGDateReformEngine") + b"\x00\x00"
    return _transform_shell(
        node_guid, display_name, VENDOR_DATETIME, engine, left, top
    )


def build_grouping_node(
    node_guid: uuid.UUID,
    display_name: str,
    left: float = 160.0,
    top: float = 100.0,
) -> bytes:
    """Virgin Группировка (TBGGroupDataEngine, DimValuesCached=true)."""
    engine = (
        s("Engine")
        + s("TBGGroupDataEngine")
        + b"\x01"
        + field_bool("DimValuesCached", True)
        + b"\x00"
    )
    return _transform_shell(
        node_guid, display_name, VENDOR_GROUPING, engine, left, top
    )


def build_replace_node(
    node_guid: uuid.UUID,
    display_name: str,
    left: float = 160.0,
    top: float = 100.0,
) -> bytes:
    """Virgin Замена (TBGCustomModelComponentEngine) — single DataSource in."""
    engine = s("Engine") + s("TBGCustomModelComponentEngine") + b"\x00\x00"
    return _transform_shell(node_guid, display_name, VENDOR_REPLACE, engine, left, top)


def _ds_out_socket_item(port_guid: uuid.UUID, name: str, display: str) -> bytes:
    return (
        b"\x00\x03"
        + field_guid("Guid", port_guid)
        + field_str("Name", name)
        + field_str("DisplayName", display)
        + b"\x01"
        + (
            s("Socket")
            + s("TBGDerivedDataSourceOutputSocket")
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


def build_filter_node(
    node_guid: uuid.UUID,
    display_name: str,
    left: float = 160.0,
    top: float = 100.0,
) -> bytes:
    """Virgin Фильтр строк — DataSource in, DataSource + DataSourceElse out."""
    input_ports = list_of_items(
        "InputPorts",
        [port_item(PORT_DS_IN, "DataSource", "Входной источник данных")],
    )
    output_ports = list_of_items(
        "OutputPorts",
        [
            port_item(PORT_DS_OUT, "DataSource", "Соответствуют условию"),
            port_item(PORT_DS_ELSE, "DataSourceElse", "Не соответствуют условию"),
        ],
    )
    service_in = list_of_items(
        "ServiceInputPorts",
        [
            port_item(PORT_SYNC_IN, "SynchronizationInputPort", "Порядок выполнения"),
            port_item(PORT_CONTROL_VARS, "ControlVariables", "Управляющие переменные"),
        ],
    )
    service_out = list_of_items(
        "ServiceOutputPorts",
        [
            port_item(PORT_SYNC_OUT, "SynchronizationOutputPort", "Порядок выполнения"),
            port_item(PORT_COMPONENT, "ComponentOutputPort", "Компонент"),
            port_item(PORT_DEPENDENT, "DependentNodeOutputPort", "Зависимые узлы"),
        ],
    )

    ds_inner = (
        s("DataSource")
        + b"\x00\x01"
        + field_bool("SyncThroughColumns", True)
        + b"\x01"
        + empty_list("ColumnDefs")
    )
    ds_in_item = (
        b"\x00\x03"
        + field_guid("Guid", PORT_DS_IN)
        + field_str("Name", "DataSource")
        + field_str("DisplayName", "Входной источник данных")
        + b"\x01"
        + (
            s("Socket")
            + s("TBGTuneDataSourceSocket")
            + b"\x00\x02"
            + empty_list("Constraints")
            + ds_inner
        )
    )
    ctrl_item = (
        b"\x00\x03"
        + field_guid("Guid", PORT_CONTROL_VARS)
        + field_str("Name", "ControlVariables")
        + field_str("DisplayName", "Управляющие переменные")
        + b"\x01"
        + (
            s("Socket")
            + s("TBGTuneVariablesSocket")
            + b"\x01"
            + field_bool("Virgin", True)
            + b"\x02"
            + empty_list("Constraints")
            + (
                s("Variables")
                + b"\x00\x01"
                + field_bool("SyncThroughVariables", True)
                + b"\x01"
                + empty_list("Elements")
            )
        )
    )
    out_ok = _ds_out_socket_item(
        PORT_DS_OUT, "DataSource", "Соответствуют условию"
    )
    out_else = _ds_out_socket_item(
        PORT_DS_ELSE, "DataSourceElse", "Не соответствуют условию"
    )
    input_sockets = (
        s("InputSockets")
        + b"\x00\x00\x02"
        + s("Item")
        + ds_in_item
        + s("Item")
        + ctrl_item
    )
    output_sockets = (
        s("OutputSockets")
        + b"\x00\x00\x02"
        + s("Item")
        + out_ok
        + s("Item")
        + out_else
    )
    # Nested object: name + \x00 + n_attrs + attrs + n_children + children.
    # Virgin sample matches Filter\x00\x01 + UseGlobalCaseSensitive + \x00 (no Items).
    filter_obj = (
        s("Filter")
        + b"\x00"
        + b"\x01"
        + field_bool("UseGlobalCaseSensitive", False)
        + b"\x00"
    )
    engine = s("Engine") + s("TBGFilterDataEngine") + b"\x00\x01" + filter_obj
    component = (
        s("Component") + b"\x00\x00\x03" + input_sockets + output_sockets + engine
    )
    layout = (
        s("Position")
        + b"\x00\x02"
        + field_float64("Left", left)
        + field_float64("Top", top)
        + b"\x00"
    )
    node = b"\x00\x03"
    node += field_guid("Guid", node_guid)
    node += field_str("DisplayName", display_name)
    node += field_guid("VendorGuid", VENDOR_FILTER)
    node += b"\x06"
    node += input_ports
    node += output_ports
    node += service_in
    node += service_out
    node += component
    node += layout
    return node


def _ds_in_socket_item(port_guid: uuid.UUID, name: str, display: str, *, virgin: bool = False) -> bytes:
    ds_inner = (
        s("DataSource")
        + b"\x00\x01"
        + field_bool("SyncThroughColumns", True)
        + b"\x01"
        + empty_list("ColumnDefs")
    )
    socket = s("Socket") + s("TBGTuneDataSourceSocket")
    if virgin:
        socket += b"\x01" + field_bool("Virgin", True) + b"\x02"
    else:
        socket += b"\x00\x02"
    socket += empty_list("Constraints") + ds_inner
    return (
        b"\x00\x03"
        + field_guid("Guid", port_guid)
        + field_str("Name", name)
        + field_str("DisplayName", display)
        + b"\x01"
        + socket
    )


def _ctrl_vars_socket_item() -> bytes:
    return (
        b"\x00\x03"
        + field_guid("Guid", PORT_CONTROL_VARS)
        + field_str("Name", "ControlVariables")
        + field_str("DisplayName", "Управляющие переменные")
        + b"\x01"
        + (
            s("Socket")
            + s("TBGTuneVariablesSocket")
            + b"\x01"
            + field_bool("Virgin", True)
            + b"\x02"
            + empty_list("Constraints")
            + (
                s("Variables")
                + b"\x00\x01"
                + field_bool("SyncThroughVariables", True)
                + b"\x01"
                + empty_list("Elements")
            )
        )
    )


def _two_table_shell(
    node_guid: uuid.UUID,
    display_name: str,
    vendor: uuid.UUID,
    engine_blob: bytes,
    left: float,
    top: float,
) -> bytes:
    """MainDataSource + JoinedDataSource in, one DataSource out."""
    input_ports = list_of_items(
        "InputPorts",
        [
            port_item(PORT_MAIN_DS, "MainDataSource", "Главная таблица"),
            port_item(PORT_JOINED_DS, "JoinedDataSource", "Присоединяемая таблица"),
        ],
    )
    output_ports = list_of_items(
        "OutputPorts",
        [port_item(PORT_DS_OUT, "DataSource", "Выходной набор данных")],
    )
    service_in = list_of_items(
        "ServiceInputPorts",
        [
            port_item(PORT_SYNC_IN, "SynchronizationInputPort", "Порядок выполнения"),
            port_item(PORT_CONTROL_VARS, "ControlVariables", "Управляющие переменные"),
        ],
    )
    service_out = list_of_items(
        "ServiceOutputPorts",
        [
            port_item(PORT_SYNC_OUT, "SynchronizationOutputPort", "Порядок выполнения"),
            port_item(PORT_COMPONENT, "ComponentOutputPort", "Компонент"),
            port_item(PORT_DEPENDENT, "DependentNodeOutputPort", "Зависимые узлы"),
        ],
    )
    main_item = _ds_in_socket_item(PORT_MAIN_DS, "MainDataSource", "Главная таблица")
    joined_item = _ds_in_socket_item(
        PORT_JOINED_DS, "JoinedDataSource", "Присоединяемая таблица"
    )
    ctrl_item = _ctrl_vars_socket_item()
    out_item = _ds_out_socket_item(PORT_DS_OUT, "DataSource", "Выходной набор данных")
    input_sockets = (
        s("InputSockets")
        + b"\x00\x00\x03"
        + s("Item")
        + main_item
        + s("Item")
        + joined_item
        + s("Item")
        + ctrl_item
    )
    output_sockets = s("OutputSockets") + b"\x00\x00\x01" + s("Item") + out_item
    component = (
        s("Component") + b"\x00\x00\x03" + input_sockets + output_sockets + engine_blob
    )
    layout = (
        s("Position")
        + b"\x00\x02"
        + field_float64("Left", left)
        + field_float64("Top", top)
        + b"\x00"
    )
    node = b"\x00\x03"
    node += field_guid("Guid", node_guid)
    node += field_str("DisplayName", display_name)
    node += field_guid("VendorGuid", vendor)
    node += b"\x06"
    node += input_ports
    node += output_ports
    node += service_in
    node += service_out
    node += component
    node += layout
    return node


def build_union_node(
    node_guid: uuid.UUID,
    display_name: str,
    left: float = 160.0,
    top: float = 100.0,
) -> bytes:
    """Virgin Объединение (TBGUnionDataEngine)."""
    engine = (
        s("Engine")
        + s("TBGUnionDataEngine")
        + b"\x01"
        + field_str("DisplayNamePrefix", "Объединение")
        + b"\x01"
        + empty_list("Links")
    )
    return _two_table_shell(
        node_guid, display_name, VENDOR_UNION, engine, left, top
    )


def build_join_node(
    node_guid: uuid.UUID,
    display_name: str,
    left: float = 160.0,
    top: float = 100.0,
) -> bytes:
    """Virgin Слияние (TBGJoinDataEngine), default join type, empty Links."""
    engine = (
        s("Engine")
        + s("TBGJoinDataEngine")
        + b"\x01"
        + field_str("DisplayNamePrefix", "Соединение")
        + b"\x01"
        + empty_list("Links")
    )
    return _two_table_shell(node_guid, display_name, VENDOR_JOIN, engine, left, top)


def build_enrich_node(
    node_guid: uuid.UUID,
    display_name: str,
    left: float = 160.0,
    top: float = 100.0,
) -> bytes:
    """Virgin Дополнение данных (TBGEnrichDataEngine), 2 tables."""
    engine = (
        s("Engine")
        + s("TBGEnrichDataEngine")
        + b"\x01"
        + field_str("DisplayNamePrefix", "Дополнение")
        + b"\x01"
        + empty_list("Links")
    )
    return _two_table_shell(
        node_guid, display_name, VENDOR_ENRICH, engine, left, top
    )
