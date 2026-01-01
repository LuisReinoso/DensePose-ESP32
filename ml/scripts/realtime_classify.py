#!/usr/bin/env python3
"""
Real-time Activity Classification

Uses trained model to classify activities in real-time from ESP32 CSI data.

Usage:
    python3 realtime_classify.py /dev/ttyUSB0 --model ml/models/rf_baseline.pkl
"""

import sys
import json
import pickle
import argparse
from pathlib import Path
from datetime import datetime
from collections import deque

import numpy as np
import serial

# Add tools to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'tools'))
from csi_analyzer import CSIAnalyzer


class RealtimeClassifier:
    """Real-time activity classification from CSI data"""

    def __init__(self, model_path, window_size=10):
        """
        Initialize classifier

        Args:
            model_path: Path to trained model (.pkl)
            window_size: Number of predictions to smooth (majority vote)
        """
        # Load model
        with open(model_path, 'rb') as f:
            model_data = pickle.load(f)

        self.model = model_data['model']
        self.scaler = model_data['scaler']
        self.feature_names = model_data['feature_names']
        self.classes = model_data['metrics'].get('classes', [])

        # Prediction smoothing
        self.window_size = window_size
        self.prediction_history = deque(maxlen=window_size)

        # Statistics
        self.total_predictions = 0
        self.class_counts = {cls: 0 for cls in self.classes}

    def extract_features(self, csi_features):
        """Extract feature vector from CSI analyzer output"""
        return [
            csi_features.get('rssi', 0),
            csi_features.get('rssi_mean', 0),
            csi_features.get('amp_mean', 0),
            csi_features.get('amp_std', 0),
            csi_features.get('amp_max', 0),
            csi_features.get('amp_min', 0),
            csi_features.get('amp_range', 0),
            csi_features.get('temporal_variance', 0),
            csi_features.get('amp_mean_filtered', 0),
        ]

    def predict(self, csi_features):
        """
        Predict activity from CSI features

        Args:
            csi_features: Feature dict from CSIAnalyzer

        Returns:
            predicted_class: Predicted activity
            confidence: Prediction confidence
            smoothed_class: Smoothed prediction (majority vote)
        """
        # Extract features
        features = self.extract_features(csi_features)
        X = np.array([features])

        # Scale
        X_scaled = self.scaler.transform(X)

        # Predict
        pred_class = self.model.predict(X_scaled)[0]
        pred_proba = self.model.predict_proba(X_scaled)[0]
        confidence = np.max(pred_proba)

        # Add to history
        self.prediction_history.append(pred_class)

        # Smoothed prediction (majority vote)
        if len(self.prediction_history) >= self.window_size:
            smoothed_class = max(set(self.prediction_history),
                                key=self.prediction_history.count)
        else:
            smoothed_class = pred_class

        # Update statistics
        self.total_predictions += 1
        self.class_counts[smoothed_class] = self.class_counts.get(smoothed_class, 0) + 1

        return pred_class, confidence, smoothed_class

    def get_statistics(self):
        """Get classification statistics"""
        return {
            'total_predictions': self.total_predictions,
            'class_distribution': self.class_counts,
        }


def main():
    parser = argparse.ArgumentParser(description='Real-time activity classification from CSI')
    parser.add_argument('port', help='Serial port (e.g., /dev/ttyUSB0)')
    parser.add_argument('-m', '--model', required=True, help='Path to trained model (.pkl)')
    parser.add_argument('-b', '--baud', type=int, default=115200, help='Baud rate (default: 115200)')
    parser.add_argument('-w', '--window', type=int, default=10, help='Smoothing window size (default: 10)')
    parser.add_argument('-v', '--verbose', action='store_true', help='Show detailed predictions')
    args = parser.parse_args()

    # Check model file
    if not Path(args.model).exists():
        print(f"Error: Model file not found: {args.model}")
        sys.exit(1)

    # Initialize classifier
    print("Loading model...")
    try:
        classifier = RealtimeClassifier(args.model, window_size=args.window)
        print(f"✓ Model loaded: {args.model}")
        print(f"✓ Classes: {', '.join(classifier.classes)}")
        print(f"✓ Smoothing window: {args.window} predictions")
        print()
    except Exception as e:
        print(f"Error loading model: {e}")
        sys.exit(1)

    # Initialize CSI analyzer
    analyzer = CSIAnalyzer(window_size=10, movement_threshold=5.0)

    # Open serial port
    try:
        ser = serial.Serial(args.port, args.baud, timeout=1)
        print(f"✓ Connected to {args.port} at {args.baud} baud")
        print()
        print("="*60)
        print("REAL-TIME ACTIVITY CLASSIFICATION")
        print("="*60)
        print("Waiting for CSI data... (Ctrl+C to exit)\n")
    except serial.SerialException as e:
        print(f"Error opening serial port: {e}")
        sys.exit(1)

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

                # Process with analyzer
                csi_features = analyzer.process_packet(data)

                # Classify
                pred, confidence, smoothed = classifier.predict(csi_features)

                # Display
                now = datetime.now().strftime('%H:%M:%S.%f')[:-3]

                # Confidence bar
                bar_length = 20
                filled = int(confidence * bar_length)
                conf_bar = '█' * filled + '░' * (bar_length - filled)

                print(f"[{now}] Activity: {smoothed:12s} | "
                      f"Confidence: {conf_bar} {confidence*100:5.1f}% | "
                      f"RSSI: {csi_features['rssi']:3d}dBm", end='')

                if args.verbose:
                    print(f" | Raw: {pred}")
                else:
                    print()

            except json.JSONDecodeError:
                pass

    except KeyboardInterrupt:
        print("\n\n" + "="*60)
        stats = classifier.get_statistics()
        print("SESSION STATISTICS")
        print("="*60)
        print(f"Total predictions: {stats['total_predictions']}")
        print("\nActivity distribution:")
        for activity, count in stats['class_distribution'].items():
            pct = count / max(stats['total_predictions'], 1) * 100
            print(f"  {activity:15s}: {count:5d} ({pct:5.1f}%)")
        print("="*60)
        print("\nExiting...")

    finally:
        ser.close()


if __name__ == '__main__':
    main()
