"""Extra palette nodes: ColUnion, Collapse, CrossTab, Sampling, Export, Variables."""
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
PORT_MAIN_DS = tr.PORT_MAIN_DS
PORT_VARS_IN = tr.PORT_VARS_IN
PORT_CONNECTION = imp.PORT_CONNECTION
PORT_CONTROL_VARS = imp.PORT_CONTROL_VARS
PORT_SYNC_IN = imp.PORT_SYNC_IN
PORT_SYNC_OUT = imp.PORT_SYNC_OUT
PORT_COMPONENT = imp.PORT_COMPONENT
PORT_DEPENDENT = imp.PORT_DEPENDENT

# ColUnion uses a different joined-port guid than Enrich/Join
PORT_COLUNION_JOINED = uuid.UUID("5a7adf70-52aa-4223-b40b-6b7837d98359")
PORT_VARS_OUT = uuid.UUID("b671426b-642b-3e7c-b9a9-9653573f3199")
PORT_JOINED_VARS = uuid.UUID("0054b2b7-4a88-3344-9b91-53d2cf60adfe")

VENDOR_COLUNION = uuid.UUID("43c697b8-a02f-4ad3-b0e4-d8cdfee83ae5")
VENDOR_COLLAPSE = uuid.UUID("247b449c-c2c9-495a-b539-7f8ab78ef5bf")
VENDOR_CROSSTAB = uuid.UUID("418295a8-c71e-48e5-89fa-abd1de8b3f9d")
VENDOR_SAMPLING = uuid.UUID("c1f70531-6c5e-42f1-a249-53a7ff269e26")
VENDOR_EXPORT_TEXT = uuid.UUID("767b14f8-3852-4463-9ede-7345c4ddb183")
VENDOR_EXPORT_EXCEL = uuid.UUID("45694995-9a46-4b18-a87a-bfbfa5a74eed")
VENDOR_CALC_VARS = uuid.UUID("3cff62aa-e3b0-4505-b2f0-90bb23b87875")
VENDOR_VARS_TO_TABLE = uuid.UUID("b00d1d89-0386-4fdd-a404-f7ef26ffcd25")
VENDOR_TABLE_TO_VARS = uuid.UUID("c0c06e4e-da43-4f30-b2dd-d95ade0e5970")
VENDOR_JOIN_VARS = uuid.UUID("b4432322-a745-46b0-93cb-83ac194d8adb")

# TailsAlignType atExtendToLongest = 1 (from sample)
AT_EXTEND_LONGEST = 1


def build_collapse_columns_node(
    node_guid: uuid.UUID,
    display_name: str,
    left: float = 160.0,
    top: float = 100.0,
) -> bytes:
    engine = s("Engine") + s("TBGColumnFlippingEngine") + b"\x00\x00"
    return tr._transform_shell(
        node_guid, display_name, VENDOR_COLLAPSE, engine, left, top
    )


def build_crosstab_node(
    node_guid: uuid.UUID,
    display_name: str,
    left: float = 160.0,
    top: float = 100.0,
) -> bytes:
    engine = (
        s("Engine")
        + s("TBGCrossTabEngine")
        + b"\x02"
        + field_bool("Trained", False)
        + field_bool("SlugNames", False)
        + b"\x01"
        + empty_list("CountCase")
    )
    return tr._transform_shell(
        node_guid, display_name, VENDOR_CROSSTAB, engine, left, top
    )


def build_sampling_node(
    node_guid: uuid.UUID,
    display_name: str,
    left: float = 160.0,
    top: float = 100.0,
) -> bytes:
    # Empty engine is invalid; copy working Random+Sampling blob from palette sample.
    # SamplingType uses type 0x09 as a single byte; RowCount uses type 0x04 (not int32 0x05).
    engine = s("Engine") + s("TBGSamplingEngine") + bytes.fromhex(
        "0002"
        "0652616e646f6d0002"
        "0852616e64536565640491a8b1c7"
        "000f416c7761797352616e646f6d697a650101"
        "00"
        "0853616d706c696e670004"
        "0c53616d706c696e67547970650900"
        "1353616d706c696e675265636f7264436f756e74030000000000407f40"
        "0947726f757053697a65030000000000004940"
        "08526f77436f756e7404f40300"
    )
    return tr._transform_shell(
        node_guid, display_name, VENDOR_SAMPLING, engine, left, top
    )


