# Roadmap — gaps agents can close

Canonical “what to build next” for contributors. For agent-facing detail and
the list of **already implemented** MCP tools, see [AGENTS.md](AGENTS.md) in this folder.

## High priority

| Gap | Status | Notes |
|-----|--------|--------|
| `inspect_source_schema` | **Missing tool** | Field Name/DisplayName/DataType as Loginom exposes them (esp. `.lgd`) |
| Import → ColumnDefs binding | **Partial** | `configure_node` exists; port errors when names/types mismatch upstream |

## Medium priority

| Gap | Notes |
|-----|--------|
| Special visualizer configure | `cluster_profiles`, `roc`, `coarse_classes`, `data_tree`. Cube, statistics, table filters and sort are in `configure_visualizer` |
| Special visualizers configure | `cluster_profiles`, `roc`, `coarse_classes`, `data_tree` |
| Deeper `configure_node` for virgin-only components | imputation, exports, loop/submodel, modeling nodes — one engine per PR |
| More / fresher `g6_blobs` | Mirror from real Loginom packages |

## Lower priority

- `remove_node` / `unlink_nodes` / `clear_package`
- CI golden `.lgp` fixtures for `verify_package` without UI
- Node preset export/import

## Done (do not reinvent)

MCP tools: `list_loginom_components`, `list_visualizers`, `create_package`,
`add_node`, `configure_node`, `link_nodes`, `add_visualizer`,
`configure_visualizer` (table / duplicates filters+sort, chart, cube, statistics,
quality, session or saved `.lgp`), `audit_visualizers`, `rename_node`, `get_package`, `inspect_lgp`,
`save_package`, `verify_package`.

Libraries: virgin visualizers + `VISUALIZERS.md` + `vendor/viz_configure.py` +
`tools/inspect_viz.py`.
