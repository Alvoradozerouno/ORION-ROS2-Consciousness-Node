#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""DDGK Vollständiger System-Status"""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

BASE = Path(__file__).parent / "cognitive_ddgk"

print("=" * 55)
print("  DDGK SYSTEM STATUS — 30.03.2026")
print("=" * 55)

# Decision Chain
try:
    from cognitive_ddgk.decision_chain import DDGKDecisionChain
    chain = DDGKDecisionChain()
    s = chain.stats()
    valid, _ = chain.verify_chain()
    print(f"\n[DECISION CHAIN]")
    print(f"  Entscheidungen  : {s['total']}")
    print(f"  ALLOW           : {s['allow']}")
    print(f"  REQUIRE_HUMAN   : {s['require_human']}")
    print(f"  HITL-flagged    : {s['hitl_flagged']}")
    print(f"  Avg Trust       : {s['avg_trust']}")
    print(f"  Chain-Integrit. : {'OK' if valid else 'FEHLER!'}")
    print(f"  Letzte Aktion   : {s['last_action']}")
except Exception as e:
    print(f"  [FEHLER] {e}")

# HyperAgent Memory
hyper_mem = BASE / "hyper_agent_memory.jsonl"
lines = [l for l in hyper_mem.read_text("utf-8").splitlines() if l.strip()] if hyper_mem.exists() else []
print(f"\n[HYPER AGENT]")
print(f"  Memory-Einträge : {len(lines)}")

tools = list((BASE / "synthesized_tools").glob("tool_*.py"))
print(f"  Synthetis. Tools: {len(tools)}")
for t in tools:
    print(f"    - {t.stem}")

# Autonomous Loop Memory
loop_mem = BASE / "autonomous_loop_memory.jsonl"
loop_lines = [l for l in loop_mem.read_text("utf-8").splitlines() if l.strip()] if loop_mem.exists() else []
print(f"\n[AUTONOMOUS LOOP]")
print(f"  Memory-Einträge : {len(loop_lines)}")

# Nuclear Audit Chain
nuc = BASE / "nuclear_audit_chain.jsonl"
nuc_lines = [l for l in nuc.read_text("utf-8").splitlines() if l.strip()] if nuc.exists() else []
print(f"\n[NUCLEAR SIMULATOR]")
print(f"  Audit-Einträge  : {len(nuc_lines)}")

# Cognitive Memory (SHA Chain)
cog = BASE / "cognitive_memory.jsonl"
cog_lines = [l for l in cog.read_text("utf-8").splitlines() if l.strip()] if cog.exists() else []
print(f"\n[COGNITIVE MEMORY (SHA-256)]")
print(f"  Einträge        : {len(cog_lines)}")

print(f"\n{'=' * 55}")
print(f"  GESAMT: {len(lines)+len(loop_lines)+len(nuc_lines)+len(cog_lines)+s.get('total',0)} Audit-Einträge")
print(f"{'=' * 55}")
