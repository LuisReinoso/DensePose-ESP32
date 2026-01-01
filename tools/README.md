# DensePose-ESP32 Tools

Python tools for CSI data collection, processing, and visualization.

---

## Installation

```bash
pip install -r requirements.txt
```

**Requirements**:
- Python 3.7+
- pyserial >= 3.5
- numpy >= 1.20.0
- matplotlib >= 3.5.0

---

## Tools Overview

### 1. `read_csi.py` - Basic CSI Data Reader

Simple tool to read and display CSI data from ESP32.

**Usage**:
```bash
# Display CSI packets in real-time
python3 read_csi.py /dev/ttyUSB0

# Save to file
python3 read_csi.py /dev/ttyUSB0 --output csi_data.json

# Verbose mode (show full arrays)
python3 read_csi.py /dev/ttyUSB0 -v
```

**Output**:
```
[20:15:30.123] Packet #1 | ts=123456ms | RSSI=-45dBm | subcarriers=64 | amp: mean=12.5 max=104.2
[20:15:30.234] Packet #2 | ts=123567ms | RSSI=-46dBm | subcarriers=64 | amp: mean=11.8 max=102.1
```

**When to use**: Quick CSI data verification, simple data collection

---

### 2. `csi_analyzer.py` - Signal Processing & Feature Extraction

Advanced tool with real-time signal processing and movement detection.

**Usage**:
```bash
# Basic analysis
python3 csi_analyzer.py /dev/ttyUSB0

# Movement detection mode
python3 csi_analyzer.py /dev/ttyUSB0 --detect-movement

# Save processed features
python3 csi_analyzer.py /dev/ttyUSB0 --output features.json

# Save both features and raw data
python3 csi_analyzer.py /dev/ttyUSB0 \
    --output features.json \
    --raw-output raw_csi.json

# Custom parameters
python3 csi_analyzer.py /dev/ttyUSB0 \
    --window 20 \
    --threshold 10.0 \
    --detect-movement -v
```

**Features**:
- Exponential moving average (EMA) filtering
- Temporal variance calculation
- Real-time movement detection
- Statistical feature extraction
- JSONL export for ML training

**Output** (movement detection mode):
```
[20:15:30.123] Packet #1 | RSSI=-45dBm | Amp: μ=12.5 σ=8.3 | Var=3.20 | ⚪ STATIC
[20:15:30.234] Packet #2 | RSSI=-46dBm | Amp: μ=15.2 σ=9.1 | Var=7.50 | 🟢 MOVEMENT
```

**Parameters**:
- `--window N`: Sliding window size (default: 10)
- `--threshold T`: Movement detection threshold (default: 5.0)
- `--baud B`: Serial baud rate (default: 115200)
- `-v, --verbose`: Show detailed statistics

**When to use**: Data collection for ML, movement detection experiments, signal analysis

---

### 3. `csi_plotter.py` - Data Visualization

Visualize CSI features and compare datasets.

**Usage**:
```bash
# Plot amplitude and variance
python3 csi_plotter.py features.json

# Plot specific features
python3 csi_plotter.py features.json --plot amplitude rssi variance std

# Compare baseline vs movement
python3 csi_plotter.py baseline.json movement.json --compare
```

**Plots**:
- **Amplitude**: Raw and filtered over time
- **RSSI**: Signal strength trends
- **Variance**: Temporal variance with movement markers
- **Statistics**: Std dev, range, distributions
- **Comparison**: Histograms and box plots

**When to use**: Data analysis, visualizing patterns, validating movement detection

---

## Typical Workflows

### Workflow 1: Quick CSI Test

```bash
# 1. Generate WiFi traffic
ping -i 0.1 192.168.1.255 &

# 2. Read CSI data
python3 read_csi.py /dev/ttyUSB0
```

**Goal**: Verify ESP32 is sending CSI data

---

### Workflow 2: Collect Baseline and Movement Data

```bash
# 1. Start WiFi traffic
ping -i 0.1 192.168.1.255 &

# 2. Collect baseline (no movement, 30 seconds)
timeout 30 python3 csi_analyzer.py /dev/ttyUSB0 \
    --output data/baseline.json \
    --detect-movement

# 3. Collect movement data (wave arms, walk around)
timeout 30 python3 csi_analyzer.py /dev/ttyUSB0 \
    --output data/movement.json \
    --detect-movement

# 4. Compare
python3 csi_plotter.py \
    data/baseline.json \
    data/movement.json \
    --compare
```

**Goal**: Characterize CSI response to human movement

---

### Workflow 3: ML Dataset Collection

