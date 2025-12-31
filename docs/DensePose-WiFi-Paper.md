# DensePose From WiFi - Paper Summary

**Paper**: [arXiv:2301.00250](https://arxiv.org/abs/2301.00250)
**PDF**: https://arxiv.org/pdf/2301.00250
**Authors**: Jiaqi Geng, Dong Huang, Fernando De la Torre
**Published**: December 31, 2022

## Abstract

This paper presents a method to estimate dense human pose (DensePose) using only WiFi signals, without any cameras. The approach uses WiFi Channel State Information (CSI) to predict UV coordinates that map to 24 body surface regions.

## Key Contributions

1. **WiFi-based DensePose**: First work to achieve dense pose estimation from WiFi signals
2. **Privacy-preserving**: No cameras needed, works through walls
3. **Low-cost**: Uses commodity WiFi hardware
4. **Multi-person support**: Can track multiple people simultaneously

## Technical Approach

### Input: WiFi CSI Data
- **Channel State Information (CSI)**: Complex-valued data representing how WiFi signals propagate
- **Amplitude**: Signal strength variations caused by human body
- **Phase**: Signal timing variations indicating body position/movement
- **Subcarriers**: Multiple frequency channels within WiFi band (~52 for 20MHz)

### Network Architecture

```
WiFi CSI Input → Encoder → Feature Extraction → Decoder → DensePose UV Output
     ↓                                              ↓
[T×3×3×(A+P)]                              [H×W×(24+1)]

T = Time steps
3×3 = Antenna array (3 TX × 3 RX)
A = Amplitude features
P = Phase features
H×W = Output spatial resolution
24 = Body surface regions (IUV format)
```

### Key Components

1. **Temporal Processing**: CNN/Transformer to process time-series CSI data
2. **Spatial Encoding**: Maps antenna array data to spatial features
3. **DensePose Decoder**: Generates UV coordinates for body surface mapping

### Training Data

- Paired WiFi CSI + camera ground truth
- DensePose annotations from camera images
- Cross-modal supervision (train with camera, deploy without)

## Hardware Setup (Original Paper)

- **TX**: 1 router with 3 antennas
- **RX**: 3 receivers with 1 antenna each (or 1 receiver with 3 antennas)
- **Sampling Rate**: ~100 Hz CSI collection
- **Distance**: 1-5 meters typical

## Relevance to ESP32 Implementation

### Challenges

1. **Limited CSI Access**: ESP32 provides raw CSI but with fewer subcarriers than research-grade hardware
2. **Memory Constraints**: 2MB PSRAM limits model size significantly
3. **Compute Power**: 240MHz dual-core vs. GPU inference
4. **Antenna Configuration**: Single antenna on ESP32-S3-Zero vs. 3×3 array

### Adaptation Strategy

1. **Simplified Model**: Use knowledge distillation to create tiny model
2. **Reduced Resolution**: Lower spatial output resolution
3. **Skeleton Instead of Dense**: Consider sparse keypoints as intermediate goal
4. **Multiple ESP32s**: Use multiple boards to simulate antenna array
5. **Edge Inference**: Quantized INT8 models via ESP-NN or TFLite Micro

## Related Work

- **WiFi-based Activity Recognition**: HumanFi, WiGest
- **WiFi-based Pose Estimation**: WiPose, Person-in-WiFi
- **Dense Pose from Images**: DensePose (Facebook/Meta)

## Implementation Milestones

### Phase 1: CSI Collection
- Set up ESP32 WiFi CSI extraction
- Collect and visualize CSI data
- Understand signal characteristics

### Phase 2: Basic Detection
- Human presence detection from CSI
- Activity classification (moving/stationary)

### Phase 3: Pose Estimation
- Train simplified model on PC
- Quantize and deploy to ESP32
- Evaluate accuracy vs. compute tradeoff

## References

1. Geng, J., Huang, D., & De la Torre, F. (2023). DensePose From WiFi. arXiv:2301.00250
2. [ESP32 WiFi CSI Documentation](https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-guides/wifi.html#wi-fi-channel-state-information)
3. [DensePose (Meta AI)](https://github.com/facebookresearch/detectron2/tree/main/projects/DensePose)
