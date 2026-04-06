#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hugging Face Zugang pruefen — liest master.env.ini.
whoami/API: ausschliesslich HUGGINGFACE_TOKEN (Abschnitt ~Zeile 306). HF_TOKEN wird nur angezeigt, nicht fuer die API genutzt.
Gibt NIE den vollen Token aus (nur Laenge + Status).
"""
import json, pathlib, re, sys, urllib.error, urllib.request

INI = pathlib.Path(
    r"C:\Users\annah\Dropbox\Mein PC (LAPTOP-RQH448P4)\Downloads\EIRA\master.env.ini"
)
CACHE = pathlib.Path.home() / ".cache" / "huggingface" / "token"


def load_hf_from_ini() -> tuple[str | None, str | None]:
    if not INI.exists():
        return None, None
    txt = INI.read_text("utf-8", errors="replace")
    hf = re.search(r"^HF_TOKEN\s*=\s*(\S+)", txt, re.M)
    hg = re.search(r"^HUGGINGFACE_TOKEN\s*=\s*(\S+)", txt, re.M)
    return (
        hf.group(1).strip() if hf else None,
        hg.group(1).strip() if hg else None,
    )


def whoami(token: str) -> tuple[int, dict | None]:
    req = urllib.request.Request(
        "https://huggingface.co/api/whoami",
        headers={"Authorization": f"Bearer {token}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status, json.loads(r.read().decode("utf-8", errors="replace"))
    except urllib.error.HTTPError as e:
        try:
            body = json.loads(e.read().decode("utf-8", errors="replace"))
        except Exception:
            body = {"raw": str(e.code)}
        return e.code, body
    except Exception as ex:
        return -1, {"error": str(ex)}


def main() -> int:
    print("=== HF Healthcheck (keine Secrets in der Ausgabe) ===\n")
    t_ini, t_hg = load_hf_from_ini()
    # API nur mit HUGGINGFACE_TOKEN (~Zeile 306); HF_TOKEN ignorieren.
    if not t_hg:
        print("FEHL: HUGGINGFACE_TOKEN fehlt in master.env.ini (~Zeile 306).")
        print("      HF_TOKEN allein reicht fuer diesen Check nicht.")
        return 2
    primary = t_hg
    same = t_ini and t_hg and (t_ini == t_hg)
    print(f"INI: HF_TOKEN (nur Info, nicht fuer API)={'gesetzt' if t_ini else 'fehlt'} (Laenge {len(t_ini) if t_ini else 0})")
    print(f"INI: HUGGINGFACE_TOKEN (API)={'gesetzt' if t_hg else 'fehlt'} (Laenge {len(t_hg) if t_hg else 0})")
    print(f"HF_TOKEN == HUGGINGFACE_TOKEN: {same}\n")

    code, data = whoami(primary)
    if code == 200 and isinstance(data, dict):
        name = data.get("name") or data.get("id") or "?"
        print(f"whoami: OK (HTTP {code}) — angemeldet als: {name}")
        print("\nNaechster Schritt: hf auth login ist nicht noetig; API funktioniert.")
        return 0

    print(f"whoami: FEHLER (HTTP {code})")
    if isinstance(data, dict):
        print(f"Detail: {data.get('error', data)}")
    print(
        "\n*** Der Token in master.env.ini wird von Hugging Face abgelehnt (401). ***\n"
        "Moegliche Ursachen: Token widerrufen, abgelaufen, Tippfehler, oder falsch kopiert.\n\n"
        "So beheben:\n"
        "  1) https://huggingface.co/settings/tokens — neuen Access Token erstellen\n"
        "     (mindestens Read; fuer Spaces/Upload: Write oder fine-grained passend).\n"
        "  2) In master.env.ini HUGGINGFACE_TOKEN setzen (~Zeile 306) — dieser Check nutzt nur diesen Key.\n"
        "       Optional: HF_TOKEN=... nur fuer andere Tools, die diese Variable erwarten.\n"
        "  3) Optional: huggingface-cli login  (speichert unter ~/.cache/huggingface/token)\n"
        "  4) Dieses Skript erneut: python hf_healthcheck.py\n"
    )

    if CACHE.exists():
        tc = CACHE.read_text(encoding="utf-8", errors="replace").strip()
        c2, d2 = whoami(tc)
        print(f"\nLokaler Cache ~/.cache/huggingface/token: HTTP {c2} (Laenge Token {len(tc)})")
        if c2 == 200:
            print("Hinweis: Cache-Token funktioniert — INI auf denselben Wert setzen.")
        else:
            print("Hinweis: Cache-Token ist ebenfalls ungueltig; neuen Token verwenden.")

    return 1


if __name__ == "__main__":
    sys.exit(main())
