#!/usr/bin/env python3
"""
Baseline ML Model Training for DensePose-ESP32

Trains activity classification models on collected CSI datasets.
Starts with Random Forest baseline, extensible to deep learning models.

Usage:
    # Train baseline Random Forest model
    python3 train_model.py --dataset ml/datasets

    # Train with specific test split
    python3 train_model.py --dataset ml/datasets --test-split 0.3

    # Save model
    python3 train_model.py --dataset ml/datasets --output ml/models/rf_model.pkl
"""

import sys
import json
import argparse
import pickle
from pathlib import Path
from collections import defaultdict, Counter

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from sklearn.preprocessing import StandardScaler


class CSIDatasetLoader:
    """Load and prepare CSI dataset for training"""

    def __init__(self, dataset_dir):
        """
        Initialize dataset loader

        Args:
            dataset_dir: Path to dataset directory
        """
        self.dataset_dir = Path(dataset_dir)
        if not self.dataset_dir.exists():
            raise FileNotFoundError(f"Dataset directory not found: {dataset_dir}")

        # Load metadata
        metadata_file = self.dataset_dir / 'metadata.json'
        if not metadata_file.exists():
            raise FileNotFoundError(f"Dataset metadata not found: {metadata_file}")

        with open(metadata_file, 'r') as f:
            self.metadata = json.load(f)

    def load_features(self):
        """
        Load all features from dataset

        Returns:
            X: Feature matrix (n_samples, n_features)
            y: Labels (n_samples,)
            feature_names: List of feature names
        """
        all_features = []
        all_labels = []

        print("Loading dataset...")

        for activity, info in self.metadata['activities'].items():
            print(f"  Loading {activity}...")

            for sample_info in info['samples']:
                sample_name = sample_info['sample_name']
                features_file = self.dataset_dir / activity / sample_name / 'features.jsonl'

                if not features_file.exists():
                    print(f"    Warning: {features_file} not found, skipping")
                    continue

                # Load features from this sample
                with open(features_file, 'r') as f:
                    for line in f:
                        data = json.loads(line.strip())

                        # Extract feature vector
                        features = self._extract_feature_vector(data)
                        label = data.get('label', activity)

                        all_features.append(features)
                        all_labels.append(label)

        # Convert to numpy arrays
        X = np.array(all_features)
        y = np.array(all_labels)

        # Feature names
        feature_names = [
            'rssi', 'rssi_mean', 'amp_mean', 'amp_std',
            'amp_max', 'amp_min', 'amp_range',
            'temporal_variance', 'amp_mean_filtered'
        ]

        print(f"\nDataset loaded:")
        print(f"  Total samples: {len(X)}")
        print(f"  Features per sample: {X.shape[1]}")
        print(f"  Classes: {len(set(y))}")
        print(f"  Class distribution: {dict(Counter(y))}")

        return X, y, feature_names

    def _extract_feature_vector(self, data):
        """Extract feature vector from data dict"""
        return [
            data.get('rssi', 0),
            data.get('rssi_mean', 0),
            data.get('amp_mean', 0),
            data.get('amp_std', 0),
            data.get('amp_max', 0),
            data.get('amp_min', 0),
            data.get('amp_range', 0),
            data.get('temporal_variance', 0),
            data.get('amp_mean_filtered', 0),
        ]


