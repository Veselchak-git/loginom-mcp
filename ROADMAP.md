# Roadmap — gaps agents can close

Canonical “what to build next” for contributors. For agent-facing detail and
the list of **already implemented** MCP tools, see [AGENTS.md](AGENTS.md).

## High priority

| Gap | Status | Notes |
|-----|--------|--------|
| `configure_visualizer` | **Missing tool** | Phase 1: table / chart / quality / duplicates_view via `vendor/viz_configure.py` |
| `inspect_source_schema` | **Missing tool** | Field Name/DisplayName/DataType as Loginom exposes them (esp. `.lgd`) |
| Import → ColumnDefs binding | **Partial** | `configure_node` exists; port errors when names/types mismatch upstream |

## Medium priority

| Gap | Notes |
|-----|--------|
| Cube (+ sorting in table visualizer) | After `configure_visualizer` phase 1 |
| Special visualizers configure | `cluster_profiles`, `roc`, `coarse_classes`, `data_tree` |
| Deeper `configure_node` for virgin-only components | imputation, exports, loop/submodel, modeling nodes — one engine per PR |
| More / fresher `g6_blobs` | Mirror from real Loginom packages |

## Lower priority

- `remove_node` / `unlink_nodes` / `clear_package`
- CI golden `.lgp` fixtures for `verify_package` without UI
- Node preset export/import

## Done (do not reinvent)

MCP tools: `list_loginom_components`, `list_visualizers`, `create_package`,
`add_node`, `configure_node`, `link_nodes`, `add_visualizer`, `rename_node`,
`get_package`, `inspect_lgp`, `save_package`, `verify_package`.

Libraries: virgin visualizers + `VISUALIZERS.md` + `vendor/viz_configure.py` +
`tools/inspect_viz.py`.
