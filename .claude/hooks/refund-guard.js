// PreToolUse: blocks process_refund above LIMIT and logs a human escalation.
// Fails closed: any parse/validation problem also blocks.
const fs = require("fs");
const path = require("path");

const LIMIT = 500;
const LOG = path.join(__dirname, "..", "escalations.jsonl");

let s = "";
process.stdin
  .on("data", (d) => (s += d))
  .on("end", () => {
    let reason = null;
    let input = null;
    try {
      input = JSON.parse(s).tool_input;
      const raw = input && input.amount;
      const amount =
        typeof raw === "number"
          ? raw
          : parseFloat(String(raw).replace(/[$,\s]/g, ""));
      if (!Number.isFinite(amount) || amount <= 0) {
        reason = `Refund blocked: invalid amount (${JSON.stringify(raw)}).`;
      } else if (amount > LIMIT) {
        reason = `Refund of $${amount} exceeds the $${LIMIT} limit.`;
      }
    } catch (e) {
      reason = `Refund blocked: could not validate request (${e.message}).`;
    }

    if (!reason) return; // allowed: no output

    try {
      fs.appendFileSync(
        LOG,
        JSON.stringify({
          ts: new Date().toISOString(),
          reason,
          tool_input: input,
        }) + "\n",
      );
    } catch (_) {}

    console.log(
      JSON.stringify({
        hookSpecificOutput: {
          hookEventName: "PreToolUse",
          permissionDecision: "deny",
          permissionDecisionReason: {
            isError: true,
            structuredContent: {
              description:
                reason +
                " Do NOT retry or split the refund. Escalated to a human agent " +
                "(logged in .claude/escalations.jsonl). Tell the user a human will follow up.",
            },
          },
        },
      }),
    );
  });