def build_colunion_node(
    node_guid: uuid.UUID,
    display_name: str,
    left: float = 160.0,
    top: float = 100.0,
) -> bytes:
    """Соединение (column union) — Main + dynamic joined table."""
    engine = (
        s("Engine")
        + s("TBGColUnionDataEngine")
        + b"\x01"
        + field_enum16("TailsAlignType", AT_EXTEND_LONGEST)
        + b"\x00"
    )
    # Reuse two-table shell but with ColUnion joined port guid via custom ports
    input_ports = list_of_items(
        "InputPorts",
        [
            port_item(PORT_MAIN_DS, "MainDataSource", "Главная таблица"),
            # Name omitted in sample; keep a stable Name for linking
            port_item(PORT_COLUNION_JOINED, "JoinedDataSource", "Присоединяемая таблица 1"),
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
    main_item = tr._ds_in_socket_item(PORT_MAIN_DS, "MainDataSource", "Главная таблица")
    joined_item = tr._ds_in_socket_item(
        PORT_COLUNION_JOINED, "JoinedDataSource", "Присоединяемая таблица 1"
    )
    ctrl_item = tr._ctrl_vars_socket_item()
    out_item = tr._ds_out_socket_item(PORT_DS_OUT, "DataSource", "Выходной набор данных")
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
    node += field_guid("VendorGuid", VENDOR_COLUNION)
    node += b"\x06"
    node += input_ports + output_ports + service_in + service_out + component + layout
    return node


def _vars_out_socket_item() -> bytes:
    return (
        b"\x00\x03"
        + field_guid("Guid", PORT_VARS_OUT)
        + field_str("Name", "Variables")
        + field_str("DisplayName", "Выходные переменные")
        + b"\x01"
        + (
            s("Socket")
            + s("TBGDerivedVariablesOutputSocket")
            + b"\x00\x01"
            + (
                s("Variables")
                + b"\x00\x01"
                + field_bool("SyncThroughVariables", True)
                + b"\x01"
                + empty_list("Elements")
            )
        )
    )


def build_calc_variables_node(
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
    vars_in = tr._vars_socket_item(
        PORT_VARS_IN, "Variables", "Входные переменные", virgin=True
    )
    ctrl = tr._ctrl_vars_socket_item()
    vars_out = _vars_out_socket_item()
    input_sockets = (
        s("InputSockets")
        + b"\x00\x00\x02"
        + s("Item")
        + vars_in
        + s("Item")
        + ctrl
    )
    output_sockets = s("OutputSockets") + b"\x00\x00\x01" + s("Item") + vars_out
    engine = s("Engine") + s("TBGCalcVariables") + b"\x00\x01" + empty_list("Expressions")
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
    node += field_guid("VendorGuid", VENDOR_CALC_VARS)
    node += b"\x06"
    node += input_ports + output_ports + service_in + service_out + component + layout
    return node


def _vars_to_table_vars_in() -> bytes:
    """Variables in for Пер→табл: no Virgin, no SyncThrough (matches silver kit)."""
    vars_inner = s("Variables") + b"\x00\x00\x01" + empty_list("Elements")
    socket = (
        s("Socket")
        + s("TBGTuneVariablesSocket")
        + b"\x00\x02"
        + empty_list("Constraints")
        + vars_inner
    )
    return (
        b"\x00\x03"
        + field_guid("Guid", PORT_VARS_IN)
        + field_str("Name", "Variables")
        + field_str("DisplayName", "Входные переменные")
        + b"\x01"
        + socket
    )


def _vars_to_table_ds_out() -> bytes:
    """DataSource out without SyncThroughColumns (matches silver kit)."""
    ds_inner = s("DataSource") + b"\x00\x00\x01" + empty_list("ColumnDefs")
    socket = (
        s("Socket") + s("TBGDerivedDataSourceOutputSocket") + b"\x00\x01" + ds_inner
    )
    return (
        b"\x00\x03"
        + field_guid("Guid", PORT_DS_OUT)
        + field_str("Name", "DataSource")
        + field_str("DisplayName", "Выходной набор данных")
        + b"\x01"
        + socket
    )


def _sync_only_service_in() -> bytes:
    return list_of_items(
        "ServiceInputPorts",
        [port_item(PORT_SYNC_IN, "SynchronizationInputPort", "Порядок выполнения")],
    )


def _standard_service_out() -> bytes:
    return list_of_items(
        "ServiceOutputPorts",
        [
            port_item(PORT_SYNC_OUT, "SynchronizationOutputPort", "Порядок выполнения"),
            port_item(PORT_COMPONENT, "ComponentOutputPort", "Компонент"),
            port_item(PORT_DEPENDENT, "DependentNodeOutputPort", "Зависимые узлы"),
        ],
    )


def build_vars_to_table_node(
    node_guid: uuid.UUID,
    display_name: str,
    left: float = 160.0,
    top: float = 100.0,
) -> bytes:
    # No ControlVariables port — sample nodes only expose sync service input.
    input_ports = list_of_items(
        "InputPorts",
        [port_item(PORT_VARS_IN, "Variables", "Входные переменные")],
    )
    output_ports = list_of_items(
        "OutputPorts",
        [port_item(PORT_DS_OUT, "DataSource", "Выходной набор данных")],
    )
    service_in = _sync_only_service_in()
    service_out = _standard_service_out()
    vars_in = _vars_to_table_vars_in()
    out = _vars_to_table_ds_out()
    input_sockets = s("InputSockets") + b"\x00\x00\x01" + s("Item") + vars_in
    output_sockets = s("OutputSockets") + b"\x00\x00\x01" + s("Item") + out
    engine = s("Engine") + s("TBGVariablesToDataEngine") + b"\x00\x00"
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
    node += field_guid("VendorGuid", VENDOR_VARS_TO_TABLE)
    node += b"\x06"
    node += input_ports + output_ports + service_in + service_out + component + layout
    return node


def build_table_to_vars_node(
    node_guid: uuid.UUID,
    display_name: str,
    left: float = 160.0,
    top: float = 100.0,
) -> bytes:
    # No ControlVariables — matches Community/sample table_to_vars.
    input_ports = list_of_items(
        "InputPorts",
        [port_item(PORT_DS_IN, "DataSource", "Входной источник данных")],
    )
    output_ports = list_of_items(
        "OutputPorts",
        [port_item(PORT_VARS_OUT, "Variables", "Выходные переменные")],
    )
    service_in = _sync_only_service_in()
    service_out = _standard_service_out()
    ds_in = tr._ds_in_socket_item(PORT_DS_IN, "DataSource", "Входной источник данных")
    vars_out = _vars_out_socket_item()
    input_sockets = s("InputSockets") + b"\x00\x00\x01" + s("Item") + ds_in
    output_sockets = s("OutputSockets") + b"\x00\x00\x01" + s("Item") + vars_out
    engine = s("Engine") + s("TBGCustomModelComponentEngine") + b"\x00\x00"
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
    node += field_guid("VendorGuid", VENDOR_TABLE_TO_VARS)
    node += b"\x06"
    node += input_ports + output_ports + service_in + service_out + component + layout
    return node


def build_join_vars_node(
    node_guid: uuid.UUID,
    display_name: str,
    left: float = 160.0,
    top: float = 100.0,
) -> bytes:
    # No ControlVariables — matches sample join_variables.
    input_ports = list_of_items(
        "InputPorts",
        [
            port_item(PORT_VARS_IN, "Variables", "Входные переменные"),
            port_item(PORT_JOINED_VARS, "JoinedVariables", "Присоединяемые переменные"),
        ],
    )
    output_ports = list_of_items(
        "OutputPorts",
        [port_item(PORT_VARS_OUT, "Variables", "Выходные переменные")],
    )
    service_in = _sync_only_service_in()
    service_out = _standard_service_out()
    v1 = tr._vars_socket_item(PORT_VARS_IN, "Variables", "Входные переменные", True)
    v2 = tr._vars_socket_item(
        PORT_JOINED_VARS, "JoinedVariables", "Присоединяемые переменные", True
    )
    out = _vars_out_socket_item()
    input_sockets = (
        s("InputSockets") + b"\x00\x00\x02" + s("Item") + v1 + s("Item") + v2
    )
    output_sockets = s("OutputSockets") + b"\x00\x00\x01" + s("Item") + out
    engine = s("Engine") + s("TBGCustomModelComponentEngine") + b"\x00\x00"
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
    node += field_guid("VendorGuid", VENDOR_JOIN_VARS)
    node += b"\x06"
    node += input_ports + output_ports + service_in + service_out + component + layout
    return node


def _export_shell(
    node_guid: uuid.UUID,
    display_name: str,
    vendor: uuid.UUID,
    engine: bytes,
    left: float,
    top: float,
) -> bytes:
    input_ports = list_of_items(
        "InputPorts",
        [
            port_item(PORT_CONNECTION, "Connection", "Подключение"),
            port_item(PORT_DS_IN, "DataSource", "Источник данных"),
            port_item(PORT_CONTROL_VARS, "ControlVariables", "Управляющие переменные"),
        ],
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
    conn = (
        b"\x00\x03"
        + field_guid("Guid", PORT_CONNECTION)
        + field_str("Name", "Connection")
        + field_str("DisplayName", "Подключение")
        + b"\x01"
        + (
            s("Socket")
            + s("TBGConnectionInputSocket")
            + b"\x01"
            + field_bool("Virgin", True)
            + b"\x01"
            + empty_list("Constraints")
        )
    )
    ds = tr._ds_in_socket_item(PORT_DS_IN, "DataSource", "Источник данных", virgin=True)
    ctrl = tr._ctrl_vars_socket_item()
    input_sockets = (
        s("InputSockets")
        + b"\x00\x00\x03"
        + s("Item")
        + conn
        + s("Item")
        + ds
        + s("Item")
        + ctrl
    )
    output_sockets = s("OutputSockets") + b"\x00\x00\x00"
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
    node += field_guid("VendorGuid", vendor)
    node += b"\x06"
    node += input_ports + output_ports + service_in + service_out + component + layout
    return node


def build_export_text_node(
    node_guid: uuid.UUID,
    display_name: str,
    left: float = 160.0,
    top: float = 100.0,
    file_name: str = "export.csv",
) -> bytes:
    # attrs: FileName, CodePage(int32=65001), LineEnding, CaptionType, DecimalSeparator, DelimiterChar
    # From sample: CodePage type \x05 = int32
    def field_i32(name: str, value: int) -> bytes:
        import struct

        return s(name) + b"\x05" + struct.pack("<i", value)

    engine = (
        s("Engine")
        + s("TBGExportTextFile")
        + b"\x06"
        + field_str("FileName", file_name)
        + field_i32("CodePage", 65001)
        + field_enum16("LineEnding", 1)  # leCRLF
        + field_enum16("CaptionType", 1)  # ctUseColumnNames
        + field_str("DecimalSeparator", ".")
        + field_str("DelimiterChar", ",")
        + b"\x00"
    )
    return _export_shell(
        node_guid, display_name, VENDOR_EXPORT_TEXT, engine, left, top
    )


def build_export_excel_node(
    node_guid: uuid.UUID,
    display_name: str,
    left: float = 160.0,
    top: float = 100.0,
    file_name: str = "export.xlsx",
    sheet_name: str = "Лист1",
) -> bytes:
    engine = (
        s("Engine")
        + s("TBGExportExcelFile")
        + b"\x02"
        + field_str("FileName", file_name)
        + field_str("SheetName", sheet_name)
        + b"\x00"
    )
    return _export_shell(
        node_guid, display_name, VENDOR_EXPORT_EXCEL, engine, left, top
    )
