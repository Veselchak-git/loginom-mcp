"""Portable path helpers for loginom_mcp (no machine-specific roots)."""
from __future__ import annotations

import os
import sys
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent
VENDOR = PACKAGE_ROOT / "vendor"
STAGING_ROOT = PACKAGE_ROOT / ".staging"


def default_output_dir() -> Path:
    """Where .lgp files are written when create_package omits output_dir.

    Order: LOGINOM_MCP_OUT env → PACKAGE_ROOT/out
    """
    env = os.environ.get("LOGINOM_MCP_OUT", "").strip()
    if env:
        return Path(env)
    return PACKAGE_ROOT / "out"


def loginom_exe() -> Path | None:
    """Optional Loginom binary for UI verify (typically Windows only)."""
    env = os.environ.get("LOGINOM_EXE", "").strip()
    if env:
        p = Path(env)
        return p if p.exists() else p  # caller may report missing
    if sys.platform == "win32":
        for candidate in (
            Path(r"C:\Program Files\Loginom\Community\loginom.exe"),
            Path(r"C:\Program Files (x86)\Loginom\Community\loginom.exe"),
        ):
            if candidate.exists():
                return candidate
    return None


def ui_verify_available() -> bool:
    """True when launching Loginom UI verify is supported on this machine."""
    if sys.platform != "win32":
        return False
    exe = loginom_exe()
    return exe is not None and exe.exists()
