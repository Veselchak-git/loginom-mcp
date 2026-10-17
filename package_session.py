"""In-memory Loginom package session: create / add / link / save / verify."""
from __future__ import annotations

import importlib.util
import shutil
import sys
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from paths import PACKAGE_ROOT, STAGING_ROOT, VENDOR, default_output_dir

DEFAULT_OUT = default_output_dir()

# Allow importing sibling modules and vendored builders
sys.path.insert(0, str(PACKAGE_ROOT))
sys.path.insert(0, str(VENDOR))

from components import COMPONENTS, list_components  # noqa: E402
from node_xml import node_xml, unit_xml  # noqa: E402
from column_config import (  # noqa: E402
    ColumnSpec,
    _make_spec,
    inject_column_defs_blob,
    inject_column_defs_xml,
    read_text_header,
    specs_for_active,
    specs_for_duplicates,
    specs_for_grouping,
)
from engine_config import (  # noqa: E402
    JOIN_TYPE_DISPLAY,
    apply_engine_settings,
    resolve_join_type,
)
from visualizers import (  # noqa: E402
    PORT_DS_IN as VIEW_PORT_DS_IN,
    PORT_COMPONENT as VIEW_PORT_COMPONENT,
    VISUALIZERS,
    build_visualizer_node,
    list_visualizers,
    model_views_xml,
    visualizer_xml,
    preferred_source_port,
)


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


bp = _load("bp", VENDOR / "build_package.py")
imp = _load("imp", VENDOR / "bgb_import_node.py")
tr = _load("tr", VENDOR / "bgb_transform_nodes.py")
ex = _load("ex", VENDOR / "bgb_palette_extra.py")
more = _load("more", VENDOR / "bgb_palette_more.py")
g6 = _load("g6", VENDOR / "bgb_palette_g6.py")
v = _load("v", VENDOR / "verify_lgp.py")

BUILDERS = {
    "import_native": lambda g, n, left, top, file_name: imp.build_import_native_node(
        g, n, file_name=file_name, left=left, top=top
    ),
    "import_text": lambda g, n, left, top, file_name: imp.build_import_text_file_node(
        g, n, file_name=file_name, left=left, top=top
    ),
    "import_excel": lambda g, n, left, top, file_name: imp.build_import_excel_node(
        g, n, file_name=file_name, left=left, top=top
    ),
    "sorting": lambda g, n, left, top, file_name: tr.build_sorting_node(g, n, left, top),
    "reform_columns": lambda g, n, left, top, file_name: tr.build_reform_columns_node(
        g, n, left, top
    ),
    "calculator": lambda g, n, left, top, file_name: tr.build_calculator_node(
        g, n, left, top
    ),
    "datetime": lambda g, n, left, top, file_name: tr.build_datetime_node(g, n, left, top),
    "grouping": lambda g, n, left, top, file_name: tr.build_grouping_node(g, n, left, top),
    "replace": lambda g, n, left, top, file_name: tr.build_replace_node(g, n, left, top),
    "filter": lambda g, n, left, top, file_name: tr.build_filter_node(g, n, left, top),
    "union": lambda g, n, left, top, file_name: tr.build_union_node(g, n, left, top),
    "join": lambda g, n, left, top, file_name: tr.build_join_node(g, n, left, top),
    "enrich": lambda g, n, left, top, file_name: tr.build_enrich_node(g, n, left, top),
    "colunion": lambda g, n, left, top, file_name: ex.build_colunion_node(g, n, left, top),
    "collapse_columns": lambda g, n, left, top, file_name: ex.build_collapse_columns_node(
        g, n, left, top
    ),
    "crosstab": lambda g, n, left, top, file_name: ex.build_crosstab_node(g, n, left, top),
    "sampling": lambda g, n, left, top, file_name: ex.build_sampling_node(g, n, left, top),
    "export_text": lambda g, n, left, top, file_name: ex.build_export_text_node(
        g, n, left, top, file_name=file_name
    ),
    "export_excel": lambda g, n, left, top, file_name: ex.build_export_excel_node(
        g, n, left, top, file_name=file_name
    ),
    "calc_variables": lambda g, n, left, top, file_name: ex.build_calc_variables_node(
        g, n, left, top
    ),
    "vars_to_table": lambda g, n, left, top, file_name: ex.build_vars_to_table_node(
        g, n, left, top
    ),
    "table_to_vars": lambda g, n, left, top, file_name: ex.build_table_to_vars_node(
        g, n, left, top
    ),
    "join_variables": lambda g, n, left, top, file_name: ex.build_join_vars_node(
        g, n, left, top
    ),
    "ungroup": lambda g, n, left, top, file_name: more.build_ungroup_node(g, n, left, top),
    "imputation": lambda g, n, left, top, file_name: more.build_imputation_node(
        g, n, left, top
    ),
    "quantize": lambda g, n, left, top, file_name: more.build_quantize_node(g, n, left, top),
    "final_classes": lambda g, n, left, top, file_name: more.build_final_classes_node(
        g, n, left, top
    ),
    "partition": lambda g, n, left, top, file_name: more.build_partition_node(
        g, n, left, top
    ),
    "outliers": lambda g, n, left, top, file_name: more.build_outliers_node(g, n, left, top),
    "smoothing": lambda g, n, left, top, file_name: more.build_smoothing_node(
        g, n, left, top
    ),
    "import_xml": lambda g, n, left, top, file_name: more.build_import_xml_node(
        g, n, left, top, file_name=file_name or "data.xml"
    ),
    "sliding_window": lambda g, n, left, top, file_name: more.build_sliding_window_node(
        g, n, left, top
    ),
    "replace_variables": lambda g, n, left, top, file_name: more.build_replace_variables_node(
        g, n, left, top
    ),
    "import_db": lambda g, n, left, top, file_name: more.build_import_db_node(
        g, n, left, top
    ),
    "import_1c": lambda g, n, left, top, file_name: more.build_import_1c_node(
        g, n, left, top
    ),
    "import_warehouse": lambda g, n, left, top, file_name: more.build_import_warehouse_node(
        g, n, left, top
    ),
    "export_xml": lambda g, n, left, top, file_name: more.build_export_xml_node(
        g, n, left, top, file_name=file_name or "export.xml"
    ),
    "export_native": lambda g, n, left, top, file_name: more.build_export_native_node(
        g, n, left, top, file_name=file_name or "export.lgd"
    ),
    "export_db": lambda g, n, left, top, file_name: more.build_export_db_node(
        g, n, left, top
    ),
    "export_warehouse": lambda g, n, left, top, file_name: more.build_export_warehouse_node(
        g, n, left, top
    ),
}

