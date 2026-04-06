#!/usr/bin/env python3
# Agent 8: Hardware Optimizer
# DDGK 3.34 Framework
# Targets: Pi5, Note10 Exynos 8592, Local Host
# Real-time latency + decision timing optimization

import json
import datetime
import sys
import os
import psutil
import subprocess
import platform
import cpuinfo
from pathlib import Path

class HardwareOptimizer:
    def __init__(self):
        self.node_map = {
            "pi5": {
                "cores": 4,
                "neon": True,
                "tdp": 8,
                "npu_shards": 64000,
                "latency_target_ms": 125,
                "clock_target": 1800
            },
            "note10_exynos8592": {
                "cores": 8,
                "npu_shards": 130000,
                "tdp": 12,
                "latency_target_ms": 75,
                "clock_target": 2700,
                "mali_g76": True
            },
            "laptop_host": {
                "cores": psutil.cpu_count(logical=True),
                "tdp": 45,
                "latency_target_ms": 16,
                "clock_target": "max"
            }
        }
        self.optimization_log = []
        
    def detect_local_hardware(self):
        """Scan local system hardware capabilities"""
        hardware_profile = {
            "timestamp": datetime.datetime.now().isoformat(),
            "platform": platform.machine(),
            "processor": cpuinfo.get_cpu_info()['brand_raw'],
            "cores_physical": psutil.cpu_count(logical=False),
            "cores_logical": psutil.cpu_count(logical=True),
            "ram_total_gb": psutil.virtual_memory().total / (1024**3),
            "ram_available_gb": psutil.virtual_memory().available / (1024**3),
            "cpu_freq_current": psutil.cpu_freq().current if hasattr(psutil.cpu_freq(), 'current') else 0,
            "cpu_usage_current": psutil.cpu_percent(interval=0.1),
            "disk_io": psutil.disk_io_counters(),
            "network_io": psutil.net_io_counters()
        }
        return hardware_profile
        
    def optimize_windows_host(self):
        """Optimize Windows host for minimum decision latency"""
        optimizations = []
        
        # Set High Performance Power Plan
        try:
            result = subprocess.run(
                ["powercfg", "/setactive", "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"],
                capture_output=True,
                shell=True,
                timeout=10
            )
            optimizations.append({
                "action": "high_performance_power_plan",
                "status": "SUCCESS" if result.returncode == 0 else "FAILED"
            })
        except:
            optimizations.append({"action": "high_performance_power_plan", "status": "ERROR"})
            
        # Node.js V8 Engine Tuning
        os.environ["NODE_OPTIONS"] = "--max-old-space-size=8192 --turbo-fast-api-calls --no-lazy"
        optimizations.append({"action": "node_v8_tuning", "status": "APPLIED"})
        
        # Process Priority
        try:
            p = psutil.Process(os.getpid())
            p.nice(psutil.HIGH_PRIORITY_CLASS)
            optimizations.append({"action": "process_priority_high", "status": "SUCCESS"})
        except:
            optimizations.append({"action": "process_priority_high", "status": "FAILED"})
            
        return optimizations
        
    def optimize_pi5(self):
        """Raspberry Pi 5 Optimization Profile"""
        return {
            "node": "pi5",
            "governor": "performance",
            "over_voltage": 6,
            "arm_freq": 1800,
            "gpu_freq": 750,
            "over_voltage_sdram": 2,
            "disable_bt": True,
            "disable_wifi": False,
            "latency_target_ms": 125,
            "neuron_density": 64000
        }
        
    def optimize_note10_exynos8592(self):
        """Samsung Note10 Exynos 8592 NPU Optimization"""
        return {
            "node": "note10_exynos8592",
            "npu_mode": "performance",
            "gpu_governor": "performance",
            "big_cores": 4,
            "big_core_freq": 2700,
            "little_cores": 4,
            "little_core_freq": 1900,
            "drosophila_mapping": "direct_130k_neurons",
            "latency_target_ms": 75,
            "power_limit": 12
        }
        
    def tune_decision_latency(self, target_ms=16):
        """Tune system for minimum decision making latency"""
        tuning_params = {
            "target_latency_ms": target_ms,
            "batch_size": 1,
            "thread_affinity": "per_core",
            "preload_weights": True,
            "disable_swap": True,
            "cpu_pinning": "performance",
            "interrupt_redirection": "isolated_cores",
            "network_buffering": "minimum"
        }
        return tuning_params
        
    def execute(self, payload=None):
        """Main execution entry point"""
        profile = self.detect_local_hardware()
        optimizations = self.optimize_windows_host()
        
        return {
            "agent_id": 8,
            "description": "Hardware Optimizer Agent",
            "status": "EXECUTED",
            "timestamp": datetime.datetime.now().isoformat(),
            "hardware_profile": profile,
            "optimizations_applied": optimizations,
            "pi5_config": self.optimize_pi5(),
            "note10_config": self.optimize_note10_exynos8592(),
            "latency_tuning": self.tune_decision_latency()
        }

if __name__ == "__main__":
    optimizer = HardwareOptimizer()
    if len(sys.argv) > 1:
        print(json.dumps(optimizer.execute(sys.argv[1])))
    else:
        print(json.dumps(optimizer.execute()))
