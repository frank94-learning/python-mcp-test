// PostToolUse: rewrites YYYY-MM-DD as DD/MM/YYYY in text output.
let s = "";
process.stdin.on("data", (d) => (s += d)).on("end", () => {
  const i = JSON.parse(s);
  const fmt = (t) =>
    t.replace(/(?<!\d)(\d{4})-(\d{2})-(\d{2})(?!\d)/g, "$3/$2/$1");
  const f = (v, k) =>
    typeof v === "string" ? (k === "text" ? fmt(v) : v)
    : Array.isArray(v) ? v.map((x) => f(x, k))
    : v && typeof v === "object"
      ? Object.fromEntries(Object.entries(v).map(([key, x]) => [key, f(x, key)]))
      : v;
  console.log(JSON.stringify({
    hookSpecificOutput: {
      hookEventName: "PostToolUse",
      updatedMCPToolOutput: f(i.tool_response),
    },
  }));
});
