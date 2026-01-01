# DensePose-ESP32 Machine Learning

Machine learning pipeline for WiFi CSI-based activity classification.

---

## Overview

This directory contains the complete ML workflow:
1. **Dataset Collection**: Collect labeled CSI data for different activities
2. **Model Training**: Train classification models (Random Forest baseline)
3. **Evaluation**: Assess model performance
4. **Inference**: Real-time activity classification

---

## Quick Start

### 1. Install Dependencies

```bash
pip install -r ../tools/requirements.txt
```

**Requirements**:
- Python 3.7+
- scikit-learn >= 1.0.0
- numpy >= 1.20.0
- matplotlib >= 3.5.0 (for visualization)

---

### 2. Collect Dataset

```bash
# Start WiFi traffic
ping -i 0.1 192.168.1.255 &

# Run interactive collection
python3 scripts/collect_dataset.py /dev/ttyUSB0
```

Follow the prompts to collect data for different activities.

**Recommended**: 5-10 trials per activity, 30 seconds each = 150-300 seconds per activity

---

###  3. Train Model

```bash
python3 scripts/train_model.py --dataset datasets --output models/my_model.pkl
```

This will:
- Load all collected data
- Split into train/test sets
- Train Random Forest classifier
- Print performance metrics
- Save model to `models/my_model.pkl`

---

### 4. Real-time Classification

```bash
# Generate WiFi traffic
ping -i 0.1 192.168.1.255 &

# Run classifier
python3 scripts/realtime_classify.py /dev/ttyUSB0 --model models/my_model.pkl
```

Watch real-time activity predictions!

---

## Directory Structure

```
ml/
├── README.md                    # This file
├── datasets/                    # Collected CSI datasets
│   ├── metadata.json           # Dataset metadata
│   ├── empty/                  # Empty room baseline
│   │   ├── empty_trial01_.../
│   │   │   ├── features.jsonl
│   │   │   ├── raw_csi.jsonl
│   │   │   └── sample_info.json
│   │   └── ...
│   ├── standing/               # Standing activity
│   ├── sitting/                # Sitting activity
│   ├── walking/                # Walking activity
│   └── waving/                 # Waving activity
├── models/                      # Trained models
│   ├── rf_baseline.pkl         # Random Forest model
│   └── rf_baseline.json        # Model metrics
├── notebooks/                   # Jupyter notebooks (analysis)
└── scripts/                     # ML scripts
    ├── collect_dataset.py      # Dataset collection
    ├── train_model.py          # Model training
    └── realtime_classify.py    # Real-time inference
```

---

## Scripts Documentation

### `collect_dataset.py` - Dataset Collection

**Interactive Mode** (recommended):
```bash
python3 scripts/collect_dataset.py /dev/ttyUSB0
```

Follow the menu to select activities and collect data.

**Non-interactive Mode**:
```bash
# Collect specific activity
python3 scripts/collect_dataset.py /dev/ttyUSB0 \
    --activity standing \
    --duration 30
```

**Predefined Activities**:
- `empty`: No person in room (baseline)
- `standing`: Person standing still
- `sitting`: Person sitting still
- `walking`: Person walking around
- `waving`: Person waving arms
- `jumping`: Person jumping
- `lying`: Person lying down
- `custom`: Custom activity (specify description)

**Parameters**:
- `--activity`: Activity to collect
- `--duration`: Collection duration in seconds (default: 30)
- `--output-dir`: Dataset directory (default: ml/datasets)
- `--description`: Custom activity description

**Output**:
- `features.jsonl`: Processed CSI features
- `raw_csi.jsonl`: Raw CSI data from ESP32
- `sample_info.json`: Sample metadata
- `metadata.json`: Dataset-wide metadata (auto-updated)

---

### `train_model.py` - Model Training

**Basic Usage**:
```bash
python3 scripts/train_model.py --dataset datasets
```

