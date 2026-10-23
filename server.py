"""Loginom .lgp builder MCP server (stdio).

Exposes tools to create packages, add nodes, link them, save .lgp, and verify in Loginom.
Entry point for MCP hosts — keep this file at the repository root.
"""
from __future__ import annotations

import functools
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
if str(_ROOT / "vendor") not in sys.path:
    sys.path.insert(0, str(_ROOT / "vendor"))

from mcp.server.mcpserver import MCPServer

from loginom_mcp import package_session as api
from loginom_mcp.components import list_components
from loginom_mcp.visualizers import list_visualizers as _list_visualizers

_INSTRUCTIONS = """\
Loginom .lgp builder. Workflow: create_package → add_node → configure_node → link_nodes \
→ add_visualizer → configure_visualizer → save_package → verify_package. \
audit_visualizers(path) checks a saved .lgp for empty views and wrong field names.

CRITICAL — visualizers: add_visualizer attaches a VIRGIN view (empty Series / \
Dimensions / ViewColumns). configure_visualizer fills table/duplicates columns, \
filters and sort, chart labels+series, cube dimensions/facts, statistics columns, \
quality indicators, cluster profiles (indicator, heat map, filters), statistics \
flags, ROC charts, and regression reports. import_settings.delimiter stores \
the text-file field separator. configure_node(source_file=...) reads the source \
header and copies the detected code page, delimiter and column types; \
inspect_source_schema(path) reports Name/DisplayName/DataType without writing. \
Types from the import are inherited by downstream nodes at save_package time, \
whatever the call order. \
configure_node engine_settings covers cluster count, correlation type, \
linear-regression method, neural-net training params, and a loop that \
references a submodel. add_node parent places a node inside a submodel. \
save_package writes \
XML and BIN together. A hand-patched \
.lgp must not be overwritten by save_package from a session that does not hold \
that config. Recipes: loginom://docs/visualizers.

CONTRIBUTE — implemented tools are listed in README / docs/AGENTS.md. Missing tools \
(visualizer socket ColumnDefs, coarse_classes / data_tree): see docs/AGENTS.md \
«Missing tools» and loginom://docs/agents / loginom://docs/roadmap. Implement on \
a feature branch, open a Pull Request; do not push to main. Follow docs/CONTRIBUTING.md \
(loginom://docs/contributing). Never commit .staging/, course .lgp, datasets, \
secrets, or personal absolute paths.
"""

mcp = MCPServer(
    "loginom-builder",
    instructions=_INSTRUCTIONS,
)


def _ok(data: dict | list) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)


_HINTS = {
    "configure_visualizer": (
        "Field names resolve by Name or DisplayName; inspect the source with "
        "get_package / inspect_source_schema to see what the node actually has."
    ),
    "configure_node": (
        "For import_* pass source_file to read the header, code page and delimiter, "
        "or columns=[{name}]. For ports pass columns for this node's input socket."
    ),
    "add_node": "Use list_loginom_components to check the component key.",
    "add_visualizer": (
        "Use list_visualizers(component) for valid keys; quality is valid on tabular nodes."
    ),
    "link_nodes": (
        "Check port names: import -> data, filter else-branch -> else, join -> main/joined."
    ),
    "save_package": "Call create_package first; the session lives in the server process.",
    "verify_package": "Call save_package first.",
}


def _safe(fn):
    """Turn an exception into a structured answer the agent can act on.

    The MCP host renders a raised exception as «Error executing tool X» and drops
    the message, so a wrong column name used to be indistinguishable from a bug.
    """

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception as exc:  # noqa: BLE001 - report, do not kill the call
            payload: dict = {
                "ok": False,
                "tool": fn.__name__,
                "error_type": type(exc).__name__,
                "error": str(exc) or type(exc).__name__,
            }
            hint = _HINTS.get(fn.__name__)
            if hint:
                payload["hint"] = hint
            return _ok(payload)

    return wrapper


@mcp.tool()
@_safe
def list_loginom_components() -> str:
    """List Loginom components that this builder can generate (keys for add_node)."""
    return _ok(list_components())


@mcp.tool()
@_safe
def list_visualizers(component: str | None = None) -> str:
    """List Loginom visualizers. Optionally filter by component key (e.g. sliding_window).

    Tabular components expose: table, chart, cube, statistics, quality.
    Some processors also expose special visualizers (duplicates_view, cluster_profiles, roc, ...).
    """
    return _ok(_list_visualizers(component))


