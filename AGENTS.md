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
3. **One PR = one concern.** Prefer a single ROADMAP item or a focused bugfix.
4. **Maintainer merges.** Always open a Pull Request / Merge Request for review;
   do not push directly to `main` unless the user explicitly owns the repo and
   asks you to.

## When a tool is missing

Typical gaps are listed in [ROADMAP.md](ROADMAP.md). Workflow:

1. Confirm the gap (user request or ROADMAP).
2. Search existing code (`server.py`, `package_session.py`, `vendor/`).
3. Implement library support first; expose a thin `@mcp.tool()` in `server.py`.
4. Update docs (`README.md`, `VISUALIZERS.md` if visualizers, ROADMAP checkmark).
5. Smoke-test import + a minimal package build if feasible.
6. **Commit on a feature branch** and **open a PR** (see below).

### Visualizers

`add_visualizer` creates virgin views only. Until `configure_visualizer` exists:

- Prefer extending `vendor/viz_configure.py` (`table_job`, `chart_job`, …).
- Keep XML Engine and BIN Engine replacements in sync.
- Document that agents must not call `save_package` again after a post-save patch.

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
- What gap from ROADMAP this closes
- Brief approach

## Test plan
- [ ] `python -c "import server"`
- [ ] Build/patch a sample .lgp and run `python tools/inspect_viz.py …`
- [ ] Maintainer: open package in Loginom (optional)

EOF
)"
```

Return the PR URL to the user. Stop there — maintainer reviews and merges.

If `gh` is unavailable, push the branch and give the compare URL:

`https://github.com/<owner>/loginom-mcp/compare/main...feat/short-topic`

## MCP server `instructions` contract

`server.py` `_INSTRUCTIONS` must stay short and always mention:

- Canonical workflow: create → add → configure → link → visualizer → save → verify
- Virgin visualizers + link to `loginom://docs/visualizers`
- Pointer to contribute missing tools via PR (`AGENTS.md` / `CONTRIBUTING.md`)

When you change contribution policy, update **both** `_INSTRUCTIONS` and this file.

## Private vs public copies

| Location | Purpose |
|----------|---------|
| This repo (`loginom-mcp`) | Open source — tools, docs, PRs |
| Maintainer’s private `Data Analysis/loginom_mcp` (if any) | Local `.staging`, course packages, experiments — **not** for PRs |

If you find course-specific scripts or absolute university paths, leave them out
of commits to this repository.

## Quick orientation commands

```bash
rg -n "def configure_|@mcp.tool" server.py package_session.py
rg -n "viz_configure|ViewColumns|TBGChartView" vendor/
python tools/inspect_viz.py path/to/package.lgp
```
