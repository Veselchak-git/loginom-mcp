# Roadmap — gaps agents can close

Priority order for new MCP tools / library work. Pick an item, implement on a
branch, open a PR (see [CONTRIBUTING.md](CONTRIBUTING.md) / [AGENTS.md](AGENTS.md)).

## High priority

| Gap | Why | Likely touch points |
|-----|-----|---------------------|
| `configure_visualizer` MCP tool | `add_visualizer` only creates virgin views; agents still patch ZIP XML+BIN by hand | `visualizers.py`, `vendor/viz_configure.py`, `server.py`, `package_session.py` |
| Reliable column binding after `import_native` / `import_*` | Downstream nodes fail with «ошибка входного порта» when `Name` / `InputColumnInfoName` / types do not match Loginom’s exposed schema | `column_config.py`, `package_session.configure_node`, docs in README |
| Schema introspection for `.lgd` / activated import | Agents guess field names (`Summ` vs `Summa_pokupki`) | new tool e.g. `inspect_source_schema`, optionally Loginom-assisted |

## Medium priority

| Gap | Notes |
|-----|--------|
| `configure_visualizer` for **cube** (dimensions + summaries + optional Charts) | Extend `viz_configure.py` beyond table/chart/quality/duplicates |
| Sorting / filtering inside table visualizer (`SortingColumns`) | Top-N without extra Sort nodes — see VISUALIZERS.md |
| More components in `list_loginom_components` | Mirror virgin XML/BGB from real Loginom packages into `vendor/g6_blobs` |
| Cross-platform `verify_package` without Loginom UI | Structure checks already work; expand golden fixtures |

## Lower priority / research

- Submodel / loop / reference node full configure surface
- Export/import of reusable node presets
- Automated regression: build sample `.lgp` → `inspect_viz` / `verify_package` in CI

## Done-enough (do not reinvent)

- Package session: create / add_node / configure_node / link / save
- Virgin visualizers + `VISUALIZERS.md` + `vendor/viz_configure.py` helpers
- `tools/inspect_viz.py` CLI for virgin vs configured views
