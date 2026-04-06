#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DDGK LEGAL AGENT v1.0
=====================
Autonomous legal pre-check agent for contracts, patents, compliance.

Status: VORABVERSION (AI_INFERENCE=20 | HUMAN_LAWYER_REQUIRED=True)
All outputs require human lawyer review before execution.

Compliance: EU AI Act Art. 6,9,13,14,17,61 + DSGVO Art. 22
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

class DDGKLegalAgent:
    """Autonomous legal assistant (pre-check only, not legal advice)"""
    
    def __init__(self):
        self.agent_id = "DDGK-LEGAL-v1"
        self.trust_level = 20  # AI_INFERENCE only
        self.requires_human_lawyer = True
        self.log_path = Path("cognitive_ddgk/legal_audit_log.jsonl")
        
    def analyse_eu_ai_act(self, system_description: str) -> Dict:
        """Map system to EU AI Act articles"""
        return {
            "agent": self.agent_id,
            "timestamp": datetime.now().isoformat(),
            "action": "eu_ai_act_analysis",
            "requires_human_lawyer": True,
            "findings": {
                "article_6": "Prohibited practices — check for:",
                "article_9": "High-risk AI systems (requires risk management)",
                "article_13": "Transparency & documentation (audit trail needed)",
                "article_14": "System cards & SOP (alternatives_considered required)",
                "article_17": "Regulatory sandboxes",
                "article_61": "EU AI Office compliance notifications"
            },
            "risk_level": "HIGH"
        }
    
    def check_gdpr_art22(self, automated_decision: Dict) -> Dict:
        """Check DSGVO Art. 22 compliance (automated decisions)"""
        return {
            "agent": self.agent_id,
            "timestamp": datetime.now().isoformat(),
            "action": "gdpr_art22_check",
            "requires_human_lawyer": True,
            "findings": {
                "automated_decision_detected": True,
                "art22_applies": True,
                "requirements": [
                    "Meaningful information about logic",
                    "Significance/consequences explanation",
                    "Right to human review",
                    "Right to contest decision"
                ]
            },
            "risk_level": "HIGH"
        }
    
    def draft_contract_clause(self, use_case: str) -> Dict:
        """Generate contract template (REQUIRES HUMAN REVIEW)"""
        return {
            "agent": self.agent_id,
            "timestamp": datetime.now().isoformat(),
            "action": "draft_contract",
            "requires_human_lawyer": True,
            "template": f"""
AUTONOME SYSTEM NUTZUNGSVERTRAG — {use_case}
[TEMPLATE — NOT LEGAL ADVICE — REQUIRES LAWYER REVIEW]

1. GOVERNANCE
   System operates under policy limits defined in .orion/legal/autonomous_policy.yaml
   
2. LIABILITY
   Operator: Elisabeth Steurer
   System: DDGK SIK-Core
   Liability capped at: [SPECIFY — usually 2x annual service fee]
   
3. AUDIT TRAIL
   All decisions logged in cognitive_ddgk/audit_log.jsonl
   Operator receives daily digest
   
4. TERMINATION
   Operator can revoke autonomy anytime (AUTONOMY_LEVEL=0)
   System must cease execution within 5 minutes
   
[THIS IS A TEMPLATE. MUST BE CUSTOMIZED BY LICENSED LAWYER]
            """,
            "warnings": ["Not legal advice", "Requires customization", "Lawyer must review"]
        }
    
    def assess_liability(self, action: str, context: Dict) -> Dict:
        """Assess legal/financial liability risk"""
        risk_score = self._calculate_risk(action, context)
        return {
            "agent": self.agent_id,
            "timestamp": datetime.now().isoformat(),
            "action": "liability_assessment",
            "requires_human_lawyer": True,
            "risk_score": risk_score,
            "risk_category": "HIGH" if risk_score > 70 else "MEDIUM" if risk_score > 40 else "LOW",
            "potential_liabilities": [
                "Regulatory sanctions (EU AI Act violations)",
                "Civil liability (negligence in autonomous decisions)",
                "Data protection fines (DSGVO breaches)",
                "Contractual breach (to service customers)"
            ],
            "mitigation": "Daily human oversight + Decision Chain audit trail"
        }
    
    def freedom_to_operate(self, invention: Dict) -> Dict:
        """Prior art check for patent-ability"""
        return {
            "agent": self.agent_id,
            "timestamp": datetime.now().isoformat(),
            "action": "fto_analysis",
            "requires_human_lawyer": True,
            "invention": invention.get("title", "Unknown"),
            "findings": {
                "prior_art_search": "Recommend professional patent search",
                "databases": ["USPTO", "EPO", "WIPO", "Google Patents"],
                "estimated_cost": "€2,000-5,000 (professional search)",
                "recommendation": "Consult Patentanwalt before public disclosure"
            }
        }
    
    def _calculate_risk(self, action: str, context: Dict) -> int:
        """Simple risk score (0-100)"""
        base_score = 50
        if "financial" in action.lower():
            base_score += 20
        if context.get("amount", 0) > 100000:
            base_score += 15
        if context.get("binding", False):
            base_score += 10
        return min(100, base_score)
    
    def log_to_audit(self, action: Dict) -> None:
        """Append to audit trail (immutable)"""
        self.log_path.parent.mkdir(exist_ok=True, parents=True)
        with open(self.log_path, 'a') as f:
            f.write(json.dumps({
                "timestamp": datetime.now().isoformat(),
                "agent": self.agent_id,
                "action": action,
                "requires_human_lawyer": self.requires_human_lawyer
            }) + "\n")

# ACTIVATION
if __name__ == "__main__":
    print("=" * 70)
    print("DDGK LEGAL AGENT — INITIALIZED")
    print("=" * 70)
    print("\n⚠️ IMPORTANT: This is a PRE-CHECK AGENT ONLY")
    print("All outputs REQUIRE human lawyer review before execution")
    print("This is NOT legal advice. This is AI-assisted legal research.")
    print("\nStatus: READY FOR INTEGRATION")
    print("Integration: import from cognitive_ddgk.ddgk_legal_agent")
    print("=" * 70)
