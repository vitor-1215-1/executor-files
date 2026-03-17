"""
BotManager v2 — Backend FastAPI
Suporte: Python (.py), Java (.java/.jar), Node.js (.js), Batch (.bat/.cmd), Shell (.sh)

Instalação:
    pip install fastapi uvicorn apscheduler

Uso:
    python server.py
    Acesse http://localhost:8000
"""

import os, sys, json, subprocess, threading, uuid, shutil
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

app = FastAPI(title="BotManager v2")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ── Estado ─────────────────────────────────────────────────────────────────────
scripts: dict = {}
processes: dict = {}
logs: dict = {}
run_counts: dict = {}
last_run: dict = {}
scheduler = BackgroundScheduler()
scheduler.start()

# ── Modelos ────────────────────────────────────────────────────────────────────
class ScriptConfig(BaseModel):
    id: str = ""
    name: str
    path: str
    args: str = ""
    schedule: str = ""
    enabled: bool = True
    lang: str = "auto"  # auto | python | java | node | jar | bat | sh

class InputPayload(BaseModel):
    text: str

# ── Detecção de linguagem ──────────────────────────────────────────────────────
def detect_lang(path: str) -> str:
    ext = Path(path).suffix.lower()
    return {
        ".py":   "python",
        ".js":   "node",
        ".java": "java",
        ".jar":  "jar",
        ".bat":  "bat",
        ".cmd":  "bat",
        ".sh":   "sh",
    }.get(ext, "unknown")

def lang_icon(lang: str) -> str:
    return {"python":"🐍","node":"🟩","java":"☕","jar":"☕","bat":"🪟","sh":"🐚"}.get(lang,"⚙️")

def build_cmd(cfg: dict):
    path = cfg["path"]
    args = cfg["args"].split() if cfg.get("args") else []
    lang = cfg.get("lang", "auto")
    if lang == "auto":
        lang = detect_lang(path)

    if lang == "python":
        return ("simple", [sys.executable, path] + args)

    elif lang == "node":
        node = shutil.which("node") or shutil.which("node.exe") or "node"
        return ("simple", [node, path] + args)

    elif lang == "java":
        javac = shutil.which("javac") or "javac"
        java  = shutil.which("java")  or "java"
        p = Path(path)
        return ("java", {"javac": javac, "java": java, "src": path,
                         "class_dir": str(p.parent), "class_name": p.stem, "args": args})

    elif lang == "jar":
        java = shutil.which("java") or "java"
        return ("simple", [java, "-jar", path] + args)

    elif lang == "bat":
        return ("simple", ["cmd.exe", "/c", path] + args)

    elif lang == "sh":
        bash = shutil.which("bash") or "/bin/bash"
        return ("simple", [bash, path] + args)

    return ("simple", [path] + args)

# ── Log helpers ────────────────────────────────────────────────────────────────
def append_log(sid: str, line: str, level: str = "info"):
    ts = datetime.now().strftime("%H:%M:%S")
    logs.setdefault(sid, []).append({"ts": ts, "msg": line, "lvl": level})
    if len(logs[sid]) > 1000:
        logs[sid] = logs[sid][-1000:]

def stream_output(sid: str, proc: subprocess.Popen):
    try:
        for raw in proc.stdout:
            line = raw.rstrip("\n")
            lvl = "err" if any(w in line.lower() for w in ["error","exception","traceback","fatal","stderr"]) else "info"
            append_log(sid, line, lvl)
        proc.wait()
        code = proc.returncode
        append_log(sid, f"── encerrado (código {code}) ──", "ok" if code == 0 else "err")
    except Exception as e:
        append_log(sid, f"[leitura] {e}", "err")
    finally:
        processes.pop(sid, None)

def _runtime_hint(lang):
    return {
        "python": "💡 Instale Python: https://python.org",
        "node":   "💡 Instale Node.js: https://nodejs.org",
        "java":   "💡 Instale JDK: https://adoptium.net",
        "jar":    "💡 Instale JRE/JDK: https://adoptium.net",
    }.get(lang, "💡 Verifique se o runtime está no PATH.")

