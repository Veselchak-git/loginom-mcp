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
| `save_package` | Write session → `.lgp` |
| `verify_package` | ZIP/XML/BGB checks; optional Loginom UI on Windows |

**Resources:** `loginom://docs/visualizers`, `loginom://docs/agents`,
`loginom://docs/contributing`, `loginom://docs/roadmap`.

**Library (not MCP tools yet):** `vendor/viz_configure.py` (patch configured
table/chart/quality/duplicates into a saved `.lgp`), `tools/inspect_viz.py` CLI.

**`configure_node` covers today:** columns / inputs / outputs / groups / values,
`filter_items`, `expressions`, `sort_columns`, `ordered_sample`, `join_type` +
`join_keys`, `import_settings` (text/excel). Many palette nodes can be *added*
but have little or no dedicated engine configure beyond ColumnDefs.

---

## Missing tools — start here

Implement **one** of these per PR. Highest value first.

### 1. `configure_visualizer` (highest priority)

**Why:** `add_visualizer` only creates virgin views. Agents still hand-patch
`Unit.xml` + `Unit.bin` after `save_package`.

**Should support (phase 1):**

- `table` / `duplicates_view` → `ViewColumns` (+ optional `Sorting`)
- `chart` → `lkLabels` FieldName + `Series` (ctColumns / …)
- `quality` → indicator column configs

**Phase 2:** `cube` (Dimensions + Summaries + optional Charts), `statistics`.

**Reuse:** `vendor/viz_configure.py` (`table_job`, `chart_job`, `quality_job`,
`duplicates_job`, `patch_package`). Expose session-aware API in
`package_session.py` + `@mcp.tool()` in `server.py`. Prefer configuring
**before** final save when possible; if patching a saved file, document that
another `save_package` in the same session must not wipe views.

**Docs to update:** `VISUALIZERS.md`, README, this file (move to “implemented”).

### 2. `inspect_source_schema` (or `peek_import_fields`)

**Why:** Wrong field names (`Summ` vs `Summa_pokupki`, LGD internal vs Loginom
DisplayName transliteration) cause «ошибка входного порта» on the first
downstream nodes.

**Goal:** Given a path to `.lgd` / CSV / existing import node, return the field
`Name` / `DisplayName` / `DataType` list as Loginom will expose them so
`configure_node` can bind `InputColumnInfoName` correctly.

### 3. Stronger import → ColumnDefs binding helpers

**Why:** Same port-error class of bugs. May be part of (2) or a
`sync_columns_from_upstream` tool / `configure_node` enhancement that copies
types from the linked import metadata.

### 4. Visualizer extras (after #1)

- Table `SortingColumns` / Filtering for top-N without Sort nodes
- Cube configure (see VISUALIZERS.md)
- Special views: `cluster_profiles`, `roc`, `coarse_classes`, `data_tree`
  (today: listable / attachable as virgin only)

### 5. Deeper `configure_node` for under-configured components

Many keys from `list_loginom_components` are virgin add only. Useful next
engines (pick one per PR, mirror a real `.lgp`):

- `imputation`, `smoothing`, `quantize`, `sampling`, `replace`
- `export_*` settings
- `loop` / `condition` / `submodel` / `reference_node`
- Modeling nodes (`cluster`, `lin_regression`, `nn_*`, …) — large surface

### 6. Session / package UX (nice to have)

- `remove_node` / `unlink_nodes` / `clear_package`
- `configure_visualizer` apply to **saved** `.lgp` path without full session
- CI golden fixtures for `verify_package` without Loginom UI

Also tracked in [ROADMAP.md](ROADMAP.md) — keep both lists in sync when you ship.

---

## When you implement a missing tool

1. Confirm the gap (user request or list above).
2. Search existing code (`server.py`, `package_session.py`, `vendor/`).
3. Implement library support first; thin `@mcp.tool()` wrapper in `server.py`.
4. Update `README.md` (tools table), this file (move item to “implemented”),
   `ROADMAP.md`, and `VISUALIZERS.md` if relevant.
5. Smoke-test: `python -c "import server"` (+ build/patch sample if feasible).
6. **Feature branch → commit → open PR** (below). Do not push to `main`.

### Visualizers (until `configure_visualizer` lands)

- Prefer extending `vendor/viz_configure.py`.
- Keep XML Engine and BIN Engine replacements in sync.
- Never call `save_package` again after a post-save patch in the same session.

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
rg -n "def configure_|def add_" package_session.py
rg -n "viz_configure|ViewColumns|TBGChartView" vendor/
python tools/inspect_viz.py path/to/package.lgp
```