def train_random_forest(X_train, y_train, X_test, y_test, feature_names):
    """
    Train Random Forest classifier

    Args:
        X_train, y_train: Training data
        X_test, y_test: Test data
        feature_names: Feature names

    Returns:
        model: Trained model
        scaler: Fitted scaler
        metrics: Performance metrics
    """
    print("\n" + "="*60)
    print("TRAINING RANDOM FOREST CLASSIFIER")
    print("="*60)

    # Normalize features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Train Random Forest
    print("\nTraining model...")
    rf = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1
    )

    rf.fit(X_train_scaled, y_train)

    # Cross-validation
    print("Running 5-fold cross-validation...")
    cv_scores = cross_val_score(rf, X_train_scaled, y_train, cv=5)
    print(f"  CV Accuracy: {cv_scores.mean():.3f} (+/- {cv_scores.std()*2:.3f})")

    # Predictions
    y_pred = rf.predict(X_test_scaled)

    # Metrics
    print("\n" + "="*60)
    print("MODEL PERFORMANCE")
    print("="*60)

    print(f"\nTest Accuracy: {accuracy_score(y_test, y_pred):.3f}")

    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, zero_division=0))

    print("Confusion Matrix:")
    cm = confusion_matrix(y_test, y_pred)
    classes = sorted(set(y_train) | set(y_test))
    print("\n" + " "*15 + "  ".join(f"{c:8s}" for c in classes))
    for i, cls in enumerate(classes):
        print(f"{cls:12s} | " + "  ".join(f"{cm[i,j]:8d}" for j in range(len(classes))))

    # Feature importance
    print("\nFeature Importance:")
    importances = rf.feature_importances_
    indices = np.argsort(importances)[::-1]
    for i in range(len(feature_names)):
        idx = indices[i]
        print(f"  {i+1}. {feature_names[idx]:20s}: {importances[idx]:.4f}")

    metrics = {
        'test_accuracy': accuracy_score(y_test, y_pred),
        'cv_accuracy_mean': cv_scores.mean(),
        'cv_accuracy_std': cv_scores.std(),
        'classification_report': classification_report(y_test, y_pred, output_dict=True, zero_division=0),
        'confusion_matrix': cm.tolist(),
        'feature_importance': {name: float(imp) for name, imp in zip(feature_names, importances)},
        'classes': classes,
    }

    return rf, scaler, metrics


def save_model(model, scaler, metrics, feature_names, output_path):
    """Save trained model and metadata"""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    model_data = {
        'model': model,
        'scaler': scaler,
        'feature_names': feature_names,
        'metrics': metrics,
        'model_type': 'RandomForestClassifier',
        'trained_date': str(np.datetime64('now')),
    }

    with open(output_path, 'wb') as f:
        pickle.dump(model_data, f)

    print(f"\nModel saved to: {output_path}")

    # Save metrics as JSON
    metrics_path = output_path.with_suffix('.json')
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)

    print(f"Metrics saved to: {metrics_path}")


def main():
    parser = argparse.ArgumentParser(
        description='Train activity classification model on CSI dataset'
    )
    parser.add_argument('--dataset', default='ml/datasets',
                       help='Path to dataset directory (default: ml/datasets)')
    parser.add_argument('--test-split', type=float, default=0.2,
                       help='Test set fraction (default: 0.2)')
    parser.add_argument('--output', default='ml/models/rf_baseline.pkl',
                       help='Output model path (default: ml/models/rf_baseline.pkl)')
    parser.add_argument('--random-seed', type=int, default=42,
                       help='Random seed for reproducibility (default: 42)')
    args = parser.parse_args()

    # Check dependencies
    try:
        import sklearn
    except ImportError:
        print("Error: scikit-learn not installed")
        print("Install with: pip install scikit-learn")
        sys.exit(1)

    # Load dataset
    try:
        loader = CSIDatasetLoader(args.dataset)
        X, y, feature_names = loader.load_features()
    except Exception as e:
        print(f"Error loading dataset: {e}")
        sys.exit(1)

    if len(X) == 0:
        print("Error: No data loaded!")
        sys.exit(1)

    # Check minimum samples
    if len(X) < 50:
        print(f"Warning: Only {len(X)} samples. Consider collecting more data (recommended: 500+)")

    # Train/test split
    print(f"\nSplitting data (test_size={args.test_split})...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=args.test_split, random_state=args.random_seed, stratify=y
    )

    print(f"  Training samples: {len(X_train)}")
    print(f"  Test samples: {len(X_test)}")

    # Train model
    model, scaler, metrics = train_random_forest(
        X_train, y_train, X_test, y_test, feature_names
    )

    # Save model
    save_model(model, scaler, metrics, feature_names, args.output)

    print("\n" + "="*60)
    print("TRAINING COMPLETE")
    print("="*60)
    print(f"Test Accuracy: {metrics['test_accuracy']:.1%}")
    print(f"Model: {args.output}")
    print("="*60 + "\n")


if __name__ == '__main__':
    main()
