# Phase 4: Machine Learning & Activity Classification

**Status**: ✅ COMPLETE (Phase 4A - Baseline ML)
**Date**: December 31, 2025

---

## Overview

Phase 4 implements the complete machine learning pipeline for WiFi CSI-based activity classification. This phase takes the processed CSI features from Phase 3 and trains models to recognize human activities.

**What's Implemented**:
- Structured dataset collection workflow
- Random Forest baseline classifier
- Real-time activity classification
- Model evaluation and metrics
- Complete ML pipeline (collect → train → infer)

---

## Phase 4A vs 4B

- **Phase 4A** (✅ COMPLETE): Baseline ML pipeline with Random Forest
- **Phase 4B** (Future): Advanced ML (Deep Learning, ESP32 deployment)

This document covers **Phase 4A**.

---

## What Was Implemented

### 1. Dataset Collection Tool (`ml/scripts/collect_dataset.py`)

**Purpose**: Systematic collection of labeled CSI data

**Features**:
- **Interactive Mode**: Menu-driven collection workflow
- **Predefined Activities**: 8 standard activities (empty, standing, sitting, walking, waving, jumping, lying, custom)
- **Automatic Organization**: Creates structured dataset directory
- **Metadata Tracking**: JSON metadata for dataset/samples
- **Trial Management**: Auto-increments trial numbers
- **Quality Control**: Countdown before collection, progress display

**Usage**:
```bash
# Interactive mode
python3 ml/scripts/collect_dataset.py /dev/ttyUSB0

# Quick collection
python3 ml/scripts/collect_dataset.py /dev/ttyUSB0 \
    --activity standing --duration 30
```

**Dataset Structure**:
```
ml/datasets/
├── metadata.json              # Dataset metadata
├── empty/
│   ├── empty_trial01_20251231_201530/
│   │   ├── features.jsonl    # Processed CSI features
│   │   ├── raw_csi.jsonl     # Raw CSI data
│   │   └── sample_info.json  # Sample metadata
│   └── empty_trial02_.../
├── standing/
│   └── standing_trial01_.../
└── walking/
    └── walking_trial01_.../
```

**Metadata Format**:
```json
{
  "created": "2025-12-31T20:15:30",
  "activities": {
    "standing": {
      "description": "Person standing still",
      "samples": [
        {
          "sample_name": "standing_trial01_20251231_201530",
          "trial_num": 1,
          "timestamp": "20251231_201530"
        }
      ]
    }
  },
  "total_samples": 5
}
```

---

### 2. Model Training Pipeline (`ml/scripts/train_model.py`)

**Purpose**: Train classification models on collected datasets

**Features**:
- **Data Loading**: Loads all features from dataset directory
- **Preprocessing**: StandardScaler for feature normalization
- **Model**: Random Forest Classifier (100 trees, max_depth=10)
- **Validation**: 5-fold cross-validation
- **Evaluation**: Classification report, confusion matrix, feature importance
- **Export**: Saves model + scaler + metrics

**Usage**:
```bash
python3 ml/scripts/train_model.py \
    --dataset ml/datasets \
    --test-split 0.2 \
    --output ml/models/rf_baseline.pkl
```

**Training Process**:
1. Load features from all samples (JSONL files)
2. Extract feature vectors (9 features per packet)
3. Split train/test (stratified, default 80/20)
4. Normalize features with StandardScaler
5. Train Random Forest with cross-validation
6. Evaluate on held-out test set
7. Save model + metadata

**Output**:
- `model.pkl`: Pickled model (RandomForest + Scaler + metadata)
- `model.json`: Metrics (accuracy, classification report, feature importance)

**Features Used** (9 total):
1. `rssi` - Raw signal strength
2. `rssi_mean` - Windowed RSSI average
3. `amp_mean` - Mean amplitude across subcarriers
4. `amp_std` - Amplitude standard deviation
5. `amp_max` - Maximum amplitude
6. `amp_min` - Minimum amplitude
7. `amp_range` - Amplitude range (max-min)
8. `temporal_variance` - Variance over time (movement indicator)
9. `amp_mean_filtered` - EMA-smoothed amplitude

---

### 3. Real-time Classification (`ml/scripts/realtime_classify.py`)

**Purpose**: Real-time activity recognition from live CSI data

**Features**:
- **Live Prediction**: Classifies activities in real-time
- **Prediction Smoothing**: Majority vote over sliding window (default: 10)
- **Confidence Display**: Visual confidence bars
- **Session Statistics**: Activity distribution summary

**Usage**:
```bash
python3 ml/scripts/realtime_classify.py /dev/ttyUSB0 \
    --model ml/models/rf_baseline.pkl \
    --window 10
```

**Output Example**:
```
[20:15:30.123] Activity: standing     | Confidence: ████████████████░░░░ 85.2% | RSSI: -45dBm
[20:15:30.234] Activity: walking      | Confidence: ██████████████████░░ 92.1% | RSSI: -46dBm
[20:15:30.345] Activity: waving       | Confidence: ███████████████████░ 95.8% | RSSI: -44dBm
```

