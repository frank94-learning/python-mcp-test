import asyncio
import json
import re
from pathlib import Path

class HookDenied(Exception):
    """Raised when a PreToolUse hook denies the tool call."""


ROOT = Path(__file__).resolve().parent.parent
SETTINGS = ROOT / ".claude" / "settings.local.json"
TOOL_PREFIX = "mcp__app__"  # so matchers like "mcp__.*" apply


def _load(event: str) -> list[dict]:
    try:
        return json.loads(SETTINGS.read_text("utf-8"))["hooks"].get(event, [])
    except (OSError, KeyError, ValueError):
        return []


async def _run(command: str, payload: dict) -> dict:
    proc = await asyncio.create_subprocess_shell(
        command,
        cwd=ROOT,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    out, err = await proc.communicate(json.dumps(payload).encode())
    if proc.returncode == 2:  # Claude Code convention: exit 2 = block
        raise HookDenied(err.decode(errors="replace").strip() or "blocked by hook")
    if proc.returncode != 0:
        print(f"[hook error] {command}: {err.decode(errors='replace')}")
        return {}
    try:
        return json.loads(out.decode() or "{}").get("hookSpecificOutput", {})
    except ValueError:
        return {}


async def run_hooks(
    event: str, tool_name: str, payload: dict, key: str, chain: str
):
    """Runs matching hooks in order; each gets the previous hook's result
    (in payload[chain]). Returns the last value found under `key`."""
    name = TOOL_PREFIX + tool_name
    result = None
    for group in _load(event):
        if not re.fullmatch(group.get("matcher") or ".*", name):
            continue
        for hook in group.get("hooks", []):
            if hook.get("type") != "command":
                continue
            data = {**payload, "hook_event_name": event, "tool_name": name}
            out = await _run(hook["command"], data)
            if out.get("permissionDecision") == "deny":
                raise HookDenied(
                    out.get("permissionDecisionReason", "blocked by hook")
                )
            if key in out:
                result = out[key]
                payload = {**payload, chain: result}
    return result


async def pre_tool_use(tool_name: str, tool_input: dict) -> dict:
    new = await run_hooks(
        "PreToolUse",
        tool_name,
        {"tool_input": tool_input},
        "updatedInput",
        "tool_input",
    )
    return new if isinstance(new, dict) else tool_input


async def post_tool_use(
    tool_name: str, tool_input: dict, texts: list[str], is_error: bool
) -> list[str]:
    response = {
        "content": [{"type": "text", "text": t} for t in texts],
        "isError": is_error,
    }
    new = await run_hooks(
        "PostToolUse",
        tool_name,
        {"tool_input": tool_input, "tool_response": response},
        "updatedMCPToolOutput",
        "tool_response",
    )
    if isinstance(new, dict) and isinstance(new.get("content"), list):
        return [c.get("text", "") for c in new["content"] if c.get("type") == "text"]
    return texts
