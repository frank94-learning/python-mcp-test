---
description: Review staged changes (git diff --cached) before commit
allowed-tools: Bash(git diff:*), Bash(git status:*), Read, Grep, Glob
---

Review only the staged changes: !`git diff --cached`

Files: !`git status --short`

Checklist:

1. **Error handling**: swallowed exceptions (`except: pass`), missing logging, missing cleanup, unpropagated errors in MCP tools/handlers.
2. **Test coverage**: every new or modified function has a test. Use Grep in `tests/`. List those without one.
3. **API naming conventions**: MCP tools/prompts/resources and public functions in `snake_case`, consistent with existing names.
4. **Secrets**: hardcoded API keys, tokens, passwords, or URLs with credentials. Also flag `.env` files in stage.

Output: for each point, OK or a list of `file:line - issue`. End with a verdict: READY / NOT READY to commit. Do not modify files.