**Smoothing Algorithm**:
- Collects last N predictions (default N=10)
- Returns most common prediction (majority vote)
- Reduces jitter and false positives
- Trade-off: Adds ~1-2 second latency

---

## Machine Learning Pipeline

### Complete Workflow

```
┌─────────────────────────────────────────────────────────────┐
│  1. DATA COLLECTION (collect_dataset.py)                   │
│     ESP32 → Serial → CSI Analyzer → Labeled Features       │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  2. DATASET ORGANIZATION                                     │
│     datasets/                                               │
│     ├── activity1/trial01/features.jsonl                   │
│     ├── activity2/trial01/features.jsonl                   │
│     └── metadata.json                                       │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  3. MODEL TRAINING (train_model.py)                         │
│     Load Features → Normalize → Train RF → Evaluate        │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  4. MODEL EXPORT                                            │
│     models/rf_baseline.pkl (Model + Scaler + Metrics)      │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  5. REAL-TIME INFERENCE (realtime_classify.py)              │
│     ESP32 → CSI Analyzer → Model → Activity Prediction     │
└─────────────────────────────────────────────────────────────┘
```

---

## Random Forest Classifier

### Why Random Forest?

**Advantages**:
- ✅ No hyperparameter tuning needed (works well with defaults)
- ✅ Fast training (<1 second for 1000 samples)
- ✅ Fast inference (<1ms per prediction)
- ✅ Feature importance analysis
- ✅ Robust to noisy features
- ✅ No need for deep learning infrastructure

**Limitations**:
- ❌ May not capture complex temporal patterns
- ❌ Limited compared to deep learning for large datasets
- ❌ No automatic feature learning

**Configuration**:
```python
RandomForestClassifier(
    n_estimators=100,      # 100 decision trees
    max_depth=10,          # Max tree depth (prevents overfitting)
    min_samples_split=5,   # Min samples to split node
    min_samples_leaf=2,    # Min samples per leaf
    random_state=42,       # Reproducibility
    n_jobs=-1              # Use all CPU cores
)
```

---

## Expected Performance

### Baseline Metrics (with recommended dataset)

**Dataset Size**: ~1500 samples (5 activities × 10 trials × 30 packets/trial)

| Metric | Expected Value |
|--------|----------------|
| Test Accuracy | 70-85% |
| CV Accuracy (5-fold) | 65-80% |
| Training Time | <5 seconds |
| Inference Time | <1ms/packet |

### Per-Activity Performance

| Activity | Precision | Recall | F1-Score |
|----------|-----------|--------|----------|
| empty | 0.90-0.95 | 0.90-0.95 | 0.90-0.95 |
| standing | 0.65-0.75 | 0.70-0.80 | 0.67-0.77 |
| sitting | 0.65-0.75 | 0.65-0.75 | 0.65-0.75 |
| walking | 0.75-0.85 | 0.80-0.90 | 0.77-0.87 |
| waving | 0.80-0.90 | 0.80-0.90 | 0.80-0.90 |

### Confusion Matrix Patterns

**High Confusion** (similar CSI signatures):
- `standing` ↔ `sitting` (both static)
- `walking` ↔ `jumping` (both dynamic)

**Low Confusion** (distinct signatures):
- `empty` ↔ any activity (presence vs absence)
- `static` ↔ `dynamic` (movement detection)

### Feature Importance

Expected ranking:
1. **temporal_variance** (40-50%) - Primary movement indicator
2. **amp_std** (15-25%) - Signal variability
3. **amp_range** (10-15%) - Dynamic range
4. **amp_mean** (5-10%) - Signal strength
5. **rssi_mean** (5-10%) - Connection quality
6. Others (<5% each)

---

## Data Collection Best Practices

### Environment Setup

**✅ Do**:
- Clear room of obstacles between ESP32 and router
- Maintain consistent ESP32 placement (2-3m from router)
- Minimize other people in room during collection
- Generate consistent WiFi traffic (`ping -i 0.1`)
- Collect at same time of day (avoid interference changes)

**❌ Don't**:
- Move ESP32 between trials
- Change router settings during collection
- Have multiple people in room
- Collect with inconsistent WiFi traffic
- Mix different environments (home/office)

### Collection Protocol

**1. Baseline Collection** (`empty`):
- 5 trials minimum
- Completely empty room
- 30 seconds per trial
- Walk out of room before starting