# G6 blob-backed builders
for _g6_key in g6.REGISTRY:
    BUILDERS[_g6_key] = g6.make_builder(_g6_key)

# Register engines in verifier
for key, info in COMPONENTS.items():
    v.COMPONENTS[key] = {"vendor": uuid.UUID(info.vendor), "engine": info.engine}


@dataclass
class NodeRec:
    id: str
    guid: uuid.UUID
    component: str
    display_name: str
    left: float
    top: float
    file_name: str = "data.csv"
    columns: list[ColumnSpec] = field(default_factory=list)
    filter_items: list[dict] | None = None
    expressions: list[dict] | None = None
    sort_columns: list | None = None
    ordered_sample: bool | None = None
    join_type: str | int | None = None
    join_keys: list | None = None
    import_settings: dict | None = None


@dataclass
class LinkRec:
    guid: uuid.UUID
    source_node: str
    target_node: str
    source_port: str
    target_port: str
    source_port_name: str
    target_port_name: str


@dataclass
class ViewRec:
    id: str
    guid: uuid.UUID
    visualizer: str
    display_name: str
    source_node: str
    source_port_name: str
    source_port_guid: str


@dataclass
class PackageSession:
    name: str
    output_dir: Path
    pkg_guid: uuid.UUID = field(default_factory=uuid.uuid4)
    unit_guid: uuid.UUID = field(default_factory=uuid.uuid4)
    module_display: str = "Модуль1"
    nodes: list[NodeRec] = field(default_factory=list)
    links: list[LinkRec] = field(default_factory=list)
    views: list[ViewRec] = field(default_factory=list)
    saved_path: Path | None = None
    _next_left: float = 80.0
    _next_top: float = 100.0

    def find_node(self, node_id: str) -> NodeRec:
        for n in self.nodes:
            if n.id == node_id or str(n.guid) == node_id or n.display_name == node_id:
                return n
        raise KeyError(f"node not found: {node_id!r}")


