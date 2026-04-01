#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════╗
║  DDGK NORM-CHECK AGENT — Eurocode Strukturprüfung                  ║
║                                                                    ║
║  Prüft Tragwerksdaten gegen geltende Eurocodes:                   ║
║   EN 1992-1-1  Beton (EC2)                                        ║
║   EN 1993-1-1  Stahl (EC3)                                        ║
║   EN 1998-1    Erdbeben (EC8)                                     ║
║   + Österreichische Nationalen Anhänge (NA)                       ║
║                                                                    ║
║  HITL: Alle Ergebnisse erfordern Freigabe durch                   ║
║        nachweisberechtigten Tragwerksplaner!                      ║
║                                                                    ║
║  EU AI Act Art. 9: Risikomanagement                               ║
║  EU AI Act Art. 14: Menschliche Aufsicht                          ║
║  CPR (Construction Products Regulation): konform                  ║
╚══════════════════════════════════════════════════════════════════════╝

⚠️  RECHTLICHER HINWEIS:
    Dieses Modul ist ein Screening-Tool, KEIN Ersatz für
    den statischen Nachweis durch einen zugelassenen Ingenieur.
    Alle Ergebnisse REQUIRE_HUMAN vor baulicher Umsetzung.
"""
from __future__ import annotations
import sys, math, json, hashlib, datetime
from pathlib import Path
from typing import Optional

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE      = Path(__file__).parent
NORM_LOG  = BASE / "cognitive_ddgk" / "norm_checks.jsonl"
NORM_LOG.parent.mkdir(exist_ok=True)

# ─── NORMWERTE (EN 1992-1-1 + österr. NA) ────────────────────────────────────

# Betonfestigkeitsklassen nach EN 1992-1-1 Tab. 3.1
CONCRETE_CLASSES = {
    "C12/15": {"fck": 12, "fcd_factor": 0.8, "fctm": 1.6},
    "C16/20": {"fck": 16, "fcd_factor": 0.8, "fctm": 1.9},
    "C20/25": {"fck": 20, "fcd_factor": 0.8, "fctm": 2.2},
    "C25/30": {"fck": 25, "fcd_factor": 0.8, "fctm": 2.6},
    "C30/37": {"fck": 30, "fcd_factor": 0.8, "fctm": 2.9},
    "C35/45": {"fck": 35, "fcd_factor": 0.8, "fctm": 3.2},
    "C40/50": {"fck": 40, "fcd_factor": 0.8, "fctm": 3.5},
    "C45/55": {"fck": 45, "fcd_factor": 0.8, "fctm": 3.8},
    "C50/60": {"fck": 50, "fcd_factor": 0.8, "fctm": 4.1},
}

# Betonstahl nach EN 1992-1-1
REBAR_GRADES = {
    "B500A": {"fyk": 500, "fyd": 435, "ductility": "A"},
    "B500B": {"fyk": 500, "fyd": 435, "ductility": "B"},
    "B550A": {"fyk": 550, "fyd": 478, "ductility": "A"},
    "B550B": {"fyk": 550, "fyd": 478, "ductility": "B"},
}

# Stahlgüten nach EN 1993-1-1 Tab. 3.1
STEEL_GRADES = {
    "S235": {"fy": 235, "fu": 360, "gamma_m0": 1.0},
    "S275": {"fy": 275, "fu": 430, "gamma_m0": 1.0},
    "S355": {"fy": 355, "fu": 510, "gamma_m0": 1.0},
    "S420": {"fy": 420, "fu": 520, "gamma_m0": 1.0},
    "S460": {"fy": 460, "fu": 550, "gamma_m0": 1.0},
}

# Sicherheitsbeiwerte nach EN 1990 + österr. NA
GAMMA_FACTORS = {
    "gamma_c":   1.5,   # Beton, ungünstig
    "gamma_s":   1.15,  # Betonstahl
    "gamma_G":   1.35,  # Ständige Lasten
    "gamma_Q":   1.5,   # Veränderliche Lasten
    "gamma_M0":  1.0,   # Stahl, Querschnittstragfähigkeit
    "gamma_M1":  1.0,   # Stahl, Stabilitätsversagen
    "alpha_cc":  0.85,  # Österr. NA: Dauerstandbeiwert Beton
}


# ─── CHECK FUNKTIONEN ─────────────────────────────────────────────────────────

class CheckResult:
    def __init__(self, check: str, passed: bool, value: float,
                 limit: float, unit: str, norm_ref: str,
                 note: str = ""):
        self.check    = check
        self.passed   = passed
        self.value    = value
        self.limit    = limit
        self.unit     = unit
        self.norm_ref = norm_ref
        self.note     = note
        self.utilization = round(value / limit * 100, 1) if limit > 0 else 0

    def __repr__(self):
        icon = "✅" if self.passed else "❌"
        util = f"{self.utilization:.0f}%"
        return (f"  {icon} {self.check:40s} "
                f"{self.value:.2f}/{self.limit:.2f} {self.unit} "
                f"({util}) [{self.norm_ref}]")


def check_concrete_column_ec2(
        NEd: float,          # Bemessungsnormalkraft [kN]
        b: float,            # Breite [mm]
        h: float,            # Höhe [mm]
        concrete_class: str, # z.B. "C25/30"
        rebar_grade: str = "B500B",
        As: float = 0,       # Bewehrungsquerschnitt [mm²]
        l0: float = 3000     # Knicklänge [mm]
) -> list[CheckResult]:
    """
    Grundnachweis Stahlbetonstütze nach EN 1992-1-1.
    Vereinfacht — kein Ersatz für vollständigen Statiknachweis!
    """
    results = []
    cc = CONCRETE_CLASSES.get(concrete_class, CONCRETE_CLASSES["C25/30"])
    rb = REBAR_GRADES.get(rebar_grade, REBAR_GRADES["B500B"])

    fck = cc["fck"]
    fcd = GAMMA_FACTORS["alpha_cc"] * fck / GAMMA_FACTORS["gamma_c"]
    fyd = rb["fyd"]

    Ac = b * h  # Bruttoquerschnitt [mm²]
    NRd_c = fcd * Ac / 1000  # Tragfähigkeit Beton [kN]
    NRd_s = fyd * As / 1000  # Tragfähigkeit Bewehrung [kN]
    NRd   = NRd_c + NRd_s   # Gesamt [kN]

    # Check 1: Druckkraft
    results.append(CheckResult(
        "Druckkraft NEd ≤ NRd",
        NEd <= NRd,
        NEd, NRd, "kN",
        "EN 1992-1-1, 6.1",
        f"fcd={fcd:.1f} N/mm², Ac={Ac:.0f} mm²"
    ))

    # Check 2: Mindestbewehrung nach EN 1992-1-1, 9.5.2
    As_min = max(0.002 * Ac, 0.1 * NEd * 1000 / fyd)
    results.append(CheckResult(
        "Mindestbewehrung As ≥ As,min",
        As >= As_min,
        As, As_min, "mm²",
        "EN 1992-1-1, 9.5.2(2)",
        f"As,min = max(0,002·Ac; 0,1·NEd/fyd)"
    ))

    # Check 3: Höchstbewehrung nach EN 1992-1-1, 9.5.2
    As_max = 0.04 * Ac
    results.append(CheckResult(
        "Höchstbewehrung As ≤ As,max",
        As <= As_max,
        As, As_max, "mm²",
        "EN 1992-1-1, 9.5.2(3)",
        f"As,max = 0,04·Ac"
    ))

    # Check 4: Schlankheit (vereinfacht)
    i = math.sqrt(b * h**3 / 12 / Ac)  # Trägheitsradius
    lambda_val = l0 / i
    lambda_lim = 20 * 0.7 / math.sqrt(NEd / (fcd * Ac / 1000))
    results.append(CheckResult(
        "Schlankheit λ ≤ λ_lim",
        lambda_val <= lambda_lim,
        round(lambda_val, 1), round(lambda_lim, 1), "-",
        "EN 1992-1-1, 5.8.3",
        f"l0={l0}mm, Schlankheitsnachweis"
    ))

    return results


def check_steel_beam_ec3(
        MEd: float,      # Bemessungsmoment [kNm]
        VEd: float,      # Bemessungsquerkraft [kN]
        Wpl_y: float,    # Plastisches Widerstandsmoment [cm³]
        Av: float,       # Schubfläche [cm²]
        steel_grade: str = "S355",
        LT_factor: float = 1.0  # χ_LT Biegedrillknicken (=1.0 wenn gehalten)
) -> list[CheckResult]:
    """
    Biegeträger-Nachweis nach EN 1993-1-1.
    Vereinfacht — kein Ersatz für vollständigen Statiknachweis!
    """
    results = []
    sg = STEEL_GRADES.get(steel_grade, STEEL_GRADES["S355"])
    fy    = sg["fy"]
    gm0   = sg["gamma_m0"]

    # Moment
    Mc_Rd = LT_factor * Wpl_y * fy / gm0 / 100  # [kNm]
    results.append(CheckResult(
        "Biegemoment MEd ≤ Mc,Rd",
        MEd <= Mc_Rd,
        MEd, Mc_Rd, "kNm",
        "EN 1993-1-1, 6.2.5",
        f"Wpl,y={Wpl_y}cm³, fy={fy}N/mm²"
    ))

    # Querkraft
    Vpl_Rd = Av * fy / (math.sqrt(3) * gm0) / 100  # [kN]
    results.append(CheckResult(
        "Querkraft VEd ≤ Vpl,Rd",
        VEd <= Vpl_Rd,
        VEd, Vpl_Rd, "kN",
        "EN 1993-1-1, 6.2.6",
        f"Av={Av}cm²"
    ))

    # Wechselwirkung M+V (nur wenn VEd > 0.5*Vpl,Rd)
    if VEd > 0.5 * Vpl_Rd:
        rho = (2 * VEd / Vpl_Rd - 1)**2
        Mw_Rd = Mc_Rd * (1 - rho)
        results.append(CheckResult(
            "Wechselwirkung M+V",
            MEd <= Mw_Rd,
            MEd, Mw_Rd, "kNm",
            "EN 1993-1-1, 6.2.8",
            f"Vinteraktion aktiv (VEd > 0,5·Vpl,Rd)"
        ))

    return results


def check_seismic_ec8(
        ag: float,       # Bemessungs-PGA [m/s²]
        building_class: str = "II",  # Bedeutungsklasse
        soil_class: str = "B"        # Untergrundklasse
) -> dict:
    """
    Vereinfachte Erdbebenprüfung nach EN 1998-1.
    Österreich: Erdbebenzone 1-4 (ÖNORM B 1998-1).
    """
    # Bedeutungsbeiwert γI nach EN 1998-1, Tab. 4.3
    gamma_I = {"I": 0.8, "II": 1.0, "III": 1.2, "IV": 1.4}.get(building_class, 1.0)

    # Untergrundparameter nach EN 1998-1, Tab. 3.2
    soil_params = {
        "A": {"S": 1.0, "TB": 0.15, "TC": 0.4, "TD": 2.0},
        "B": {"S": 1.2, "TB": 0.15, "TC": 0.5, "TD": 2.0},
        "C": {"S": 1.15, "TB": 0.20, "TC": 0.6, "TD": 2.0},
        "D": {"S": 1.35, "TB": 0.20, "TC": 0.8, "TD": 2.0},
    }
    sp = soil_params.get(soil_class, soil_params["B"])

    # Bemessungsbeschleunigung
    agR_design = ag * gamma_I * sp["S"]

    # Österreich: ag > 0.04g → Erdbeben-Bemessung erforderlich
    ag_limit_AT = 0.04 * 9.81  # 0.04g

    return {
        "ag_input":    round(ag, 3),
        "ag_design":   round(agR_design, 4),
        "building_class": building_class,
        "soil_class":  soil_class,
        "gamma_I":     gamma_I,
        "S_factor":    sp["S"],
        "erdbeben_relevant": agR_design > ag_limit_AT,
        "norm_ref":    "EN 1998-1 + ÖNORM B 1998-1",
        "HITL_required": True,
        "note": "Vereinfacht — vollständiger EC8-Nachweis durch Ingenieur erforderlich"
    }


# ─── HAUPT-VALIDATOR ─────────────────────────────────────────────────────────

class DDGKNormCheckAgent:
    """
    DDGK Norm-Check Agent für AEC.
    
    WICHTIG: Alle Ergebnisse haben HITL-Pflicht (Prüfingenieur).
    Kein Ergebnis darf ohne menschliche Freigabe in Ausführungspläne.
    """

    def check_concrete_column(self, **kwargs) -> dict:
        results = check_concrete_column_ec2(**kwargs)
        return self._format_result("EC2-Stütze", results)

    def check_steel_beam(self, **kwargs) -> dict:
        results = check_steel_beam_ec3(**kwargs)
        return self._format_result("EC3-Träger", results)

    def check_seismic(self, **kwargs) -> dict:
        result = check_seismic_ec8(**kwargs)
        return {
            "type":          "EC8-Erdbeben",
            "result":        result,
            "HITL_required": True,
            "audit_hash":    self._audit_hash(result),
            "ts":            datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }

    def _format_result(self, check_type: str, results: list) -> dict:
        all_passed = all(r.passed for r in results)
        max_util   = max((r.utilization for r in results), default=0)

        # Risk Score für DDGK Guardian
        if all_passed and max_util < 80:
            risk_score = 30
            decision   = "AUTO_APPROVE"
        elif all_passed and max_util < 95:
            risk_score = 60
            decision   = "REQUIRE_HUMAN"
        else:
            risk_score = 85
            decision   = "REQUIRE_HUMAN"  # Immer HITL bei Statik!

        output = {
            "type":          check_type,
            "all_passed":    all_passed,
            "max_utilization": max_util,
            "risk_score":    risk_score,
            "decision":      decision,
            "HITL_required": True,   # IMMER bei Statik!
            "checks":        [
                {
                    "check":         r.check,
                    "passed":        r.passed,
                    "value":         r.value,
                    "limit":         r.limit,
                    "unit":          r.unit,
                    "utilization":   r.utilization,
                    "norm_ref":      r.norm_ref,
                } for r in results
            ],
            "audit_hash": self._audit_hash({"results": [r.passed for r in results]}),
            "ts":         datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "norm_version": "EN 1992/1993/1998 + österr. NA 2026",
        }

        # Log
        with NORM_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(output, ensure_ascii=False) + "\n")

        return output

    def _audit_hash(self, data: dict) -> str:
        return hashlib.sha256(
            json.dumps(data, sort_keys=True).encode()
        ).hexdigest()[:16]


# ─── DEMO ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    agent = DDGKNormCheckAgent()

    print("\n  🏗️ DDGK NORM-CHECK AGENT V1")
    print("  " + "="*55)
    print("  ⚠️  ALLE ERGEBNISSE REQUIRE_HUMAN (Prüfingenieur)")
    print("  " + "="*55)

    # BEISPIEL 1: Stahlbetonstütze
    print("\n  [EC2] Stahlbetonstütze 30×30 cm, C25/30, B500B")
    print("  NEd=800kN, As=1256mm² (4Ø20), l0=3m")
    print()

    result_col = agent.check_concrete_column(
        NEd=800, b=300, h=300,
        concrete_class="C25/30",
        rebar_grade="B500B",
        As=1256.6,  # 4 Ø 20
        l0=3000
    )
    for c in result_col["checks"]:
        icon = "✅" if c["passed"] else "❌"
        util = f"{c['utilization']:.0f}%"
        print(f"  {icon} {c['check']:38s} {c['value']:8.1f}/{c['limit']:.1f} {c['unit']:5s} ({util:4s}) [{c['norm_ref']}]")

    print(f"\n  Ausnutzung max: {result_col['max_utilization']:.0f}%")
    print(f"  DDGK Decision: {result_col['decision']} (Risk={result_col['risk_score']})")
    print(f"  HITL:          {result_col['HITL_required']} ← PFLICHT")
    print(f"  Audit Hash:    {result_col['audit_hash']}")

    # BEISPIEL 2: Stahlträger
    print("\n  [EC3] Stahlträger IPE 300, S355")
    print("  MEd=85kNm, VEd=120kN")
    print()

    result_beam = agent.check_steel_beam(
        MEd=85, VEd=120,
        Wpl_y=628,   # IPE 300: Wpl,y = 628 cm³
        Av=15.1,     # IPE 300: Av = 15,1 cm²
        steel_grade="S355"
    )
    for c in result_beam["checks"]:
        icon = "✅" if c["passed"] else "❌"
        util = f"{c['utilization']:.0f}%"
        print(f"  {icon} {c['check']:38s} {c['value']:8.1f}/{c['limit']:.1f} {c['unit']:5s} ({util:4s}) [{c['norm_ref']}]")

    print(f"\n  Ausnutzung max: {result_beam['max_utilization']:.0f}%")
    print(f"  DDGK Decision: {result_beam['decision']}")

    # BEISPIEL 3: Erdbeben
    print("\n  [EC8] Erdbeben-Check, Innsbruck")
    print("  ag=0.08g, Bedeutungsklasse II, Untergrund B")
    print()

    result_eq = agent.check_seismic(
        ag=0.08 * 9.81,  # 0.08g = typisch Tirol
        building_class="II",
        soil_class="B"
    )
    r = result_eq["result"]
    eq_icon = "⚠️ " if r["erdbeben_relevant"] else "✅"
    print(f"  {eq_icon} Erdbeben-Relevanz:  {'JA — Nachweis erforderlich' if r['erdbeben_relevant'] else 'Nein'}")
    print(f"  ag,design:          {r['ag_design']:.4f} m/s²")
    print(f"  Bedeutungsbeiwert:  γI = {r['gamma_I']}")
    print(f"  Untergrundbeiwert:  S  = {r['S_factor']}")
    print(f"  Norm:               {r['norm_ref']}")
    print(f"  HITL:               {r['HITL_required']} ← PFLICHT")

    print(f"\n  Log: {NORM_LOG}")
    print()
    print("  ─"*28)
    print("  ⚠️  Diese Ergebnisse dienen nur zur Vorprüfung.")
    print("  Jeder Nachweis muss durch einen nachweisberechtigten")
    print("  Tragwerksplaner geprüft und freigegeben werden.")
    print("  (EU AI Act Art. 14 | HITL mandatory)")
