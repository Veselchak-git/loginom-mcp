"""G6 palette nodes: Control / Research / Data Mining / Data Tree / Integration.

Built from exact virgin node blobs extracted from Cursor_G6.lgp
(Guid / DisplayName / Position patched per instance).
"""
from __future__ import annotations

import json
import struct
import uuid
from pathlib import Path

BLOB_DIR = Path(__file__).resolve().parent / "g6_blobs"
# encode_bgb_len lives in sibling module
import sys

_VENDOR = Path(__file__).resolve().parent
if str(_VENDOR) not in sys.path:
    sys.path.insert(0, str(_VENDOR))

_REGISTRY = json.loads((BLOB_DIR / "registry.json").read_text(encoding="utf-8"))
REGISTRY: dict[str, dict] = {r["key"]: r for r in _REGISTRY}


def s(text: str) -> bytes:
    # Must match Loginom BGB length encoding (>=64 → two bytes).
    from bgb_import_node import encode_bgb_len

    b = text.encode("utf-8")
    return encode_bgb_len(len(b)) + b


def _read_bgb_len(data: bytes, i: int) -> tuple[int, int]:
    """Return (length, index_after_length_prefix)."""
    b0 = data[i]
    if b0 < 64:
        return b0, i + 1
    return (b0 & 0x7F) | (data[i + 1] << 7), i + 2


def field_guid(name: str, g: uuid.UUID) -> bytes:
    return s(name) + b"\x0b" + g.bytes_le


def field_str(name: str, value: str) -> bytes:
    return s(name) + b"\x07" + s(value)


def field_float64(name: str, value: float) -> bytes:
    return s(name) + b"\x03" + struct.pack("<d", value)


def _skip_field(data: bytes, i: int) -> int:
    namelen = data[i]
    i += 1 + namelen
    typ = data[i]
    i += 1
    if typ == 0x0B:  # guid
        return i + 16
    if typ == 0x07:  # string
        ln, i = _read_bgb_len(data, i)
        return i + ln
    if typ == 0x01:  # bool
        return i + 1
    if typ == 0x03:  # float64
        return i + 8
    if typ == 0x05:  # int32
        return i + 4
    if typ == 0x09:  # enum (1 or 2 bytes — peek)
        # Most engine enums in samples are 1-byte when next is nested/attr;
        # header attrs use bool/guid/string only for our G6 nodes.
        return i + 2
    if typ == 0x08:  # char
        return i + 1
    raise ValueError(f"unknown field type {typ:#x} at {i}")


def patch_node_blob(
    blob: bytes,
    node_guid: uuid.UUID,
    display_name: str,
    left: float,
    top: float,
) -> bytes:
    """Replace Guid, DisplayName and Position coordinates; keep rest intact."""
    assert blob[0] == 0
    attr_count = blob[1]
    i = 2
    fields: list[tuple[str, bytes]] = []
    for _ in range(attr_count):
        name_start = i
        namelen = blob[i]
        name = blob[i + 1 : i + 1 + namelen].decode("utf-8")
        i = _skip_field(blob, i)
        fields.append((name, blob[name_start:i]))

    new_attrs = bytearray()
    new_attrs += b"\x00" + bytes([attr_count])
    for name, raw in fields:
        if name == "Guid":
            new_attrs += field_guid("Guid", node_guid)
        elif name == "DisplayName":
            new_attrs += field_str("DisplayName", display_name)
        else:
            new_attrs += raw

    # body after attrs through start of Position name (exclude len byte)
    # Original: attrs end at i, then child_count + children..., Position at end
    rest = blob[i:]
    pos = rest.rfind(b"Position")
    if pos < 0:
        raise ValueError("Position not found in blob")
    # include length byte before Position
    before_pos = rest[: pos - 1]
    new_pos = (
        s("Position")
        + b"\x00\x02"
        + field_float64("Left", left)
        + field_float64("Top", top)
        + b"\x00"
    )
    return bytes(new_attrs) + before_pos + new_pos


def build_g6_node(
    key: str,
    node_guid: uuid.UUID,
    display_name: str,
    left: float = 160.0,
    top: float = 100.0,
) -> bytes:
    path = BLOB_DIR / f"{key}.bgb"
    if not path.exists():
        raise KeyError(key)
    return patch_node_blob(path.read_bytes(), node_guid, display_name, left, top)


def make_builder(key: str):
    def _builder(g, n, left, top, file_name=None):
        return build_g6_node(key, g, n, left, top)

    return _builder