_SESSION: PackageSession | None = None


def get_session() -> PackageSession:
    if _SESSION is None:
        raise RuntimeError("No active package. Call create_package first.")
    return _SESSION


def create_package(
    name: str,
    output_dir: str | None = None,
    module_display: str = "Модуль1",
) -> dict:
    global _SESSION
    out = Path(output_dir) if output_dir else default_output_dir()
    out.mkdir(parents=True, exist_ok=True)
    _SESSION = PackageSession(name=name, output_dir=out, module_display=module_display)
    return {
        "ok": True,
        "name": name,
        "output_dir": str(out),
        "pkg_guid": str(_SESSION.pkg_guid),
        "nodes": 0,
        "links": 0,
    }


def rename_node(node: str, display_name: str) -> dict:
    """Rename a workflow node or visualizer on the canvas (DisplayName)."""
    s = get_session()
    try:
        n = s.find_node(node)
    except KeyError:
        n = None
    if n is not None:
        old = n.display_name
        n.display_name = display_name
        return {
            "ok": True,
            "kind": "node",
            "node_id": n.id,
            "old": old,
            "display_name": display_name,
        }
    for v in s.views:
        if v.id == node or str(v.guid) == node or v.display_name == node:
            old = v.display_name
            v.display_name = display_name
            return {
                "ok": True,
                "kind": "visualizer",
                "view_id": v.id,
                "old": old,
                "display_name": display_name,
            }
    raise KeyError(f"node/visualizer not found: {node!r}")


def add_node(
    component: str,
    display_name: str,
    *,
    node_id: str | None = None,
    left: float | None = None,
    top: float | None = None,
    file_name: str = "data.csv",
) -> dict:
    s = get_session()
    if component not in COMPONENTS:
        raise KeyError(f"unknown component {component!r}; use list_components")
    nid = node_id or f"n{len(s.nodes) + 1}"
    if any(n.id == nid for n in s.nodes):
        raise ValueError(f"node_id already exists: {nid}")
    if left is None:
        left = s._next_left
        s._next_left += 200.0
    if top is None:
        top = s._next_top
    # Prefer short relative paths; BGB length uses 2 bytes when UTF-8 len >= 64.
    if component.startswith("import_") or component.startswith("export_"):
        fn_len = len(file_name.encode("utf-8"))
        if fn_len >= 16384:
            raise ValueError(
                f"file_name UTF-8 length is {fn_len} (>=16384); too long for BGB."
            )
    rec = NodeRec(
        id=nid,
        guid=uuid.uuid4(),
        component=component,
        display_name=display_name,
        left=float(left),
        top=float(top),
        file_name=file_name,
    )
    s.nodes.append(rec)
    info = COMPONENTS[component]
    return {
        "ok": True,
        "node_id": nid,
        "guid": str(rec.guid),
        "component": component,
        "display_name": display_name,
        "inputs": list(info.inputs.keys()),
        "outputs": list(info.outputs.keys()),
        "left": rec.left,
        "top": rec.top,
    }


