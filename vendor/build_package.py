"""Build a minimal Loginom .lgp package (BGB binaries + XML)."""
from __future__ import annotations

import struct
import uuid
import zipfile
from pathlib import Path

MAGIC = b"BGB\xc3"
_VENDOR = Path(__file__).resolve().parent
OUT_DIR = _VENDOR.parent / ".staging" / "build_package"
PACKAGE_NAME = "Cursor_MCP_Demo"
DISPLAY_MODULE = "Модуль1"


def s(text: str) -> bytes:
    b = text.encode("utf-8")
    if len(b) > 255:
        raise ValueError(f"string too long: {text!r}")
    return bytes([len(b)]) + b


def root_header(root_name: str) -> bytes:
    return MAGIC + struct.pack("<I", 1) + b"\x01" + s(root_name)


def field_guid(name: str, g: uuid.UUID) -> bytes:
    return s(name) + b"\x0b" + g.bytes_le


def field_str(name: str, value: str) -> bytes:
    return s(name) + b"\x07" + s(value)


def field_bool(name: str, value: bool) -> bytes:
    return s(name) + b"\x01" + (b"\x01" if value else b"\x00")


def build_package_info(guid: uuid.UUID, name: str) -> bytes:
    body = b"\x00\x05"
    body += field_guid("Guid", guid)
    body += field_str("Name", name)
    body += field_str("ApplicationVersion", "7.4.2")
    body += field_bool("UseBasePackageFileStorage", True)
    body += field_str("Locale", "ru_RU")
    body += b"\x00"
    return root_header("PackageInfo") + body


def build_info(guid: uuid.UUID, name: str, display_name: str) -> bytes:
    body = b"\x00\x03"
    body += field_guid("Guid", guid)
    body += field_str("Name", name)
    body += field_str("DisplayName", display_name)
    body += b"\x00"
    return root_header("Info") + body


def build_references() -> bytes:
    return root_header("References") + b"\x00\x00\x00"


def build_variables() -> bytes:
    return root_header("Variables") + b"\x00\x00\x01" + s("Elements") + b"\x00\x00\x00"


def build_reports_empty() -> bytes:
    # Match Loginom 7.4 virgin packages: empty Reports root (no ModelReportGroups).
    return root_header("Reports") + b"\x00\x00\x00"


def file_ref(bin_path: str, xml_path: str) -> bytes:
    # object with 2 string fields BinFile, XMLFile
    return (
        b"\x00\x02"
        + field_str("BinFile", bin_path)
        + field_str("XMLFile", xml_path)
        + b"\x00"
    )


def build_package_index() -> bytes:
    # PackageIndex: \x00\x00 + 5 named children
    body = b"\x00\x00\x05"
    for name, bpath, xpath in [
        ("PackageInfo", r"\PackageInfo.bin", r"\PackageInfo.xml"),
        ("References", r"\References.bin", r"\References.xml"),
        ("Reports", r"\Reports.bin", r"\Reports.xml"),
        ("Variables", r"\Variables.bin", r"\Variables.xml"),
    ]:
        body += s(name) + file_ref(bpath, xpath)

    # Units -> list[1] of Item(attr BasePath, children Info+Unit)
    item = b"\x00\x01" + field_str("BasePath", r"\Unit_0")
    item += b"\x02"
    item += s("Info") + file_ref(r"\Unit_0\Info.bin", r"\Unit_0\Info.xml")
    item += s("Unit") + file_ref(r"\Unit_0\Unit.bin", r"\Unit_0\Unit.xml")

    body += s("Units") + b"\x00\x00\x01" + s("Item") + item
    return root_header("PackageIndex") + body


def build_empty_unit() -> bytes:
    """Empty Unit = WorkFlow (5 empty lists) + ModelViews (Nodes/Links empty)."""

    def empty_list_child(name: str) -> bytes:
        return s(name) + b"\x00\x00\x00"

    wf = b"\x00\x05"
    for n in ("Nodes", "Links", "ServiceNodes", "ServiceLinks", "Annotations"):
        wf += empty_list_child(n)
    workflow = s("WorkFlow") + s("TBGPackageModelWorkFlow") + wf

    mv = b"\x00\x02"
    mv += empty_list_child("Nodes")
    mv += empty_list_child("Links")
    model_views = s("ModelViews") + mv

    body = b"\x00\x00\x02" + workflow + model_views
    return root_header("Unit") + body

def write_xmls(out: Path, pkg_guid: uuid.UUID, unit_guid: uuid.UUID, name: str) -> None:
    (out / "PackageInfo.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<PackageInfo Guid="{pkg_guid}" Name="{name}" '
        f'ApplicationVersion="7.4.2" '
        f'UseBasePackageFileStorage="true" Locale="ru_RU"/>\n',
        encoding="utf-8",
    )
    (out / "PackageIndex.xml").write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<PackageIndex>
