## Commands

- Run chat: `uv run main.py [extra_mcp_server.py ...]`
- Code review: `python main.py --review <dir>` (needs >= 7 source files)

## Architecture

- `mcp_server.py`: FastMCP server (stdio) with in-memory `docs`, tools, resources, prompts. Edits are lost on restart.
- `mcp_client.py`: async wrapper over `ClientSession`.
- `core/chat.py` / `cli_chat.py`: tool-use loop; `@doc` injects content, `/cmd doc_id` runs an MCP prompt.
- `core/tools.py`: routes tool calls to the first client that owns the tool, wrapped by hooks.
- `core/hooks.py`: in-app Claude Code-style hooks read from `.claude/settings.json` (exit 2 = block; tools prefixed `mcp__app__`).

## Rules

- All changes (code, comments, docs, commands, commit messages) must be written in English.