def configure_node(
    node: str,
    *,
    columns: list[dict] | None = None,
    inputs: list[str] | None = None,
    outputs: list[str] | None = None,
    groups: list[str] | None = None,
    values: list | None = None,
    all_as_input: bool = False,
    source_file: str | None = None,
    default_agg: str = "gdSum",
    filter_items: list[dict] | None = None,
    expressions: list[dict] | None = None,
    sort_columns: list | None = None,
    ordered_sample: bool | None = None,
    join_type: str | int | None = None,
    join_keys: list | None = None,
    import_settings: dict | None = None,
) -> dict:
    """Set input ColumnDefs and/or engine settings on a node.

    Shortcuts by component:
      duplicates — inputs/outputs or all_as_input=True (+ optional source_file)
      grouping — groups= [...], values= [\"Qty\"] or [{\"name\":\"Qty\",\"aggs\":[\"gdSum\"]}]
      outliers/filter/others — inputs= [...] as utActive
      filter — filter_items=[{name, relation?, value?, lower?, upper?, values?, ...}]
      calculator — expressions=[{name, expression, data_type?, display_name?}]
      sorting — sort_columns=[\"Date\"] or [{name, direction?}]
      outliers — ordered_sample=True for ordered sample
      join — join_type=\"left\"|\"inner\"|..., join_keys=[{\"left\":\"Tovar_Kod\",\"right\":\"Tovar_Kod\"}]
      import_text / import_excel — import_settings={file_name?, code_page?/encoding?,
        decimal_separator?, date_format?, date_separator?, sheet_number?, columns?}
        Note: Loginom does not store delimiter/quote/skip_rows in .lgp.

    Or pass columns=[{name, usage, data_type?, data_kind?, aggs?, order?}].
    For import_* nodes, columns= without usage goes into Engine ColumnDefs via import_settings.
    """
    s = get_session()
    n = s.find_node(node)
    specs: list[ColumnSpec]
    touched_columns = False

    if columns:
        touched_columns = True
        # Import nodes: Engine ColumnDefs (no UsageType required)
        if n.component in ("import_text", "import_excel"):
            col_dicts = []
            for c in columns:
                d = dict(c)
                if "usage" not in d and "UsageType" not in d:
                    d["usage"] = "utActive"
                col_dicts.append(d)
            settings = dict(n.import_settings or {})
            settings["columns"] = col_dicts
            n.import_settings = settings
            specs = list(n.columns)  # keep any prior DataSource cols unused
            touched_columns = False  # do not inject into DataSource ColumnDefs
        else:
            specs = []
            for c in columns:
                usage = c.get("usage") or c.get("UsageType")
                if not usage:
                    raise ValueError("columns[].usage required")
                aggs = list(c.get("aggs") or c.get("functions") or [])
                label = c["name"]
                origin = bool(c.get("origin_custom"))
                if n.component == "duplicates" or usage == "utValue":
                    origin = True
                ext = None
                if (
                    (usage in ("utGroup", "utValue") or aggs or c.get("order") is not None)
                    and n.component == "grouping"
                ):
                    ext = "group"
                spec = _make_spec(
                    label,
                    usage,
                    origin_custom=origin,
                    extension=ext,
                    group_functions=aggs,
                    group_order=c.get("order"),
                    data_type=c.get("data_type") or c.get("DataType"),
                    data_kind=c.get("data_kind") or c.get("DataKind"),
                )
                if c.get("display_name") or c.get("displayName"):
                    spec.display_name = c.get("display_name") or c.get("displayName")
                specs.append(spec)
    elif n.component == "duplicates" and (
        inputs is not None or outputs is not None or all_as_input
    ):
        touched_columns = True
        names: list[str] = []
        src = source_file
        if all_as_input and not src:
            for lk in s.links:
                if lk.target_node == n.id:
                    up = s.find_node(lk.source_node)
                    if up.component.startswith("import_"):
                        src = up.file_name
                        break
        if src:
            path = Path(src)
            if not path.is_file():
                path = s.output_dir / src
            names = read_text_header(path)
        specs = specs_for_duplicates(
            names,
            inputs=inputs,
            outputs=outputs,
            all_as_input=all_as_input,
        )
    elif n.component == "grouping" and groups:
        touched_columns = True
        specs = specs_for_grouping(groups, values, default_agg=default_agg)
    elif inputs or all_as_input:
        touched_columns = True
        names = list(inputs or [])
        if all_as_input:
            src = source_file
            if not src:
                for lk in s.links:
                    if lk.target_node == n.id:
                        up = s.find_node(lk.source_node)
                        if up.component.startswith("import_"):
                            src = up.file_name
                            break
            if not src:
                raise ValueError("all_as_input needs source_file or upstream import")
            path = Path(src)
            if not path.is_file():
                path = s.output_dir / src
            names = read_text_header(path)
        specs = specs_for_active(names)
    else:
        specs = list(n.columns)

    if touched_columns:
        n.columns = specs

    if filter_items is not None:
        if n.component != "filter":
            raise ValueError("filter_items only valid for filter nodes")
        n.filter_items = filter_items
    if expressions is not None:
        if n.component != "calculator":
            raise ValueError("expressions only valid for calculator nodes")
        n.expressions = expressions
    if sort_columns is not None:
        if n.component != "sorting":
            raise ValueError("sort_columns only valid for sorting nodes")
        n.sort_columns = sort_columns
    if ordered_sample is not None:
        if n.component != "outliers":
            raise ValueError("ordered_sample only valid for outliers nodes")
        n.ordered_sample = ordered_sample
    if join_type is not None or join_keys is not None:
        if n.component != "join":
            raise ValueError("join_type/join_keys only valid for join nodes")
        if join_type is not None:
            n.join_type = join_type
            jt = resolve_join_type(join_type)
            n.display_name = JOIN_TYPE_DISPLAY[jt]
        if join_keys is not None:
            n.join_keys = join_keys
        if n.join_type is None:
            n.join_type = "left"
        if n.join_keys is None:
            n.join_keys = []

    if import_settings is not None:
        if n.component not in ("import_text", "import_excel"):
            raise ValueError("import_settings only valid for import_text / import_excel")
        merged = dict(n.import_settings or {})
        merged.update(import_settings)
        if "encoding" in merged and "code_page" not in import_settings:
            merged["code_page"] = merged["encoding"]
        if merged.get("file_name"):
            n.file_name = str(merged["file_name"])
        # columns shortcut inside import_settings
        cols = merged.get("columns")
        if cols:
            norm = []
            for c in cols:
                d = dict(c)
                if "usage" not in d and "UsageType" not in d:
                    d["usage"] = "utActive"
                norm.append(d)
            merged["columns"] = norm
        n.import_settings = merged

    if (
        not touched_columns
        and filter_items is None
        and expressions is None
        and sort_columns is None
        and ordered_sample is None
        and join_type is None
        and join_keys is None
        and import_settings is None
        and not (
            n.component in ("import_text", "import_excel")
            and columns is not None
        )
    ):
        raise ValueError(
            "nothing to configure: pass columns/inputs/groups or "
            "filter_items/expressions/sort_columns/ordered_sample/"
            "join_type/join_keys/import_settings"
        )

    return {
        "ok": True,
        "node_id": n.id,
        "component": n.component,
        "display_name": n.display_name,
        "columns": [
            {
                "name": c.name,
                "usage": c.usage,
                "data_type": c.data_type,
                "aggs": c.group_functions,
            }
            for c in n.columns
        ],
        "filter_items": n.filter_items,
        "expressions": n.expressions,
        "sort_columns": n.sort_columns,
        "ordered_sample": n.ordered_sample,
        "join_type": n.join_type,
        "join_keys": n.join_keys,
        "import_settings": n.import_settings,
        "file_name": n.file_name,
    }