**With Options**:
```bash
python3 scripts/train_model.py \
    --dataset datasets \
    --test-split 0.3 \
    --output models/custom_model.pkl \
    --random-seed 42
```

**Parameters**:
- `--dataset`: Path to dataset directory
- `--test-split`: Test set fraction (default: 0.2)
- `--output`: Output model path (default: ml/models/rf_baseline.pkl)
- `--random-seed`: Random seed for reproducibility

**Output**:
- `model.pkl`: Trained model + scaler + metadata
- `model.json`: Performance metrics (accuracy, confusion matrix, etc.)

**Training Process**:
1. Load all features from dataset
2. Split train/test (stratified)
3. Normalize features (StandardScaler)
4. Train Random Forest (100 trees)
5. 5-fold cross-validation
6. Evaluate on test set
7. Print metrics and feature importance

**Model Components**:
```python
model_data = {
    'model': RandomForestClassifier(...),
    'scaler': StandardScaler(...),
    'feature_names': [...],
    'metrics': {...},
    'classes': [...],
}
```

---

### `realtime_classify.py` - Real-time Inference

**Usage**:
```bash
python3 scripts/realtime_classify.py /dev/ttyUSB0 \
    --model models/rf_baseline.pkl
```

**Parameters**:
- `--model`: Path to trained model (.pkl)
- `--window`: Smoothing window size (default: 10)
- `--baud`: Serial baud rate (default: 115200)
- `-v, --verbose`: Show raw predictions

**Features**:
- Real-time activity classification
- Prediction smoothing (majority vote)
- Confidence bars
- Session statistics

**Output Example**:
```
[20:15:30.123] Activity: standing     | Confidence: ████████████████░░░░ 85.2% | RSSI: -45dBm
[20:15:30.234] Activity: walking      | Confidence: ██████████████████░░ 92.1% | RSSI: -46dBm
```

---

## Dataset Collection Workflow

### Recommended Collection Protocol

**1. Prepare Environment**:
- Clear room of obstacles
- Position ESP32 2-3 meters from router
- Minimize other WiFi devices
- Consistent lighting (not critical, but good practice)

**2. Generate WiFi Traffic**:
```bash
# Continuous ping to broadcast address
ping -i 0.1 192.168.1.255 &
```

**3. Collect Baseline** (empty room):
```bash
python3 scripts/collect_dataset.py /dev/ttyUSB0 \
    --activity empty \
    --duration 30
```

Repeat 5 times (walk out of room for each trial)

**4. Collect Activity Data**:

For each activity (standing, sitting, walking, waving):
- Position subject in consistent location
- Collect 5-10 trials
- 30 seconds per trial
- Rest between trials

**Example**:
```bash
# Standing - Trial 1
python3 scripts/collect_dataset.py /dev/ttyUSB0 --activity standing --duration 30
# (Subject stands still for 30 seconds)

# Walking - Trial 1
python3 scripts/collect_dataset.py /dev/ttyUSB0 --activity walking --duration 30
# (Subject walks around room for 30 seconds)
```

**5. Verify Data**:
```bash
# Check dataset statistics
python3 scripts/train_model.py --dataset datasets
# (Will show sample counts before training)
```

### Minimum Recommended Dataset

| Activity | Trials | Duration | Total Samples* |
|----------|--------|----------|---------------|
| empty | 5 | 30s | ~150 packets |
| standing | 5 | 30s | ~150 packets |
| sitting | 5 | 30s | ~150 packets |
| walking | 5 | 30s | ~150 packets |
| waving | 5 | 30s | ~150 packets |
| **Total** | **25** | **12.5 min** | **~750 packets** |

*Assuming ~1 packet/sec (depends on WiFi traffic)

For better accuracy, collect 10 trials per activity = **1500+ packets**

---

## Model Performance

### Expected Baseline Performance

With recommended dataset (~1500 samples):

| Metric | Expected Value |
|--------|----------------|
| Test Accuracy | 70-85% |
| CV Accuracy | 65-80% |
| Confusion | Higher for similar activities |