# ── Executor ───────────────────────────────────────────────────────────────────
def run_script(sid: str):
    cfg = scripts.get(sid)
    if not cfg or not cfg.get("enabled", True):
        return
    if sid in processes:
        append_log(sid, "[AVISO] Script já está rodando.", "warn")
        return

    script_path = Path(cfg["path"])
    if not script_path.exists():
        append_log(sid, f"[ERRO] Arquivo não encontrado: {cfg['path']}", "err")
        return

    last_run[sid] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    run_counts[sid] = run_counts.get(sid, 0) + 1

    lang = cfg.get("lang", "auto")
    if lang == "auto":
        lang = detect_lang(cfg["path"])

    kind, cmd_data = build_cmd(cfg)

    # Java: compilar antes
    if kind == "java":
        j = cmd_data
        append_log(sid, f"☕ Compilando {Path(j['src']).name}...", "info")
        comp = subprocess.run(
            [j["javac"], j["src"]], capture_output=True, text=True, cwd=j["class_dir"]
        )
        if comp.returncode != 0:
            for line in (comp.stderr or "Erro de compilação").splitlines():
                append_log(sid, line, "err")
            return
        append_log(sid, "✔ Compilado com sucesso!", "ok")
        cmd = [j["java"], "-cp", j["class_dir"], j["class_name"]] + j["args"]
    else:
        cmd = cmd_data

    append_log(sid, f"▶ Iniciando: {' '.join(str(c) for c in cmd)}", "ok")

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.PIPE,
            text=True,
            bufsize=1,
            cwd=str(script_path.parent),
        )
        processes[sid] = proc
        threading.Thread(target=stream_output, args=(sid, proc), daemon=True).start()
    except FileNotFoundError as e:
        append_log(sid, f"[ERRO] Runtime não encontrado: {e}", "err")
        append_log(sid, _runtime_hint(lang), "warn")

def _stop(sid: str):
    proc = processes.pop(sid, None)
    if proc:
        try: proc.terminate()
        except: pass
        append_log(sid, "■ Parado manualmente.", "warn")

def _register_schedule(sid, cron):
    try:
        parts = cron.strip().split()
        if len(parts) != 5: return
        trigger = CronTrigger(minute=parts[0], hour=parts[1], day=parts[2], month=parts[3], day_of_week=parts[4])
        scheduler.add_job(run_script, trigger, args=[sid], id=f"job_{sid}", replace_existing=True)
    except Exception as e:
        print(f"[scheduler] {e}")

def _remove_schedule(sid):
    try: scheduler.remove_job(f"job_{sid}")
    except: pass

# ── API ────────────────────────────────────────────────────────────────────────
@app.get("/")
def index():
    p = Path(__file__).parent / "panel.html"
    return FileResponse(str(p)) if p.exists() else HTMLResponse("<h2>panel.html não encontrado na mesma pasta</h2>")

@app.get("/api/scripts")
def list_scripts():
    return [{
        **s,
        "running": sid in processes,
        "run_count": run_counts.get(sid, 0),
        "last_run": last_run.get(sid, "—"),
        "detected_lang": detect_lang(s["path"]) if s.get("lang","auto") == "auto" else s["lang"],
        "lang_icon": lang_icon(detect_lang(s["path"]) if s.get("lang","auto") == "auto" else s["lang"]),
    } for sid, s in scripts.items()]

@app.post("/api/scripts")
def add_script(cfg: ScriptConfig):
    sid = str(uuid.uuid4())[:8]
    scripts[sid] = {**cfg.dict(), "id": sid}
    logs[sid] = []
    if cfg.schedule: _register_schedule(sid, cfg.schedule)
    return scripts[sid]

@app.put("/api/scripts/{sid}")
def update_script(sid: str, cfg: ScriptConfig):
    if sid not in scripts: raise HTTPException(404)
    scripts[sid] = {**cfg.dict(), "id": sid}
    _remove_schedule(sid)
    if cfg.schedule: _register_schedule(sid, cfg.schedule)
    return scripts[sid]

@app.delete("/api/scripts/{sid}")
def delete_script(sid: str):
    if sid not in scripts: raise HTTPException(404)
    _stop(sid); _remove_schedule(sid)
    del scripts[sid]; logs.pop(sid, None)
    return {"ok": True}

@app.post("/api/scripts/{sid}/start")
def start(sid: str):
    if sid not in scripts: raise HTTPException(404)
    run_script(sid); return {"ok": True}

@app.post("/api/scripts/{sid}/stop")
def stop_route(sid: str):
    _stop(sid); return {"ok": True}

@app.post("/api/scripts/{sid}/restart")
def restart(sid: str):
    import time; _stop(sid); time.sleep(0.4); run_script(sid)
    return {"ok": True}

@app.post("/api/scripts/{sid}/input")
def send_input(sid: str, payload: InputPayload):
    proc = processes.get(sid)
    if not proc: raise HTTPException(400, "Processo não está rodando")
    try:
        proc.stdin.write(payload.text + "\n"); proc.stdin.flush()
    except Exception as e:
        raise HTTPException(500, str(e))
    return {"ok": True}

@app.get("/api/scripts/{sid}/logs")
def get_logs(sid: str, since: int = 0):
    all_logs = logs.get(sid, [])
    return {"lines": all_logs[since:], "total": len(all_logs)}

@app.delete("/api/scripts/{sid}/logs")
def clear_logs(sid: str):
    logs[sid] = []; return {"ok": True}

@app.get("/api/status")
def status():
    return {
        "total": len(scripts),
        "running": len(processes),
        "scheduled": sum(1 for s in scripts.values() if s.get("schedule")),
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 BotManager v2 → http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