def _resolve_port(node: NodeRec, port_name: str | None, side: str) -> tuple[str, str]:
    info = COMPONENTS[node.component]
    ports = info.outputs if side == "out" else info.inputs
    if not ports:
        raise ValueError(f"node {node.id} has no {side}puts")
    if port_name is None:
        # default: first port
        name = next(iter(ports))
    else:
        name = port_name
    if name not in ports:
        raise KeyError(f"port {name!r} not on {node.component}; have {list(ports)}")
    return name, ports[name]


def link_nodes(
    source_node: str,
    target_node: str,
    *,
    source_port: str | None = None,
    target_port: str | None = None,
) -> dict:
    s = get_session()
    src = s.find_node(source_node)
    tgt = s.find_node(target_node)
    sp_name, sp_guid = _resolve_port(src, source_port, "out")
    tp_name, tp_guid = _resolve_port(tgt, target_port, "in")
    rec = LinkRec(
        guid=uuid.uuid4(),
        source_node=src.id,
        target_node=tgt.id,
        source_port=sp_guid,
        target_port=tp_guid,
        source_port_name=sp_name,
        target_port_name=tp_name,
    )
    s.links.append(rec)
    return {
        "ok": True,
        "link_guid": str(rec.guid),
        "from": f"{src.id}.{sp_name}",
        "to": f"{tgt.id}.{tp_name}",
    }


