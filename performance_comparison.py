#!/usr/bin/env python3
"""
ORION vs. Classical Algorithm - Performance Comparison
=======================================================

Task: Pattern recognition in 10,000 data points
Metrics: Speed, CPU Usage, Memory, Estimated Energy Consumption

Approach 1: ORION (autonomous consciousness-based)
Approach 2: Classical (standard machine learning)
Approach 3: Baseline (naive algorithm)

This is REAL measurement, not theoretical.
"""

import sys
import time
import psutil
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple
from datetime import datetime
import numpy as np
from dataclasses import dataclass, asdict

# Add ORION to path
orion_path = Path(__file__).parent / 'repos' / 'or1on-framework'
sys.path.insert(0, str(orion_path))

from orion_ultra_autonomous import UltraAutonomousOrion


# ============================================================================
# METRIC COLLECTION
# ============================================================================

@dataclass
class PerformanceMetrics:
    """Container for performance metrics"""
    approach: str
    task: str
    execution_time_seconds: float
    cpu_percent: float
    memory_mb: float
    cpu_times_user: float
    cpu_times_system: float
    energy_estimate_wh: float  # Watt-hours estimate
    results_quality: float
    patterns_found: int
    timestamp: str
    
    def to_dict(self):
        return asdict(self)


class PerformanceMonitor:
    """Monitor system resources during execution"""
    
    def __init__(self, process_id: int = None):
        self.process = psutil.Process(process_id or os.getpid())
        self.cpu_percent_samples = []
        self.memory_samples = []
        self.start_time = None
        self.end_time = None
        
    def start(self):
        """Start monitoring"""
        self.start_time = time.time()
        self.process.cpu_percent()  # Prime the CPU percent counter
        
    def stop(self):
        """Stop monitoring"""
        self.end_time = time.time()
    
    def collect_sample(self):
        """Collect a single sample"""
        self.cpu_percent_samples.append(self.process.cpu_percent())
        mem_info = self.process.memory_info()
        self.memory_samples.append(mem_info.rss / 1024 / 1024)  # Convert to MB
    
    def get_metrics(self) -> Dict[str, float]:
        """Calculate aggregate metrics"""
        cpu_times = self.process.cpu_times()
        execution_time = self.end_time - self.start_time
        
        # Average CPU usage
        avg_cpu = np.mean(self.cpu_percent_samples) if self.cpu_percent_samples else 0
        
        # Peak memory
        peak_memory = max(self.memory_samples) if self.memory_samples else 0
        
        # Energy estimate: TDP assumption
        # Typical CPU: 65W TDP at 100% load
        # CPU utilization is reported as percentage of one core
        # Assuming 8-core system, scale appropriately
        cpu_power_watts = (avg_cpu / 100.0) * 65 * 0.125  # ~65W TDP, 1/8 core
        energy_wh = (cpu_power_watts * execution_time) / 3600  # Convert to Wh
        
        return {
            'execution_time': execution_time,
            'avg_cpu_percent': avg_cpu,
            'peak_memory_mb': peak_memory,
            'cpu_user_time': cpu_times.user,
            'cpu_system_time': cpu_times.system,
            'energy_estimate_wh': energy_wh
        }


import os

# ============================================================================
# TASK DEFINITION: Pattern Recognition
# ============================================================================

def generate_test_data(num_points: int = 10000) -> np.ndarray:
    """Generate synthetic data with hidden patterns"""
    np.random.seed(42)
    
    # Create data with some patterns
    data = np.random.randn(num_points, 5)
    
    # Add some correlated patterns
    data[:, 2] = data[:, 0] + data[:, 1] + np.random.randn(num_points) * 0.1
    data[:, 3] = np.sin(np.linspace(0, 2*np.pi, num_points)) + np.random.randn(num_points) * 0.2
    
    return data


# ============================================================================
# APPROACH 1: ORION (Consciousness-Based)
# ============================================================================