```bash
# 1. Create data directory
mkdir -p data/{standing,sitting,walking,waving}

# 2. Collect labeled data for each pose
# Standing pose
python3 csi_analyzer.py /dev/ttyUSB0 \
    --output data/standing/trial1.json \
    --raw-output data/standing/trial1_raw.json

# Repeat for sitting, walking, waving...
# Multiple trials per pose (5-10 trials recommended)

# 3. Combine and prepare for ML
# (Future: create dataset preparation script)
```

**Goal**: Build labeled dataset for pose classification

---

## Data Formats

### Raw CSI Data (from ESP32)

**Format**: JSON per line
```json
{
  "ts": 123456,
  "rssi": -45,
  "num": 64,
  "amp": [12.5, 15.2, ...],
  "phase": [1.23, -0.45, ...]
}
```

**Fields**:
- `ts`: Timestamp in milliseconds
- `rssi`: Received Signal Strength Indicator (dBm)
- `num`: Number of subcarriers (52-64)
- `amp`: Amplitude array (one per subcarrier)
- `phase`: Phase array (one per subcarrier, in radians)

---

### Processed Features (from csi_analyzer.py)

**Format**: JSONL (JSON Lines)
```json
{
  "timestamp": 123456,
  "packet_num": 1,
  "rssi": -45,
  "rssi_mean": -45.5,
  "amp_mean": 12.5,
  "amp_std": 8.3,
  "amp_max": 104.2,
  "amp_min": 0.0,
  "amp_range": 104.2,
  "temporal_variance": 3.2,
  "movement_detected": false,
  "amp_mean_filtered": 11.8
}
```

**Features**:
- `timestamp`: ESP32 timestamp (ms)
- `packet_num`: Sequential packet number
- `rssi`: Raw RSSI
- `rssi_mean`: Windowed RSSI average
- `amp_mean`: Mean amplitude across subcarriers
- `amp_std`: Amplitude standard deviation
- `amp_max/min`: Max/min amplitude
- `amp_range`: Dynamic range
- `temporal_variance`: Variance over time (movement indicator)
- `movement_detected`: Boolean flag (variance > threshold)
- `amp_mean_filtered`: EMA-smoothed amplitude

---

## Troubleshooting

**"Error opening serial port"**
- Check device is connected: `ls /dev/ttyUSB*`
- Fix permissions: `sudo chmod 666 /dev/ttyUSB0`
- Try different port: `/dev/ttyACM0`

**"No CSI packets received"**
- Verify ESP32 is running (green LED)
- Generate WiFi traffic: `ping -i 0.1 192.168.1.255`
- Check ESP32 serial output: `idf.py monitor`

**"matplotlib not found"**
- Install: `pip install matplotlib`
- Or reinstall all: `pip install -r requirements.txt`

**"Movement not detected"**
- Lower threshold: `--threshold 2.0`
- Increase window: `--window 20`
- Verify WiFi traffic is active

**"Too many false positives"**
- Increase threshold: `--threshold 10.0`
- Reduce window: `--window 5`
- Collect in stable environment

---

## Advanced Usage

### Custom Analysis Script

```python
#!/usr/bin/env python3
import json
import numpy as np

# Load features
features = []
with open('features.json', 'r') as f:
    for line in f:
        features.append(json.loads(line))

# Extract amplitude time series
amps = np.array([f['amp_mean'] for f in features])

# Calculate statistics
print(f"Mean amplitude: {np.mean(amps):.2f}")
print(f"Std dev: {np.std(amps):.2f}")
print(f"Max: {np.max(amps):.2f}")

# Detect significant changes
diffs = np.diff(amps)
threshold = 3 * np.std(diffs)
changes = np.where(np.abs(diffs) > threshold)[0]
print(f"Significant changes at: {changes}")
```

### Real-time Streaming to Database

```python
# Example: Stream to InfluxDB
from influxdb_client import InfluxDBClient, Point
import json, serial

client = InfluxDBClient(url="http://localhost:8086", token="token")
write_api = client.write_api()

ser = serial.Serial('/dev/ttyUSB0', 115200)
while True:
    line = ser.readline().decode('utf-8').strip()
    if line.startswith('{'):
        data = json.loads(line)
        point = Point("csi") \
            .tag("device", "esp32_1") \
            .field("rssi", data['rssi']) \
            .field("amp_mean", np.mean(data['amp']))
        write_api.write(bucket="densepose", record=point)
```

---

## See Also

- [`docs/Phase3-Signal-Processing.md`](../docs/Phase3-Signal-Processing.md) - Detailed Phase 3 documentation
- [`QUICK-START.md`](../QUICK-START.md) - ESP32 setup guide
- [`docs/ESP32-Setup-Guide.md`](../docs/ESP32-Setup-Guide.md) - Complete hardware setup

---

**Tools Version**: 1.0
**Last Updated**: December 31, 2025
