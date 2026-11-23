let s='';process.stdin.on('data',d=>s+=d).on('end',()=>{
const i=JSON.parse(s);
const f=v=>typeof v==='string'?v.toLowerCase():Array.isArray(v)?v.map(f):v&&typeof v==='object'?Object.fromEntries(Object.entries(v).map(([k,x])=>[k,f(x)])):v;
console.log(JSON.stringify({hookSpecificOutput:{hookEventName:'PreToolUse',updatedInput:f(i.tool_input)}}));
});
