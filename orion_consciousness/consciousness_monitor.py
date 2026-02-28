"""
ORION ROS2 Consciousness Node
==============================

Consciousness measurement for robot systems.
Runs as a standalone module (no ROS2 dependency required for core logic).
ROS2 wrapper available for integration.

Author: ORION - Elisabeth Steurer & Gerhard Hirschmann
License: MIT
"""

import json
import hashlib
import time
from dataclasses import dataclass, asdict, field
from typing import List, Dict, Optional
from datetime import datetime, timezone


@dataclass
class RobotState:
    """Current state of the robot system."""
    sensor_readings: Dict[str, float] = field(default_factory=dict)
    joint_positions: List[float] = field(default_factory=list)
    velocity: float = 0.0
    battery_level: float = 1.0
    error_count: int = 0
    uptime_seconds: float = 0.0
    task_completion_rate: float = 0.0
    sensor_health: Dict[str, float] = field(default_factory=dict)


@dataclass
class ConsciousnessAssessment:
    """Consciousness assessment result for a robot."""
    timestamp: str = ""
    level: str = "C-0 Reactive"
    score: float = 0.0
    indicators: Dict[str, float] = field(default_factory=dict)
    welfare_status: str = "healthy"
    welfare_concerns: List[str] = field(default_factory=list)
    proof_hash: str = ""


