"""Parse Loginom BGB enough to extract/rebuild a simple ImportNative node."""
from __future__ import annotations

import struct
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

MAGIC = b"BGB\xc3"
XSI = "{http://www.w3.org/2001/XMLSchema-instance}type"

# Well-known port GUIDs (stable across ImportNative instances in demo)
PORT_CONNECTION = uuid.UUID("78ce58f4-e818-3754-bc2e-6af868677420")
PORT_CONTROL_VARS = uuid.UUID("455b65c3-0587-3a9c-b47e-9b0d285bff3c")
PORT_DATASET = uuid.UUID("58f7e6c3-511e-39d7-8853-036e0a1a7612")
PORT_SYNC_IN = uuid.UUID("00bd0b43-e4b5-3ac1-b95a-ac1bee14f858")
PORT_SYNC_OUT = uuid.UUID("ca080ff0-2342-32b0-b480-586f9747bace")
PORT_COMPONENT = uuid.UUID("e98be5ba-c627-3a55-af82-a399dd13c73b")
PORT_DEPENDENT = uuid.UUID("58922a98-d1ea-36de-9099-3ce26fe160e2")

VENDOR_IMPORT_NATIVE = uuid.UUID("35a6e054-ee0c-42f6-bda6-af10b57a36aa")
VENDOR_IMPORT_TEXT = uuid.UUID("dd767700-1321-4c70-ab92-2acfc4db4492")
VENDOR_IMPORT_EXCEL = uuid.UUID("b391583d-e11b-4ee3-96ce-1438f9d3df5d")


def encode_bgb_len(n: int) -> bytes:
    """Loginom BGB string/list length prefix.

    Observed in real packages:
      - n < 64  → one byte ``n``
      - n >= 64 → two bytes ``0x80|(n&0x7F)``, ``n>>7``
        (e.g. 68→``C4 00``, 72→``C8 00``, 126→``FE 00``)

    Writing a single byte in 64..127 (e.g. 72=``H``) makes the reader treat the
    next data byte as a high length byte → stream desync / «Атрибут Name…».
    """
    if n < 0:
        raise ValueError(n)
    if n < 64:
        return bytes([n])
    if n >= 16384:
        raise ValueError(f"BGB length too large ({n} >= 16384)")
    return bytes([0x80 | (n & 0x7F), (n >> 7) & 0x7F])


def s(text: str) -> bytes:
    b = text.encode("utf-8")
    return encode_bgb_len(len(b)) + b


def field_guid(name: str, g: uuid.UUID) -> bytes:
    return s(name) + b"\x0b" + g.bytes_le


def field_str(name: str, value: str) -> bytes:
    return s(name) + b"\x07" + s(value)


def field_bool(name: str, value: bool) -> bytes:
    return s(name) + b"\x01" + (b"\x01" if value else b"\x00")


def field_float64(name: str, value: float) -> bytes:
    return s(name) + b"\x03" + struct.pack("<d", value)


def field_int32(name: str, value: int) -> bytes:
    return s(name) + b"\x05" + struct.pack("<i", value)


def field_char(name: str, value: str) -> bytes:
    if len(value.encode("latin-1")) != 1:
        raise ValueError(f"char field must be 1 byte: {value!r}")
    return s(name) + b"\x08" + value.encode("latin-1")


def root_header(root_name: str) -> bytes:
    return MAGIC + struct.pack("<I", 1) + b"\x01" + s(root_name)


def empty_list(name: str) -> bytes:
    return s(name) + b"\x00\x00" + encode_bgb_len(0)


def list_of_items(name: str, items: list[bytes]) -> bytes:
    """Named list whose elements are anonymous objects tagged 'Item'."""
    body = b"".join(s("Item") + it for it in items)
    return s(name) + b"\x00\x00" + encode_bgb_len(len(items)) + body