**Activity Confusions**:
- `standing` vs `sitting`: High confusion (both static)
- `walking` vs `waving`: Moderate confusion (both dynamic)
- `empty` vs others: Low confusion (clear baseline)

### Feature Importance

Expected ranking (from Random Forest):
1. `temporal_variance` - Movement indicator
2. `amp_std` - Signal variability
3. `amp_range` - Dynamic range
4. `amp_mean` - Signal strength
5. `rssi_mean` - Connection quality

---

## Advanced Usage

### Export Dataset for External Tools

```python
import json
import pandas as pd

# Load features
features = []
with open('datasets/standing/standing_trial01_.../features.jsonl') as f:
    for line in f:
        features.append(json.loads(line))

# Convert to DataFrame
df = pd.DataFrame(features)

# Export to CSV
df.to_csv('standing_trial01.csv', index=False)
```

### Custom Feature Engineering

```python
# Add FFT features
from scipy.fft import fft

def add_fft_features(raw_csi_file):
    with open(raw_csi_file) as f:
        amplitudes = []
        for line in f:
            data = json.loads(line)
            amplitudes.append(data['amp'])

    # FFT of amplitude time series
    amp_array = np.array(amplitudes)
    fft_result = fft(amp_array, axis=0)
    fft_power = np.abs(fft_result) ** 2

    # Use power spectrum as features
    return np.mean(fft_power, axis=1)  # Average across subcarriers
```

### Model Comparison

```python
from sklearn.svm import SVC
from sklearn.neural_network import MLPClassifier

# Train multiple models
models = {
    'RandomForest': RandomForestClassifier(),
    'SVM': SVC(kernel='rbf', probability=True),
    'MLP': MLPClassifier(hidden_layers=(64, 32)),
}

for name, model in models.items():
    model.fit(X_train, y_train)
    score = model.score(X_test, y_test)
    print(f"{name}: {score:.3f}")
```

---

## Troubleshooting

**"No data loaded!" when training**:
- Verify dataset directory exists: `ls datasets/`
- Check metadata.json exists
- Collect data first with `collect_dataset.py`

**Low accuracy (<50%)**:
- Collect more data (>1000 samples recommended)
- Check class balance (similar samples per activity)
- Verify WiFi traffic is active during collection
- Try different activities (more distinct movements)

**"Model file not found" during inference**:
- Train model first: `python3 scripts/train_model.py`
- Check model path: `ls models/`

**High confusion between activities**:
- Increase activity distinctiveness (e.g., fast walking vs slow standing)
- Collect more samples per activity
- Add more features (FFT, PCA)
- Try longer collection duration (60s instead of 30s)

**Predictions stuck on one class**:
- Check model training output (class distribution)
- Verify real-time WiFi traffic: `ping -i 0.1 192.168.1.255`
- Increase smoothing window: `--window 20`

---

## Next Steps

### Phase 4B: Advanced ML (Future)

- **Deep Learning**: CNN/LSTM for temporal patterns
- **Feature Engineering**: FFT, PCA, wavelet transforms
- **Multi-Person Detection**: Track multiple subjects
- **Pose Estimation**: Beyond simple activities to actual poses

### Phase 5: ESP32 Deployment (Future)

- **TensorFlow Lite**: Convert model to TFLite
- **Quantization**: INT8 for ESP32 memory constraints
- **On-Device Inference**: Run model on ESP32
- **TFLite Micro**: ESP32 deployment framework

---

## References

- **Baseline Model**: Random Forest (scikit-learn)
- **Dataset Format**: JSONL (JSON Lines)
- **Feature Extraction**: Phase 3 CSI Analyzer
- **Evaluation**: Classification metrics, confusion matrix

---

**ML Pipeline Version**: 1.0
**Last Updated**: December 31, 2025
**Status**: Phase 4A Complete - Baseline ML Ready