@mcp.tool()
@_safe
def create_package(
    name: str,
    output_dir: str | None = None,
    module_display: str = "Модуль1",
) -> str:
    """Create a new empty Loginom package session (in memory). Call save_package to write .lgp.

    Args:
        name: Package file stem, e.g. Cursor_Lab1 (writes name.lgp).
        output_dir: Directory for the .lgp (default: LOGINOM_MCP_OUT or loginom_mcp/out).
        module_display: Display name of the first module.
    """
    return _ok(api.create_package(name, output_dir, module_display))


@mcp.tool()
@_safe
def add_node(
    component: str,
    display_name: str,
    node_id: str | None = None,
    left: float | None = None,
    top: float | None = None,
    file_name: str = "data.csv",
    parent: str | None = None,
) -> str:
    """Add a virgin node to the current package session.

    Args:
        component: Component key from list_loginom_components (e.g. import_text, sorting, filter).
        display_name: Node title on the canvas.
        node_id: Optional stable id for linking (default n1, n2, ...).
        left: Canvas X (auto-increment if omitted).
        top: Canvas Y.
        file_name: For import_* nodes — source file path/name inside the node.
        parent: Submodel node id. The new node is placed inside that submodel.
    """
    return _ok(
        api.add_node(
            component,
            display_name,
            node_id=node_id,
            left=left,
            top=top,
            file_name=file_name,
            parent=parent,
        )
    )


def _read_doc(name: str) -> str:
    path = _ROOT / "docs" / name
    if not path.is_file():
        return f"(missing docs/{name})"
    return path.read_text(encoding="utf-8")


@mcp.resource("loginom://docs/visualizers")
def visualizers_docs() -> str:
    """How to configure chart/cube/table ModelViews after add_visualizer (XML + BIN)."""
    return _read_doc("VISUALIZERS.md")


@mcp.resource("loginom://docs/agents")
def agents_docs() -> str:
    """Playbook for AI agents: implement missing tools and open Pull Requests."""
    return _read_doc("AGENTS.md")


@mcp.resource("loginom://docs/contributing")
def contributing_docs() -> str:
    """Human + agent contribution guide (branches, PR checklist, public vs private)."""
    return _read_doc("CONTRIBUTING.md")


@mcp.resource("loginom://docs/roadmap")
def roadmap_docs() -> str:
    """Known gaps / suggested MCP tools for contributors."""
    return _read_doc("ROADMAP.md")


@mcp.tool()
@_safe
def add_visualizer(
    node: str,
    visualizer: str,
    display_name: str | None = None,
    source_port: str | None = None,
    view_id: str | None = None,
) -> str:
    """Attach a VIRGIN visualizer to a node's output (ModelViews).

    Virgin means empty Series (chart), Dimensions/Summaries (cube), ViewColumns (table).
    Call configure_visualizer before save_package.
    Read resource loginom://docs/visualizers (docs/VISUALIZERS.md).

    Args:
        node: Workflow node_id, display_name, or guid.
        visualizer: Key from list_visualizers (table, chart, cube, statistics, quality, ...).
        display_name: Optional title (default = Russian visualizer name).
        source_port: Output port name on the node (default first). Filter: data or else.
        view_id: Optional stable id (default v1, v2, ...).
    """
    return _ok(
        api.add_visualizer(
            node,
            visualizer,
            display_name=display_name,
            source_port=source_port,
            view_id=view_id,
        )
    )


