#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DDGK v2.0 — Privates Netzwerk + Credential-Health (read-only) + EIRA/ORION: naechster Schritt.
Secrets: nur aus master.env.ini oder Umgebung, niemals in Ausgabe/Repo.
"""
import json, datetime, hashlib, os, pathlib, time, urllib.error, urllib.parse, urllib.request

WS = pathlib.Path(__file__).resolve().parent
MEM = WS / "cognitive_ddgk" / "cognitive_memory.jsonl"
OUT = WS / "ZENODO_UPLOAD" / "DDGK_NEXT_STEP_REPORT.json"
try:
    from workspace_env import load_workspace_dotenv, resolve_master_ini_path

    load_workspace_dotenv(override=False)
    _INI_PATH = resolve_master_ini_path()
except ImportError:
    _INI_PATH = None

LOC = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
PI5 = os.environ.get("OLLAMA_PI5", "http://192.168.1.103:11434")

def _last_hash():
    if not MEM.exists():
        return ""
    ls = [l for l in MEM.read_text("utf-8").splitlines() if l.strip()]
    return json.loads(ls[-1]).get("hash", "") if ls else ""

def ddgk_log(agent, action, data):
    prev = _last_hash()
    e = {
        "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "agent": agent,
        "action": action,
        "data": data,
        "prev": prev,
        "ddgk_version": "2.0_passive_observer",
        "topic": "dev_next_step_network",
    }
    raw = json.dumps(e, ensure_ascii=False, sort_keys=True)
    e["hash"] = hashlib.sha256(raw.encode()).hexdigest()
    with MEM.open("a", encoding="utf-8") as f:
        f.write(json.dumps(e, ensure_ascii=False) + "\n")

def load_ini() -> dict:
    path = _INI_PATH
    if path is None or not path.is_file():
        return {}
    out = {}
    for line in path.read_text("utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            k, _, v = line.partition("=")
            k, v = k.strip(), v.strip()
            if k and v:
                out[k] = v
    return out

def pick(cfg: dict, *names: str) -> str | None:
    for n in names:
        v = os.environ.get(n, "").strip() or cfg.get(n, "").strip()
        if v:
            return v
    return None

def http_json(url, headers=None, timeout=20):
    req = urllib.request.Request(url, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read().decode("utf-8", errors="replace"))
    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode("utf-8", errors="replace")[:200]
        except Exception:
            body = ""
        return e.code, {"_error": body}
    except Exception as ex:
        return -1, {"_exc": str(ex)[:120]}

def check_hf(token: str | None) -> dict:
    if not token:
        return {"ok": False, "reason": "no_token"}
    st, data = http_json(
        "https://huggingface.co/api/whoami",
        headers={"Authorization": f"Bearer {token}"},
    )
    ok = st == 200 and isinstance(data, dict) and ("name" in data or "id" in data)
    return {"ok": ok, "http": st, "user": (data.get("name") or data.get("id")) if ok else None}

def check_hf_try_both(cfg: dict) -> dict:
    """Zwei moegliche Keys in INI (HF_TOKEN, HUGGINGFACE_TOKEN) nacheinander."""
    last: dict = {"ok": False, "reason": "no_hf_keys"}
    for key in ("HF_TOKEN", "HUGGINGFACE_TOKEN"):
        t = pick(cfg, key)
        if not t:
            continue
        r = check_hf(t)
        r["attempt"] = key
        last = r
        if r.get("ok"):
            r["key_used"] = key
            return r
    last["key_used"] = None
    return last

def check_github(token: str | None) -> dict:
    if not token:
        return {"ok": False, "reason": "no_token"}
    st, data = http_json(
        "https://api.github.com/user",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "ORION-DDGK-Health",
        },
    )
    ok = st == 200 and isinstance(data, dict) and "login" in data
    return {"ok": ok, "http": st, "login": data.get("login") if ok else None}

def check_serpapi(key: str | None) -> dict:
    if not key:
        return {"ok": False, "reason": "no_key"}
    q = urllib.parse.urlencode({"engine": "google", "q": "CCRN kappa", "api_key": key})
    st, data = http_json(f"https://serpapi.com/search.json?{q}")
    ok = st == 200 and isinstance(data, dict) and "error" not in str(data).lower()
    return {"ok": ok, "http": st}

def check_ollama(base: str) -> dict:
    st, data = http_json(f"{base.rstrip('/')}/api/tags")
    ok = st == 200 and isinstance(data, dict) and "models" in data
    n = len(data.get("models") or []) if ok else 0
    return {"ok": ok, "http": st, "models": n}

def check_news_api(key: str | None) -> dict:
    if not key:
        return {"ok": False, "reason": "no_key"}
    url = f"https://newsapi.org/v2/top-headlines?country=at&pageSize=1&apiKey={key}"
    st, _ = http_json(url)
    return {"ok": st == 200, "http": st}

def check_zenodo(token: str | None) -> dict:
    if not token:
        return {"ok": False, "reason": "no_token"}
    st, data = http_json(
        "https://zenodo.org/api/deposit/depositions?size=1",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    return {"ok": st == 200, "http": st}

def ollama_generate(base: str, model: str, prompt: str, timeout=90) -> tuple[str | None, float]:
    pl = json.dumps(
        {"model": model, "prompt": prompt, "stream": False, "options": {"num_predict": 280, "temperature": 0.45}}
    ).encode()
    req = urllib.request.Request(
        f"{base.rstrip('/')}/api/generate", data=pl, headers={"Content-Type": "application/json"}
    )
    try:
        t0 = time.time()
        with urllib.request.urlopen(req, timeout=timeout) as r:
            txt = json.loads(r.read()).get("response", "").strip()
            return txt, round(time.time() - t0, 1)
    except Exception:
        return None, -1.0

def main():
    cfg = load_ini()
    health = {
        "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "ini_loaded": bool(cfg),
        "huggingface": check_hf_try_both(cfg),
        "github": check_github(pick(cfg, "GITHUB_TOKEN", "GITHUB_PAT")),
        "serpapi": check_serpapi(pick(cfg, "SERPAPI_KEY")),
        "newsapi": check_news_api(pick(cfg, "NEWS_API_KEY")),
        "zenodo": check_zenodo(pick(cfg, "ZENODO_API_TOKEN", "ZENODO_TOKEN")),
        "ollama_local": check_ollama(LOC),
        "ollama_pi5": check_ollama(PI5),
    }
    ddgk_log(
        "DDGK-NET",
        "credential_health",
        {
            "huggingface": health["huggingface"].get("ok"),
            "github": health["github"].get("ok"),
            "serpapi": health["serpapi"].get("ok"),
            "newsapi": health["newsapi"].get("ok"),
            "zenodo": health["zenodo"].get("ok"),
            "ollama_local": health["ollama_local"].get("ok"),
            "ollama_pi5": health["ollama_pi5"].get("ok"),
        },
    )

    ctx = json.dumps(health, ensure_ascii=False)[:2000]
    prompt_base = f"""Du bist Teil des ORION-CCRN Lab (privates Netzwerk: Laptop, Pi5, optional Note10).
