"""In-memory Loginom package session: create / add / link / save / verify."""
from __future__ import annotations

import importlib.util
import shutil
import sys
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from .paths import PACKAGE_ROOT, STAGING_ROOT, VENDOR, default_output_dir

DEFAULT_OUT = default_output_dir()

# Vendored BGB builders stay importable as top-level modules
if str(VENDOR) not in sys.path:
    sys.path.insert(0, str(VENDOR))

from .components import COMPONENTS, list_components  # noqa: E402
from .node_xml import node_xml, unit_xml  # noqa: E402
from .column_config import (  # noqa: E402
    ColumnSpec,
    _make_spec,
    inject_column_defs_blob,
    inject_column_defs_xml,
    read_text_header,
    specs_for_active,
    specs_for_duplicates,
    specs_for_grouping,
)
from .source_schema import (  # noqa: E402
    columns_for_import,
    columns_from_schema,
    inspect_source_schema as _inspect_source_schema,
)
from .loginom_ident import loginom_ident  # noqa: E402
from .engine_config import (  # noqa: E402
    JOIN_TYPE_DISPLAY,
    apply_engine_settings,
    resolve_join_type,
)
from .visualizers import (  # noqa: E402
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
    engine_settings: dict | None = None
    parent_id: str | None = None


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
    # Filled by configure_visualizer; applied in save_package (not a virgin engine).
    config: dict | None = None


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
    parent: str | None = None,
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
    if parent:
        host = s.find_node(parent)
        if host.component != "submodel":
            raise ValueError("parent must be a submodel node")
        rec.parent_id = host.id
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


def inspect_source_schema(
    path: str,
    *,
    encoding: str | None = None,
    delimiter: str | None = None,
    sample_rows: int = 500,
    sheet: int | str | None = 1,
) -> dict:
    """Field list Loginom will expose for a .txt/.csv/.xlsx source (Name, DisplayName, types)."""
    return _inspect_source_schema(
        path,
        encoding=encoding,
        delimiter=delimiter,
        sample_rows=sample_rows,
        sheet=sheet,
    )


def _resolve_source_path(session, src: str) -> Path:
    """Absolute path, or a file next to the package output directory."""
    path = Path(src)
    if path.is_file():
        return path
    alt = session.output_dir / src
    if alt.is_file():
        return alt
    raise FileNotFoundError(
        f"source file not found: {src!r} (also tried {str(alt)!r})"
    )


def _code_page_for_encoding(encoding: str) -> int | str:
    """Map a detected encoding label to a Loginom code page."""
    label = encoding.replace(" (BOM)", "").strip().lower()
    mapping = {
        "utf-8": 65001,
        "utf8": 65001,
        "cp1251": 1251,
        "windows-1251": 1251,
        "cp1252": 1252,
        "windows-1252": 1252,
        "ascii": 20127,
        "cp866": 866,
    }
    return mapping.get(label, encoding)


_SPECIAL_FIELDS = frozenset(
    {"Duplicate", "DuplicateGroup", "Contradiction", "ContradictionGroup"}
)


def _node_output_schema(node) -> dict[str, tuple[str | None, str | None]]:
    schema: dict[str, tuple[str | None, str | None]] = {}
    for col in node.columns:
        schema[col.name] = (col.data_type, col.data_kind)
    for col in (node.import_settings or {}).get("columns") or []:
        label = col.get("name") or col.get("Name")
        if not label:
            continue
        schema[loginom_ident(label)] = (
            col.get("data_type") or col.get("DataType"),
            col.get("data_kind") or col.get("DataKind"),
        )
    for expr in node.expressions or []:
        label = expr.get("name") or expr.get("Name")
        if not label:
            continue
        schema[loginom_ident(label)] = (
            expr.get("data_type") or expr.get("DataType"),
            None,
        )
    return schema


def _propagate_types(session) -> None:
    """Carry import DataType/DataKind down the graph, whatever the call order.

    ``configure_node`` may run before ``link_nodes``, so a node cannot always
    see its upstream at configure time. At save time the links do exist: any
    column still sitting on the name-based guess takes the upstream type and
    kind, even when only the kind differs.
    """
    from .column_config import guess_type

    by_id = {node.id: node for node in session.nodes}
    donors_of: dict[str, list[str]] = {}
    for link in session.links:
        donors_of.setdefault(link.target_node, []).append(link.source_node)

    for _ in range(len(session.nodes) + 1):
        changed = False
        for node in session.nodes:
            donors: dict[str, tuple[str | None, str | None]] = {}
            for up_id in donors_of.get(node.id, []):
                for name, types in _node_output_schema(by_id[up_id]).items():
                    donors.setdefault(name, types)
            if not donors:
                continue
            for col in node.columns:
                dtype, dkind = donors.get(col.name, (None, None))
                if not dtype:
                    continue
                guessed_type, guessed_kind = guess_type(col.display_name or col.name)
                # Leave a type the caller set on purpose. A column still sitting
                # on the name-based guess takes both the upstream type and kind,
                # including the case where only the kind differs (dates).
                if col.data_type != guessed_type:
                    continue
                if col.data_type != dtype:
                    col.data_type = dtype
                    if dkind:
                        col.data_kind = dkind
                    changed = True
                elif dkind and col.data_kind == guessed_kind and col.data_kind != dkind:
                    col.data_kind = dkind
                    changed = True
        if not changed:
            break


def _check_bound_fields(session, node) -> None:
    """Fail loudly when a filter/sort refers to a field the node cannot see."""
    if not node.filter_items and not node.sort_columns:
        return
    lookup = _session_column_index(node.id)
    if not lookup:
        return
    for item in node.filter_items or []:
        if not isinstance(item, dict):
            continue
        label = item.get("name")
        if not label or label in _SPECIAL_FIELDS:
            continue
        if _resolve_field(label, lookup) is None:
            raise KeyError(
                f"filter field {label!r} is not on node {node.display_name!r}; "
                f"{_known_hint(lookup)}"
            )
    for item in node.sort_columns or []:
        label = item if isinstance(item, str) else (item or {}).get("name")
        if not label or label in _SPECIAL_FIELDS:
            continue
        if _resolve_field(label, lookup) is None:
            raise KeyError(
                f"sort field {label!r} is not on node {node.display_name!r}; "
                f"{_known_hint(lookup)}"
            )


def _upstream_import_columns(session, node_id: str) -> dict[str, tuple[str | None, str | None]]:
    """Columns declared by import nodes upstream of ``node_id`` (Name → types)."""
    seen = {node_id}
    frontier = [node_id]
    found: dict[str, tuple[str | None, str | None]] = {}
    while frontier:
        current = frontier.pop(0)
        for link in session.links:
            if link.target_node != current or link.source_node in seen:
                continue
            seen.add(link.source_node)
            up = session.find_node(link.source_node)
            cols = (up.import_settings or {}).get("columns") or []
            for col in cols:
                label = col.get("name") or col.get("Name")
                if not label:
                    continue
                key = loginom_ident(label)
                found.setdefault(
                    key,
                    (
                        col.get("data_type") or col.get("DataType"),
                        col.get("data_kind") or col.get("DataKind"),
                    ),
                )
            frontier.append(up.id)
    return found


def _apply_upstream_types(session, node, specs: list[ColumnSpec]) -> None:
    """Copy DataType/DataKind from the import node so ports match downstream."""
    upstream = _upstream_import_columns(session, node.id)
    if not upstream:
        return
    for spec in specs:
        hit = upstream.get(spec.name)
        if not hit:
            continue
        if hit[0]:
            spec.data_type = hit[0]
        if hit[1]:
            spec.data_kind = hit[1]


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
    sheet: int | str | None = None,
    default_agg: str = "gdSum",
    filter_items: list[dict] | None = None,
    expressions: list[dict] | None = None,
    sort_columns: list | None = None,
    ordered_sample: bool | None = None,
    join_type: str | int | None = None,
    join_keys: list | None = None,
    import_settings: dict | None = None,
    engine_settings: dict | None = None,
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
        delimiter?, decimal_separator?, date_format?, date_separator?, sheet_number?, columns?}
        source_file= reads that file; sheet= (number or name) selects an Excel sheet
        and is stored as sheet_number. Quote and skip_rows are not stored in .lgp.
      calc_variables — expressions=[{name, expression, data_type?, display_name?}]
      cluster — engine_settings={n_clusters, auto_select?, rand_seed?}
      corr_analysis — engine_settings={corr_types: caPirson or a 16-bit mask}
      lin_regression — engine_settings={method: linregEnter, rand_seed?}
      log_regression — engine_settings={rand_seed?}
      nn_regress / nn_classify — engine_settings={hidden_layers?, decay?, max_epochs?,
        structure_autofit?, use_initial_structure?, decay_autofit?, use_initial_decay?,
        rand_seed?}
      loop — engine_settings={reference, loop_kind?, append_iteration_identifiers?,
        condition: {name, socket, value?},
        mappings: [{left, left_socket, right, right_socket}]}

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
    elif n.component in ("import_text", "import_excel") and (source_file or all_as_input):
        # Read the source the way Loginom will expose it: names, types and,
        # for text files, the code page and delimiter actually detected.
        src = source_file or n.file_name
        resolved = _resolve_source_path(s, src)
        chosen_sheet = sheet
        if chosen_sheet is None and import_settings:
            chosen_sheet = import_settings.get("sheet", import_settings.get("sheet_number"))
        schema = _inspect_source_schema(
            resolved, sheet=1 if chosen_sheet is None else chosen_sheet
        )
        settings = dict(n.import_settings or {})
        settings.setdefault("columns", columns_from_schema(schema))
        if n.component == "import_text":
            if schema.get("encoding") and "code_page" not in settings:
                settings["code_page"] = _code_page_for_encoding(schema["encoding"])
            if schema.get("delimiter") and "delimiter" not in settings:
                settings["delimiter"] = schema["delimiter"]
        if n.component == "import_excel" and schema.get("sheet_number") is not None:
            settings["sheet_number"] = schema["sheet_number"]
        n.import_settings = settings
        specs = list(n.columns)
        touched_columns = False
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
            names = read_text_header(_resolve_source_path(s, src))
        specs = specs_for_duplicates(
            names,
            inputs=inputs,
            outputs=outputs,
            all_as_input=all_as_input,
        )
        _apply_upstream_types(s, n, specs)
    elif n.component == "grouping" and groups:
        touched_columns = True
        specs = specs_for_grouping(groups, values, default_agg=default_agg)
        _apply_upstream_types(s, n, specs)
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
            names = read_text_header(_resolve_source_path(s, src))
        specs = specs_for_active(names)
        _apply_upstream_types(s, n, specs)
    else:
        specs = list(n.columns)

    if touched_columns:
        n.columns = specs

    if filter_items is not None:
        if n.component != "filter":
            raise ValueError("filter_items only valid for filter nodes")
        n.filter_items = filter_items
    if expressions is not None:
        if n.component not in ("calculator", "calc_variables"):
            raise ValueError("expressions only valid for calculator or calc_variables")
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

    if engine_settings is not None:
        if n.component not in (
            "cluster",
            "corr_analysis",
            "lin_regression",
            "log_regression",
            "nn_regress",
            "nn_classify",
            "loop",
        ):
            raise ValueError(
                "engine_settings is implemented for cluster, corr_analysis, "
                "lin_regression, log_regression, nn_regress, nn_classify, loop"
            )
        n.engine_settings = engine_settings

    if (
        not touched_columns
        and filter_items is None
        and expressions is None
        and sort_columns is None
        and ordered_sample is None
        and join_type is None
        and join_keys is None
        and import_settings is None
        and engine_settings is None
        and not (
            n.component in ("import_text", "import_excel")
            and (columns is not None or source_file is not None)
        )
    ):
        raise ValueError(
            "nothing to configure: pass columns/inputs/groups/source_file or "
            "filter_items/expressions/sort_columns/ordered_sample/"
            "join_type/join_keys/import_settings/engine_settings"
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
        "engine_settings": n.engine_settings,
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
    if src.parent_id != tgt.parent_id:
        raise ValueError(
            "link both nodes at the same level: inside one submodel, or both on the root workflow"
        )
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
                "configured": v.config is not None,
                "config": v.config,
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
                    "delimiter": engine_el.get("DelimiterChar"),
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


def _find_view(view: str) -> ViewRec:
    s = get_session()
    hits = [
        v
        for v in s.views
        if v.id == view or str(v.guid) == view or v.display_name == view
    ]
    if not hits:
        raise KeyError(f"visualizer not found: {view!r}")
    if len(hits) > 1:
        raise KeyError(
            f"visualizer name {view!r} is ambiguous: {[v.id for v in hits]}"
        )
    return hits[0]


def _index_add(
    index: dict[str, tuple[str, str, str]], name: str, display: str | None, data_type: str | None
) -> None:
    """Register a column under its Name *and* its DisplayName.

    Loginom keeps the label (Cyrillic header) only in DisplayName; the field that
    views and nodes reference is the transliterated Name. Accepting both spellings
    here is what stops «ошибка входного порта» / «column not on the source node»,
    because an agent naturally copies the header from the file.
    """
    if not name:
        return
    # The value tied to a view/port is Loginom's Name, which is always ASCII:
    # a caller that passes the Cyrillic header as `name` must still get
    # Name="Kolichestvo", not Name="Количество".
    ident = name if name.isascii() else loginom_ident(name)
    display = display or name
    dtype = data_type or "dtString"
    index.setdefault(name, (ident, display, dtype))
    index.setdefault(ident, (ident, display, dtype))
    index.setdefault(display, (ident, display, dtype))


def _session_column_index(
    node_id: str, _seen: set[str] | None = None
) -> dict[str, tuple[str, str, str]]:
    session = get_session()
    node = session.find_node(node_id)
    seen = set(_seen or ())
    seen.add(node_id)
    index: dict[str, tuple[str, str, str]] = {}
    import_columns = (node.import_settings or {}).get("columns") or []
    if not node.columns and not import_columns:
        # The node keeps no schema of its own (calculator, filter, sorting...):
        # its dataset is inherited from the upstream node, so views and field
        # lookups must resolve those fields too.
        for link in session.links:
            if link.target_node != node_id or link.source_node in seen:
                continue
            for value in _session_column_index(link.source_node, seen).values():
                _index_add(index, *value)
    for col in node.columns:
        _index_add(index, col.name, col.display_name, col.data_type)
    for col in import_columns:
        name = col.get("name") or col.get("Name")
        _index_add(
            index,
            name,
            col.get("display_name") or col.get("DisplayName"),
            col.get("data_type") or col.get("DataType"),
        )
    for expr in node.expressions or []:
        name = expr.get("name") or expr.get("Name")
        _index_add(
            index,
            name,
            expr.get("display_name") or expr.get("DisplayName"),
            expr.get("data_type") or expr.get("DataType"),
        )
    return index


def _known_hint(lookup: dict[str, tuple[str, str, str]]) -> str:
    names = sorted({value[0] for value in lookup.values()})
    shown = ", ".join(repr(n) for n in names[:15])
    more = "" if len(names) <= 15 else f", … (+{len(names) - 15})"
    return f"available: {shown}{more}" if names else "the source node has no columns yet"


def _resolve_field(
    label: str, lookup: dict[str, tuple[str, str, str]]
) -> tuple[str, str, str] | None:
    if label in lookup:
        return lookup[label]
    folded = {key.casefold(): value for key, value in lookup.items()}
    return folded.get(label.casefold())


def _normalize_columns(
    specs: list, lookup: dict[str, tuple[str, str, str]]
) -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for spec in specs:
        if isinstance(spec, str):
            known = _resolve_field(spec, lookup)
            if known is None:
                raise KeyError(
                    f"column {spec!r} is not on the source node; {_known_hint(lookup)}"
                )
            out.append(known)
            continue
        label = spec["name"]
        known = _resolve_field(label, lookup)
        name = known[0] if known else label
        display = spec.get("display_name") or spec.get("displayName") or (known[1] if known else label)
        data_type = spec.get("data_type") or spec.get("DataType") or (known[2] if known else "")
        if not data_type:
            raise ValueError(
                f"data_type required for column {label!r}; {_known_hint(lookup)}"
            )
        out.append((name, display, data_type))
    return out


def _as_field(spec, lookup: dict[str, tuple[str, str, str]]):
    if isinstance(spec, str):
        spec = {"name": spec}
    label = spec["name"]
    known = _resolve_field(label, lookup)
    name = known[0] if known else label
    display = (
        spec.get("display_name")
        or spec.get("displayName")
        or (known[1] if known else label)
        or label
    )
    data_type = (
        spec.get("data_type") or spec.get("DataType") or (known[2] if known else "") or ""
    )
    return name, display, data_type, spec


def _normalize_filters(
    filters: list | None, lookup: dict[str, tuple[str, str, str]]
) -> list | None:
    """Resolve filter field labels to Loginom field Names (row-number filters stay)."""
    if not filters:
        return filters
    out = []
    for item in filters:
        if not isinstance(item, dict):
            out.append(item)
            continue
        copy = dict(item)
        name = copy.get("name")
        known = _resolve_field(name, lookup) if name else None
        if known:
            copy["name"] = known[0]
            copy.setdefault("display_name", known[1])
            copy.setdefault("data_type", known[2])
        elif name and lookup and name not in _SPECIAL_FIELDS:
            raise KeyError(
                f"filter field {name!r} is not on the source node; {_known_hint(lookup)}"
            )
        out.append(copy)
    return out


def _normalize_sort(
    sort: list | None, lookup: dict[str, tuple[str, str, str]] | None = None
) -> list[tuple[str, str]] | None:
    if not sort:
        return None
    out: list[tuple[str, str]] = []
    for item in sort:
        if isinstance(item, str):
            known = _resolve_field(item, lookup) if lookup else None
            if lookup and known is None and item not in _SPECIAL_FIELDS:
                raise KeyError(
                    f"sort field {item!r} is not on the source node; {_known_hint(lookup)}"
                )
            out.append((known[0] if known else item, "sdAsc"))
        else:
            label = item["name"]
            known = _resolve_field(label, lookup) if lookup else None
            if lookup and known is None and label not in _SPECIAL_FIELDS:
                raise KeyError(
                    f"sort field {label!r} is not on the source node; {_known_hint(lookup)}"
                )
            out.append(
                (known[0] if known else label, item.get("direction") or "sdAsc")
            )
    return out


def _normalize_cube_dim(spec, lookup: dict[str, tuple[str, str, str]]) -> dict:
    name, display, data_type, raw = _as_field(spec, lookup)
    item = {
        "name": name,
        "display_name": display,
        "data_type": data_type or "dtString",
        "axis": raw.get("axis") or raw.get("DimensionType") or "rows",
    }
    if "order" in raw:
        item["order"] = raw["order"]
    return item


def _normalize_cube_fact(spec, lookup: dict[str, tuple[str, str, str]]) -> dict:
    name, display, data_type, raw = _as_field(spec, lookup)
    item = {"name": name, "display_name": display}
    if raw.get("count_case") or raw.get("CountCase") or name == "CountCase":
        item["count_case"] = True
        return item
    item["data_type"] = data_type or "dtFloat"
    if "functions" in raw:
        item["functions"] = raw["functions"]
    return item


def _normalize_cube_sort(spec, lookup: dict[str, tuple[str, str, str]]) -> dict:
    name, _display, data_type, raw = _as_field(spec, lookup)
    item = {"name": name, "data_type": data_type or "dtFloat"}
    if "function" in raw:
        item["function"] = raw["function"]
    return item


def _normalize_stat_columns(specs: list, lookup: dict[str, tuple[str, str, str]]) -> list[dict]:
    out = []
    for spec in specs:
        name, display, data_type, raw = _as_field(spec, lookup)
        if not data_type:
            raise ValueError(f"data_type required for column {name!r}")
        item = {"name": name, "display_name": display, "data_type": data_type}
        if "decimals" in raw:
            item["decimals"] = raw["decimals"]
        if "round_mode" in raw or "RoundMode" in raw:
            item["round_mode"] = raw.get("round_mode", raw.get("RoundMode"))
        out.append(item)
    return out


def _with_duplicate_flags(
    cols: list[tuple[str, str, str]], enabled: bool
) -> list[tuple[str, str, str]]:
    if not enabled:
        return cols
    from viz_configure import DUPLICATE_FLAGS

    have = {name for name, _, _ in cols}
    return cols + [flag for flag in DUPLICATE_FLAGS if flag[0] not in have]


def _render_view(view: ViewRec) -> tuple[str, bytes]:
    xml = visualizer_xml(view.visualizer, view.guid, view.display_name)
    blob = build_visualizer_node(view.visualizer, view.guid, view.display_name)
    if not view.config:
        return xml, blob
    from viz_configure import (
        chart_job,
        cube_job,
        duplicates_job,
        find_engine_span,
        patch_xml_engine,
        quality_job,
        statistics_job,
        table_job,
    )

    cfg = view.config
    guid = str(view.guid)
    kind = cfg["kind"]
    if kind == "quality":
        job = quality_job(guid)
    elif kind == "chart":
        job = chart_job(
            guid,
            tuple(cfg["labels"]),
            [tuple(col) for col in cfg["series"]],
            cfg.get("series_type") or "ctColumns",
        )
    elif kind == "cube":
        job = cube_job(
            guid, cfg["dimensions"], cfg["facts"], cfg.get("case_sort"), cfg.get("chart")
        )
    elif kind == "statistics":
        job = statistics_job(guid, cfg["columns"], cfg.get("settings"))
    elif kind in ("cluster_profiles", "roc", "regress_report"):
        job = None
    else:
        cols = [tuple(col) for col in cfg["columns"]]
        sort = [tuple(item) for item in cfg["sort"]] if cfg.get("sort") else None
        filters = cfg.get("filters")
        if kind == "duplicates":
            job = duplicates_job(guid, cols, sort, filters)
        else:
            job = table_job(guid, cols, sort, filters)
    if kind in ("cluster_profiles", "roc", "regress_report"):
        from .scenario_settings import (
            cluster_profiles_engine_blob,
            cluster_profiles_engine_xml,
            regress_report_engine_blob,
            regress_report_engine_xml,
            roc_engine_blob,
            roc_engine_xml,
        )

        if kind == "cluster_profiles":
            job = (
                guid,
                "TBGClusterProfilesView",
                cluster_profiles_engine_xml(cfg.get("settings")),
                cluster_profiles_engine_blob(cfg.get("settings")),
            )
        elif kind == "roc":
            job = (guid, "TBGROCView", roc_engine_xml(cfg.get("charts")), roc_engine_blob(cfg.get("charts")))
        else:
            job = (
                guid,
                cfg["engine"],
                regress_report_engine_xml(cfg["engine"], cfg["sort_order"], cfg["sort_direction"]),
                regress_report_engine_blob(cfg["engine"], cfg["sort_order"], cfg["sort_direction"]),
            )
    xml = patch_xml_engine(xml, guid, job[2])
    start, end = find_engine_span(blob, guid, job[1])
    blob = blob[:start] + job[3] + blob[end:]
    return xml, blob


def configure_visualizer(
    view: str,
    *,
    path: str | None = None,
    columns: list | None = None,
    labels_field: str | dict | None = None,
    y_fields: list | None = None,
    series_type: str = "ctColumns",
    sort: list | None = None,
    include_duplicate_flags: bool = False,
    filters: list | None = None,
    dimensions: list | None = None,
    facts: list | None = None,
    case_sort: dict | None = None,
    cube_chart: dict | None = None,
    view_settings: dict | None = None,
) -> dict:
    """Configure a table, chart, cube, statistics, quality, or duplicates visualizer.

    Without ``path``, stores the setup on the current session. ``save_package``
    writes it into both Unit.xml and Unit.bin, and a later save keeps it.

    With ``path``, patches that ``.lgp`` immediately. Do not ``save_package``
    over the same file from a session that does not contain this config.
    """
    if path:
        return _configure_saved_visualizer(
            path,
            view,
            columns=columns,
            labels_field=labels_field,
            y_fields=y_fields,
            series_type=series_type,
            sort=sort,
            include_duplicate_flags=include_duplicate_flags,
            filters=filters,
            dimensions=dimensions,
            facts=facts,
            case_sort=case_sort,
            cube_chart=cube_chart,
            view_settings=view_settings,
        )
    rec = _find_view(view)
    lookup = _session_column_index(rec.source_node)
    rec.config = _build_view_config(
        rec.visualizer,
        lookup,
        columns=columns,
        labels_field=labels_field,
        y_fields=y_fields,
        series_type=series_type,
        sort=sort,
        include_duplicate_flags=include_duplicate_flags,
        filters=filters,
        dimensions=dimensions,
        facts=facts,
        case_sort=case_sort,
        cube_chart=cube_chart,
        view_settings=view_settings,
        existing_columns=None,
    )
    return {
        "ok": True,
        "view_id": rec.id,
        "guid": str(rec.guid),
        "visualizer": rec.visualizer,
        "configured": True,
        "config": rec.config,
        "applied": "on_save",
    }


def _build_view_config(
    visualizer: str,
    lookup: dict[str, tuple[str, str, str]],
    *,
    columns: list | None,
    labels_field: str | dict | None,
    y_fields: list | None,
    series_type: str,
    sort: list | None,
    include_duplicate_flags: bool,
    filters: list | None,
    dimensions: list | None,
    facts: list | None,
    case_sort: dict | None,
    cube_chart: dict | None,
    view_settings: dict | None,
    existing_columns: list[tuple[str, str, str]] | None,
) -> dict:
    if visualizer == "cluster_profiles":
        return {"kind": "cluster_profiles", "settings": view_settings or {}}
    if visualizer == "roc":
        charts = None if not view_settings else view_settings.get("charts")
        return {"kind": "roc", "charts": charts}
    if visualizer in ("lin_regress_report", "log_regress_report"):
        vs = view_settings or {}
        return {
            "kind": "regress_report",
            "engine": VISUALIZERS[visualizer].engine,
            "sort_order": vs.get("sort_order", "rsoIndex"),
            "sort_direction": vs.get("sort_direction", "sdAsc"),
        }
    if visualizer == "quality":
        return {"kind": "quality"}
    if visualizer == "cube":
        if not dimensions or not facts:
            raise ValueError("cube requires dimensions and facts")
        return {
            "kind": "cube",
            "dimensions": [_normalize_cube_dim(item, lookup) for item in dimensions],
            "facts": [_normalize_cube_fact(item, lookup) for item in facts],
            "case_sort": _normalize_cube_sort(case_sort, lookup) if case_sort else None,
            "chart": cube_chart,
        }
    if visualizer == "statistics":
        specs = columns if columns is not None else [
            {"name": name, "display_name": display, "data_type": data_type}
            for name, display, data_type in (existing_columns or [])
        ]
        if not specs:
            raise ValueError("statistics requires columns")
        return {
            "kind": "statistics",
            "columns": _normalize_stat_columns(specs, lookup),
            "settings": view_settings or {},
        }
    if visualizer == "chart":
        if labels_field is None or not y_fields:
            raise ValueError("chart requires labels_field and y_fields")
        labels = _normalize_columns([labels_field], lookup)[0]
        series = _normalize_columns(list(y_fields), lookup)
        return {
            "kind": "chart",
            "labels": list(labels),
            "series": [list(col) for col in series],
            "series_type": series_type,
        }
    if visualizer not in ("table", "duplicates_view"):
        raise ValueError(
            f"configure_visualizer does not support {visualizer!r} "
            "(table, chart, cube, statistics, quality, duplicates_view)"
        )
    if columns is None:
        if not existing_columns:
            raise ValueError("columns are required")
        cols = list(existing_columns)
    else:
        cols = _normalize_columns(columns, lookup)
    if visualizer == "duplicates_view":
        cols = _with_duplicate_flags(cols, include_duplicate_flags)
    elif include_duplicate_flags:
        raise ValueError("include_duplicate_flags is only for duplicates_view")
    return {
        "kind": "duplicates" if visualizer == "duplicates_view" else "table",
        "columns": [list(col) for col in cols],
        "sort": [list(item) for item in _normalize_sort(sort, lookup)] if sort else None,
        "filters": _normalize_filters(filters, lookup),
    }


def _configure_saved_visualizer(
    path: str,
    view: str,
    *,
    columns: list | None,
    labels_field: str | dict | None,
    y_fields: list | None,
    series_type: str,
    sort: list | None,
    include_duplicate_flags: bool,
    filters: list | None = None,
    dimensions: list | None = None,
    facts: list | None = None,
    case_sort: dict | None = None,
    cube_chart: dict | None = None,
    view_settings: dict | None = None,
) -> dict:
    import zipfile

    from viz_configure import (
        chart_job,
        cube_job,
        duplicates_job,
        patch_package,
        quality_job,
        statistics_job,
        table_job,
    )

    lgp = Path(path)
    if not lgp.is_file():
        raise FileNotFoundError(path)
    with zipfile.ZipFile(lgp) as zf:
        xml = zf.read("Unit_0/Unit.xml").decode("utf-8")
    lookup = _xml_column_index(xml)
    guid, engine, existing = _saved_view(xml, view)
    key = {
        "TBGBrowseView": "table",
        "TBGDuplicatesView": "duplicates_view",
        "TBGChartView": "chart",
        "TBGQualityView": "quality",
        "TBGCubeView": "cube",
        "TBGStatView": "statistics",
        "TBGClusterProfilesView": "cluster_profiles",
        "TBGROCView": "roc",
        "TBGLinRegressReport": "lin_regress_report",
        "TBGLogRegressReport": "log_regress_report",
    }.get(engine)
    if key is None:
        raise ValueError(f"engine {engine} is not configurable yet")
    cfg = _build_view_config(
        key,
        lookup,
        columns=columns,
        labels_field=labels_field,
        y_fields=y_fields,
        series_type=series_type,
        sort=sort,
        include_duplicate_flags=include_duplicate_flags,
        filters=filters,
        dimensions=dimensions,
        facts=facts,
        case_sort=case_sort,
        cube_chart=cube_chart,
        view_settings=view_settings,
        existing_columns=existing,
    )
    if cfg["kind"] == "quality":
        job = quality_job(guid)
    elif cfg["kind"] == "chart":
        job = chart_job(
            guid,
            tuple(cfg["labels"]),
            [tuple(col) for col in cfg["series"]],
            cfg.get("series_type") or "ctColumns",
        )
    elif cfg["kind"] == "cube":
        job = cube_job(
            guid, cfg["dimensions"], cfg["facts"], cfg.get("case_sort"), cfg.get("chart")
        )
    elif cfg["kind"] == "statistics":
        job = statistics_job(guid, cfg["columns"], cfg.get("settings"))
    elif cfg["kind"] in ("cluster_profiles", "roc", "regress_report"):
        from .scenario_settings import (
            cluster_profiles_engine_blob,
            cluster_profiles_engine_xml,
            regress_report_engine_blob,
            regress_report_engine_xml,
            roc_engine_blob,
            roc_engine_xml,
        )

        if cfg["kind"] == "cluster_profiles":
            job = (
                guid,
                "TBGClusterProfilesView",
                cluster_profiles_engine_xml(cfg.get("settings")),
                cluster_profiles_engine_blob(cfg.get("settings")),
            )
        elif cfg["kind"] == "roc":
            job = (
                guid,
                "TBGROCView",
                roc_engine_xml(cfg.get("charts")),
                roc_engine_blob(cfg.get("charts")),
            )
        else:
            job = (
                guid,
                cfg["engine"],
                regress_report_engine_xml(
                    cfg["engine"], cfg["sort_order"], cfg["sort_direction"]
                ),
                regress_report_engine_blob(
                    cfg["engine"], cfg["sort_order"], cfg["sort_direction"]
                ),
            )
    else:
        cols = [tuple(col) for col in cfg["columns"]]
        sort_cols = [tuple(item) for item in cfg["sort"]] if cfg.get("sort") else None
        job = (
            duplicates_job(guid, cols, sort_cols, cfg.get("filters"))
            if cfg["kind"] == "duplicates"
            else table_job(guid, cols, sort_cols, cfg.get("filters"))
        )
    patch_package(lgp, [job], quiet=True)
    return {
        "ok": True,
        "path": str(lgp.resolve()),
        "guid": guid,
        "engine": engine,
        "configured": True,
        "config": cfg,
        "applied": "file",
    }


def _xml_column_index(xml: str) -> dict[str, tuple[str, str, str]]:
    import re

    index: dict[str, tuple[str, str, str]] = {}
    for match in re.finditer(
        r'<Item Name="([^"]+)"(?: DisplayName="([^"]*)")?(?:[^>]*?DataType="([^"]+)")?',
        xml,
    ):
        name, display, data_type = match.group(1), match.group(2), match.group(3)
        if not data_type:
            continue
        if name not in index:
            _index_add(index, name, display, data_type)
    return index


def _saved_view(xml: str, view: str) -> tuple[str, str, list[tuple[str, str, str]]]:
    import re

    model = re.search(r"<ModelViews>(.*)</ModelViews>", xml, re.S)
    if not model:
        raise KeyError("ModelViews missing")
    body = model.group(1)
    items = list(
        re.finditer(
            r'<Item Guid="([^"]+)" DisplayName="([^"]*)"[^>]*VendorGuid="[^"]+"',
            body,
        )
    )
    # ModelViews items are those whose following engine is a view engine.
    hits: list[tuple[str, str, str]] = []
    for match in items:
        guid, display = match.group(1), match.group(2)
        window = body[match.start() : match.start() + 8000]
        engine = re.search(r'xsi:type="(TBG(?:Browse|Duplicates|Chart|Quality|Cube|Stat)View)"', window)
        if not engine:
            continue
        if view in (guid, display) or display.replace("\r\n", " / ") == view:
            hits.append((guid, display, engine.group(1)))
    if not hits:
        raise KeyError(f"visualizer not found in package: {view!r}")
    if len(hits) > 1 and view not in {h[0] for h in hits}:
        raise KeyError(
            f"visualizer name {view!r} is ambiguous ({len(hits)} matches); pass Guid"
        )
    guid, _display, engine = hits[0] if len(hits) == 1 else next(h for h in hits if h[0] == view)
    at = body.find(f'Guid="{guid}"')
    window = body[at : at + 8000]
    block = re.search(
        r"<(?:ViewColumns|StatViewColumns)>(.*?)</(?:ViewColumns|StatViewColumns)>",
        window,
        re.S,
    )
    existing: list[tuple[str, str, str]] = []
    if block:
        for col in re.finditer(
            r'<Item Name="([^"]+)"(?: DisplayName="([^"]*)")?[^>]*DataType="([^"]+)"',
            block.group(1),
        ):
            existing.append((col.group(1), col.group(2) or col.group(1), col.group(3)))
    return guid, engine, existing


def audit_visualizers(path: str) -> dict:
    """Check a saved .lgp: empty views, missing duplicate flags, unknown field names."""
    from viz_audit import audit_package

    return audit_package(path)


def save_package() -> dict:
    s = get_session()
    _propagate_types(s)
    for node in s.nodes:
        _check_bound_fields(s, node)
    staging = STAGING_ROOT / f"staging_mcp_{s.name}"
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)
    (staging / "Unit_0").mkdir()

    guid_by_id = {n.id: n.guid for n in s.nodes}
    built: dict[str, tuple[bytes, str]] = {}

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
            or (n.engine_settings is not None and n.component != "loop")
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
                component=n.component,
                engine_settings=None if n.component == "loop" else n.engine_settings,
            )
        if n.component == "loop" and n.engine_settings:
            from .scenario_settings import apply_loop_settings

            ref = s.find_node(str(n.engine_settings["reference"]))
            blob, xml = apply_loop_settings(
                blob, xml, n.engine_settings, str(ref.guid)
            )
        built[n.id] = (blob, xml)

    from .scenario_settings import nest_workflow

    parent_of = {n.id: n.parent_id for n in s.nodes}
    links_by_parent: dict[str | None, list] = {}
    for lk in s.links:
        host = parent_of[lk.source_node]
        links_by_parent.setdefault(host, []).append(lk)

    def _link_pair(lk: LinkRec) -> tuple[bytes, str]:
        blob = imp.build_link_item(
            lk.guid,
            guid_by_id[lk.source_node],
            uuid.UUID(lk.source_port),
            guid_by_id[lk.target_node],
            uuid.UUID(lk.target_port),
        )
        xml = (
            f'<Item Guid="{lk.guid}">'
            f'<SourcePort NodeGuid="{guid_by_id[lk.source_node]}" PortGuid="{lk.source_port}"/>'
            f'<TargetPort NodeGuid="{guid_by_id[lk.target_node]}" PortGuid="{lk.target_port}"/>'
            "</Item>"
        )
        return blob, xml

    pending = {n.id for n in s.nodes if n.parent_id}
    guard = 0
    while pending:
        guard += 1
        if guard > len(s.nodes) + 2:
            raise ValueError("submodel parent cycle")
        ready_hosts = []
        for host in s.nodes:
            kids = [c for c in s.nodes if c.parent_id == host.id and c.id in pending]
            if not kids:
                continue
            if any(any(g.parent_id == c.id and g.id in pending for g in s.nodes) for c in kids):
                continue
            ready_hosts.append(host)
        if not ready_hosts:
            raise ValueError("submodel parent cycle")
        for host in ready_hosts:
            kids = [c for c in s.nodes if c.parent_id == host.id]
            pairs = [_link_pair(lk) for lk in links_by_parent.get(host.id, [])]
            host_blob, host_xml = built[host.id]
            built[host.id] = nest_workflow(
                host_blob,
                host_xml,
                [built[c.id][0] for c in kids],
                [built[c.id][1] for c in kids],
                [p[0] for p in pairs],
                [p[1] for p in pairs],
            )
            for c in kids:
                pending.discard(c.id)

    node_bins = [built[n.id][0] for n in s.nodes if n.parent_id is None]
    nodes_xml = [built[n.id][1] for n in s.nodes if n.parent_id is None]
    link_bins = []
    link_dicts = []
    for lk in links_by_parent.get(None, []):
        blob, _xml = _link_pair(lk)
        link_bins.append(blob)
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
        view_xml, view_bin = _render_view(v)
        view_bins.append(view_bin)
        view_xmls.append(view_xml)
        link_guid = uuid.uuid4()
        view_link_bins.append(
            imp.build_link_item(
                link_guid,
                guid_by_id[v.source_node],
                uuid.UUID(v.source_port_guid),
                v.guid,
                uuid.UUID(VISUALIZERS[v.visualizer].input_guid),
            )
        )
        view_link_dicts.append(
            {
                "guid": link_guid,
                "source_node": guid_by_id[v.source_node],
                "target_node": v.guid,
                "source_port": v.source_port_guid,
                "target_port": VISUALIZERS[v.visualizer].input_guid,
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
