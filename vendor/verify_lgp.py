"""Verify a generated .lgp without manual Loginom clicking.

Checks:
1) ZIP structure + XML well-formed + BGB magic
2) Expected VendorGuid / Engine / DisplayName present in Unit.xml and Unit.bin
3) Loginom opens the package (window title) and stays alive
4) Loginom error dialogs — text captured via Win32 + UI Automation
"""
from __future__ import annotations

import re
import subprocess
import time
import uuid
import xml.etree.ElementTree as ET
import zipfile
import os
from pathlib import Path

LOGINOM = Path(
    os.environ.get("LOGINOM_EXE", "").strip()
    or (
        r"C:\Program Files\Loginom\Community\loginom.exe"
        if __import__("sys").platform == "win32"
        else ""
    )
)
CAPTURE_UI_PS1 = Path(__file__).resolve().parent / "capture_loginom_ui.ps1"
XSI = "{http://www.w3.org/2001/XMLSchema-instance}type"
MAGIC = b"BGB\xc3"

# Phrases that indicate Loginom failed to open/load a package
_ERROR_MARKERS = (
    "возникли ошибки",
    "ошибка загрузки",
    "не удалось загрузить",
    "не существует",
    "не найден",
    "элемент схемы",
    "aggregateexception",
    "ebgexception",
    "одинаковые идентификаторы",
    "list index out of bounds",
    "access violation",
)

# Known components we can assert
COMPONENTS = {
    "import_native": {
        "vendor": uuid.UUID("35a6e054-ee0c-42f6-bda6-af10b57a36aa"),
        "engine": "TBGImportNative",
    },
    "import_text": {
        "vendor": uuid.UUID("dd767700-1321-4c70-ab92-2acfc4db4492"),
        "engine": "TBGImportTextFile",
    },
    "import_excel": {
        "vendor": uuid.UUID("b391583d-e11b-4ee3-96ce-1438f9d3df5d"),
        "engine": "TBGImportExcelFileEngine",
    },
}


def verify_structure(lgp: Path, component: str, display_name: str) -> list[str]:
    errors: list[str] = []
    meta = COMPONENTS[component]
    with zipfile.ZipFile(lgp) as zf:
        names = set(zf.namelist())
        required = [
            "PackageIndex.bin",
            "PackageIndex.xml",
            "PackageInfo.bin",
            "PackageInfo.xml",
            "Unit_0/Unit.bin",
            "Unit_0/Unit.xml",
            "Unit_0/Info.bin",
            "Unit_0/Info.xml",
        ]
        for r in required:
            if r not in names and r.replace("/", "\\") not in names:
                errors.append(f"missing entry {r}")

        def read(name: str) -> bytes:
            if name in names:
                return zf.read(name)
            alt = name.replace("/", "\\")
            return zf.read(alt)

        for bin_name in [
            "PackageInfo.bin",
            "PackageIndex.bin",
            "Unit_0/Unit.bin",
            "Unit_0/Info.bin",
        ]:
            data = read(bin_name)
            if not data.startswith(MAGIC):
                errors.append(f"{bin_name}: bad BGB magic")

        unit_xml = read("Unit_0/Unit.xml")
        try:
            root = ET.fromstring(unit_xml)
        except ET.ParseError as e:
            errors.append(f"Unit.xml parse: {e}")
            return errors

        nodes = []
        wf = root.find("WorkFlow")
        if wf is None:
            errors.append("no WorkFlow")
            return errors
        nlist = wf.find("Nodes")
        if nlist is None:
            errors.append("no Nodes")
            return errors
        for item in list(nlist):
            if item.tag != "Item":
                continue
            eng = item.find("Component/Engine")
            comp = item.find("Component")
            engine = None
            if eng is not None:
                engine = eng.get(XSI)
            elif comp is not None:
                engine = comp.get(XSI)
            nodes.append(
                {
                    "display": item.get("DisplayName"),
                    "vendor": item.get("VendorGuid"),
                    "engine": engine,
                }
            )

        if not nodes:
            errors.append("no workflow nodes")
        else:
            hit = next((n for n in nodes if n["display"] == display_name), None)
            if hit is None:
                errors.append(
                    f"display name {display_name!r} not found; have {[n['display'] for n in nodes]}"
                )
            else:
                if hit["vendor"] != str(meta["vendor"]):
                    errors.append(f"vendor {hit['vendor']} != {meta['vendor']}")
                if hit["engine"] != meta["engine"]:
                    errors.append(f"engine {hit['engine']} != {meta['engine']}")

        unit_bin = read("Unit_0/Unit.bin")
        if display_name.encode("utf-8") not in unit_bin:
            errors.append("display name missing in Unit.bin")
        if meta["engine"].encode("ascii") not in unit_bin:
            errors.append(f"engine {meta['engine']} missing in Unit.bin")
        if meta["vendor"].bytes_le not in unit_bin:
            errors.append("vendor guid missing in Unit.bin")

    return errors


