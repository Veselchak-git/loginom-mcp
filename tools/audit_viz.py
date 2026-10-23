# -*- coding: utf-8 -*-
"""Audit ModelViews in a Loginom .lgp.

Usage:
  python tools/audit_viz.py path/to/package.lgp
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
if str(_ROOT / "vendor") not in sys.path:
    sys.path.insert(0, str(_ROOT / "vendor"))

from viz_audit import audit_package  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 1:
        print("usage: python tools/audit_viz.py package.lgp", file=sys.stderr)
        return 1
    report = audit_package(args[0])
    print(json.dumps(
        {"ok": report["ok"], "view_count": report["view_count"], "issues": report["issues"]},
        ensure_ascii=False,
        indent=2,
    ))
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