def add_visualizer(
    node: str,
    visualizer: str,
    *,
    display_name: str | None = None,
    source_port: str | None = None,
    view_id: str | None = None,
) -> dict:
    """Attach a virgin visualizer to a workflow node's output port."""
    s = get_session()
    if visualizer not in VISUALIZERS:
        raise KeyError(
            f"unknown visualizer {visualizer!r}; use list_visualizers"
        )
    src = s.find_node(node)
    available = {v["key"] for v in list_visualizers(src.component)}
    if visualizer not in available:
        raise ValueError(
            f"visualizer {visualizer!r} is not available for component "
            f"{src.component!r}; available: {sorted(available)}"
        )
    info = COMPONENTS[src.component]
    if source_port is None:
        sp_name = preferred_source_port(visualizer)
        # Fall back to first dataset output when preferred port is "data"
        if sp_name == "data":
            if not info.outputs:
                raise ValueError(f"node {src.id} has no outputs to visualize")
            sp_name = next(iter(info.outputs))
    else:
        sp_name = source_port

    if sp_name == "component":
        sp_guid = str(VIEW_PORT_COMPONENT)
    elif sp_name in info.outputs:
        sp_guid = info.outputs[sp_name]
    else:
        raise KeyError(
            f"port {sp_name!r} not on {src.component}; have "
            f"{list(info.outputs) + ['component']}"
        )

    vid = view_id or f"v{len(s.views) + 1}"
    if any(v.id == vid for v in s.views):
        raise ValueError(f"view_id already exists: {vid}")
    vinfo = VISUALIZERS[visualizer]
    rec = ViewRec(
        id=vid,
        guid=uuid.uuid4(),
        visualizer=visualizer,
        display_name=display_name or vinfo.title,
        source_node=src.id,
        source_port_name=sp_name,
        source_port_guid=sp_guid,
    )
    s.views.append(rec)
    return {
        "ok": True,
        "view_id": vid,
        "guid": str(rec.guid),
        "visualizer": visualizer,
        "display_name": rec.display_name,
        "attached_to": f"{src.id}.{sp_name}",
        "title": vinfo.title,
        "engine": vinfo.engine,
    }


def package_info() -> dict:
    s = get_session()
    return {
        "name": s.name,
        "output_dir": str(s.output_dir),
        "saved_path": str(s.saved_path) if s.saved_path else None,
        "module_display": s.module_display,
        "nodes": [
            {
                "id": n.id,
                "guid": str(n.guid),
                "component": n.component,
                "display_name": n.display_name,
                "left": n.left,
                "top": n.top,
                "columns": [
                    {"name": c.name, "usage": c.usage, "aggs": c.group_functions}
                    for c in n.columns
                ],
                "join_type": n.join_type,
                "join_keys": n.join_keys,
                "import_settings": n.import_settings,
                "file_name": n.file_name if n.component.startswith("import_") else None,
            }
            for n in s.nodes
        ],
        "links": [
            {
                "from": f"{lk.source_node}.{lk.source_port_name}",
                "to": f"{lk.target_node}.{lk.target_port_name}",
            }
            for lk in s.links
        ],
        "visualizers": [
            {
                "id": v.id,
                "guid": str(v.guid),
                "visualizer": v.visualizer,
                "display_name": v.display_name,
                "attached_to": f"{v.source_node}.{v.source_port_name}",
            }
            for v in s.views
        ],
    }