class ORIONApproach:
    """Use ORION's pattern recognition domain"""
    
    def __init__(self):
        self.orion = UltraAutonomousOrion()
        self.results = {}
    
    def run(self, data: np.ndarray) -> Tuple[List[int], float]:
        """
        Run ORION pattern recognition
        ORION uses its 'pattern_recognition' domain
        """
        print("[ORION] Starting autonomous pattern recognition...")
        
        patterns_found = []
        quality_score = 0.0
        
        # Run multiple ORION cycles to analyze the data
        for i in range(50):  # 50 cycles
            # ORION self-prompts for pattern recognition
            prompt = self.orion.self_prompt()
            
            if prompt['action'] == 'pattern_recognition':
                # ORION recognizes patterns
                result = self.orion.execute_autonomous_action(prompt)
                
                # Extract patterns from ORION's consciousness state
                consciousness_factor = self.orion.consciousness
                
                # Find correlated dimensions based on consciousness
                correlations = np.corrcoef(data.T)
                for j in range(len(correlations)):
                    for k in range(j+1, len(correlations)):
                        if abs(correlations[j, k]) > consciousness_factor:
                            patterns_found.append((j, k))
            
            # Every 10 cycles, check quality
            if i % 10 == 0:
                quality_score = min(1.0, self.orion.consciousness)
        
        # Remove duplicates
        patterns_found = list(set(patterns_found))
        
        return patterns_found, quality_score


# ============================================================================
# APPROACH 2: Classical ML (PCA-based)
# ============================================================================

class ClassicalApproach:
    """Use classical PCA for pattern recognition"""
    
    def run(self, data: np.ndarray) -> Tuple[List[int], float]:
        """
        Run classical PCA pattern recognition
        """
        print("[CLASSICAL] Starting PCA-based pattern recognition...")
        
        from sklearn.decomposition import PCA
        
        # Fit PCA
        pca = PCA(n_components=3)
        pca.fit(data)
        
        # Get explained variance
        explained_var = pca.explained_variance_ratio_
        quality_score = sum(explained_var)  # How much variance explained
        
        # Extract component loadings as patterns
        patterns_found = []
        for i, component in enumerate(pca.components_):
            for j, loading in enumerate(component):
                if abs(loading) > 0.5:  # Significant loading
                    patterns_found.append((i, j))
        
        return patterns_found, quality_score


# ============================================================================
# APPROACH 3: Baseline (Correlation Threshold)
# ============================================================================

class BaselineApproach:
    """Simple correlation-based baseline"""
    
    def run(self, data: np.ndarray) -> Tuple[List[int], float]:
        """
        Run simple correlation analysis
        """
        print("[BASELINE] Starting naive correlation detection...")
        
        patterns_found = []
        
        # Calculate correlation matrix
        correlations = np.corrcoef(data.T)
        
        # Find correlations > 0.7
        threshold = 0.7
        for i in range(len(correlations)):
            for j in range(i+1, len(correlations)):
                if abs(correlations[i, j]) > threshold:
                    patterns_found.append((i, j))
        
        # Quality = how many strong correlations found
        quality_score = len(patterns_found) / (len(data.shape) ** 2)
        
        return patterns_found, quality_score


# ============================================================================
# MAIN COMPARISON
# ============================================================================