def loginom_titles() -> list[str]:
    ps = r"""
Get-Process loginom -ErrorAction SilentlyContinue | ForEach-Object { $_.MainWindowTitle }
"""
    r = subprocess.run(
        ["powershell", "-NoProfile", "-Command", ps],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return [ln.strip() for ln in (r.stdout or "").splitlines() if ln.strip()]


def capture_loginom_ui_text(timeout_s: float = 4.0) -> str:
    """Run UI capture script; return raw combined text from Loginom windows."""
    if not CAPTURE_UI_PS1.exists():
        return ""
    try:
        r = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(CAPTURE_UI_PS1),
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_s,
        )
    except subprocess.TimeoutExpired:
        return ""
    return (r.stdout or "").strip()


def extract_loginom_errors(ui_text: str) -> list[str]:
    """Pick error-like lines/blocks from captured UI text."""
    if not ui_text:
        return []
    lower = ui_text.lower()
    if not any(m in lower for m in _ERROR_MARKERS):
        return []

    blocks = re.split(r"\n---\s*\n", ui_text)
    hits: list[str] = []
    for block in blocks:
        bl = block.lower()
        if not any(m in bl for m in _ERROR_MARKERS):
            continue
        lines = []
        for ln in block.splitlines():
            s = ln.strip()
            if not s:
                continue
            if s.startswith("WINTITLE:") or s.startswith("UIA_WINDOW:"):
                lines.append(s)
                continue
            if len(s) >= 8:
                lines.append(s)
        text = "\n".join(lines).strip()
        if text and text not in hits:
            hits.append(text)
    if hits:
        return hits

    return [
        ln.strip()
        for ln in ui_text.splitlines()
        if any(m in ln.lower() for m in _ERROR_MARKERS)
    ]


