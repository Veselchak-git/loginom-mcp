"""Loginom .lgp builder MCP server (stdio).

Exposes tools to create packages, add nodes, link them, save .lgp, and verify in Loginom.
Entry point for MCP hosts — keep this file at the repository root.
"""
from __future__ import annotations

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
→ add_visualizer → save_package → verify_package.

CRITICAL — visualizers: add_visualizer attaches a VIRGIN view only (empty Series / \
Dimensions / ViewColumns). For deliverable packages you MUST configure charts \
(labels FieldName + Series), cubes (dimensions + summaries), and tables (ViewColumns). \
There is no configure_visualizer tool yet: after save_package, patch Unit_0/Unit.xml AND \
Unit_0/Unit.bin in the .lgp ZIP (Loginom loads BIN), or use vendor/viz_configure.py. \
Do not call save_package again from the MCP session after that patch — it would \
overwrite configured views with virgin ones. Recipes: resource loginom://docs/visualizers \
(docs/VISUALIZERS.md).

CONTRIBUTE — implemented tools are listed in README / docs/AGENTS.md. Missing tools \
(start with configure_visualizer, inspect_source_schema): see docs/AGENTS.md \
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


@mcp.tool()
def list_loginom_components() -> str:
    """List Loginom components that this builder can generate (keys for add_node)."""
    return _ok(list_components())


@mcp.tool()
def list_visualizers(component: str | None = None) -> str:
    """List Loginom visualizers. Optionally filter by component key (e.g. sliding_window).

    Tabular components expose: table, chart, cube, statistics, quality.
    Some processors also expose special visualizers (duplicates_view, cluster_profiles, roc, ...).
    """
    return _ok(_list_visualizers(component))


@mcp.tool()
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
def add_node(
    component: str,
    display_name: str,
    node_id: str | None = None,
    left: float | None = None,
    top: float | None = None,
    file_name: str = "data.csv",
) -> str:
    """Add a virgin node to the current package session.

    Args:
        component: Component key from list_loginom_components (e.g. import_text, sorting, filter).
        display_name: Node title on the canvas.
        node_id: Optional stable id for linking (default n1, n2, ...).
        left: Canvas X (auto-increment if omitted).
        top: Canvas Y.
        file_name: For import_* nodes — source file path/name inside the node.
    """
    return _ok(
        api.add_node(
            component,
            display_name,
            node_id=node_id,
            left=left,
            top=top,
            file_name=file_name,
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
def add_visualizer(
    node: str,
    visualizer: str,
    display_name: str | None = None,
    source_port: str | None = None,
    view_id: str | None = None,
) -> str:
    """Attach a VIRGIN visualizer to a node's output (ModelViews).

    Virgin means empty Series (chart), Dimensions/Summaries (cube), ViewColumns (table).
    That is NOT enough for a finished package: after save_package configure the view in
    Unit.xml + Unit.bin. Read resource loginom://docs/visualizers (docs/VISUALIZERS.md).
    There is no configure_visualizer tool yet.

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
def rename_node(node: str, display_name: str) -> str:
    """Rename a node or visualizer on the canvas (DisplayName).

    Args:
        node: Workflow node_id, display_name, guid, or visualizer view_id.
        display_name: New title shown on the canvas.
    """
    return _ok(api.rename_node(node, display_name))


@mcp.tool()
def configure_node(
    node: str,
    columns: list | None = None,
    inputs: list[str] | None = None,
    outputs: list[str] | None = None,
    groups: list[str] | None = None,
    values: list | None = None,
    all_as_input: bool = False,
    source_file: str | None = None,
    default_agg: str = "gdSum",
    filter_items: list | None = None,
    expressions: list | None = None,
    sort_columns: list | None = None,
    ordered_sample: bool | None = None,
    join_type: str | int | None = None,
    join_keys: list | None = None,
    import_settings: dict | None = None,
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

    Args:
        node: node_id, display_name, or guid.
        columns: Explicit list of {name, usage, data_type?, aggs?, order?}.
            For import_*: {name, data_type?} → Engine ColumnDefs (usage defaults to active).
        inputs: Column names as input/active (duplicates: utActive).
        outputs: Column names as output/predicted (duplicates: utPredicted).
        groups: Grouping keys (utGroup).
        values: Measures — strings or {name, aggs: [gdSum, gdAvg, ...]}.
        all_as_input: Mark every column from source_file/upstream import as input.
        source_file: Text file to read header from (relative to package dir OK).
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
            decimal_separator, date_format, date_separator, columns_required,
            sheet_number (excel), columns=[{name, data_type?, data_kind?}].
            Delimiter/quote/skip_rows are NOT stored by Loginom in .lgp.
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
            default_agg=default_agg,
            filter_items=filter_items,
            expressions=expressions,
            sort_columns=sort_columns,
            ordered_sample=ordered_sample,
            join_type=join_type,
            join_keys=join_keys,
            import_settings=import_settings,
        )
    )


@mcp.tool()
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
def get_package() -> str:
    """Show current package session: nodes, links, and visualizers."""
    return _ok(api.package_info())


@mcp.tool()
def inspect_lgp(path: str) -> str:
    """Read an existing .lgp from disk (no session required) and summarize nodes.

    Extracts Unit_0/Unit.xml and reports DisplayName, VendorGuid/engine hints,
    JoinType/Links, Expressions, Filter items — useful to mirror hand-tuned packages.

    Args:
        path: Absolute or relative path to a .lgp file.
    """
    return _ok(api.inspect_lgp(path))


@mcp.tool()
def save_package() -> str:
    """Write the current session to a .lgp file under output_dir."""
    return _ok(api.save_package())


@mcp.tool()
def verify_package(open_ui: bool = True, close_after: bool = True) -> str:
    """Validate the last saved .lgp (structure + optional Loginom UI on Windows).

    Args:
        open_ui: If true and Loginom is available, open the package in the UI.
        close_after: Close Loginom after the check (when open_ui was used).
    """
    return _ok(api.verify_package(open_ui=open_ui, close_after=close_after))


if __name__ == "__main__":
    mcp.run()
