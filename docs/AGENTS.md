# Instructions for AI agents using / extending loginom-mcp

You are working with (or improving) the **Loginom Builder MCP** in this
repository. Follow this file whenever the user asks you to add a missing tool,
fix a builder bug, or contribute upstream.

## Non-negotiables

1. **Do not invent Loginom file formats.** Prefer mirroring a real `.lgp`
   (`Unit_0/Unit.xml` + `Unit_0/Unit.bin`) or extending `vendor/viz_configure.py`
   / `g6_blobs`.
2. **Never commit** `.staging/`, course homework `.lgp`, datasets, secrets, or
   personal absolute paths.
3. **One PR = one concern.** Prefer a single missing tool or a focused bug fix.
4. **Maintainer merges.** Always open a Pull Request / Merge Request for review;
   do not push directly to `main` unless the user explicitly owns the repo and
   asks you to.

---

## MCP tools already implemented

Do **not** reinvent these. They live in `server.py` → `package_session.py`.

| Tool | Purpose |
|------|---------|
| `list_loginom_components` | Keys for `add_node` (imports, transforms, G6 palette, …) |
| `list_visualizers` | Keys for `add_visualizer` (optionally filter by component) |
| `create_package` | New in-memory session (name, output_dir, module_display) |
| `add_node` | Virgin workflow node (`component`, layout, `file_name` for imports) |
| `configure_node` | ColumnDefs + engines: filter, calculator, sort, outliers ordered flag, join, import_settings, grouping aggs, duplicates in/out |
| `link_nodes` | Wire ports (`data` / `else` / join `main`·`joined`, …) |
| `add_visualizer` | Attach **virgin** ModelView (empty Series / ViewColumns / Dimensions) |
| `rename_node` | Rename workflow node or visualizer DisplayName |
| `get_package` | Dump current session (nodes, links, visualizers) |
| `inspect_lgp` | Read an existing `.lgp` from disk (no session) |
| `inspect_source_schema` | Read an import source (`.txt` / `.csv` / `.xlsx`) and report Name / DisplayName / DataType / DataKind as Loginom will expose them |
| `save_package` | Write session → `.lgp` |
| `verify_package` | ZIP/XML/BGB checks; optional Loginom UI on Windows |

**Resources:** `loginom://docs/visualizers`, `loginom://docs/agents`,
`loginom://docs/contributing`, `loginom://docs/roadmap`.

**Library:** `vendor/viz_configure.py` (configured table/chart/quality/duplicates
engines), `vendor/viz_audit.py`, `tools/inspect_viz.py`, `tools/audit_viz.py`.

**`configure_node` covers today:** columns / inputs / outputs / groups / values,
`filter_items`, `expressions`, `sort_columns`, `ordered_sample`, `join_type` +
`join_keys`, `import_settings` (text/excel). `source_file` on an import reads the
header, guesses types and copies the detected code page + delimiter into
`import_settings`, so the text reader opens the file the same way
`inspect_source_schema` did. Unknown filter/sort fields raise with the list of
available names instead of writing a view that Loginom cannot bind. Many palette
nodes can be *added* but have little or no dedicated engine configure beyond
ColumnDefs.

Data types flow down the graph at `save_package` time: a column whose type is
still the `guess_type` default takes the upstream column's `DataType` /
`DataKind` with the same Name, so `configure_node` before `link_nodes` is safe.

---

## Implemented visualizer tools

- `configure_visualizer` — table / duplicates_view (`ViewColumns`, `Sorting`,
  `Filtering` including boolean `is_true`, value compare, row-number top-N, and
  between), chart (`lkLabels` + `Series`), cube (`Dimensions`, `Summaries`,
  optional `CaseSortItems` and `Charts`), statistics (`StatViewColumns` plus the
  indicator panels Loginom stores on a configured view), quality (indicator
  configs and Loginom 7 child order). Session mode is applied by `save_package`.
  `path=` patches a saved `.lgp` (do not `save_package` over that file from a
  session without the same config). Omitting `filters` writes an empty filter.
- `audit_visualizers` — empty columns/series/cubes/statistics, missing duplicate
  flags, fields that are not on the linked node, quality engine shape.

**Still missing on visualizers:** socket `ColumnDefs` for quality field
selection, and special views `coarse_classes` and `data_tree`.
`cluster_profiles` (scaling, indicator, heat map, filters), `roc`, and
linear/logistic regression reports are configurable. Statistics can store
`ShowHistogram` and `StatisticsInRows`. `Grouping` and `Options` on tables stay
empty: saved packages do not persist a richer form. View filter `in` / `not_in`
lists are not encoded.

`configure_node` `engine_settings` covers the pre-training knobs used in the
elbow, clustering, and regression scenarios: cluster count, Pearson
correlation, linear-regression enter method, neural-net hidden layer / decay /
epochs. `expressions` also fills the variable calculator. Trained model
bodies (centers, coefficients, coarse-class limits) are left for Loginom to
compute. A text import stores `delimiter` when it is set, and `configure_node(source_file=...)`
fills it (plus `code_page`) automatically. Nodes can be placed
inside a submodel, and a loop can reference that submodel; publishing the
submodel ports on its boundary is still missing.

