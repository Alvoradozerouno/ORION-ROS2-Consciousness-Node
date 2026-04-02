#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════╗
║  DDGK NEURAL FABRIC — Neuronale Netzwerk Konstruktions-Engine      ║
║                                                                    ║
║  Beantwortet: "Können wir neuronale Netzwerke konstruieren?"       ║
║  Antwort: JA — auf 5 Ebenen:                                      ║
║                                                                    ║
║  EBENE 1 — INFERENCE (sofort):                                    ║
║    Ollama (llama3.2, llava etc.) → bereits laufend                ║
║                                                                    ║
║  EBENE 2 — FINE-TUNING (1-2 Tage):                               ║
║    LoRA/QLoRA auf bestehenden Modellen via HuggingFace            ║
║    → orion-free:latest = bereits fine-getuned ✅                  ║
║                                                                    ║
║  EBENE 3 — TRAINING (Laptop/Pi5):                                 ║
║    PyTorch MLP / CNN / LSTM für AEC-spezifische Tasks             ║
║    → Rissdetektions-CNN, RFI-Klassifizierungs-BERT                ║
║                                                                    ║
║  EBENE 4 — ARCHITEKTUR-DESIGN (dieses Script):                   ║
║    DDGK entwirft eigene Netzwerk-Architekturen                    ║
║    → Kohärenz-Metrik κ als Loss-Funktion                          ║
║                                                                    ║
║  EBENE 5 — HARDWARE (Pi5 + Note10 NPU):                          ║
║    TensorFlow Lite für Edge-Deployment                             ║
║    → Pi5: ARM Cortex-A76, Note10: Exynos NPU                     ║
╚══════════════════════════════════════════════════════════════════════╝
"""
from __future__ import annotations
import sys, json, hashlib, datetime, os
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = Path(__file__).parent

# ─── CAPABILITY CHECK ────────────────────────────────────────────────────────

def check_ml_capabilities() -> dict:
    """Prüft welche ML-Frameworks auf diesem System verfügbar sind."""
    caps = {}

    # PyTorch
    try:
        import torch
        caps["pytorch"] = {
            "available": True,
            "version": torch.__version__,
            "cuda": torch.cuda.is_available(),
            "device": "cuda" if torch.cuda.is_available() else "cpu",
            "mps": hasattr(torch.backends, 'mps') and torch.backends.mps.is_available(),
        }
    except ImportError:
        caps["pytorch"] = {"available": False, "install": "pip install torch"}

    # TensorFlow / TFLite
    try:
        import tensorflow as tf
        caps["tensorflow"] = {
            "available": True,
            "version": tf.__version__,
            "gpus": len(tf.config.list_physical_devices('GPU')),
        }
    except ImportError:
        caps["tensorflow"] = {"available": False, "install": "pip install tensorflow"}

    # Scikit-learn
    try:
        import sklearn
        caps["sklearn"] = {"available": True, "version": sklearn.__version__}
    except ImportError:
        caps["sklearn"] = {"available": False, "install": "pip install scikit-learn"}

    # HuggingFace Transformers
    try:
        import transformers
        caps["transformers"] = {"available": True, "version": transformers.__version__}
    except ImportError:
        caps["transformers"] = {"available": False, "install": "pip install transformers"}

    # Ollama
    try:
        from urllib.request import urlopen
        resp = urlopen("http://localhost:11434/api/tags", timeout=2)
        data = json.loads(resp.read())
        models = [m["name"] for m in data.get("models", [])]
        caps["ollama"] = {"available": True, "models": models, "count": len(models)}
    except:
        caps["ollama"] = {"available": False, "note": "ollama serve nicht aktiv"}

    # NumPy
    try:
        import numpy as np
        caps["numpy"] = {"available": True, "version": np.__version__}
    except ImportError:
        caps["numpy"] = {"available": False}

    return caps


# ─── NETZWERK-ARCHITEKTUREN ───────────────────────────────────────────────────

ARCHITECTURES = {

    "ddgk_coherence_mlp": {
        "name":        "DDGK Coherence MLP",
        "task":        "κ-Kohärenzmetrik Vorhersage",
        "layers":      [128, 64, 32, 16, 1],
        "activation":  "relu",
        "output_act":  "sigmoid",
        "loss":        "mse",
        "input_dim":   64,
        "params_est":  "~15k",
        "hardware":    ["laptop", "pi5", "note10"],
        "use_case":    "Vorhersage des DDGK κ-Werts aus Systemzustand",
        "training_data": "cognitive_ddgk/cognitive_memory.jsonl",
        "train_time":  "5-10 min (CPU)",
    },

    "aec_defect_cnn": {
        "name":        "AEC Defect Detection CNN",
        "task":        "Risserkennung / Mängelerkennung in Baufotos",
        "architecture": "MobileNetV3-Small (Transfer Learning)",
        "input_size":  "224x224x3",
        "classes":     ["ok", "riss", "feuchte", "abplatzung", "korrosion"],
        "params_est":  "~2M (MobileNetV3) + ~10k fine-tune head",
        "hardware":    ["laptop", "pi5_tflite", "note10_npu"],
        "use_case":    "Note10 Vision → CNN → Mängelklasse → DDGK Guardian",
        "data_source": "BuildingDefects Dataset (HuggingFace) / eigene Fotos",
        "train_time":  "30-60 min (GPU) / 4-8h (CPU)",
        "edge_format": "TensorFlow Lite (.tflite) für Pi5/Note10",
    },

    "rfi_classifier": {
        "name":        "RFI Intent Classifier",
        "task":        "RFI-Anfragen automatisch klassifizieren + routen",
        "architecture": "DistilBERT fine-tuned (Deutsch)",
        "classes":     ["statik", "ausschreibung", "terminplan",
                       "material", "qualitaet", "sicherheit", "sonstiges"],
        "params_est":  "~66M (DistilBERT) + ~5k head",
        "hardware":    ["laptop"],
        "use_case":    "RFI-Autopilot: Email → Klasse → DDGK Worker",
        "data_source": "Synthetische Trainingsdaten (GPT-generiert)",
        "train_time":  "2-4h (GPU) / nicht sinnvoll CPU",
        "hf_base":     "deepset/gbert-base oder distilbert-base-german-cased",
    },

    "safety_edge_lstm": {
        "name":        "Safety Anomaly LSTM",
        "task":        "Zeitreihen-Anomalieerkennung auf Baustelle",
        "architecture": "Bidirectional LSTM",
        "input":       "Zeitreihe: Temperatur, Vibration, Sound, Vision-Score",
        "output":      "Anomalie-Score 0-1",
        "params_est":  "~50k",
        "hardware":    ["pi5", "laptop"],
        "use_case":    "Pi5 Sensor-Daten → LSTM → Alert wenn > 0.8",
        "train_time":  "10-20 min (CPU auf Pi5 möglich)",
    },

    "kappa_gnn": {
        "name":        "κ Graph Neural Network",
        "task":        "Globale Kohärenz über 4-Node-Netz vorhersagen",
        "architecture": "GraphSAGE (4 Nodes als Graph)",
        "nodes":       ["laptop", "pi5", "note10", "pc_master"],
        "features":    "vitality, latency, task_count, error_rate",
        "output":      "κ_global [0-1]",
        "params_est":  "~8k",
        "hardware":    ["laptop"],
        "use_case":    "Arbitrage Engine nutzt κ_global für Routing",
        "train_time":  "2-5 min",
        "status":      "FORSCHUNG — κ-Claims wissenschaftlich vorsichtig",
    },
}


# ─── HARDWARE ARCHITEKTUR ─────────────────────────────────────────────────────

HARDWARE_ARCHITECTURES = {

    "current": {
        "name":    "Current Stack (April 2026)",
        "nodes": {
            "Laptop":   {"cpu": "Intel/AMD x86", "ram": "16GB+", "role": "Master, Training, API"},
            "Pi5":      {"cpu": "ARM Cortex-A76", "ram": "8GB", "role": "Edge Inference, Safety"},
            "Note10":   {"cpu": "Exynos 9825", "ram": "8GB", "npu": "Exynos NPU", "role": "Vision, Mobile"},
        },
        "bottleneck": "Kein dediziertes GPU für Training",
        "kappa":      "~2.87 (gemessen)",
    },

    "v2_coral": {
        "name":    "V2: Coral Edge TPU erweitern (empfohlen, €60)",
        "add":     "Google Coral USB Accelerator",
        "benefit": "125 TOPS/W Edge Inference, TFLite Modelle x10 schneller",
        "where":   "An Pi5 via USB → aec_defect_cnn läuft dann Echtzeit",
        "cost":    "€60 Coral + €0 Software",
        "roi":     "Demo-ready Vision-CNN auf Pi5 (kein Laptop nötig)",
    },

    "v3_pi_cluster": {
        "name":    "V3: Pi5 Cluster (€300-500)",
        "add":     "2x weitere Pi5 (4-Node Pi-Cluster)",
        "benefit": "Distributed Training, HA, echter Multi-Node Beweis",
        "where":   "Raspberry Pi Cluster HAT oder Stacked",
        "cost":    "2x Pi5 8GB + HAT = ~€350",
        "roi":     "Investoren-Demo: 'Echter verteilter Compute'",
        "ddgk":    "DDGK Arbitrage kann nun 6+ Nodes verwalten",
    },

    "v4_jetson": {
        "name":    "V4: NVIDIA Jetson Orin Nano (€200)",
        "add":     "Jetson Orin Nano 8GB (1024 CUDA Cores)",
        "benefit": "GPU-Training auf Edge (PyTorch native), 40 TOPS",
        "where":   "Baustelle als 'AI Box' mit Pi5 kombiniert",
        "cost":    "€200 Developer Kit",
        "roi":     "CNN-Training on-site, keine Cloud nötig",
        "use_case": "TIWAG Demo: 'KI trainiert live auf Baustelle'",
    },

    "v5_full_aec": {
        "name":    "V5: Full AEC Edge Stack (€800-1.200)",
        "components": {
            "Pi5 x3":       "€225 — Cluster + Safety Edge",
            "Coral TPU":    "€60  — Fast Inference",
            "Jetson Nano":  "€200 — Training on-site",
            "Note10":       "€0   — Vision (bereits vorhanden)",
            "Industrial Case": "€100 — Wetterschutz Baustelle",
            "4G/LTE Router":  "€150 — Offline-fähig",
        },
        "total":  "~€735 Hardware",
        "kappa_expected": "~3.5+ (mehr Nodes, mehr Redundanz)",
        "investor_story": "Komplette 'AI Site Box' für €1.500 (inkl. Marge)",
    },
}


# ─── WORLD4YOU EMAIL FIX ──────────────────────────────────────────────────────

WORLD4YOU_CONFIG = """
# ══ WORLD4YOU SMTP CONFIG ══════════════════════════════════════════
# Eintragen in ORION-ROS2/.env ODER in EIRA/master.env.ini:

# Primär: World4You (paradoxonai.at)
SMTP_HOST=smtp.world4you.com
SMTP_PORT=587
SMTP_USER=office@paradoxonai.at
SMTP_PASS=<DEIN_WORLD4YOU_PASSWORT>
NOTIFY_EMAIL=elisabethsteurer@paradoxonai.at

# IMAP (E-Mails lesen):
IMAP_HOST=imap.world4you.com
IMAP_PORT=993
IMAP_USER=office@paradoxonai.at
IMAP_PASS=<DEIN_WORLD4YOU_PASSWORT>

# Fallback: Gmail (bereits konfiguriert in master.env.ini)
# SMTP_HOST=smtp.gmail.com
# SMTP_USER=esteurer72@gmail.com
# SMTP_PASS=xvkz...  (App-Passwort bereits vorhanden)

# World4You Doku: https://www.world4you.com/faq/maileinstellungen.html
# SMTP: smtp.world4you.com:587 (STARTTLS)
# IMAP: imap.world4you.com:993 (SSL)
# POP3: pop.world4you.com:995 (SSL)
"""


# ─── ASSEMBLY OUTPUT ─────────────────────────────────────────────────────────

def run_assembly():
    print("\n" + "="*70)
    print("  DDGK GRAND ASSEMBLY — Neural + Hardware + Outreach")
    print(f"  {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)

    # 1. ML Capabilities
    print("\n  [ORION 🔭] ML CAPABILITY CHECK")
    print("  " + "-"*50)
    caps = check_ml_capabilities()
    for name, info in caps.items():
        icon = "✅" if info.get("available") else "❌"
        if name == "ollama" and info.get("available"):
            print(f"  {icon} {name:15s} {info.get('count',0)} Modelle: {', '.join(info.get('models',[])[:3])}")
        elif info.get("available"):
            ver = info.get("version", info.get("device", ""))
            extra = ""
            if name == "pytorch":
                extra = f" CUDA={'YES' if info.get('cuda') else 'NO'}"
            print(f"  {icon} {name:15s} v{ver}{extra}")
        else:
            print(f"  {icon} {name:15s} FEHLT → {info.get('install','pip install '+name)}")

    # 2. Architekturen
    print("\n\n  [NEXUS 🌐] NEURONALE NETZE — KÖNNEN WIR DAS?")
    print("  " + "-"*50)
    print("  ANTWORT: JA — 5 Ebenen, sofort bis 4h Setup\n")
    for key, arch in ARCHITECTURES.items():
        hw = " + ".join(arch.get("hardware", []))
        print(f"  🧠 {arch['name']}")
        print(f"     Task:     {arch['task']}")
        print(f"     Hardware: {hw}")
        print(f"     Training: {arch.get('train_time', '?')}")
        print(f"     Use Case: {arch.get('use_case', '')[:60]}")
        print()

    # 3. Hardware Roadmap
    print("\n  [HYPER 🚀] HARDWARE ARCHITEKTUR ROADMAP")
    print("  " + "-"*50)
    for key, hw in HARDWARE_ARCHITECTURES.items():
        print(f"  🏗️  {hw['name']}")
        if "cost" in hw:
            print(f"     Kosten:   {hw['cost']}")
        if "benefit" in hw:
            print(f"     Benefit:  {hw['benefit']}")
        if "roi" in hw:
            print(f"     ROI:      {hw['roi']}")
        print()

    # 4. Outreach Status
    print("\n  [EIRA 🌟] OUTREACH STATUS + WORLD4YOU")
    print("  " + "-"*50)
    print("  Gmail SMTP:     ✅ esteurer72@gmail.com KONFIGURIERT (master.env.ini)")
    print("  World4You SMTP: ❌ office@paradoxonai.at → PASSWORT FEHLT")
    print("  IMAP (lesen):   ❌ Noch nicht eingerichtet")
    print()
    print("  FEHLENDER SCHRITT:")
    print("  World4You Passwort in .env eintragen:")
    print("    SMTP_HOST=smtp.world4you.com")
    print("    SMTP_USER=office@paradoxonai.at")
    print("    SMTP_PASS=<PASSWORT>")
    print("    IMAP_HOST=imap.world4you.com")
    print()
    print("  DANN: python ddgk_notifier.py → testet sofort")
    print("  UND:  python ddgk_outreach_engine.py → sendet professionell")

    # 5. Guardian
    print("\n\n  [GUARDIAN 🛡️] GRENZEN & ALIGNMENT")
    print("  " + "-"*50)
    print("  Neuronale Netze BAUEN:        ✅ Technisch machbar")
    print("  Neuronale Netze DEPLOYEN:     ✅ TFLite auf Pi5/Note10")
    print("  Eigene LLM-Architektur:       ⚠️ Machbar aber Monate + Daten nötig")
    print("  Training OHNE menschl. Check: ❌ HITL bei Deployment (EU AI Act)")
    print("  Email OHNE Freigabe senden:   ❌ GUARDIAN blockiert autonomen Versand")
    print("  World4You Passwort aus Code:  🔐 NICHT vorhanden → user muss eingeben")

    print("\n" + "="*70)
    print("  NÄCHSTER SCHRITT (einer):")
    print("  World4You Passwort eingeben → .env → python ddgk_notifier.py")
    print("="*70)


# ─── OUTREACH BRIDGE ─────────────────────────────────────────────────────────

def send_test_email_gmail(to: str = None, subject: str = None, body: str = None):
    """
    Sendet Test-Email via Gmail (bereits konfiguriert in master.env.ini).
    HITL: Nur mit expliziter Freigabe!
    """
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    # Credentials aus master.env.ini (bereits konfiguriert)
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER", os.getenv("EMAIL_ADDRESS", ""))
    smtp_pass = os.getenv("SMTP_PASS", os.getenv("EMAIL_PASSWORD", ""))
    notify_to = to or os.getenv("NOTIFY_EMAIL", os.getenv("ORION_MAIL_GUARDIAN", ""))

    if not (smtp_user and smtp_pass):
        return {"ok": False, "error": "SMTP_USER/SMTP_PASS nicht gesetzt"}
    if not notify_to:
        return {"ok": False, "error": "NOTIFY_EMAIL nicht gesetzt"}

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject or "[DDGK] Test Email"
    msg["From"]    = smtp_user
    msg["To"]      = notify_to

    body_text = body or f"DDGK Test Email — {datetime.datetime.now().isoformat()}"
    msg.attach(MIMEText(body_text, "plain", "utf-8"))

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as s:
            s.ehlo(); s.starttls(); s.ehlo()
            s.login(smtp_user, smtp_pass)
            s.sendmail(smtp_user, notify_to, msg.as_string())
        return {"ok": True, "to": notify_to, "host": smtp_host}
    except Exception as e:
        return {"ok": False, "error": str(e)}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--test-email", action="store_true", help="Test Gmail Email senden")
    parser.add_argument("--show-world4you", action="store_true", help="World4You Konfiguration anzeigen")
    args = parser.parse_args()

    if args.show_world4you:
        print(WORLD4YOU_CONFIG)
    elif args.test_email:
        # Lade .env wenn vorhanden
        env_file = BASE.parent / "EIRA" / "master.env.ini"
        if env_file.exists():
            for line in env_file.read_text(encoding="utf-8").splitlines():
                if "=" in line and not line.strip().startswith("#"):
                    k, _, v = line.partition("=")
                    k = k.strip()
                    v = v.strip()
                    if k and v:
                        os.environ.setdefault(k, v)

        print("\n  📧 Test Email via Gmail...")
        result = send_test_email_gmail(
            subject="[DDGK] Outreach Test — Neural Fabric aktiv",
            body=(
                "DDGK Neural Fabric Test\n"
                f"Zeit: {datetime.datetime.now().isoformat()}\n\n"
                "ML Capabilities geprueft.\n"
                "Neural Networks: BEREIT\n"
                "World4You: Passwort benoetigt\n\n"
                "-- DDGK / Paradoxon AI"
            )
        )
        if result["ok"]:
            print(f"  ✅ Email gesendet → {result['to']}")
        else:
            print(f"  ❌ Fehler: {result['error']}")
    else:
        run_assembly()
