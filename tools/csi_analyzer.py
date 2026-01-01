#!/usr/bin/env python3
"""
CSI Data Analyzer with Signal Processing

This tool collects CSI data from ESP32 and performs real-time signal processing:
- Noise filtering (moving average, exponential smoothing)
- Feature extraction (amplitude statistics, variance, change detection)
- Movement detection
- Data visualization and export

Usage:
    # Collect and analyze CSI data
    python3 csi_analyzer.py /dev/ttyUSB0

    # Save processed data
    python3 csi_analyzer.py /dev/ttyUSB0 --output processed_csi.json

    # Real-time movement detection
    python3 csi_analyzer.py /dev/ttyUSB0 --detect-movement
"""

import sys
import json
import serial
import argparse
import numpy as np
from datetime import datetime
from collections import deque


class CSIAnalyzer:
    """Real-time CSI data analysis and processing"""

    def __init__(self, window_size=10, movement_threshold=5.0):
        """
        Initialize CSI analyzer

        Args:
            window_size: Number of packets for moving average
            movement_threshold: Amplitude variance threshold for movement detection
        """
        self.window_size = window_size
        self.movement_threshold = movement_threshold

        # Ring buffers for windowed analysis
        self.amp_history = deque(maxlen=window_size)
        self.rssi_history = deque(maxlen=window_size)

        # Statistics
        self.packet_count = 0
        self.movement_detected_count = 0

    def process_packet(self, data):
        """
        Process a single CSI packet

        Args:
            data: Dict with CSI data (ts, rssi, num, amp, phase)

        Returns:
            Dict with processed features
        """
        self.packet_count += 1

        # Extract raw data
        timestamp = data.get('ts', 0)
        rssi = data.get('rssi', 0)
        amp = np.array(data.get('amp', []))
        phase = np.array(data.get('phase', []))

        # Calculate amplitude statistics
        amp_mean = np.mean(amp)
        amp_std = np.std(amp)
        amp_max = np.max(amp)
        amp_min = np.min(amp)

        # Add to history
        self.amp_history.append(amp)
        self.rssi_history.append(rssi)

        # Calculate windowed features
        features = {
            'timestamp': timestamp,
            'packet_num': self.packet_count,
            'rssi': rssi,
            'rssi_mean': np.mean(self.rssi_history) if self.rssi_history else rssi,
            'amp_mean': amp_mean,
            'amp_std': amp_std,
            'amp_max': amp_max,
            'amp_min': amp_min,
            'amp_range': amp_max - amp_min,
        }

        # Movement detection (if we have enough history)
        if len(self.amp_history) >= self.window_size:
            # Calculate variance across time for each subcarrier
            amp_array = np.array(self.amp_history)  # shape: (window_size, num_subcarriers)
            temporal_variance = np.var(amp_array, axis=0)  # variance over time for each subcarrier
            mean_temporal_variance = np.mean(temporal_variance)

            features['temporal_variance'] = mean_temporal_variance
            features['movement_detected'] = mean_temporal_variance > self.movement_threshold

            if features['movement_detected']:
                self.movement_detected_count += 1
        else:
            features['temporal_variance'] = 0.0
            features['movement_detected'] = False

        # Filtered amplitude (exponential moving average)
        if len(self.amp_history) > 1:
            alpha = 0.3  # Smoothing factor
            prev_amp = self.amp_history[-2]
            features['amp_mean_filtered'] = alpha * amp_mean + (1 - alpha) * np.mean(prev_amp)
        else:
            features['amp_mean_filtered'] = amp_mean

        return features

    def get_statistics(self):
        """Get overall statistics"""
        return {
            'total_packets': self.packet_count,
            'movement_detected_count': self.movement_detected_count,
            'movement_ratio': self.movement_detected_count / max(self.packet_count, 1),
        }