@mcp.tool()
@_safe
def configure_visualizer(
    view: str,
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
) -> str:
    """Fill a table, duplicates view, chart, cube, statistics, quality, cluster-profile, ROC, or regression-report visualizer.

    Session mode (no path): remembered until save_package, which writes Unit.xml
    and Unit.bin together. A later save_package keeps this config.

    File mode (path): patches that .lgp now. Do not save_package over it from a
    session that does not contain the same config.

    Args:
        view: Session view_id / guid / unique DisplayName, or a guid in the file.
        path: Optional .lgp to patch instead of the current session.
        columns: Table or duplicates columns. Strings must exist on the source
            node. Or {name, display_name?, data_type?}. Omit to keep file columns.
        labels_field: Chart category field (name or {name, display_name?, data_type?}).
        y_fields: Chart measures, same shape as columns.
        series_type: ctColumns (default), ctArea, or ctSpline.
        sort: Table/duplicates sort, ["Field"] or [{name, direction: sdAsc|sdDesc}].
        include_duplicate_flags: Append Duplicate / Contradiction columns.
            Only for duplicates_view.
        filters: Table/duplicates row filter. Each item is
            {name, relation, value?, data_type?, display_name?} or
            {row_number: true, relation: "<=", value: 20}.
            relation: =, <, <=, >, >=, !=, is_true, is_false, is_null, between
            (between needs lower and upper). is_true has no value.
            Omitting filters clears Filtering.
        dimensions: Cube axes. {name, axis: rows|cols|free, display_name?, data_type?}.
        facts: Cube measures. {name, data_type?, functions?: [sum, count] or [0, 1]}
            or {name: "CountCase", count_case: true}.
        case_sort: {name, data_type?, function?: sum}.
        cube_chart: {source, title?, width?: 300, position?: rows|cols}.
        view_settings: cluster_profiles {histogram_scaling?: hsSizeScale,
            indicator?: cpitMin|cpitClusterCenter, importance_heat_map?,
            filter_cluster?, filter_column?, filter_cell?,
            show_total_histogram?, show_comparison?}.
            statistics {show_histogram?, statistics_in_rows?} together with columns.
            roc uses the standard chart set from the course scenarios (optional charts list).
            Regression reports: {sort_order?: rsoIndex, sort_direction?: sdAsc|sdDesc}.
    """
    return _ok(
        api.configure_visualizer(
            view,
            path=path,
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
    )


@mcp.tool()
@_safe
def audit_visualizers(path: str) -> str:
    """Check visualizers in a saved .lgp (no session).

    Reports empty tables/charts, quality engines missing Loginom 7 children,
    duplicates views without Duplicate/Contradiction columns, and view fields
    that are not on the linked node.

    Args:
        path: Absolute or relative path to a .lgp file.
    """
    return _ok(api.audit_visualizers(path))


@mcp.tool()
@_safe
def rename_node(node: str, display_name: str) -> str:
    """Rename a node or visualizer on the canvas (DisplayName).

    Args:
        node: Workflow node_id, display_name, guid, or visualizer view_id.
        display_name: New title shown on the canvas.
    """
    return _ok(api.rename_node(node, display_name))


@mcp.tool()
@_safe
def configure_node(
    node: str,
    columns: list | None = None,
    inputs: list[str] | None = None,
    outputs: list[str] | None = None,
    groups: list[str] | None = None,
    values: list | None = None,
    all_as_input: bool = False,
    source_file: str | None = None,
    sheet: int | str | None = None,
    default_agg: str = "gdSum",
    filter_items: list | None = None,
    expressions: list | None = None,
    sort_columns: list | None = None,
    ordered_sample: bool | None = None,
    join_type: str | int | None = None,
    join_keys: list | None = None,
    import_settings: dict | None = None,
    engine_settings: dict | None = None,
) -> str:
    """Configure ColumnDefs and/or engine settings on a node.

    Fixes «Не указаны столбцы для обработки» for duplicates, grouping, etc.
    Column labels may be Cyrillic headers or Latin identifiers; Name is always
    a valid Loginom identifier (transliterated), DisplayName keeps the label.

    Engine settings:
      filter_items — filter conditions
      expressions — calculator formulas
      sort_columns — sorting keys
      ordered_sample — ordered outliers flag
      join_type / join_keys — Слияние (left/inner/right/full/diff + key pairs)
      import_settings — import_text / import_excel (code page, separators, sheet, columns)
      engine_settings — cluster {n_clusters, auto_select?, rand_seed?};
        corr_analysis {corr_types}; lin_regression {method, rand_seed?};
        nn_regress/nn_classify {hidden_layers?, decay?, max_epochs?, rand_seed?}
      loop {reference, loop_kind?: lkRepeat, append_iteration_identifiers?,
        condition: {name, socket, value?}, mappings: [{left, left_socket, right, right_socket}]}

    expressions also configure calc_variables (variable formulas, not column formulas).

    Args:
        node: node_id, display_name, or guid.
        columns: Explicit list of {name, usage, data_type?, aggs?, order?}.
            For import_*: {name, data_type?} → Engine ColumnDefs (usage defaults to active).
        inputs: Column names as input/active (duplicates: utActive).
        outputs: Column names as output/predicted (duplicates: utPredicted).
        groups: Grouping keys (utGroup).
        values: Measures — strings or {name, aggs: [gdSum, gdAvg, ...]}.
        all_as_input: Mark every column from source_file/upstream import as input.
        source_file: Text or Excel file to read the header from (relative to package dir OK).
        sheet: Excel sheet number (1-based) or sheet name. Stored as sheet_number.
        default_agg: Default aggregate for grouping values (gdSum).
        filter_items: [{name, relation?, value?, lower?, upper?, values?, concat?,
            data_type?, display_name?}]. relation accepts UI ops (=, <>, пустой,
            в интервале, в списке, содержит, начинается с, …) or frt* names.
            Nullary (пустой/не пустой/is_true): no value. Between: lower+upper or
            value=[lo,hi]. In/not_in: values=[...] or value=[...].
        expressions: [{name, expression, data_type?, display_name?}].
        sort_columns: ["Data_pokupki"] or [{name, direction?}].
        ordered_sample: True for ordered-sample outliers.
        join_type: left|inner|right|full|diff (or jtLeftJoin / 0..4).
        join_keys: [{left, right}] or [{main, joined}] key column pairs.
        import_settings: for import_text / import_excel:
            file_name, code_page|encoding (1251, 65001, utf-8, windows-1251),
            delimiter (one character, e.g. ";"), decimal_separator, date_format,
            date_separator, columns_required, sheet_number (excel),
            columns=[{name, data_type?, data_kind?}].
            Quote and skip_rows are not stored by Loginom in .lgp.
    """
    return _ok(
        api.configure_node(
            node,
            columns=columns,
            inputs=inputs,
            outputs=outputs,
            groups=groups,
            values=values,
            all_as_input=all_as_input,
            source_file=source_file,
            sheet=sheet,
            default_agg=default_agg,
            filter_items=filter_items,
            expressions=expressions,
            sort_columns=sort_columns,
            ordered_sample=ordered_sample,
            join_type=join_type,
            join_keys=join_keys,
            import_settings=import_settings,
            engine_settings=engine_settings,
        )
    )


@mcp.tool()
@_safe
def link_nodes(
    source_node: str,
    target_node: str,
    source_port: str | None = None,
    target_port: str | None = None,
) -> str:
    """Connect output of source_node to input of target_node.

    Args:
        source_node: node_id, display_name, or guid.
        target_node: node_id, display_name, or guid.
        source_port: Output port name (default first). Import: data. Filter else-branch: else.
        target_port: Input port name (default first). Transform: data. Multi-input: main or joined.
    """
    return _ok(
        api.link_nodes(
            source_node,
            target_node,
            source_port=source_port,
            target_port=target_port,
        )
    )


@mcp.tool()
@_safe
def get_package() -> str:
    """Show current package session: nodes, links, and visualizers."""
    return _ok(api.package_info())


@mcp.tool()
@_safe
def inspect_lgp(path: str) -> str:
    """Read an existing .lgp from disk (no session required) and summarize nodes.

    Extracts Unit_0/Unit.xml and reports DisplayName, VendorGuid/engine hints,
    JoinType/Links, Expressions, Filter items — useful to mirror hand-tuned packages.

    Args:
        path: Absolute or relative path to a .lgp file.
    """
    return _ok(api.inspect_lgp(path))


@mcp.tool()
@_safe
def save_package() -> str:
    """Write the current session to a .lgp file under output_dir."""
    return _ok(api.save_package())


@mcp.tool()
@_safe
def verify_package(open_ui: bool = True, close_after: bool = True) -> str:
    """Validate the last saved .lgp (structure + optional Loginom UI on Windows).

    Args:
        open_ui: If true and Loginom is available, open the package in the UI.
        close_after: Close Loginom after the check (when open_ui was used).
    """
    return _ok(api.verify_package(open_ui=open_ui, close_after=close_after))


@mcp.tool()
@_safe
def inspect_source_schema(
    path: str,
    encoding: str | None = None,
    delimiter: str | None = None,
    sample_rows: int = 500,
    sheet: int | str | None = 1,
) -> str:
    """Read an import source (.txt/.csv/.tsv/.xlsx) and report the fields Loginom will create.

    Returns Name (transliterated identifier), DisplayName (original header),
    inferred DataType/DataKind, null counts and sample values. Use the labels in
    configure_node(columns=...) / inputs= / groups= and in configure_visualizer.

    Args:
        path: Absolute or session-relative path to the source.
        encoding: utf-8, cp1251, ... (default: auto from BOM/UTF-8 fallback cp1251).
        delimiter: Column delimiter (default: auto — tab, ';' or ',').
        sample_rows: How many data rows to scan for types and nulls.
        sheet: Sheet number (1-based) or name for .xlsx sources.
    """
    return _ok(
        api.inspect_source_schema(
            path,
            encoding=encoding,
            delimiter=delimiter,
            sample_rows=sample_rows,
            sheet=sheet,
        )
    )


if __name__ == "__main__":
    mcp.run()