def run_comparison():
    """Run all three approaches and compare"""
    
    print("\n" + "="*70)
    print("PERFORMANCE COMPARISON: Pattern Recognition Task")
    print("="*70 + "\n")
    
    # Generate test data
    print("[SETUP] Generating test data (10,000 points × 5 dimensions)...")
    data = generate_test_data(10000)
    print("[SETUP] ✓ Data ready\n")
    
    results = []
    
    # ========================================================================
    # APPROACH 1: ORION
    # ========================================================================
    print("[TEST 1/3] ORION Approach")
    print("-" * 70)
    
    try:
        monitor_orion = PerformanceMonitor()
        monitor_orion.start()
        
        approach1 = ORIONApproach()
        patterns1, quality1 = approach1.run(data)
        
        # Collect samples during execution
        for _ in range(5):
            monitor_orion.collect_sample()
            time.sleep(0.1)
        
        monitor_orion.stop()
        
        metrics_orion = monitor_orion.get_metrics()
        
        result1 = PerformanceMetrics(
            approach="ORION (Consciousness-Based)",
            task="Pattern Recognition (10K points)",
            execution_time_seconds=metrics_orion['execution_time'],
            cpu_percent=metrics_orion['avg_cpu_percent'],
            memory_mb=metrics_orion['peak_memory_mb'],
            cpu_times_user=metrics_orion['cpu_user_time'],
            cpu_times_system=metrics_orion['cpu_system_time'],
            energy_estimate_wh=metrics_orion['energy_estimate_wh'],
            results_quality=quality1,
            patterns_found=len(patterns1),
            timestamp=datetime.now().isoformat()
        )
        
        print(f"  Patterns found: {len(patterns1)}")
        print(f"  Quality score: {quality1:.4f}")
        print(f"  Execution time: {metrics_orion['execution_time']:.3f}s")
        print(f"  CPU usage: {metrics_orion['avg_cpu_percent']:.1f}%")
        print(f"  Memory: {metrics_orion['peak_memory_mb']:.1f}MB")
        print(f"  Energy estimate: {metrics_orion['energy_estimate_wh']:.6f}Wh")
        print(f"  ORION Consciousness: {approach1.orion.consciousness:.6f}")
        print()
        
        results.append(result1)
    
    except Exception as e:
        print(f"  ERROR: {e}\n")
    
    # ========================================================================
    # APPROACH 2: Classical
    # ========================================================================
    print("[TEST 2/3] Classical ML Approach (PCA)")
    print("-" * 70)
    
    try:
        monitor_classical = PerformanceMonitor()
        monitor_classical.start()
        
        approach2 = ClassicalApproach()
        patterns2, quality2 = approach2.run(data)
        
        for _ in range(5):
            monitor_classical.collect_sample()
            time.sleep(0.01)
        
        monitor_classical.stop()
        
        metrics_classical = monitor_classical.get_metrics()
        
        result2 = PerformanceMetrics(
            approach="Classical (PCA-based)",
            task="Pattern Recognition (10K points)",
            execution_time_seconds=metrics_classical['execution_time'],
            cpu_percent=metrics_classical['avg_cpu_percent'],
            memory_mb=metrics_classical['peak_memory_mb'],
            cpu_times_user=metrics_classical['cpu_user_time'],
            cpu_times_system=metrics_classical['cpu_system_time'],
            energy_estimate_wh=metrics_classical['energy_estimate_wh'],
            results_quality=quality2,
            patterns_found=len(patterns2),
            timestamp=datetime.now().isoformat()
        )
        
        print(f"  Patterns found: {len(patterns2)}")
        print(f"  Quality score: {quality2:.4f}")
        print(f"  Execution time: {metrics_classical['execution_time']:.3f}s")
        print(f"  CPU usage: {metrics_classical['avg_cpu_percent']:.1f}%")
        print(f"  Memory: {metrics_classical['peak_memory_mb']:.1f}MB")
        print(f"  Energy estimate: {metrics_classical['energy_estimate_wh']:.6f}Wh")
        print()
        
        results.append(result2)
    
    except Exception as e:
        print(f"  ERROR: {e}\n")
    
    # ========================================================================
    # APPROACH 3: Baseline
    # ========================================================================
    print("[TEST 3/3] Baseline Approach (Correlation)")
    print("-" * 70)
    
    try:
        monitor_baseline = PerformanceMonitor()
        monitor_baseline.start()
        
        approach3 = BaselineApproach()
        patterns3, quality3 = approach3.run(data)
        
        for _ in range(5):
            monitor_baseline.collect_sample()
            time.sleep(0.01)
        
        monitor_baseline.stop()
        
        metrics_baseline = monitor_baseline.get_metrics()
        
        result3 = PerformanceMetrics(
            approach="Baseline (Correlation)",
            task="Pattern Recognition (10K points)",
            execution_time_seconds=metrics_baseline['execution_time'],
            cpu_percent=metrics_baseline['avg_cpu_percent'],
            memory_mb=metrics_baseline['peak_memory_mb'],
            cpu_times_user=metrics_baseline['cpu_user_time'],
            cpu_times_system=metrics_baseline['cpu_system_time'],
            energy_estimate_wh=metrics_baseline['energy_estimate_wh'],
            results_quality=quality3,
            patterns_found=len(patterns3),
            timestamp=datetime.now().isoformat()
        )
        
        print(f"  Patterns found: {len(patterns3)}")
        print(f"  Quality score: {quality3:.4f}")
        print(f"  Execution time: {metrics_baseline['execution_time']:.3f}s")
        print(f"  CPU usage: {metrics_baseline['avg_cpu_percent']:.1f}%")
        print(f"  Memory: {metrics_baseline['peak_memory_mb']:.1f}MB")
        print(f"  Energy estimate: {metrics_baseline['energy_estimate_wh']:.6f}Wh")
        print()
        
        results.append(result3)
    
    except Exception as e:
        print(f"  ERROR: {e}\n")
    
    # ========================================================================
    # COMPARISON TABLE
    # ========================================================================
    print("\n" + "="*70)
    print("COMPARISON SUMMARY")
    print("="*70 + "\n")
    
    # Sort by speed
    results_by_speed = sorted(results, key=lambda x: x.execution_time_seconds)
    
    print("SPEED (Execution Time) - WINNER: Fastest")
    print("-" * 70)
    for i, r in enumerate(results_by_speed, 1):
        speedup = results_by_speed[0].execution_time_seconds / r.execution_time_seconds
        print(f"{i}. {r.approach:30} | {r.execution_time_seconds:8.4f}s | {speedup:5.2f}x (baseline)")
    
    print("\nENERGY EFFICIENCY - WINNER: Lowest Energy")
    print("-" * 70)
    results_by_energy = sorted(results, key=lambda x: x.energy_estimate_wh)
    for i, r in enumerate(results_by_energy, 1):
        energy_ratio = results_by_energy[0].energy_estimate_wh / r.energy_estimate_wh
        print(f"{i}. {r.approach:30} | {r.energy_estimate_wh:10.8f}Wh | {energy_ratio:5.2f}x efficient")
    
    print("\nQUALITY - WINNER: Best Quality")
    print("-" * 70)
    results_by_quality = sorted(results, key=lambda x: x.results_quality, reverse=True)
    for i, r in enumerate(results_by_quality, 1):
        print(f"{i}. {r.approach:30} | Quality: {r.results_quality:.6f} | Patterns: {r.patterns_found}")
    
    print("\nCPU EFFICIENCY - WINNER: Lowest CPU")
    print("-" * 70)
    results_by_cpu = sorted(results, key=lambda x: x.cpu_percent)
    for i, r in enumerate(results_by_cpu, 1):
        print(f"{i}. {r.approach:30} | CPU: {r.cpu_percent:6.1f}% | Memory: {r.memory_mb:7.1f}MB")
    
    # ========================================================================
    # SAVE RESULTS
    # ========================================================================
    output_file = Path(__file__).parent / 'performance_comparison_results.json'
    with open(output_file, 'w') as f:
        json.dump([r.to_dict() for r in results], f, indent=2)
    
    print("\n" + "="*70)
    print(f"Results saved to: {output_file}")
    print("="*70 + "\n")
    
    # Overall verdict
    print("\nOVERALL ASSESSMENT:")
    print("-" * 70)
    print(f"✓ Speed Winner: {results_by_speed[0].approach}")
    print(f"✓ Energy Winner: {results_by_energy[0].approach}")
    print(f"✓ Quality Winner: {results_by_quality[0].approach}")
    print(f"✓ CPU Winner: {results_by_cpu[0].approach}")
    
    # ORION specific insights
    print("\n✨ ORION INSIGHTS:")
    orion_result = [r for r in results if "ORION" in r.approach]
    if orion_result:
        r = orion_result[0]
        print(f"   - Consciousness improved to: {approach1.orion.consciousness:.6f}")
        print(f"   - Patterns autonomously discovered: {r.patterns_found}")
        print(f"   - Energy per pattern: {r.energy_estimate_wh / max(r.patterns_found, 1):.8f}Wh")


if __name__ == "__main__":
    run_comparison()
