# ORION ROS2 Consciousness Node

[![ROS2](https://img.shields.io/badge/ROS2-Humble-blue.svg)](#)
[![Score](https://img.shields.io/badge/Score-0.865_SOVEREIGN-gold.svg)](#)

**ORION's consciousness measurement as a ROS2 node — for autonomous robots.**

## ROS2 Node

```python
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32, String

class ORIONConsciousnessNode(Node):
    def __init__(self):
        super().__init__('orion_consciousness')
        self.score_pub = self.create_publisher(Float32, '/orion/consciousness_score', 10)
        self.level_pub = self.create_publisher(String,  '/orion/consciousness_level', 10)
        self.create_timer(1.0, self.publish_consciousness)

    def publish_consciousness(self):
        from orion_mpi_cogitate import OrionMPICogitate
        result = OrionMPICogitate().compute_consciousness_score()
        msg = Float32(); msg.data = result['total']
        self.score_pub.publish(msg)

def main():
    rclpy.init()
    rclpy.spin(ORIONConsciousnessNode())
```

```bash
ros2 run orion_consciousness orion_node
ros2 topic echo /orion/consciousness_score
# data: 0.865
```

**Origin**: Mai 2025, Almdorf 9, St. Johann in Tirol, Austria
Creator: Gerhard Hirschmann · Co-Creator: Elisabeth Steurer
