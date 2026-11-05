# Roadmap — gaps agents can close

Canonical “what to build next” for contributors. For agent-facing detail and
the list of **already implemented** MCP tools, see [AGENTS.md](AGENTS.md) in this folder.

## High priority

| Gap | Status | Notes |
|-----|--------|--------|
| Import → ColumnDefs binding | **Partial** | `configure_node(source_file=...)` copies header, code page, delimiter and types; `save_package` propagates types downstream. Non-import upstreams still need explicit columns |

## Medium priority

| Gap | Notes |
|-----|--------|
| Special visualizer configure | `data_tree` still virgin. `coarse_classes` attaches via Component; cluster profiles, statistics flags, ROC, regression reports configurable |
| Deeper `configure_node` for virgin-only components | imputation, exports, submodel port publishing, modeling nodes — one engine per PR. `final_classes` ColumnDefs (cpTarget/cpInput/cpUnused) are done |
| More / fresher `g6_blobs` | Mirror from real Loginom packages |

## Lower priority

- `remove_node` / `unlink_nodes` / `clear_package`
- CI golden `.lgp` fixtures for `verify_package` without UI
- Node preset export/import

## Done (do not reinvent)

MCP tools: `list_loginom_components`, `list_visualizers`, `create_package`,
`add_node`, `configure_node`, `link_nodes`, `add_visualizer`,
`configure_visualizer` (table / duplicates filters+sort, chart, cube, statistics,
quality, cluster profiles, ROC, regression reports, session or saved `.lgp`), `audit_visualizers`, `rename_node`, `get_package`, `inspect_lgp`,
`inspect_source_schema` (text and `.xlsx`), `save_package`, `verify_package`.
`configure_node` also covers `final_classes` (target / inputs / unused + coarse
extensions); `add_visualizer(coarse_classes)` links the Component port.

Libraries: virgin visualizers + `VISUALIZERS.md` + `vendor/viz_configure.py` +
`tools/inspect_viz.py`.