def dismiss_loginom_error_dialogs() -> None:
    """Send Escape/Enter to Loginom to close modal error dialogs."""
    ps = r"""
Add-Type @"
using System;
using System.Runtime.InteropServices;
public static class Kbd {
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
  [DllImport("user32.dll")] public static extern void keybd_event(byte bVk, byte bScan, uint dwFlags, UIntPtr dwExtraInfo);
}
"@
$vkEscape = 0x1B
$vkReturn = 0x0D
foreach ($p in Get-Process loginom -ErrorAction SilentlyContinue) {
  if ($p.MainWindowHandle -ne 0) {
    [void][Kbd]::SetForegroundWindow($p.MainWindowHandle)
    Start-Sleep -Milliseconds 80
    [Kbd]::keybd_event($vkEscape, 0, 0, [UIntPtr]::Zero)
    [Kbd]::keybd_event($vkEscape, 0, 2, [UIntPtr]::Zero)
    Start-Sleep -Milliseconds 40
    [Kbd]::keybd_event($vkReturn, 0, 0, [UIntPtr]::Zero)
    [Kbd]::keybd_event($vkReturn, 0, 2, [UIntPtr]::Zero)
  }
}
"""
    subprocess.run(
        ["powershell", "-NoProfile", "-Command", ps],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def close_loginom_package(package_name: str, timeout_s: float = 8.0) -> list[str]:
    """Close Loginom windows whose title contains package_name; wait for .lck release."""
    errors: list[str] = []
    ps = f"""
$procs = Get-Process loginom -ErrorAction SilentlyContinue |
  Where-Object {{ $_.MainWindowTitle -like '*{package_name}*' }}
foreach ($p in $procs) {{
  $null = $p.CloseMainWindow()
}}
"""
    subprocess.run(
        ["powershell", "-NoProfile", "-Command", ps],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        titles = loginom_titles()
        if not any(package_name in t for t in titles):
            break
        time.sleep(0.4)
    else:
        # force-kill only windows still showing this package
        ps2 = f"""
Get-Process loginom -ErrorAction SilentlyContinue |
  Where-Object {{ $_.MainWindowTitle -like '*{package_name}*' }} |
  Stop-Process -Force
"""
        subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps2],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        time.sleep(0.5)
        if any(package_name in t for t in loginom_titles()):
            errors.append(f"failed to close Loginom window for {package_name!r}")

    # wait for lock file to disappear
    return errors


def close_lock(lgp: Path, timeout_s: float = 6.0) -> list[str]:
    errors: list[str] = []
    lck = Path(str(lgp) + ".lck")
    deadline = time.time() + timeout_s
    while lck.exists() and time.time() < deadline:
        time.sleep(0.3)
    if lck.exists():
        try:
            lck.unlink()
            errors.append("warning: removed stale .lck manually")
        except OSError as e:
            errors.append(f"warning: .lck still present: {e}")
    return errors


def verify_open(lgp: Path, package_name: str, timeout_s: float = 14.0) -> list[str]:
    errors: list[str] = []
    import sys

    if sys.platform != "win32":
        errors.append("warning: UI verify skipped (Loginom UI check is Windows-only)")
        return errors
    if not str(LOGINOM) or not LOGINOM.exists():
        errors.append(
            "warning: UI verify skipped (set LOGINOM_EXE to loginom.exe to enable)"
        )
        return errors

    subprocess.Popen([str(LOGINOM), str(lgp.resolve())])
    deadline = time.time() + timeout_s
    seen = False

    while time.time() < deadline:
        titles = loginom_titles()
        if any(package_name in t for t in titles):
            seen = True
            break
        time.sleep(0.4)

    # One UI scrape after open attempt (or timeout) — avoid per-tick 8s PS captures
    time.sleep(1.2)
    try:
        ui_errors = extract_loginom_errors(capture_loginom_ui_text(timeout_s=5.0))
    except Exception as e:
        errors.append(f"warning: UI capture failed: {e}")
        ui_errors = []

    if ui_errors:
        for block in ui_errors:
            errors.append("Loginom dialog:\n" + block)
        dismiss_loginom_error_dialogs()
        return errors

    if not seen:
        errors.append(
            f"Loginom window title with {package_name!r} not seen; titles={loginom_titles()}"
        )
        return errors

    titles = loginom_titles()
    if not any(package_name in t for t in titles):
        errors.append(f"window disappeared; titles={titles}")

    lck = Path(str(lgp) + ".lck")
    if not lck.exists():
        errors.append("warning: .lck not created (package may be read-only open)")

    return errors


_LAST_VERIFY_ERRS: list[str] = []


def verify(
    lgp: Path,
    component: str,
    display_name: str,
    open_ui: bool = True,
    close_after: bool = True,
) -> int:
    global _LAST_VERIFY_ERRS
    print("==", lgp.name, "==")
    errs = verify_structure(lgp, component, display_name)
    if open_ui:
        errs.extend(verify_open(lgp, lgp.stem))
        if close_after:
            errs.extend(close_loginom_package(lgp.stem))
            errs.extend(close_lock(lgp))
    _LAST_VERIFY_ERRS = list(errs)
    hard = [e for e in errs if not e.startswith("warning:")]
    warns = [e for e in errs if e.startswith("warning:")]
    for w in warns:
        print("WARN", w)
    if hard:
        for e in hard:
            print("FAIL", e)
        print("RESULT FAIL")
        return 1
    print("RESULT OK")
    return 0


if __name__ == "__main__":
    import sys

    # Pass .lgp paths on the CLI; no machine-specific defaults.
    open_ui = "--no-open" not in sys.argv
    args = [a for a in sys.argv[1:] if a != "--no-open"]
    if not args:
        print("Usage: verify_lgp.py [--no-open] <file.lgp> [component_key] [display_name]")
        raise SystemExit(2)
    lgp = Path(args[0])
    comp = args[1] if len(args) > 1 else "import_text"
    name = args[2] if len(args) > 2 else lgp.stem
    raise SystemExit(verify(lgp, comp, name, open_ui=open_ui))