DDGK v2.0 Passive Observer ist aktiv.
Credential-Health (nur Status, keine Secrets): {ctx}

Was sind die 3 konkretesten ENTWICKLUNGS-Schritte fuer die naechsten 7 Tage?
Nummeriert 1-3, je 2 Saetze Deutsch, Prioritaet absteigend."""

    eira_m = "qwen2.5:1.5b"
    orion_m = "orion-genesis:latest"
    eira_r, eira_t = ollama_generate(LOC, eira_m, "Du bist EIRA.\n" + prompt_base, timeout=95)
    orion_r, orion_t = ollama_generate(LOC, orion_m, "Du bist ORION (Genesis).\n" + prompt_base, timeout=110)

    if eira_r:
        ddgk_log("EIRA", "next_step_dev", {"model": eira_m, "elapsed_s": eira_t, "preview": eira_r[:400]})
    else:
        ddgk_log("EIRA", "next_step_timeout", {"model": eira_m})
    if orion_r:
        ddgk_log("ORION", "next_step_dev", {"model": orion_m, "elapsed_s": orion_t, "preview": orion_r[:400]})
    else:
        ddgk_log("ORION", "next_step_timeout", {"model": orion_m})

    report = {
        "health": health,
        "eira": {"model": eira_m, "elapsed_s": eira_t, "text": eira_r},
        "orion": {"model": orion_m, "elapsed_s": orion_t, "text": orion_r},
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    ddgk_log("SYSTEM", "ddgk_next_step_report", {"path": str(OUT)})
    print("OK ->", OUT)
    print("EIRA:", (eira_r or "TIMEOUT")[:500])
    print("---")
    print("ORION:", (orion_r or "TIMEOUT")[:500])

if __name__ == "__main__":
    main()