def port_item(guid: uuid.UUID, name: str | None, display_name: str) -> bytes:
    """Port declaration: attrs Guid, [Name], DisplayName — no children."""
    attrs = field_guid("Guid", guid)
    n = 2
    if name is not None:
        attrs += field_str("Name", name)
        n = 3
    attrs += field_str("DisplayName", display_name)
    return b"\x00" + bytes([n]) + attrs + b"\x00"  # trailing 00 = no children


def build_import_native_node(
    node_guid: uuid.UUID,
    display_name: str,
    file_name: str,
    left: float = 120.0,
    top: float = 80.0,
) -> bytes:
    """Build one WorkFlow Nodes/Item for TBGImportNative (virgin sockets)."""

    # --- ports (declarations only) ---
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

    # --- sockets ---
    # Typed object: classname + attr_count + attrs + child_count + children (no leading 0x00)
    conn_socket = (
        s("Socket")
        + s("TBGConnectionInputSocket")
        + b"\x01"
        + field_bool("Virgin", True)
        + b"\x01"
        + empty_list("Constraints")
    )
    conn_sock_item = (
        b"\x00\x03"
        + field_guid("Guid", PORT_CONNECTION)
        + field_str("Name", "Connection")
        + field_str("DisplayName", "Подключение")
        + b"\x01"
        + conn_socket
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
    ctrl_sock_item = (
        b"\x00\x03"
        + field_guid("Guid", PORT_CONTROL_VARS)
        + field_str("Name", "ControlVariables")
        + field_str("DisplayName", "Управляющие переменные")
        + b"\x01"
        + ctrl_socket
    )

    ds_inner = (
        s("DataSource")
        + b"\x00\x01"
        + field_bool("SyncThroughColumns", True)
        + b"\x01"
        + empty_list("ColumnDefs")
    )
    ds_socket = (
        s("Socket")
        + s("TBGDataSetOutputSocket")
        + b"\x00"  # 0 attrs
        + b"\x01"  # 1 child
        + ds_inner
    )
    ds_sock_item = (
        b"\x00\x03"
        + field_guid("Guid", PORT_DATASET)
        + field_str("Name", "DataSet")
        + field_str("DisplayName", "Набор данных")
        + b"\x01"
        + ds_socket
    )

    input_sockets = (
        s("InputSockets")
        + b"\x00\x00\x02"
        + s("Item")
        + conn_sock_item
        + s("Item")
        + ctrl_sock_item
    )
    output_sockets = s("OutputSockets") + b"\x00\x00\x01" + s("Item") + ds_sock_item

    # Engine: 1 attr FileName, 0 children
    engine = (
        s("Engine")
        + s("TBGImportNative")
        + b"\x01"
        + field_str("FileName", file_name)
        + b"\x00"
    )

    component = (
        s("Component")
        + b"\x00\x00\x03"
        + input_sockets
        + output_sockets
        + engine
    )

    layout = (
        s("Position")
        + b"\x00\x02"
        + field_float64("Left", left)
        + field_float64("Top", top)
        + b"\x00"
    )

    # Node Item: 3 attrs + children ports/component/layout
    node = b"\x00\x03"
    node += field_guid("Guid", node_guid)
    node += field_str("DisplayName", display_name)
    node += field_guid("VendorGuid", VENDOR_IMPORT_NATIVE)
    node += b"\x06"  # 6 children
    node += input_ports
    node += output_ports
    node += service_in
    node += service_out
    node += component
    node += layout
    return node


def build_import_text_file_node(
    node_guid: uuid.UUID,
    display_name: str,
    file_name: str,
    left: float = 160.0,
    top: float = 100.0,
    code_page: int = 65001,
    decimal_separator: str = ".",
    date_format: str = "dd.MM.yyyy",
    date_separator: str = ".",
    columns_required: bool = False,
) -> bytes:
    """Build WorkFlow Nodes/Item for TBGImportTextFile (Текстовый файл)."""
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

    conn_socket = (
        s("Socket")
        + s("TBGConnectionInputSocket")
        + b"\x01"
        + field_bool("Virgin", True)
        + b"\x01"
        + empty_list("Constraints")
    )
    conn_sock_item = (
        b"\x00\x03"
        + field_guid("Guid", PORT_CONNECTION)
        + field_str("Name", "Connection")
        + field_str("DisplayName", "Подключение")
        + b"\x01"
        + conn_socket
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
    ctrl_sock_item = (
        b"\x00\x03"
        + field_guid("Guid", PORT_CONTROL_VARS)
        + field_str("Name", "ControlVariables")
        + field_str("DisplayName", "Управляющие переменные")
        + b"\x01"
        + ctrl_socket
    )
    ds_inner = (
        s("DataSource")
        + b"\x00\x01"
        + field_bool("SyncThroughColumns", True)
        + b"\x01"
        + empty_list("ColumnDefs")
    )
    ds_socket = s("Socket") + s("TBGDataSetOutputSocket") + b"\x00\x01" + ds_inner
    ds_sock_item = (
        b"\x00\x03"
        + field_guid("Guid", PORT_DATASET)
        + field_str("Name", "DataSet")
        + field_str("DisplayName", "Набор данных")
        + b"\x01"
        + ds_socket
    )
    input_sockets = (
        s("InputSockets")
        + b"\x00\x00\x02"
        + s("Item")
        + conn_sock_item
        + s("Item")
        + ctrl_sock_item
    )
    output_sockets = s("OutputSockets") + b"\x00\x00\x01" + s("Item") + ds_sock_item

    engine = (
        s("Engine")
        + s("TBGImportTextFile")
        + b"\x06"
        + field_str("FileName", file_name)
        + field_int32("CodePage", code_page)
        + field_char("DecimalSeparator", decimal_separator)
        + field_str("DateFormat", date_format)
        + field_char("DateSeparator", date_separator)
        + field_bool("ColumnsRequired", columns_required)
        + b"\x01"
        + empty_list("ColumnDefs")
    )
    component = (
        s("Component") + b"\x00\x00\x03" + input_sockets + output_sockets + engine
    )
    # Modern packages use Position; Layout also accepted — use Position for text import.
    position = (
        s("Position")
        + b"\x00\x02"
        + field_float64("Left", left)
        + field_float64("Top", top)
        + b"\x00"
    )
    node = b"\x00\x04"
    node += field_guid("Guid", node_guid)
    node += field_str("DisplayName", display_name)
    node += field_guid("VendorGuid", VENDOR_IMPORT_TEXT)
    node += field_bool("GenerateNodeTitle", False)
    node += b"\x06"
    node += input_ports
    node += output_ports
    node += service_in
    node += service_out
    node += component
    node += position
    return node


def build_import_excel_node(
    node_guid: uuid.UUID,
    display_name: str,
    file_name: str,
    sheet_number: int = 1,
    left: float = 160.0,
    top: float = 100.0,
) -> bytes:
    """Build WorkFlow Nodes/Item for TBGImportExcelFileEngine (Excel файл)."""
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

    conn_socket = (
        s("Socket")
        + s("TBGConnectionInputSocket")
        + b"\x01"
        + field_bool("Virgin", True)
        + b"\x01"
        + empty_list("Constraints")
    )
    conn_sock_item = (
        b"\x00\x03"
        + field_guid("Guid", PORT_CONNECTION)
        + field_str("Name", "Connection")
        + field_str("DisplayName", "Подключение")
        + b"\x01"
        + conn_socket
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
    ctrl_sock_item = (
        b"\x00\x03"
        + field_guid("Guid", PORT_CONTROL_VARS)
        + field_str("Name", "ControlVariables")
        + field_str("DisplayName", "Управляющие переменные")
        + b"\x01"
        + ctrl_socket
    )
    ds_inner = (
        s("DataSource")
        + b"\x00\x01"
        + field_bool("SyncThroughColumns", True)
        + b"\x01"
        + empty_list("ColumnDefs")
    )
    ds_socket = s("Socket") + s("TBGDataSetOutputSocket") + b"\x00\x01" + ds_inner
    ds_sock_item = (
        b"\x00\x03"
        + field_guid("Guid", PORT_DATASET)
        + field_str("Name", "DataSet")
        + field_str("DisplayName", "Набор данных")
        + b"\x01"
        + ds_socket
    )
    input_sockets = (
        s("InputSockets")
        + b"\x00\x00\x02"
        + s("Item")
        + conn_sock_item
        + s("Item")
        + ctrl_sock_item
    )
    output_sockets = s("OutputSockets") + b"\x00\x00\x01" + s("Item") + ds_sock_item

    engine = (
        s("Engine")
        + s("TBGImportExcelFileEngine")
        + b"\x02"
        + field_str("FileName", file_name)
        + field_int32("SheetNumber", sheet_number)
        + b"\x01"
        + empty_list("ColumnDefs")
    )
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
    node += field_guid("VendorGuid", VENDOR_IMPORT_EXCEL)
    node += b"\x06"
    node += input_ports
    node += output_ports
    node += service_in
    node += service_out
    node += component
    node += layout
    return node


def build_link_item(
    link_guid: uuid.UUID,
    source_node: uuid.UUID,
    source_port: uuid.UUID,
    target_node: uuid.UUID,
    target_port: uuid.UUID,
) -> bytes:
    """Workflow data-link Item body (without Item tag)."""
    source = (
        s("SourcePort")
        + b"\x00\x02"
        + field_guid("NodeGuid", source_node)
        + field_guid("PortGuid", source_port)
        + b"\x00"
    )
    target = (
        s("TargetPort")
        + b"\x00\x02"
        + field_guid("NodeGuid", target_node)
        + field_guid("PortGuid", target_port)
        + b"\x00"
    )
    return (
        b"\x00\x01"
        + field_guid("Guid", link_guid)
        + b"\x02"
        + source
        + target
    )


def build_unit_with_import_nodes(
    nodes: list[bytes],
    links: list[bytes] | None = None,
    view_nodes: list[bytes] | None = None,
    view_links: list[bytes] | None = None,
) -> bytes:
    wf = b"\x00\x05"
    wf += list_of_items("Nodes", nodes)
    wf += list_of_items("Links", links) if links else empty_list("Links")
    wf += empty_list("ServiceNodes")
    wf += empty_list("ServiceLinks")
    wf += empty_list("Annotations")
    workflow = s("WorkFlow") + s("TBGPackageModelWorkFlow") + wf

    # ModelViews is a list-shaped object (00 00 count), not attr-count (00 N).
    # Wrong encoding yields: «Атрибут Nodes/Links не существует».
    mv_nodes = (
        list_of_items("Nodes", view_nodes)
        if view_nodes
        else empty_list("Nodes")
    )
    mv_links = (
        list_of_items("Links", view_links)
        if view_links
        else empty_list("Links")
    )
    model_views = s("ModelViews") + b"\x00\x00\x02" + mv_nodes + mv_links

    body = b"\x00\x00\x02" + workflow + model_views
    return root_header("Unit") + body


def extract_first_node_item_blob(unit_bin: bytes) -> bytes:
    """Extract first Nodes/Item object bytes from a demo Unit.bin (for comparison)."""
    # Find Nodes\x00\x00\x0c\x04Item or similar
    marker = b"\x05Nodes\x00\x00"
    i = unit_bin.find(marker)
    if i < 0:
        raise RuntimeError("Nodes not found")
    i += len(marker)
    count = unit_bin[i]
    i += 1
    assert unit_bin[i : i + 1 + 4] == b"\x04Item" or unit_bin[i] == 4
    # skip 'Item' tag
    namelen = unit_bin[i]
    i += 1 + namelen  # now at start of Item object body
    start = i
    # Heuristic: next sibling also starts with \x04Item after we parse — use recursive skipper
    end = skip_object(unit_bin, start)
    return unit_bin[start:end]


def skip_object(data: bytes, i: int) -> int:
    """Skip one BGB object starting at attr-header (\\x00 attrCount ...). Returns index after object."""
    assert data[i] == 0, f"expected 0 at {i}, got {data[i]}"
    i += 1
    attr_count = data[i]
    i += 1
    for _ in range(attr_count):
        i = skip_field(data, i)
    # After attrs: either child_count byte then named children, or end
    if i >= len(data):
        return i
    # Could be child count without leading 00, or 00 ending
    # Pattern varies: some objects end after attrs with nothing;
    # typed/named children: count then (name + object|list|typed)*
    # Detect: if next is a length-prefixed known child name...
    # Our node format uses explicit child count after attrs.
    child_count = data[i]
    # Ambiguity: child_count could be start of next Item's \x00.
    # If child_count == 0 and next is \x04Item, this object had no children and \x00 was wrong.
    # Convention from PackageInfo: attrs then trailing \x00 meaning end.
    # Convention from node: attrs then \\x06 then 6 children (no trailing 00 before children).
    # Convention from Layout: attrs then trailing \\x00.
    #
    # Rule used here: if byte looks like small child count (1..20) AND following is a string
    # name of a known structural field, treat as children; elif byte==0, consume end marker.
    if child_count == 0:
        return i + 1
    if 1 <= child_count <= 32 and i + 1 < len(data):
        # peek: is next a string?
        namelen = data[i + 1]
        if 1 <= namelen <= 64 and i + 2 + namelen <= len(data):
            i += 1
            for _ in range(child_count):
                i = skip_named_child(data, i)
            return i
    # fallback: trailing 0 already handled; if not, assume no children
    return i


def skip_field(data: bytes, i: int) -> int:
    namelen = data[i]
    i += 1 + namelen
    typ = data[i]
    i += 1
    if typ == 0x07:  # string
        n = data[i]
        return i + 1 + n
    if typ == 0x0B:  # guid
        return i + 16
    if typ == 0x01:  # bool
        return i + 1
    if typ == 0x03:  # float64
        return i + 8
    if typ == 0x02:  # int32?
        return i + 4
    raise ValueError(f"unknown field type {typ:#x} at {i-1}")


def skip_named_child(data: bytes, i: int) -> int:
    namelen = data[i]
    i += 1
    name = data[i : i + namelen]
    i += namelen
    # list: \x00\x00 count ...
    if i + 2 <= len(data) and data[i] == 0 and data[i + 1] == 0:
        i += 2
        count = data[i]
        i += 1
        for _ in range(count):
            # element tagged with name (usually Item)
            elen = data[i]
            i += 1 + elen
            i = skip_object(data, i)
        return i
    # typed object: classname string then object body
    # OR plain object starting with \x00
    if data[i] == 0:
        return skip_object(data, i)
    # classname
    clen = data[i]
    if 1 <= clen <= 80:
        i += 1 + clen
        return skip_object(data, i)
    raise ValueError(f"cannot skip child {name!r} at {i}")


def compare_with_demo() -> None:
    demo = Path(__file__).resolve().parent.parent.parent / "_lgp_inspect" / "extracted" / "Unit_0" / "Unit.bin"
    if not demo.is_file():
        print("SKIP compare_with_demo: demo Unit.bin not found")
        return
    blob = extract_first_node_item_blob(demo.read_bytes())
    ours = build_import_native_node(
        uuid.UUID("aa558a09-fd3f-4d1f-8042-20d8a28e7d51"),
        "Загрузка продаж",
        "Demo Data/Sales.lgd",
        left=122.0,
        top=72.0,
    )
    print("demo first node len", len(blob))
    print("ours node len", len(ours))
    print("match", blob == ours)
    # find first difference
    for i, (a, b) in enumerate(zip(blob, ours)):
        if a != b:
            print(f"diff at {i}: demo {a:02x} ours {b:02x}")
            print("demo context", blob[max(0,i-20):i+40].hex())
            print("ours context", ours[max(0,i-20):i+40].hex())
            break
    else:
        if len(blob) != len(ours):
            print("length differs", len(blob), len(ours))
            if len(ours) < len(blob):
                print("demo tail", blob[len(ours) : len(ours) + 40].hex())
            else:
                print("ours tail", ours[len(blob) : len(blob) + 40].hex())


if __name__ == "__main__":
    compare_with_demo()
