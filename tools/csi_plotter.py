#!/usr/bin/env python3
"""
CSI Data Visualization Tool

Plots CSI features from saved JSON data to visualize patterns and movement.

Usage:
    # Plot amplitude over time
    python3 csi_plotter.py csi_features.json --plot amplitude

    # Plot RSSI and variance
    python3 csi_plotter.py csi_features.json --plot rssi variance

    # Compare baseline vs movement
    python3 csi_plotter.py baseline.json movement.json --compare
"""

import sys
import json
import argparse
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime


def load_csi_data(filename):
    """Load CSI feature data from JSONL file"""
    data = []
    with open(filename, 'r') as f:
        for line in f:
            try:
                data.append(json.loads(line.strip()))
            except json.JSONDecodeError:
                continue
    return data


def plot_features(data, features_to_plot):
    """Plot specified features over time"""
    if not data:
        print("No data to plot!")
        return

    # Extract timestamps (convert ms to seconds)
    timestamps = np.array([d['timestamp'] for d in data]) / 1000.0
    timestamps = timestamps - timestamps[0]  # Start from 0

    # Number of subplots needed
    n_plots = len(features_to_plot)
    fig, axes = plt.subplots(n_plots, 1, figsize=(12, 4*n_plots), sharex=True)

    if n_plots == 1:
        axes = [axes]

    for ax, feature in zip(axes, features_to_plot):
        if feature == 'amplitude':
            values = [d['amp_mean'] for d in data]
            filtered = [d.get('amp_mean_filtered', d['amp_mean']) for d in data]
            ax.plot(timestamps, values, 'b-', alpha=0.5, label='Raw')
            ax.plot(timestamps, filtered, 'r-', linewidth=2, label='Filtered')
            ax.set_ylabel('Amplitude (mean)')
            ax.legend()
            ax.grid(True, alpha=0.3)

        elif feature == 'rssi':
            values = [d['rssi'] for d in data]
            filtered = [d.get('rssi_mean', d['rssi']) for d in data]
            ax.plot(timestamps, values, 'g-', alpha=0.5, label='Raw RSSI')
            ax.plot(timestamps, filtered, 'darkgreen', linewidth=2, label='Mean RSSI')
            ax.set_ylabel('RSSI (dBm)')
            ax.legend()
            ax.grid(True, alpha=0.3)

        elif feature == 'variance':
            values = [d.get('temporal_variance', 0) for d in data]
            ax.plot(timestamps, values, 'purple', linewidth=2)
            ax.set_ylabel('Temporal Variance')
            ax.grid(True, alpha=0.3)

            # Mark movement detection
            movement = [d.get('movement_detected', False) for d in data]
            movement_times = timestamps[np.array(movement)]
            movement_vals = np.array(values)[np.array(movement)]
            ax.scatter(movement_times, movement_vals, color='red', s=50, label='Movement', zorder=5)
            ax.legend()

        elif feature == 'std':
            values = [d['amp_std'] for d in data]
            ax.plot(timestamps, values, 'orange', linewidth=2)
            ax.set_ylabel('Amplitude Std Dev')
            ax.grid(True, alpha=0.3)

        elif feature == 'range':
            values = [d['amp_range'] for d in data]
            ax.plot(timestamps, values, 'brown', linewidth=2)
            ax.set_ylabel('Amplitude Range')
            ax.grid(True, alpha=0.3)

        else:
            print(f"Unknown feature: {feature}")

    axes[-1].set_xlabel('Time (seconds)')
    plt.suptitle('CSI Features Over Time', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.show()


def compare_datasets(baseline_data, movement_data):
    """Compare baseline and movement datasets"""
    if not baseline_data or not movement_data:
        print("Need both baseline and movement data!")
        return

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # Extract features
    baseline_amp = [d['amp_mean'] for d in baseline_data]
    movement_amp = [d['amp_mean'] for d in movement_data]

    baseline_var = [d.get('temporal_variance', 0) for d in baseline_data]
    movement_var = [d.get('temporal_variance', 0) for d in movement_data]

    baseline_std = [d['amp_std'] for d in baseline_data]
    movement_std = [d['amp_std'] for d in movement_data]

    # Plot 1: Amplitude comparison
    axes[0,0].hist(baseline_amp, bins=30, alpha=0.5, label='Baseline', color='blue')
    axes[0,0].hist(movement_amp, bins=30, alpha=0.5, label='Movement', color='red')
    axes[0,0].set_xlabel('Amplitude Mean')
    axes[0,0].set_ylabel('Frequency')
    axes[0,0].set_title('Amplitude Distribution')
    axes[0,0].legend()
    axes[0,0].grid(True, alpha=0.3)

    # Plot 2: Temporal variance comparison
    axes[0,1].hist(baseline_var, bins=30, alpha=0.5, label='Baseline', color='blue')
    axes[0,1].hist(movement_var, bins=30, alpha=0.5, label='Movement', color='red')
    axes[0,1].set_xlabel('Temporal Variance')
    axes[0,1].set_ylabel('Frequency')
    axes[0,1].set_title('Temporal Variance Distribution')
    axes[0,1].legend()
    axes[0,1].grid(True, alpha=0.3)

    # Plot 3: Amplitude std comparison
    axes[1,0].boxplot([baseline_amp, movement_amp], labels=['Baseline', 'Movement'])
    axes[1,0].set_ylabel('Amplitude Mean')
    axes[1,0].set_title('Amplitude Statistics')
    axes[1,0].grid(True, alpha=0.3)

    # Plot 4: Variance boxplot
    axes[1,1].boxplot([baseline_var, movement_var], labels=['Baseline', 'Movement'])
    axes[1,1].set_ylabel('Temporal Variance')
    axes[1,1].set_title('Variance Statistics')
    axes[1,1].grid(True, alpha=0.3)

    plt.suptitle('Baseline vs Movement Comparison', fontsize=14, fontweight='bold')
    plt.tight_layout()

    # Print statistics
    print("\n" + "="*60)
    print("BASELINE STATISTICS:")
    print(f"  Amplitude:  μ={np.mean(baseline_amp):.2f}, σ={np.std(baseline_amp):.2f}")
    print(f"  Variance:   μ={np.mean(baseline_var):.2f}, σ={np.std(baseline_var):.2f}")
    print(f"  Std Dev:    μ={np.mean(baseline_std):.2f}, σ={np.std(baseline_std):.2f}")

    print("\nMOVEMENT STATISTICS:")
    print(f"  Amplitude:  μ={np.mean(movement_amp):.2f}, σ={np.std(movement_amp):.2f}")
    print(f"  Variance:   μ={np.mean(movement_var):.2f}, σ={np.std(movement_var):.2f}")
    print(f"  Std Dev:    μ={np.mean(movement_std):.2f}, σ={np.std(movement_std):.2f}")

    print("\nDIFFERENCES:")
    print(f"  Amplitude:  Δμ={np.mean(movement_amp) - np.mean(baseline_amp):.2f} "
          f"({(np.mean(movement_amp) - np.mean(baseline_amp)) / np.mean(baseline_amp) * 100:+.1f}%)")
    print(f"  Variance:   Δμ={np.mean(movement_var) - np.mean(baseline_var):.2f} "
          f"({(np.mean(movement_var) - np.mean(baseline_var)) / max(np.mean(baseline_var), 0.001) * 100:+.1f}%)")
    print("="*60 + "\n")

    plt.show()


def main():
    parser = argparse.ArgumentParser(description='Visualize CSI feature data')
    parser.add_argument('input', nargs='+', help='Input JSONL file(s) with CSI features')
    parser.add_argument('-p', '--plot', nargs='+',
                       choices=['amplitude', 'rssi', 'variance', 'std', 'range'],
                       default=['amplitude', 'variance'],
                       help='Features to plot (default: amplitude variance)')
    parser.add_argument('-c', '--compare', action='store_true',
                       help='Compare two datasets (baseline vs movement)')
    args = parser.parse_args()

    # Check matplotlib
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("Error: matplotlib not installed")
        print("Install with: pip install matplotlib")
        sys.exit(1)

    if args.compare:
        if len(args.input) != 2:
            print("Error: --compare requires exactly 2 input files")
            print("Usage: csi_plotter.py baseline.json movement.json --compare")
            sys.exit(1)

        print(f"Loading baseline: {args.input[0]}")
        baseline_data = load_csi_data(args.input[0])
        print(f"  {len(baseline_data)} packets")

        print(f"Loading movement: {args.input[1]}")
        movement_data = load_csi_data(args.input[1])
        print(f"  {len(movement_data)} packets")

        compare_datasets(baseline_data, movement_data)

    else:
        if len(args.input) > 1:
            print("Warning: Multiple files provided but --compare not set")
            print("Using first file only")

        print(f"Loading data: {args.input[0]}")
        data = load_csi_data(args.input[0])
        print(f"  {len(data)} packets")

        if len(data) == 0:
            print("Error: No data found in file")
            sys.exit(1)

        plot_features(data, args.plot)


if __name__ == '__main__':
    main()