**2. Activity Collection**:
- Consistent subject positioning
- Same subject for all trials (or balanced across subjects)
- Clear activity definition (fast walk vs slow walk)
- Natural movements (don't freeze unnaturally)

**3. Data Quality**:
- Monitor packet rate during collection (>0.5 packets/sec)
- Check RSSI stability (-30 to -80 dBm)
- Verify no errors in console output

### Minimum Dataset

| Component | Quantity | Duration | Total Time |
|-----------|----------|----------|------------|
| Activities | 5 | - | - |
| Trials/activity | 5 | 30s | 2.5 min/activity |
| **Total Collection** | **25 trials** | - | **~15 minutes** |
| **Total Samples** | **~750 packets** | - | - |

**Recommended**: 10 trials/activity = 50 trials = **~1500 packets**

---

## Improving Model Performance

### 1. Collect More Data

**Impact**: High
- Target: 1000+ samples per activity
- Helps: Reduces overfitting, improves generalization

### 2. Balance Dataset

**Impact**: High
- Equal samples per activity
- Prevents bias toward majority class

### 3. Feature Engineering

**Impact**: Medium-High
- Add FFT features (frequency domain)
- Add PCA components (dimensionality reduction)
- Subcarrier correlation matrix

### 4. Tune Hyperparameters

**Impact**: Medium
```python
# Grid search
from sklearn.model_selection import GridSearchCV

param_grid = {
    'n_estimators': [50, 100, 200],
    'max_depth': [5, 10, 15],
    'min_samples_split': [2, 5, 10],
}

grid_search = GridSearchCV(RandomForestClassifier(), param_grid, cv=5)
grid_search.fit(X_train, y_train)
print(f"Best params: {grid_search.best_params_}")
```

### 5. Ensemble Methods

**Impact**: Medium
- Combine Random Forest + SVM + MLP
- Voting classifier
- Stacking

### 6. Deep Learning (Phase 4B)

**Impact**: High (for large datasets)
- CNN for spatial patterns
- LSTM for temporal sequences
- Attention mechanisms

---

## Troubleshooting

### Training Issues

**"No data loaded!"**:
```bash
# Check dataset structure
ls ml/datasets/
cat ml/datasets/metadata.json

# Collect data first
python3 ml/scripts/collect_dataset.py /dev/ttyUSB0
```

**Low accuracy (<50%)**:
- Collect more data (>1000 samples)
- Check class balance (similar samples per activity)
- Verify WiFi traffic during collection
- Try more distinct activities

**Overfitting (train >> test accuracy)**:
- Reduce `max_depth` (try 5 instead of 10)
- Increase `min_samples_split` (try 10)
- Collect more diverse data

### Inference Issues

**Predictions stuck on one class**:
- Check training output for class imbalance
- Generate WiFi traffic: `ping -i 0.1 192.168.1.255`
- Increase smoothing: `--window 20`

**Low confidence (<50%)**:
- Normal for ambiguous activities
- Collect more training data
- Check if activity is in training set

**Jittery predictions**:
- Increase smoothing window: `--window 20`
- Trade-off: Adds latency

---

## Next Steps

### Phase 4B: Advanced ML (Future Work)

**1. Feature Engineering**:
- FFT of amplitude (frequency domain)
- PCA for dimensionality reduction
- Subcarrier correlation matrix
- Wavelet transforms

**2. Deep Learning Models**:
- **CNN**: Spatial patterns in CSI
- **LSTM/GRU**: Temporal sequences
- **Transformer**: Attention mechanisms
- **Hybrid**: CNN + LSTM for spatio-temporal

**3. Multi-Activity Detection**:
- Multiple people in room
- Simultaneous activities
- Activity tracking over time

**4. Transfer Learning**:
- Pre-train on large CSI dataset
- Fine-tune for specific environment

### Phase 5: ESP32 Deployment (Future)

**1. Model Conversion**:
- TensorFlow → TensorFlow Lite
- Quantization (FP32 → INT8)
- Model size <500KB

**2. ESP32 Integration**:
- TFLite Micro library
- On-device inference
- Flash storage for model

**3. Performance Optimization**:
- Reduce latency (<100ms)
- Minimize memory usage
- Power consumption optimization

---

## Files Created

```
ml/
├── README.md                      # ML pipeline documentation
├── datasets/                      # Dataset storage (populated by user)
├── models/                        # Trained models (populated by user)
└── scripts/
    ├── collect_dataset.py         # Dataset collection tool
    ├── train_model.py             # Model training pipeline
    └── realtime_classify.py       # Real-time inference

docs/
└── Phase4-Machine-Learning.md     # This file
```

---

## Quick Reference

### Collect Data
```bash
ping -i 0.1 192.168.1.255 &
python3 ml/scripts/collect_dataset.py /dev/ttyUSB0
```

### Train Model
```bash
python3 ml/scripts/train_model.py \
    --dataset ml/datasets \
    --output ml/models/my_model.pkl
```

### Real-time Classification
```bash
ping -i 0.1 192.168.1.255 &
python3 ml/scripts/realtime_classify.py /dev/ttyUSB0 \
    --model ml/models/my_model.pkl
```

---

## Phase 4A Success Criteria

| Criterion | Status |
|-----------|--------|
| ✅ Dataset collection tool | COMPLETE |
| ✅ Structured dataset format | COMPLETE |
| ✅ Model training pipeline | COMPLETE |
| ✅ Random Forest baseline | COMPLETE |
| ✅ Real-time inference | COMPLETE |
| ✅ Performance metrics | COMPLETE |
| ✅ Documentation | COMPLETE |

**Overall Phase 4A Status**: ✅ **COMPLETE**

---

**Document Version**: 1.0
**Last Updated**: December 31, 2025
**Status**: Phase 4A Complete - Baseline ML Ready
**Next Phase**: Phase 4B (Advanced ML) or Phase 5 (ESP32 Deployment)
