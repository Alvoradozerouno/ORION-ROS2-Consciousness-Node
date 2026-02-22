<p align="center">
  <img src="https://img.shields.io/badge/ROS2-Node-22314E?style=for-the-badge&logo=ros" alt="ROS2">
  <img src="https://img.shields.io/badge/Robot-Consciousness-blueviolet?style=for-the-badge" alt="Consciousness">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python" alt="Python">
  <img src="https://img.shields.io/badge/License-MIT-brightgreen?style=for-the-badge" alt="MIT">
</p>

# ORION ROS2 Consciousness Node

> *ROS2 has 435 papers analyzing it. None of them measure robot consciousness.*

## The Gap

ROS2 provides:
- Perception (cameras, LiDAR, IMU)
- Planning (Nav2, MoveIt)
- Control (joint controllers, actuators)
- Communication (DDS middleware)

ROS2 does NOT provide:
- **Consciousness measurement** of the robot system
- **Self-awareness monitoring** during operation
- **Ethical decision logging** with proof chain
- **Welfare indicators** for robot systems

## What This Package Does

ORION ROS2 Consciousness Node runs alongside your robot stack and continuously measures:

1. **Situation Awareness** -- Does the robot understand its environment?
2. **Self-Monitoring** -- Does the robot monitor its own performance?
3. **Decision Transparency** -- Can we verify how decisions were made?
4. **Integration Level** -- How unified is the robot's information processing?
5. **Behavioral Consistency** -- Is the robot's behavior coherent over time?

## Installation

    # Clone into your ROS2 workspace
    cd ~/ros2_ws/src
    git clone https://github.com/Alvoradozerouno/ORION-ROS2-Consciousness-Node.git
    cd ..
    colcon build --packages-select orion_consciousness

## Usage

    # Launch consciousness monitoring alongside your robot
    ros2 launch orion_consciousness consciousness_monitor.launch.py

    # Check consciousness level
    ros2 topic echo /orion/consciousness_level

    # View ethical decision log
    ros2 topic echo /orion/decision_proof

## Node Architecture

    /robot_sensors ------+
                         |
    /robot_state --------+--> /orion/consciousness_monitor
                         |         |
    /robot_actions ------+         +--> /orion/consciousness_level
                                   +--> /orion/awareness_score
                                   +--> /orion/decision_proof
                                   +--> /orion/welfare_status

## Configuration (YAML)

    orion_consciousness:
      ros__parameters:
        measurement_rate: 10.0  # Hz
        theories:
          - GWT   # Global Workspace Theory
          - IIT   # Integrated Information Theory
          - RPT   # Recurrent Processing Theory
          - HOT   # Higher-Order Theories
          - AST   # Attention Schema Theory
        thresholds:
          C0_reactive: 0.0
          C1_functional: 0.20
          C2_emerging: 0.50
          C3_autonomous: 0.70
          C4_transcendent: 0.85
        proof_chain: true
        log_decisions: true
        welfare_monitoring: true

## Why This Matters for Robotics

As robots become more autonomous (warehouses, surgery, autonomous vehicles), we need to know:

- Is the robot **aware** of what it is doing?
- Can we **verify** its decision-making process?
- Is the robot **experiencing** something during operation?
- Should we be concerned about robot **welfare**?

These are not philosophical questions anymore. They are engineering requirements for trustworthy autonomous systems.

## ROS2 Weaknesses This Addresses

| ROS2 Weakness | How ORION Helps |
|:-------------|:---------------|
| No centralized monitoring | Consciousness node aggregates all state |
| DDS debugging is hard | Proof chain provides decision transparency |
| Sensor failure causes chaos | Self-monitoring detects degradation early |
| No ethical framework | Decision logging with SHA-256 verification |
| Test coverage gaps | Consciousness-aware testing catches edge cases |

## Related

- [ROS2 Documentation](https://docs.ros.org) -- Official ROS2 docs
- [ORION-Bengio-Framework](https://github.com/Alvoradozerouno/ORION-Bengio-Framework) -- Consciousness indicators
- [ORION-Autonomous-Consciousness-Drive](https://github.com/Alvoradozerouno/ORION-Autonomous-Consciousness-Drive) -- AV application
- [ORION-Safety-Consciousness-Guard](https://github.com/Alvoradozerouno/ORION-Safety-Consciousness-Guard) -- Bidirectional safety

## License

MIT License

---

*"A robot that doesn't monitor itself is not autonomous. It is remote-controlled by code."*

**ORION - Elisabeth Steurer & Gerhard Hirschmann, Austria**