def main():
    parser = argparse.ArgumentParser(description='Analyze CSI data from ESP32 with signal processing')
    parser.add_argument('port', help='Serial port (e.g., /dev/ttyUSB0, COM3)')
    parser.add_argument('-b', '--baud', type=int, default=115200, help='Baud rate (default: 115200)')
    parser.add_argument('-w', '--window', type=int, default=10, help='Window size for moving average (default: 10)')
    parser.add_argument('-t', '--threshold', type=float, default=5.0, help='Movement detection threshold (default: 5.0)')
    parser.add_argument('-o', '--output', help='Save processed features to file (JSONL format)')
    parser.add_argument('-r', '--raw-output', help='Save raw CSI data to file (JSONL format)')
    parser.add_argument('-d', '--detect-movement', action='store_true', help='Enable movement detection alerts')
    parser.add_argument('-v', '--verbose', action='store_true', help='Show detailed output')
    args = parser.parse_args()

    # Initialize analyzer
    analyzer = CSIAnalyzer(window_size=args.window, movement_threshold=args.threshold)

    # Open serial port
    try:
        ser = serial.Serial(args.port, args.baud, timeout=1)
        print(f"✓ Connected to {args.port} at {args.baud} baud")
        print(f"✓ Analysis window: {args.window} packets")
        print(f"✓ Movement threshold: {args.threshold}")
        if args.detect_movement:
            print("✓ Movement detection: ENABLED")
        print()
        print("Waiting for CSI data... (Ctrl+C to exit)")
        print()
    except serial.SerialException as e:
        print(f"Error opening serial port: {e}")
        sys.exit(1)

    # Open output files if specified
    outfile = None
    raw_outfile = None
    if args.output:
        outfile = open(args.output, 'a')
        print(f"Saving processed features to {args.output}")
    if args.raw_output:
        raw_outfile = open(args.raw_output, 'a')
        print(f"Saving raw CSI data to {args.raw_output}")
    if outfile or raw_outfile:
        print()

    try:
        while True:
            line = ser.readline().decode('utf-8', errors='ignore').strip()

            # Skip empty lines and ESP-IDF log lines
            if not line or not line.startswith('{'):
                continue

            try:
                # Parse JSON
                data = json.loads(line)

                # Validate expected fields
                if 'ts' not in data or 'rssi' not in data or 'amp' not in data:
                    continue

                # Process packet
                features = analyzer.process_packet(data)

                # Display
                now = datetime.now().strftime('%H:%M:%S.%f')[:-3]
                status = "🟢 MOVEMENT" if features.get('movement_detected', False) else "⚪ STATIC"

                if args.detect_movement:
                    print(f"[{now}] Packet #{features['packet_num']:4d} | "
                          f"RSSI={features['rssi']:3d}dBm | "
                          f"Amp: μ={features['amp_mean']:5.1f} σ={features['amp_std']:5.1f} | "
                          f"Var={features.get('temporal_variance', 0):5.2f} | {status}")
                else:
                    print(f"[{now}] Packet #{features['packet_num']:4d} | "
                          f"RSSI={features['rssi']:3d}dBm (avg={features['rssi_mean']:5.1f}) | "
                          f"Amp: μ={features['amp_mean']:5.1f} σ={features['amp_std']:5.1f} | "
                          f"Filtered={features['amp_mean_filtered']:5.1f}")

                if args.verbose:
                    print(f"  Range: [{features['amp_min']:.1f}, {features['amp_max']:.1f}] "
                          f"span={features['amp_range']:.1f}")
                    if 'temporal_variance' in features:
                        print(f"  Temporal variance: {features['temporal_variance']:.2f}")
                    print()

                # Save processed features
                if outfile:
                    outfile.write(json.dumps(features) + '\n')
                    outfile.flush()

                # Save raw data
                if raw_outfile:
                    raw_outfile.write(json.dumps(data) + '\n')
                    raw_outfile.flush()

            except json.JSONDecodeError:
                # Not valid JSON, skip
                pass

    except KeyboardInterrupt:
        print("\n")
        print("="*60)
        stats = analyzer.get_statistics()
        print(f"Session Statistics:")
        print(f"  Total packets: {stats['total_packets']}")
        print(f"  Movement detected: {stats['movement_detected_count']} "
              f"({stats['movement_ratio']*100:.1f}%)")
        print("="*60)
        print("Exiting...")

    finally:
        ser.close()
        if outfile:
            outfile.close()
            print(f"Processed features saved to {args.output}")
        if raw_outfile:
            raw_outfile.close()
            print(f"Raw CSI data saved to {args.raw_output}")


if __name__ == '__main__':
    main()
