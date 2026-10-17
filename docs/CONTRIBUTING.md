# Contributing to loginom-mcp

This project is an MCP server that builds Loginom `.lgp` packages. Humans and
**AI agents** are welcome to implement missing tools — maintainers review via
pull requests / merge requests.

## Workflow (required)

1. **Fork** the repository (or use a collaborator branch).
2. Create a branch from `main`:
   ```bash
   git checkout -b feat/configure-visualizer
   ```
3. Implement **one** focused change (one tool or one bugfix). Prefer items from
   [ROADMAP.md](ROADMAP.md).
4. Smoke-test locally:
   ```bash
   python -m pip install -r requirements.txt
   python -c "import server; print('import ok')"
   # if you touch visualizers:
   python tools/inspect_viz.py path/to/sample.lgp
   ```
5. Commit with a clear message (`feat:`, `fix:`, `docs:`, `refactor:`).
6. Push and open a **Pull Request** against `main`.
7. Wait for maintainer review — do not merge your own PR unless you are a
   maintainer.

### Pull request checklist

- [ ] Title describes the user-visible outcome
- [ ] PR body: problem → approach → how to test
- [ ] No secrets, no personal absolute paths, no course `.lgp` / `.staging` data
- [ ] `README.md` / `docs/VISUALIZERS.md` / tool docstrings updated if API changed
- [ ] New MCP tool registered in `server.py` with a precise docstring (args matter)

## What belongs in this public repo

| Include | Exclude |
|---------|---------|
| Python MCP server + `vendor/` builders + `g6_blobs` | `.staging/`, `out/`, personal `mcp.json` |
| Docs: README, VISUALIZERS, ROADMAP, AGENTS | University homework packages / datasets |
| Generic examples (`*.example`) | Absolute paths like `C:\Users\...` or course folders |
| MIT-licensed code | Proprietary Loginom installers / license keys |

## Architecture map

| Path | Role |
|------|------|
| `server.py` | MCP entrypoint: tools / resources / `instructions` |
| `loginom_mcp/` | Python package (session, nodes, columns, virgin views) |
| `loginom_mcp/package_session.py` | In-memory package graph → save `.lgp` |
| `loginom_mcp/components.py`, `node_xml.py`, `engine_config.py` | Registry + virgin engines |
| `loginom_mcp/column_config.py`, `loginom_ident.py` | ColumnDefs XML+BGB |
| `loginom_mcp/visualizers.py` | Virgin ModelViews |
| `vendor/viz_configure.py` | **Configured** visualizer engines (post-save patch) |
| `vendor/bgb_*.py`, `vendor/g6_blobs/` | Low-level BGB/XML templates |
| `vendor/verify_lgp.py` | ZIP/XML/BGB (+ optional Loginom UI) verify |
| `tools/inspect_viz.py` | CLI: virgin vs configured views |
| `docs/` | AGENTS, CONTRIBUTING, ROADMAP, VISUALIZERS |
| `examples/` | Host config templates |

## Adding a new MCP tool

1. Implement logic in the right module (prefer library first, thin `server.py` wrapper).
2. Decorate in `server.py` with `@mcp.tool()` and a docstring that lists Args.
3. If the tool configures visualizers, reuse / extend `vendor/viz_configure.py`
   instead of one-off scripts.
4. Mention the tool in README «Что внутри» and tick/clear the ROADMAP row.
5. Open a PR.

## Code style

- Python 3.10+, type hints on public functions
- No machine-specific roots — use `paths.py` + env vars
- Keep BGB/XML XML and BIN in sync when patching packages
- After configuring views in a saved `.lgp`, never call `save_package` again in
  the same session (it rewrites virgin visualizers)

## License

By contributing you agree that your contributions are licensed under the MIT
License (see [LICENSE](LICENSE)).
