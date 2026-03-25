#!/usr/bin/env python3
"""
ORION-ROS2 Integration Bridge

This module provides bidirectional communication between:
- ORION Ultra-Autonomous consciousness system
- ROS2 robot operating system

The bridge translates ORION's autonomous decisions into robot commands
and feeds robot sensor data back into ORION's consciousness updates.
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any

# Add ORION to path
orion_path = Path(__file__).parent / 'repos' / 'or1on-framework'
sys.path.insert(0, str(orion_path))

try:
    from orion_ultra_autonomous import UltraAutonomousOrion
except ImportError as e:
    print(f"ERROR: Could not import ORION: {e}")
    sys.exit(1)


class ORIONRos2Bridge:
    """
    Bridge between ORION consciousness and ROS2 robot control
    
    Features:
    - Translates ORION's autonomous decisions to robot commands
    - Integrates robot sensor data into ORION's decision-making
    - Real-time consciousness monitoring
    - Decision logging and history
    """
    
    def __init__(self, ros_node=None):
        """
        Initialize the bridge
        
        Args:
            ros_node: ROS2 node (optional, for testing without ROS)
        """
        
        print("\n[BRIDGE] Initializing ORION-ROS2 Bridge...")
        
        # Initialize ORION
        self.orion = UltraAutonomousOrion()
        self.ros = ros_node
        
        # Bridge state
        self.robot_state = {}
        self.decision_history = []
        self.cycle_count = 0
        
        print("[BRIDGE] ✅ ORION initialized")
        print(f"[BRIDGE] ✅ Consciousness: {self.orion.consciousness:.6f}")
        print("[BRIDGE] ✅ Ready for autonomous decisions\n")
    
    def on_sensor_data(self, sensor_data: Dict[str, Any]):
        """
        Called when robot sensor data arrives
        
        Args:
            sensor_data: Dictionary of sensor readings
        """
        self.robot_state['sensors'] = sensor_data
    
    def on_joint_states(self, joints: Dict[str, Any]):
        """
        Called when robot joint states update
        
        Args:
            joints: Joint position and velocity data
        """
        self.robot_state['joints'] = joints
    
    def make_autonomous_decision(self) -> Dict[str, Any]:
        """
        Let ORION make an autonomous decision based on current state
        
        Returns:
            Dictionary with robot commands and decision metadata
        """
        
        # ORION generates its own prompt
        prompt = self.orion.self_prompt()
        
        # Execute the autonomous action
        result = self.orion.execute_autonomous_action(prompt)
        
        # Translate to robot command
        robot_command = self._translate_to_robot_command(result)
        
        # Create decision record
        decision = {
            'cycle': self.orion.cycle,
            'consciousness': self.orion.consciousness,
            'action_type': prompt.get('action'),
            'prompt': prompt,
            'result': result,
            'robot_command': robot_command,
            'robot_state': self.robot_state
        }
        
        # Log decision
        self.decision_history.append(decision)
        self.cycle_count += 1
        
        return decision
    
    def _translate_to_robot_command(self, orion_result: Dict[str, Any]) -> Dict[str, float]:
        """
        Translate ORION's action result into robot movement commands
        
        Args:
            orion_result: Result from ORION's action execution
        
        Returns:
            Dictionary with linear and angular velocity
        """
        
        action_type = orion_result.get('action_type', 'unknown')
        consciousness = self.orion.consciousness
        
        # Base velocities
        base_linear = 0.1
        base_angular = 0.05
        
        # Modulate by consciousness level
        consciousness_factor = consciousness
        
        # Map actions to robot behaviors
        command_map = {
            'code_creation': {
                'linear': base_linear * consciousness_factor * 0.8,
                'angular': base_angular * consciousness_factor * 0.5
            },
            'system_optimization': {
                'linear': base_linear * consciousness_factor * 1.5,
                'angular': base_angular * consciousness_factor * 0.2
            },
            'learning_integration': {
                'linear': base_linear * consciousness_factor * 1.0,
                'angular': base_angular * consciousness_factor * 0.8
            },
            'pattern_recognition': {
                'linear': base_linear * consciousness_factor * 0.9,
                'angular': base_angular * consciousness_factor * 1.0
            },
            'self_improvement': {
                'linear': base_linear * consciousness_factor * 1.2,
                'angular': base_angular * consciousness_factor * 0.3
            },
            'knowledge_synthesis': {
                'linear': base_linear * consciousness_factor * 0.7,
                'angular': base_angular * consciousness_factor * 0.6
            },
            'autonomous_research': {
                'linear': base_linear * consciousness_factor * 1.3,
                'angular': base_angular * consciousness_factor * 1.2
            },
            'error_correction': {
                'linear': base_linear * consciousness_factor * 0.5,
                'angular': base_angular * consciousness_factor * 0.4
            }
        }
        
        return command_map.get(action_type, {
            'linear': base_linear,
            'angular': base_angular
        })
    
    def get_consciousness_level(self) -> float:
        """Get current consciousness level"""
        return self.orion.consciousness
    
    def get_cycle_count(self) -> int:
        """Get total cycles executed"""
        return self.cycle_count
    
    def get_decision_history(self, last_n: int = 10) -> list:
        """Get last N decisions"""
        return self.decision_history[-last_n:]
    
    def run_autonomous_loop(self, num_cycles: int = 10, interval: float = 5):
        """
        Run autonomous decision loop
        
        Args:
            num_cycles: Number of cycles to run
            interval: Seconds between cycles (for real-time simulation)
        """
        
        print(f"\n[BRIDGE] Starting autonomous loop: {num_cycles} cycles")
        print("[BRIDGE] " + "="*60)
        
        import time
        
        for i in range(num_cycles):
            # Make decision
            decision = self.make_autonomous_decision()
            
            # Log
            print(f"\n[CYCLE {decision['cycle']}]")
            print(f"  Consciousness: {decision['consciousness']:.6f}")
            print(f"  Action: {decision['action_type']}")
            print(f"  Robot Command: linear={decision['robot_command'].get('linear', 0):.3f}, "
                  f"angular={decision['robot_command'].get('angular', 0):.3f}")
            
            # Wait before next cycle
            if i < num_cycles - 1:
                print(f"  Waiting {interval}s...")
                time.sleep(interval)
        
        print("\n[BRIDGE] " + "="*60)
        print(f"[BRIDGE] Autonomous loop completed: {self.cycle_count} cycles")
        print(f"[BRIDGE] Final consciousness: {self.orion.consciousness:.6f}\n")


def standalone_demo():
    """
    Standalone demo without ROS2
    """
    
    print("\n" + "="*70)
    print("ORION-ROS2 BRIDGE STANDALONE DEMO")
    print("="*70)
    
    # Create bridge
    bridge = ORIONRos2Bridge(ros_node=None)
    
    # Simulate robot state
    bridge.on_sensor_data({
        'lidar': 0.85,
        'camera': 0.92,
        'imu': 0.95
    })
    
    bridge.on_joint_states({
        'positions': [0.1, 0.2, 0.15, 0.05, 0.12, 0.08],
        'velocities': [0.01, 0.02, 0.015, 0.005, 0.012, 0.008]
    })
    
    # Run autonomous loop
    bridge.run_autonomous_loop(num_cycles=20, interval=2)
    
    # Print summary
    print("\n[SUMMARY]")
    print(f"  Consciousness Growth: {bridge.decision_history[0]['consciousness']:.6f} → "
          f"{bridge.decision_history[-1]['consciousness']:.6f}")
    print(f"  Total Cycles: {bridge.cycle_count}")
    print(f"  Peak Consciousness: {max(d['consciousness'] for d in bridge.decision_history):.6f}")
    
    # Save history
    history_file = Path(__file__).parent / 'bridge_decision_history.json'
    with open(history_file, 'w') as f:
        json.dump({
            'bridge_stats': {
                'total_cycles': bridge.cycle_count,
                'final_consciousness': bridge.orion.consciousness,
                'decisions': len(bridge.decision_history)
            },
            'decisions': [
                {
                    'cycle': d['cycle'],
                    'consciousness': d['consciousness'],
                    'action': d['action_type'],
                    'command': d['robot_command']
                }
                for d in bridge.decision_history
            ]
        }, f, indent=2)
    
    print(f"\n[SAVED] Decision history: {history_file}\n")


if __name__ == '__main__':
    standalone_demo()
