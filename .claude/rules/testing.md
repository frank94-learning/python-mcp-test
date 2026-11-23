---
paths:
  - "tests/**/*.py"
---

# Testing conventions

No tests exist yet; these are the target conventions. Stack: `pytest` + `pytest-asyncio` (add as dev deps). Run: `uv run pytest`.

## Layout
- `tests/` mirrors source: `core/chat.py` -> `tests/core/test_chat.py`; `mcp_server.py` -> `tests/test_mcp_server.py`.
- Shared fixtures in `tests/conftest.py`.

## Naming
- Files `test_<module>.py`; functions `test_<unit>_<scenario>_<expected>`, e.g. `test_read_doc_unknown_id_raises`.
- One behavior per test. Group with `class Test<Unit>` only if >5 tests share setup.

## Assertions
- Plain `assert` (no `unittest` style). Compare whole values, not truthiness: `assert result == "x"`.
- Errors: `with pytest.raises(ValueError, match="...")`; always set `match`.
- Structure: Arrange / Act / Assert, separated by blank lines. Max one Act per test.

## Fixtures
- Default scope `function`. Use wider scope only for read-only, expensive setup.
- `mcp_server.docs` is in-memory global state: reset it via an autouse fixture (copy before, restore after) or tests leak into each other.
- Async tests: mark `@pytest.mark.asyncio` (or `asyncio_mode = "auto"` in pyproject). Test `MCPClient` against `mcp_server.py` over stdio; close the session in fixture teardown.
- Mock the Anthropic client; never hit the real API or read `.env`. Use `tmp_path` / `monkeypatch`, not real paths or env.
- Hooks (`core/hooks.py`): test with temp `settings.local.json`; assert exit 2 blocks the tool call.

## Risks
- Real API calls = cost + flaky tests. Patch at the client boundary.
- Shared `docs` state without reset = order-dependent failures.
- Orphaned stdio subprocesses if async fixtures skip teardown.
