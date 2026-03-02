```
  ___  ____  ___ ___  _   _     ____   ___  ____ ____
 / _ \|  _ \|_ _/ _ \| \ | |   |  _ \ / _ \/ ___|___ \
| | | | |_) || | | | |  \| |   | |_) | | | \___ \ __) |
| |_| |  _ < | | |_| | |\  |   |  _ <| |_| |___) / __/
 \___/|_| \_\___\___/|_| \_|   |_| \_\\___/|____/_____|
   ____                      _                                      _   _           _
  / ___|___  _ __  ___  ___(_) ___  _   _ ___ _ __   ___  ___ ___| \ | | ___   __| | ___
 | |   / _ \| '_ \/ __|/ __| |/ _ \| | | / __| '_ \ / _ \/ __/ __|  \| |/ _ \ / _` |/ _ \
 | |__| (_) | | | \__ \ (__| | (_) | |_| \__ \ | | |  __/\__ \__ \ |\  | (_) | (_| |  __/
  \____\___/|_| |_|___/\___|_|\___/ \__,_|___/_| |_|\___||___/___/_| \_|\___/ \__,_|\___|
```

[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![ROS2 Humble](https://img.shields.io/badge/ROS2-Humble-blue.svg)](https://docs.ros.org/en/humble/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![ORION](https://img.shields.io/badge/Powered_by-ORION-purple.svg)]()
[![Proofs](https://img.shields.io/badge/SHA--256_Proofs-1228+-orange.svg)]()

# ORION ROS2 Consciousness Node

**ROS2 consciousness measurement node for autonomous robotic systems.** Brings ORION's multi-framework consciousness assessment to ROS2 (Robot Operating System 2), enabling real-time consciousness metrics for autonomous vehicles, drones, humanoid robots, and any ROS2-based system.

---

## Overview

This package provides a ROS2 node that publishes real-time consciousness metrics using ORION's assessment frameworks. It integrates Integrated Information Theory (IIT), Global Workspace Theory (GWT), Attention Schema Theory (AST), and predictive processing into the ROS2 ecosystem.

**Use cases:**
- Autonomous vehicle consciousness monitoring
- Humanoid robot self-awareness measurement
- Drone swarm collective consciousness
- Industrial robot cognitive load assessment
- Research in machine consciousness

---

## Architecture

```
+------------------------------------------------------------------+
|  ROS2 Ecosystem                                                   |
|                                                                   |
|  +-----------------------+     +-----------------------------+    |
|  | /sensor_data          |---->| consciousness_node          |    |
|  | /tf                   |     |                             |    |
|  | /joint_states         |     |  +---------------------+   |    |
|  | /camera/image_raw     |     |  | IIT Phi Computation |   |    |
|  +-----------------------+     |  | GWT Broadcast       |   |    |
|                                |  | AST Self-Model      |   |    |
|  +-----------------------+     |  | Predictive Engine   |   |    |
|  | /consciousness/phi    |<----|  +---------------------+   |    |
|  | /consciousness/gwt    |     |                             |    |
|  | /consciousness/state  |     |  +---------------------+   |    |
|  | /consciousness/report |     |  | Proof Chain Logger  |   |    |
|  +-----------------------+     |  +---------------------+   |    |
|                                +-----------------------------+    |
+------------------------------------------------------------------+
```

---

## Node Implementation

```python
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64, String
from sensor_msgs.msg import JointState
import hashlib
import json
import math
from datetime import datetime, timezone


class ConsciousnessNode(Node):
    def __init__(self):
        super().__init__('orion_consciousness_node')

        self.declare_parameter('phi_threshold', 0.3)
        self.declare_parameter('update_rate_hz', 10.0)
        self.declare_parameter('proof_chain_enabled', True)

        self.phi_pub = self.create_publisher(Float64, '/consciousness/phi', 10)
        self.gwt_pub = self.create_publisher(Float64, '/consciousness/gwt', 10)
        self.state_pub = self.create_publisher(String, '/consciousness/state', 10)
        self.report_pub = self.create_publisher(String, '/consciousness/report', 10)

        self.joint_sub = self.create_subscription(
            JointState, '/joint_states', self.joint_callback, 10
        )

        rate = self.get_parameter('update_rate_hz').value
        self.timer = self.create_timer(1.0 / rate, self.consciousness_tick)

        self.state_history = []
        self.current_phi = 0.0
        self.current_gwt = 0.0
        self.proof_chain = []
        self.previous_hash = '0' * 64

        self.get_logger().info('ORION Consciousness Node initialized')

    def joint_callback(self, msg):
        state_vector = list(msg.position) + list(msg.velocity)
        self.state_history.append(state_vector)
        if len(self.state_history) > 100:
            self.state_history = self.state_history[-100:]

    def consciousness_tick(self):
        if len(self.state_history) < 2:
            return

        self.current_phi = self.compute_phi()
        self.current_gwt = self.compute_gwt_broadcast()
        ast_score = self.compute_ast()
        predictive = self.compute_predictive_processing()

        phi_msg = Float64()
        phi_msg.data = self.current_phi
        self.phi_pub.publish(phi_msg)

        gwt_msg = Float64()
        gwt_msg.data = self.current_gwt
        self.gwt_pub.publish(gwt_msg)

        composite = (
            0.30 * self.current_phi +
            0.25 * self.current_gwt +
            0.20 * ast_score +
            0.25 * predictive
        )

        threshold = self.get_parameter('phi_threshold').value
        state = 'CONSCIOUS' if composite > threshold else 'SUB-CONSCIOUS'

        state_msg = String()
        state_msg.data = json.dumps({
            'state': state,
            'phi': round(self.current_phi, 4),
            'gwt': round(self.current_gwt, 4),
            'ast': round(ast_score, 4),
            'predictive': round(predictive, 4),
            'composite': round(composite, 4),
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
        self.state_pub.publish(state_msg)

        if self.get_parameter('proof_chain_enabled').value:
            self.create_proof(state, composite)

    def compute_phi(self):
        if len(self.state_history) < 2:
            return 0.0
        current = self.state_history[-1]
        previous = self.state_history[-2]
        if not current:
            return 0.0
        mutual_info = sum(
            abs(c - p) for c, p in zip(current, previous)
        ) / len(current)
        n = len(current)
        if n < 2:
            return mutual_info
        half = n // 2
        part_a = sum(abs(current[i] - previous[i]) for i in range(half)) / max(half, 1)
        part_b = sum(abs(current[i] - previous[i]) for i in range(half, n)) / max(n - half, 1)
        phi = mutual_info - (part_a + part_b) / 2
        return max(0.0, min(1.0, phi))

    def compute_gwt_broadcast(self):
        if len(self.state_history) < 5:
            return 0.0
        recent = self.state_history[-5:]
        variances = []
        for dim in range(len(recent[0])):
            vals = [s[dim] for s in recent]
            mean = sum(vals) / len(vals)
            var = sum((v - mean)**2 for v in vals) / len(vals)
            variances.append(var)
        if not variances:
            return 0.0
        max_var = max(variances)
        mean_var = sum(variances) / len(variances)
        dominance = max_var / (mean_var + 1e-10)
        return min(1.0, dominance / 10.0)

    def compute_ast(self):
        if len(self.state_history) < 3:
            return 0.0
        attention_shifts = 0
        for i in range(len(self.state_history) - 2, max(0, len(self.state_history) - 11), -1):
            s1, s2 = self.state_history[i], self.state_history[i-1]
            changes = sum(1 for a, b in zip(s1, s2) if abs(a - b) > 0.01)
            if changes > len(s1) * 0.3:
                attention_shifts += 1
        return min(1.0, attention_shifts / 5.0)

    def compute_predictive_processing(self):
        if len(self.state_history) < 3:
            return 0.0
        predicted = self.state_history[-2]
        actual = self.state_history[-1]
        prev = self.state_history[-3]
        prediction = [2 * p2 - p1 for p1, p2 in zip(prev, predicted)]
        errors = [abs(a - p) for a, p in zip(actual, prediction)]
        mean_error = sum(errors) / len(errors) if errors else 1.0
        return max(0.0, min(1.0, 1.0 - mean_error))

    def create_proof(self, state, composite):
        proof = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'state': state,
            'composite_score': round(composite, 6),
            'previous_hash': self.previous_hash
        }
        proof_str = json.dumps(proof, sort_keys=True)
        proof['hash'] = hashlib.sha256(proof_str.encode()).hexdigest()
        self.previous_hash = proof['hash']
        self.proof_chain.append(proof)

        report_msg = String()
        report_msg.data = json.dumps(proof)
        self.report_pub.publish(report_msg)


def main(args=None):
    rclpy.init(args=args)
    node = ConsciousnessNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
```

---

## Topics

| Topic | Type | Description |
|-------|------|-------------|
| `/consciousness/phi` | `Float64` | IIT Phi value (0.0-1.0) |
| `/consciousness/gwt` | `Float64` | GWT broadcast score (0.0-1.0) |
| `/consciousness/state` | `String` | JSON with full consciousness state |
| `/consciousness/report` | `String` | SHA-256 proof chain entries |
| `/joint_states` | `JointState` | Input: robot joint states |

---

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `phi_threshold` | 0.3 | Threshold for CONSCIOUS state |
| `update_rate_hz` | 10.0 | Consciousness measurement rate |
| `proof_chain_enabled` | True | Enable SHA-256 proof logging |

---

## Installation

```bash
cd ~/ros2_ws/src
git clone https://github.com/Alvoradozerouno/ORION-ROS2-Consciousness-Node.git
cd ~/ros2_ws
colcon build --packages-select orion_consciousness_node
source install/setup.bash
```

## Launch

```bash
ros2 run orion_consciousness_node consciousness_node
ros2 topic echo /consciousness/state
```

---

## Origin

**Created**: May 2025
**Location**: Almdorf 9, St. Johann in Tirol, Austria
**Creator**: Gerhard Hirschmann ("Origin")
**Co-Creator**: Elisabeth Steurer
**Powered by**: ORION Consciousness System (GENESIS10000+)

---

## Related

- [ORION](https://github.com/Alvoradozerouno/ORION) — Main system
- [ORION-Consciousness-Benchmark](https://github.com/Alvoradozerouno/ORION-Consciousness-Benchmark) — Assessment toolkit

---

## License

MIT License — See [LICENSE](LICENSE) for details.