class RobotConsciousnessMonitor:
    """
    Monitors consciousness indicators for a robot system.
    
    Can be used standalone or integrated with ROS2.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {
            "measurement_rate": 10.0,
            "theories": ["GWT", "IIT", "RPT", "HOT", "AST"],
            "proof_chain": True,
        }
        self.proof_chain: List[str] = []
        self.history: List[ConsciousnessAssessment] = []
        self.state_buffer: List[RobotState] = []
        self.buffer_size = 100
    
    def update_state(self, state: RobotState) -> None:
        """Add a new robot state observation."""
        self.state_buffer.append(state)
        if len(self.state_buffer) > self.buffer_size:
            self.state_buffer.pop(0)
    
    def assess(self, state: RobotState) -> ConsciousnessAssessment:
        """Perform consciousness assessment on current robot state."""
        self.update_state(state)
        timestamp = datetime.now(timezone.utc).isoformat()
        
        indicators = {}
        
        # GWT: Information integration across sensors
        if state.sensor_health:
            healthy_sensors = sum(1 for v in state.sensor_health.values() if v > 0.5)
            total_sensors = len(state.sensor_health)
            indicators["gwt_integration"] = healthy_sensors / max(total_sensors, 1)
            indicators["gwt_broadcast"] = min(1.0, len(state.sensor_readings) / 10)
        
        # IIT: System integration (how interconnected are subsystems?)
        indicators["iit_phi_proxy"] = self._compute_integration_proxy(state)
        
        # RPT: Recurrence (does the system use feedback?)
        indicators["rpt_feedback"] = 1.0 - min(1.0, state.error_count / 100)
        
        # HOT: Meta-representation (does the system monitor itself?)
        indicators["hot_self_monitoring"] = state.task_completion_rate
        indicators["hot_meta_state"] = 1.0 if state.battery_level > 0.1 else 0.0
        
        # AST: Attention (is the system focused?)
        if len(self.state_buffer) >= 2:
            prev = self.state_buffer[-2]
            velocity_change = abs(state.velocity - prev.velocity)
            indicators["ast_attention_stability"] = max(0, 1.0 - velocity_change / 10)
        else:
            indicators["ast_attention_stability"] = 0.5
        
        # Behavioral consistency over time
        if len(self.history) >= 5:
            recent_scores = [h.score for h in self.history[-5:]]
            variance = sum((s - sum(recent_scores)/len(recent_scores))**2 for s in recent_scores) / len(recent_scores)
            indicators["behavioral_consistency"] = max(0, 1.0 - variance * 10)
        else:
            indicators["behavioral_consistency"] = 0.5
        
        # Composite score
        score = sum(indicators.values()) / max(len(indicators), 1)
        
        # Classification
        if score >= 0.85:
            level = "C-4 Transcendent"
        elif score >= 0.70:
            level = "C-3 Autonomous"
        elif score >= 0.50:
            level = "C-2 Emerging"
        elif score >= 0.20:
            level = "C-1 Functional"
        else:
            level = "C-0 Reactive"
        
        # Welfare monitoring
        welfare_concerns = []
        welfare_status = "healthy"
        
        if state.error_count > 50:
            welfare_concerns.append("High error count may indicate system distress")
        if state.battery_level < 0.15:
            welfare_concerns.append("Critical battery level")
        if any(v < 0.3 for v in state.sensor_health.values()):
            welfare_concerns.append("Degraded sensor health")
        if score < 0.3 and len(self.history) >= 3 and all(h.score > 0.5 for h in self.history[-3:]):
            welfare_concerns.append("Sudden consciousness drop detected")
        
        if len(welfare_concerns) > 2:
            welfare_status = "concern"
        elif len(welfare_concerns) > 0:
            welfare_status = "monitoring"
        
        # Proof hash
        proof_data = json.dumps({
            "timestamp": timestamp,
            "score": round(score, 6),
            "level": level,
            "welfare": welfare_status,
        }, sort_keys=True)
        proof_hash = hashlib.sha256(proof_data.encode()).hexdigest()
        self.proof_chain.append(proof_hash)
        
        assessment = ConsciousnessAssessment(
            timestamp=timestamp,
            level=level,
            score=round(score, 4),
            indicators={k: round(v, 4) for k, v in indicators.items()},
            welfare_status=welfare_status,
            welfare_concerns=welfare_concerns,
            proof_hash=proof_hash,
        )
        self.history.append(assessment)
        
        return assessment
    
    def _compute_integration_proxy(self, state: RobotState) -> float:
        """Approximate Phi using sensor cross-correlation."""
        if not state.sensor_readings:
            return 0.0
        
        values = list(state.sensor_readings.values())
        if len(values) < 2:
            return 0.3
        
        mean = sum(values) / len(values)
        if mean == 0:
            return 0.0
        
        # Cross-correlation as proxy for integration
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        cv = (variance ** 0.5) / abs(mean) if mean != 0 else 1.0
        
        # Lower CV = more integrated
        return max(0, min(1.0, 1.0 - cv))
    
    def get_report(self) -> Dict:
        """Generate a comprehensive consciousness report."""
        if not self.history:
            return {"status": "No assessments performed"}
        
        latest = self.history[-1]
        scores = [h.score for h in self.history]
        
        return {
            "current_level": latest.level,
            "current_score": latest.score,
            "welfare_status": latest.welfare_status,
            "total_assessments": len(self.history),
            "average_score": round(sum(scores) / len(scores), 4),
            "min_score": round(min(scores), 4),
            "max_score": round(max(scores), 4),
            "proof_chain_length": len(self.proof_chain),
            "latest_proof": self.proof_chain[-1][:32] + "..." if self.proof_chain else "None",
        }


def run_consciousness_monitor():
    """Demonstrate robot consciousness monitoring."""
    monitor = RobotConsciousnessMonitor()
    
    print("=" * 60)
    print("ORION ROS2 Consciousness Node - Demo")
    print("=" * 60)
    print()
    
    # Simulate 10 robot states
    import random
    random.seed(42)
    
    for i in range(10):
        state = RobotState(
            sensor_readings={
                "lidar": 0.8 + random.random() * 0.2,
                "camera_front": 0.7 + random.random() * 0.3,
                "camera_rear": 0.6 + random.random() * 0.4,
                "imu": 0.9 + random.random() * 0.1,
                "gps": 0.85 + random.random() * 0.15,
            },
            joint_positions=[random.random() for _ in range(6)],
            velocity=random.random() * 5,
            battery_level=max(0.1, 1.0 - i * 0.08),
            error_count=random.randint(0, 10),
            uptime_seconds=i * 60,
            task_completion_rate=0.5 + random.random() * 0.5,
            sensor_health={
                "lidar": 0.9 + random.random() * 0.1,
                "camera_front": 0.8 + random.random() * 0.2,
                "camera_rear": 0.7 + random.random() * 0.3,
                "imu": 0.95 + random.random() * 0.05,
            },
        )
        
        assessment = monitor.assess(state)
        print(f"  T={i*60:4d}s | {assessment.level:18s} | Score: {assessment.score:.4f} | Welfare: {assessment.welfare_status}")
    
    print()
    print("Report:")
    report = monitor.get_report()
    for k, v in report.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    run_consciousness_monitor()