\t<PackageInfo BinFile="\\PackageInfo.bin" XMLFile="\\PackageInfo.xml"/>
\t<References BinFile="\\References.bin" XMLFile="\\References.xml"/>
\t<Reports BinFile="\\Reports.bin" XMLFile="\\Reports.xml"/>
\t<Variables BinFile="\\Variables.bin" XMLFile="\\Variables.xml"/>
\t<Units>
\t\t<Item BasePath="\\Unit_0">
\t\t\t<Info BinFile="\\Unit_0\\Info.bin" XMLFile="\\Unit_0\\Info.xml"/>
\t\t\t<Unit BinFile="\\Unit_0\\Unit.bin" XMLFile="\\Unit_0\\Unit.xml"/>
\t\t</Item>
\t</Units>
</PackageIndex>
""",
        encoding="utf-8",
    )
    (out / "References.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<References/>\n', encoding="utf-8"
    )
    (out / "Variables.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<Variables>\n\t<Elements/>\n</Variables>\n',
        encoding="utf-8",
    )
    (out / "Reports.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<Reports/>\n',
        encoding="utf-8",
    )
    unit0 = out / "Unit_0"
    unit0.mkdir(parents=True, exist_ok=True)
    (unit0 / "Info.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<Info Guid="{unit_guid}" Name="Unit1" DisplayName="{DISPLAY_MODULE}"/>\n',
        encoding="utf-8",
    )
    (unit0 / "Unit.xml").write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<Unit xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
\t<WorkFlow xsi:type="TBGPackageModelWorkFlow">
\t\t<Nodes/>
\t\t<Links/>
\t\t<ServiceNodes/>
\t\t<ServiceLinks/>
\t\t<Annotations/>
\t</WorkFlow>
\t<ModelViews>
\t\t<Nodes/>
\t\t<Links/>
\t</ModelViews>
</Unit>
""",
        encoding="utf-8",
    )


def pack_lgp(src: Path, dest: Path) -> None:
    with zipfile.ZipFile(dest, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for f in sorted(src.rglob("*")):
            if f.is_file():
                zf.write(f, f.relative_to(src).as_posix().replace("/", "\\") if False else f.relative_to(src).as_posix())
                # Loginom sample used backslash paths inside zip entry names?
    # Re-pack with backslash names like original
    with zipfile.ZipFile(dest, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        mapping = {
            "PackageIndex.bin": "PackageIndex.bin",
            "PackageIndex.xml": "PackageIndex.xml",
            "PackageInfo.bin": "PackageInfo.bin",
            "PackageInfo.xml": "PackageInfo.xml",
            "References.bin": "References.bin",
            "References.xml": "References.xml",
            "Reports.bin": "Reports.bin",
            "Reports.xml": "Reports.xml",
            "Variables.bin": "Variables.bin",
            "Variables.xml": "Variables.xml",
            "Unit_0/Info.bin": "Unit_0/Info.bin",
            "Unit_0/Info.xml": "Unit_0/Info.xml",
            "Unit_0/Unit.bin": "Unit_0/Unit.bin",
            "Unit_0/Unit.xml": "Unit_0/Unit.xml",
        }
        for rel in mapping:
            zf.write(src / rel, rel.replace("/", "\\") if False else rel)


def verify_against_demo() -> None:
    demo = _VENDOR.parent.parent / "_lgp_inspect" / "extracted"
    if not demo.is_dir():
        print("SKIP verify_against_demo: no local _lgp_inspect/extracted")
        return
    assert build_references() == (demo / "References.bin").read_bytes()
    assert build_variables() == (demo / "Variables.bin").read_bytes()
    assert build_info(
        uuid.UUID("27cb94a9-f6e9-35ff-80b7-bc7d01ba6aa7"), "Unit1", "Модуль1"
    ) == (demo / "Unit_0" / "Info.bin").read_bytes()
    assert build_package_info(
        uuid.UUID("08e48178-28b4-4768-a705-8690fd87d98f"),
        "День_2___Демо_интерфейса",
    ) == (demo / "PackageInfo.bin").read_bytes()
    idx = build_package_index()
    print("PackageIndex match", idx == (demo / "PackageIndex.bin").read_bytes())
    if idx != (demo / "PackageIndex.bin").read_bytes():
        print("ours len", len(idx), "orig", len((demo / "PackageIndex.bin").read_bytes()))
        print("ours", idx.hex())
        print("orig", (demo / "PackageIndex.bin").read_bytes().hex())
    reports = build_reports_empty()
    print("empty reports", reports.hex())


def main() -> None:
    verify_against_demo()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    staging = OUT_DIR / "staging"
    if staging.exists():
        import shutil

        shutil.rmtree(staging)
    staging.mkdir(parents=True)
    (staging / "Unit_0").mkdir()

    pkg_guid = uuid.uuid4()
    unit_guid = uuid.uuid4()

    (staging / "PackageInfo.bin").write_bytes(build_package_info(pkg_guid, PACKAGE_NAME))
    (staging / "PackageIndex.bin").write_bytes(build_package_index())
    (staging / "References.bin").write_bytes(build_references())
    (staging / "Variables.bin").write_bytes(build_variables())
    (staging / "Reports.bin").write_bytes(build_reports_empty())
    (staging / "Unit_0" / "Info.bin").write_bytes(
        build_info(unit_guid, "Unit1", DISPLAY_MODULE)
    )
    (staging / "Unit_0" / "Unit.bin").write_bytes(build_empty_unit())
    write_xmls(staging, pkg_guid, unit_guid, PACKAGE_NAME)

    dest = OUT_DIR / f"{PACKAGE_NAME}.lgp"
    pack_lgp(staging, dest)
    print("Created", dest, "size", dest.stat().st_size)
    print("pkg_guid", pkg_guid)
    with zipfile.ZipFile(dest) as zf:
        print("entries:", zf.namelist())


if __name__ == "__main__":
    main()