def inspect_lgp(path: str) -> dict:
    """Summarize workflow nodes / join / calc / filter settings from an on-disk .lgp."""
    import html
    import re
    import tempfile
    import zipfile
    from xml.etree import ElementTree as ET

    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(path)
    with tempfile.TemporaryDirectory() as tmp:
        with zipfile.ZipFile(p) as zf:
            zf.extractall(tmp)
        unit = Path(tmp) / "Unit_0" / "Unit.xml"
        if not unit.is_file():
            raise FileNotFoundError("Unit_0/Unit.xml missing inside .lgp")
        text = unit.read_text(encoding="utf-8")

    # Localize xsi:type without full namespace map
    text_ns = re.sub(r"\sxmlns(:\w+)?=\"[^\"]*\"", "", text)
    text_ns = text_ns.replace("xsi:type", "type")
    root = ET.fromstring(text_ns)

    def _find_workflow_nodes(elem: ET.Element) -> list[ET.Element]:
        for child in elem.iter():
            if child.tag == "Nodes":
                parent = None
                # WorkFlow.Nodes: items with VendorGuid
                items = [
                    it
                    for it in list(child)
                    if it.tag == "Item" and it.get("VendorGuid")
                ]
                if items:
                    return items
        return []

    wf_nodes = _find_workflow_nodes(root)
    nodes: list[dict] = []
    for item in wf_nodes:
        display = html.unescape(item.get("DisplayName") or "").replace("\r\n", " / ")
        engine_el = None
        for el in item.iter("Engine"):
            engine_el = el
            break
        join_type = None
        join_keys: list[dict] = []
        expressions: list[dict] = []
        filters: list[dict] = []
        import_info: dict | None = None
        engine = None
        if engine_el is not None:
            engine = engine_el.get("type")
            join_type = engine_el.get("JoinType")
            if engine in ("TBGImportTextFile", "TBGImportExcelFileEngine"):
                cols = []
                for ci in engine_el.findall("./ColumnDefs/Item"):
                    cols.append(
                        {
                            "name": ci.get("Name"),
                            "display_name": ci.get("DisplayName"),
                            "data_type": ci.get("DataType"),
                            "data_kind": ci.get("DataKind"),
                        }
                    )
                import_info = {
                    "file_name": engine_el.get("FileName"),
                    "code_page": engine_el.get("CodePage"),
                    "decimal_separator": engine_el.get("DecimalSeparator"),
                    "date_format": engine_el.get("DateFormat"),
                    "date_separator": engine_el.get("DateSeparator"),
                    "sheet_number": engine_el.get("SheetNumber"),
                    "columns": cols or None,
                }
            for link in engine_el.findall("./Links/Item"):
                left = link.find("Left")
                right = link.find("Right")
                if left is not None and right is not None:
                    join_keys.append(
                        {"left": left.get("Name"), "right": right.get("Name")}
                    )
            for expr in engine_el.findall("./Expressions/Item"):
                expressions.append(
                    {
                        "name": expr.get("Name"),
                        "display_name": expr.get("DisplayName"),
                        "expression": expr.get("Expression"),
                    }
                )
            # Filter is sibling under Component
            for filt in item.iter("Filter"):
                for fi in filt.findall("./Item"):
                    filters.append(
                        {
                            "name": fi.get("Name"),
                            "relation": fi.get("RelationType"),
                            "data_type": fi.get("DataType"),
                        }
                    )
                break
        nodes.append(
            {
                "guid": item.get("Guid"),
                "display_name": display,
                "vendor_guid": item.get("VendorGuid"),
                "engine": engine,
                "join_type": join_type,
                "join_keys": join_keys or None,
                "expressions": expressions or None,
                "filter_items": filters or None,
                "import_settings": import_info,
            }
        )

    return {
        "ok": True,
        "path": str(p.resolve()),
        "size": p.stat().st_size,
        "nodes": nodes,
        "node_count": len(nodes),
    }