## Missing tools — start here

Implement **one** of these per PR. Highest value first.

### 1. Stronger import → ColumnDefs binding helpers

**Why:** Same port-error class of bugs that `inspect_source_schema` fixed for
the first hop. The builder now propagates types down the graph at
`save_package`; a `sync_columns_from_upstream` tool could still help for graphs
whose upstream is not an import (calculator → grouping → join).

### 2. Visualizer extras

- Special views still virgin: `coarse_classes`, `data_tree`.
  `cluster_profiles`, `roc`, and regression reports are configurable.
- Quality socket `ColumnDefs` (which fields the quality view calculates).

### 3. Deeper `configure_node` for under-configured components

Many keys from `list_loginom_components` are virgin add only. Useful next
engines (pick one per PR, mirror a real `.lgp`):

- Submodel port publishing (inner sockets shown on the submodel boundary) and a full derived `InternalComponent` copy inside a loop. Nodes can already be placed inside a submodel, and a loop can reference it.
- `imputation`, `smoothing`, `quantize`, `sampling`, `replace`
- `export_*` settings
- `condition` / `reference_node`
- Modeling nodes beyond the pre-training knobs already in `engine_settings`
  (trained centers, coefficients, coarse-class limits)

### 4. Session / package UX (nice to have)

- `remove_node` / `unlink_nodes` / `clear_package`
- `configure_visualizer` already covers cube and statistics
- CI golden fixtures for `verify_package` without Loginom UI

Also tracked in [ROADMAP.md](ROADMAP.md) — keep both lists in sync when you ship.

---

## When you implement a missing tool

1. Confirm the gap (user request or list above).
2. Search existing code (`server.py`, `loginom_mcp/`, `vendor/`).
3. Implement library support in `loginom_mcp/` (or `vendor/`) first; thin
   `@mcp.tool()` wrapper in `server.py`.
4. Update `README.md` (tools table), this file (move item to “implemented”),
   `docs/ROADMAP.md`, and `docs/VISUALIZERS.md` if relevant.
5. Smoke-test: `python -c "import server"` (+ build/patch sample if feasible).
6. **Feature branch → commit → open PR** (below). Do not push to `main`.

### Visualizers

- Extend `vendor/viz_configure.py` for new engines (cube next).
- Keep XML Engine and BIN Engine in sync.
- `save_package` preserves `configure_visualizer` state. It does **not** reload
  a file you patched with `path=`.

Resource: `loginom://docs/visualizers` (= `VISUALIZERS.md`).

## Git + Pull Request protocol (agents)

Run these in the **clone of this public repo** (not in a private course folder).

```bash
git status
git checkout main
git pull origin main
git checkout -b feat/short-topic

# ... implement ...

git add -A
git status   # ensure no .staging / .lgp / secrets
git commit -m "$(cat <<'EOF'
feat: add configure_visualizer MCP tool

Expose table/chart/quality configuration via viz_configure helpers.
EOF
)"
git push -u origin HEAD
gh pr create --title "feat: add configure_visualizer MCP tool" --body "$(cat <<'EOF'
## Summary
- Which missing tool from AGENTS.md this adds
- Brief approach

## Test plan
- [ ] `python -c "import server"`
- [ ] Exercise the new tool / patch sample .lgp
- [ ] `python tools/inspect_viz.py …` if visualizers
- [ ] Maintainer: open package in Loginom (optional)

EOF
)"
```

Return the PR URL to the user. Stop there — maintainer reviews and merges.

If `gh` is unavailable, push the branch and give the compare URL:

`https://github.com/Veselchak-git/loginom-mcp/compare/main...feat/short-topic`

## MCP server `instructions` contract

`server.py` `_INSTRUCTIONS` must stay short and always mention:

- Canonical workflow: create → add → configure → link → visualizer → save → verify
- Virgin visualizers + link to `loginom://docs/visualizers`
- Missing tools → implement + PR (`AGENTS.md` / `CONTRIBUTING.md`)

When you change contribution policy or the implemented/missing tool lists,
update **`_INSTRUCTIONS`**, **this file**, and **README**.

## Private vs public copies

| Location | Purpose |
|----------|---------|
| This repo (`loginom-mcp`) | Open source — tools, docs, PRs |
| Maintainer’s private `Data Analysis/loginom_mcp` (if any) | Local `.staging`, course packages — **not** for PRs |

## Quick orientation commands

```bash
rg -n "@mcp.tool" server.py
rg -n "def configure_|def add_" loginom_mcp/package_session.py
rg -n "viz_configure|ViewColumns|TBGChartView" vendor/ loginom_mcp/
python tools/inspect_viz.py path/to/package.lgp
```
