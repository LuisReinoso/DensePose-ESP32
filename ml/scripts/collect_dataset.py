#!/usr/bin/env python3
"""
Dataset Collection Tool for DensePose-ESP32

Collects labeled CSI data for training pose estimation models.
Provides guided workflow for systematic data collection.

Usage:
    # Interactive mode
    python3 collect_dataset.py /dev/ttyUSB0

    # Specify activity and duration
    python3 collect_dataset.py /dev/ttyUSB0 --activity standing --duration 30

    # Custom output directory
    python3 collect_dataset.py /dev/ttyUSB0 --output-dir my_dataset
"""

import sys
import os
import json
import serial
import argparse
import numpy as np
from datetime import datetime
from pathlib import Path

# Add parent tools directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'tools'))
from csi_analyzer import CSIAnalyzer


class DatasetCollector:
    """Manages labeled dataset collection"""

    # Predefined activity categories
    ACTIVITIES = {
        'empty': 'No person in room (baseline)',
        'standing': 'Person standing still',
        'sitting': 'Person sitting still',
        'walking': 'Person walking around',
        'waving': 'Person waving arms',
        'jumping': 'Person jumping',
        'lying': 'Person lying down',
        'custom': 'Custom activity (specify description)'
    }

    def __init__(self, output_dir='ml/datasets'):
        """
        Initialize dataset collector

        Args:
            output_dir: Root directory for dataset storage
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Create metadata file
        self.metadata_file = self.output_dir / 'metadata.json'
        self.metadata = self.load_metadata()

    def load_metadata(self):
        """Load or create dataset metadata"""
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r') as f:
                return json.load(f)
        else:
            return {
                'created': datetime.now().isoformat(),
                'activities': {},
                'total_samples': 0,
                'collection_info': {
                    'device': 'ESP32-D0WD',
                    'firmware': 'DensePose-ESP32',
                    'sampling_rate': 'variable (WiFi traffic dependent)',
                }
            }

    def save_metadata(self):
        """Save dataset metadata"""
        self.metadata['updated'] = datetime.now().isoformat()
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2)

    def create_sample(self, activity, description='', trial_num=1):
        """
        Create a new sample collection session

        Args:
            activity: Activity name
            description: Optional description
            trial_num: Trial number for this activity

        Returns:
            Sample directory path
        """
        # Create activity directory
        activity_dir = self.output_dir / activity
        activity_dir.mkdir(exist_ok=True)

        # Create sample directory
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        sample_name = f"{activity}_trial{trial_num:02d}_{timestamp}"
        sample_dir = activity_dir / sample_name
        sample_dir.mkdir(exist_ok=True)

        # Create sample metadata
        sample_meta = {
            'activity': activity,
            'description': description or self.ACTIVITIES.get(activity, ''),
            'trial_num': trial_num,
            'timestamp': timestamp,
            'created': datetime.now().isoformat(),
        }

        with open(sample_dir / 'sample_info.json', 'w') as f:
            json.dump(sample_meta, f, indent=2)

        # Update dataset metadata
        if activity not in self.metadata['activities']:
            self.metadata['activities'][activity] = {
                'description': description or self.ACTIVITIES.get(activity, ''),
                'samples': []
            }

        self.metadata['activities'][activity]['samples'].append({
            'sample_name': sample_name,
            'trial_num': trial_num,
            'timestamp': timestamp,
        })
        self.metadata['total_samples'] += 1
        self.save_metadata()

        return sample_dir

    def get_next_trial_num(self, activity):
        """Get next trial number for activity"""
        if activity in self.metadata['activities']:
            return len(self.metadata['activities'][activity]['samples']) + 1
        return 1

    def print_dataset_summary(self):
        """Print current dataset statistics"""
        print("\n" + "="*60)
        print("DATASET SUMMARY")
        print("="*60)
        print(f"Dataset location: {self.output_dir}")
        print(f"Total samples: {self.metadata['total_samples']}")
        print(f"Activities collected: {len(self.metadata['activities'])}")
        print()

        if self.metadata['activities']:
            print("Samples per activity:")
            for activity, info in self.metadata['activities'].items():
                print(f"  {activity:15s}: {len(info['samples']):3d} samples")
        else:
            print("No samples collected yet.")

        print("="*60 + "\n")


def collect_csi_data(port, sample_dir, duration, activity, trial_num, baud=115200):
    """
    Collect CSI data for specified duration

    Args:
        port: Serial port
        sample_dir: Directory to save data
        duration: Collection duration in seconds
        activity: Activity name
        trial_num: Trial number
        baud: Baud rate
    """
    # Open serial port
    try:
        ser = serial.Serial(port, baud, timeout=1)
    except serial.SerialException as e:
        print(f"Error opening serial port: {e}")
        sys.exit(1)

    # Initialize analyzer
    analyzer = CSIAnalyzer(window_size=10, movement_threshold=5.0)

    # Open output files
    features_file = sample_dir / 'features.jsonl'
    raw_file = sample_dir / 'raw_csi.jsonl'

    features_out = open(features_file, 'w')
    raw_out = open(raw_file, 'w')

    print(f"\n{'='*60}")
    print(f"COLLECTING DATA")
    print(f"{'='*60}")
    print(f"Activity: {activity}")
    print(f"Trial: {trial_num}")
    print(f"Duration: {duration} seconds")
    print(f"Output: {sample_dir}")
    print()
    print("Data collection will start in:")
    for i in range(3, 0, -1):
        print(f"  {i}...")
        import time
        time.sleep(1)
    print("  START!\n")

    start_time = datetime.now()
    packet_count = 0

    try:
        while (datetime.now() - start_time).total_seconds() < duration:
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

                packet_count += 1

                # Process packet
                features = analyzer.process_packet(data)

                # Add label
                features['label'] = activity
                features['trial_num'] = trial_num

                # Display progress
                elapsed = (datetime.now() - start_time).total_seconds()
                remaining = duration - elapsed
                now = datetime.now().strftime('%H:%M:%S')
                print(f"[{now}] {packet_count:4d} packets | "
                      f"Elapsed: {elapsed:5.1f}s | Remaining: {remaining:5.1f}s | "
                      f"RSSI: {features['rssi']:3d}dBm", end='\r')

                # Save data
                features_out.write(json.dumps(features) + '\n')
                features_out.flush()

                raw_out.write(json.dumps(data) + '\n')
                raw_out.flush()

            except json.JSONDecodeError:
                pass

    except KeyboardInterrupt:
        print("\n\nCollection interrupted by user")

    finally:
        ser.close()
        features_out.close()
        raw_out.close()

        # Print summary
        elapsed = (datetime.now() - start_time).total_seconds()
        print(f"\n\n{'='*60}")
        print("COLLECTION COMPLETE")
        print(f"{'='*60}")
        print(f"Duration: {elapsed:.1f} seconds")
        print(f"Packets collected: {packet_count}")
        print(f"Avg rate: {packet_count/max(elapsed, 1):.1f} packets/sec")
        print(f"Features saved: {features_file}")
        print(f"Raw CSI saved: {raw_file}")

        # Get analyzer statistics
        stats = analyzer.get_statistics()
        print(f"\nMovement Statistics:")
        print(f"  Movement detected: {stats['movement_detected_count']} packets "
              f"({stats['movement_ratio']*100:.1f}%)")
        print(f"{'='*60}\n")


def interactive_mode(port, output_dir, baud=115200):
    """Interactive data collection mode"""
    collector = DatasetCollector(output_dir)

    print("\n" + "="*60)
    print("DENSEPOSE-ESP32 DATASET COLLECTION")
    print("="*60)

    while True:
        collector.print_dataset_summary()

        print("Available activities:")
        for i, (name, desc) in enumerate(DatasetCollector.ACTIVITIES.items(), 1):
            print(f"  {i}. {name:12s} - {desc}")
        print(f"  q. Quit")
        print()

        choice = input("Select activity (1-8 or 'q'): ").strip().lower()

        if choice == 'q':
            print("\nExiting dataset collection.")
            break

        try:
            idx = int(choice) - 1
            if idx < 0 or idx >= len(DatasetCollector.ACTIVITIES):
                print("Invalid choice!")
                continue

            activity = list(DatasetCollector.ACTIVITIES.keys())[idx]
        except ValueError:
            print("Invalid input!")
            continue

        # Get description for custom activity
        description = ''
        if activity == 'custom':
            description = input("Enter activity description: ").strip()

        # Get duration
        try:
            duration = int(input("Collection duration (seconds, default 30): ").strip() or "30")
        except ValueError:
            duration = 30

        # Get trial number
        trial_num = collector.get_next_trial_num(activity)
        print(f"\nThis will be trial #{trial_num} for '{activity}'")

        # Confirm
        confirm = input("Start collection? (y/n): ").strip().lower()
        if confirm != 'y':
            print("Collection cancelled.\n")
            continue

        # Create sample
        sample_dir = collector.create_sample(activity, description, trial_num)

        # Collect data
        collect_csi_data(port, sample_dir, duration, activity, trial_num, baud)

        # Ask to continue
        cont = input("\nCollect another sample? (y/n): ").strip().lower()
        if cont != 'y':
            break

    collector.print_dataset_summary()


def main():
    parser = argparse.ArgumentParser(
        description='Collect labeled CSI dataset for pose estimation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode
  python3 collect_dataset.py /dev/ttyUSB0

  # Quick collection
  python3 collect_dataset.py /dev/ttyUSB0 --activity standing --duration 30

  # Custom output directory
  python3 collect_dataset.py /dev/ttyUSB0 --output-dir my_data
        """
    )
    parser.add_argument('port', help='Serial port (e.g., /dev/ttyUSB0)')
    parser.add_argument('-b', '--baud', type=int, default=115200, help='Baud rate (default: 115200)')
    parser.add_argument('-o', '--output-dir', default='ml/datasets', help='Dataset directory (default: ml/datasets)')
    parser.add_argument('-a', '--activity', choices=list(DatasetCollector.ACTIVITIES.keys()),
                       help='Activity to collect (non-interactive mode)')
    parser.add_argument('-d', '--duration', type=int, default=30, help='Collection duration in seconds (default: 30)')
    parser.add_argument('--description', help='Custom activity description')
    args = parser.parse_args()

    # Check if tools are available
    try:
        from csi_analyzer import CSIAnalyzer
    except ImportError:
        print("Error: csi_analyzer.py not found in tools/")
        print("Make sure you're running from the project root directory")
        sys.exit(1)

    if args.activity:
        # Non-interactive mode
        collector = DatasetCollector(args.output_dir)
        trial_num = collector.get_next_trial_num(args.activity)
        sample_dir = collector.create_sample(args.activity, args.description or '', trial_num)
        collect_csi_data(args.port, sample_dir, args.duration, args.activity, trial_num, args.baud)
        collector.print_dataset_summary()
    else:
        # Interactive mode
        interactive_mode(args.port, args.output_dir, args.baud)


if __name__ == '__main__':
    main()