def save_package() -> dict:
    s = get_session()
    staging = STAGING_ROOT / f"staging_mcp_{s.name}"
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)
    (staging / "Unit_0").mkdir()

    node_bins: list[bytes] = []
    nodes_xml: list[str] = []
    guid_by_id = {n.id: n.guid for n in s.nodes}

    for n in s.nodes:
        builder = BUILDERS[n.component]
        blob = builder(n.guid, n.display_name, n.left, n.top, n.file_name)
        xml = node_xml(
            n.component,
            n.guid,
            n.display_name,
            n.left,
            n.top,
            file_name=n.file_name,
        )
        if n.columns:
            blob = inject_column_defs_blob(blob, n.columns)
            xml = inject_column_defs_xml(xml, n.columns)
        if (
            n.filter_items is not None
            or n.expressions is not None
            or n.sort_columns is not None
            or n.ordered_sample is not None
            or n.join_type is not None
            or n.join_keys is not None
            or n.import_settings is not None
        ):
            blob, xml = apply_engine_settings(
                blob,
                xml,
                filter_items=n.filter_items,
                expressions=n.expressions,
                sort_columns=n.sort_columns,
                ordered_sample=n.ordered_sample,
                join_type=n.join_type,
                join_keys=n.join_keys,
                import_settings=n.import_settings,
                import_component=n.component if n.import_settings else None,
                file_name=n.file_name,
            )
        node_bins.append(blob)
        nodes_xml.append(xml)

    link_bins: list[bytes] = []
    link_dicts: list[dict] = []
    for lk in s.links:
        link_bins.append(
            imp.build_link_item(
                lk.guid,
                guid_by_id[lk.source_node],
                uuid.UUID(lk.source_port),
                guid_by_id[lk.target_node],
                uuid.UUID(lk.target_port),
            )
        )
        link_dicts.append(
            {
                "guid": lk.guid,
                "source_node": guid_by_id[lk.source_node],
                "target_node": guid_by_id[lk.target_node],
                "source_port": lk.source_port,
                "target_port": lk.target_port,
            }
        )

    view_bins: list[bytes] = []
    view_xmls: list[str] = []
    view_link_bins: list[bytes] = []
    view_link_dicts: list[dict] = []
    for v in s.views:
        view_bins.append(
            build_visualizer_node(v.visualizer, v.guid, v.display_name)
        )
        view_xmls.append(visualizer_xml(v.visualizer, v.guid, v.display_name))
        link_guid = uuid.uuid4()
        view_link_bins.append(
            imp.build_link_item(
                link_guid,
                guid_by_id[v.source_node],
                uuid.UUID(v.source_port_guid),
                v.guid,
                VIEW_PORT_DS_IN,
            )
        )
        view_link_dicts.append(
            {
                "guid": link_guid,
                "source_node": guid_by_id[v.source_node],
                "target_node": v.guid,
                "source_port": v.source_port_guid,
                "target_port": str(VIEW_PORT_DS_IN),
            }
        )

    unit_bin = imp.build_unit_with_import_nodes(
        node_bins,
        links=link_bins or None,
        view_nodes=view_bins or None,
        view_links=view_link_bins or None,
    )

    (staging / "PackageInfo.bin").write_bytes(bp.build_package_info(s.pkg_guid, s.name))
    (staging / "PackageIndex.bin").write_bytes(bp.build_package_index())
    (staging / "References.bin").write_bytes(bp.build_references())
    (staging / "Variables.bin").write_bytes(bp.build_variables())
    (staging / "Reports.bin").write_bytes(bp.build_reports_empty())
    (staging / "Unit_0" / "Info.bin").write_bytes(
        bp.build_info(s.unit_guid, "Unit1", s.module_display)
    )
    (staging / "Unit_0" / "Unit.bin").write_bytes(unit_bin)
    bp.write_xmls(staging, s.pkg_guid, s.unit_guid, s.name)
    # overwrite module display if custom
    (staging / "Unit_0" / "Info.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<Info Guid="{s.unit_guid}" Name="Unit1" DisplayName="{s.module_display}"/>\n',
        encoding="utf-8",
    )
    (staging / "Unit_0" / "Unit.xml").write_text(
        unit_xml(
            nodes_xml,
            link_dicts,
            model_views_xml=model_views_xml(view_xmls, view_link_dicts),
        ),
        encoding="utf-8",
    )

    dest = s.output_dir / f"{s.name}.lgp"
    bp.pack_lgp(staging, dest)
    s.saved_path = dest
    return {
        "ok": True,
        "path": str(dest),
        "size": dest.stat().st_size,
        "nodes": len(s.nodes),
        "links": len(s.links),
        "visualizers": len(s.views),
    }


def verify_package(open_ui: bool = True, close_after: bool = True) -> dict:
    """Save if needed, validate .lgp; optionally open Loginom UI (Windows only)."""
    from paths import ui_verify_available

    s = get_session()
    if s.saved_path is None or not s.saved_path.exists():
        save_package()
    assert s.saved_path is not None
    if not s.nodes:
        return {"ok": False, "error": "package has no nodes"}
    probe = s.nodes[-1]
    do_ui = bool(open_ui) and ui_verify_available()
    # Structure assert needs a known key in verify_lgp.COMPONENTS
    known = getattr(v, "COMPONENTS", {})
    comp = probe.component if probe.component in known else next(
        (n.component for n in s.nodes if n.component in known),
        "import_text",
    )
    display = probe.display_name
    if comp != probe.component:
        for n in s.nodes:
            if n.component == comp:
                display = n.display_name
                break
    code = v.verify(
        s.saved_path,
        comp,
        display,
        open_ui=do_ui,
        close_after=close_after and do_ui,
    )
    errs = list(getattr(v, "_LAST_VERIFY_ERRS", []))
    dialogs = [e for e in errs if e.startswith("Loginom dialog:")]
    hard = [e for e in errs if not e.startswith("warning:")]
    return {
        "ok": code == 0,
        "path": str(s.saved_path),
        "checked_node": display,
        "component": comp,
        "open_ui": do_ui,
        "ui_skipped": bool(open_ui) and not do_ui,
        "result": "OK" if code == 0 else "FAIL",
        "errors": hard,
        "loginom_dialogs": dialogs,
    }
