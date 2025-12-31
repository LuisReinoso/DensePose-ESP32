# DensePose-ESP32 Project

## Overview

This project implements WiFi-based human pose estimation on ESP32-S3 hardware, inspired by the paper "DensePose From WiFi" (arXiv:2301.00250). The goal is to extract human pose information using WiFi Channel State Information (CSI) on low-cost embedded hardware.

## Hardware

- **Board**: Waveshare ESP32-S3-Zero (3-pack from Amazon)
- **Chip**: ESP32-S3FH4R2
- **CPU**: Dual-core Xtensa LX7 @ 240MHz
- **Memory**: 512KB SRAM + 2MB PSRAM + 4MB Flash
- **Connectivity**: WiFi 802.11 b/g/n + Bluetooth 5.0 LE

See `docs/ESP32-S3-Hardware-Reference.md` for detailed specs.

## Project Goals

1. Extract WiFi CSI data on ESP32-S3
2. Process CSI to detect human presence/activity
3. Run simplified pose estimation model on-device
4. Demonstrate privacy-preserving sensing without cameras

## Development Environment

### ESP-IDF (Primary)
```bash
# Set up ESP-IDF v5.x
git clone --recursive https://github.com/espressif/esp-idf.git
cd esp-idf
./install.sh esp32s3
source export.sh

# Build and flash
idf.py set-target esp32s3
idf.py build
idf.py -p /dev/ttyUSB0 flash monitor
```

### Project Structure
```
DensePose-ESP32/
├── CLAUDE.md           # This file - project context
├── AGENTS.md           # Agent guidelines
├── docs/               # Documentation
│   ├── ESP32-S3-Hardware-Reference.md
│   └── DensePose-WiFi-Paper.md
├── firmware/           # ESP-IDF project
│   ├── main/
│   │   ├── CMakeLists.txt
│   │   ├── main.c
│   │   ├── wifi_csi.c
│   │   └── pose_inference.c
│   ├── components/     # Custom components
│   └── CMakeLists.txt
├── models/             # ML models
│   ├── training/       # Python training scripts
│   └── tflite/         # Quantized models for ESP32
└── tools/              # Helper scripts
```

## Key Technical Concepts

### WiFi CSI (Channel State Information)
CSI describes how WiFi signals propagate between transmitter and receiver. Human bodies absorb and reflect signals, creating patterns in CSI data that can be analyzed for pose estimation.

```c
// CSI callback function signature
void wifi_csi_rx_cb(void *ctx, wifi_csi_info_t *info);

// CSI data format
typedef struct {
    int8_t *buf;          // Raw CSI buffer (I/Q interleaved)
    uint16_t len;         // Buffer length
    wifi_pkt_rx_ctrl_t rx_ctrl;  // Packet metadata
} wifi_csi_info_t;
```

### Memory Constraints
- **Internal SRAM**: 512KB - use for critical paths, model weights
- **PSRAM**: 2MB - use for large buffers, intermediate tensors
- **Flash**: 4MB - firmware + model storage

For ML inference, consider:
- TensorFlow Lite Micro (ESP-NN optimized)
- INT8 quantization mandatory
- Model size target: <500KB

### ESP-IDF Key APIs

```c
// WiFi initialization
esp_wifi_init(&wifi_config);
esp_wifi_set_mode(WIFI_MODE_STA);
esp_wifi_start();

// CSI configuration
wifi_csi_config_t csi_config = { .lltf_en = true, ... };
esp_wifi_set_csi_config(&csi_config);
esp_wifi_set_csi_rx_cb(wifi_csi_rx_cb, NULL);
esp_wifi_set_csi(true);

// PSRAM allocation
uint8_t *buffer = heap_caps_malloc(size, MALLOC_CAP_SPIRAM);
```

## Firmware Development Notes

### Building
```bash
cd firmware
idf.py set-target esp32s3
idf.py menuconfig  # Configure WiFi, PSRAM, etc.
idf.py build flash monitor
```

### Important menuconfig Settings
- Component config → ESP32S3-Specific → SPIRAM: Enable
- Component config → WiFi → WiFi CSI: Enable
- Compiler options → Optimization: -O2 or -Os

### Debugging
- Use `ESP_LOGI()`, `ESP_LOGD()`, `ESP_LOGE()` for logging
- Monitor output: `idf.py monitor` (Ctrl+] to exit)
- GDB debugging available via JTAG

## References

- Paper: https://arxiv.org/abs/2301.00250
- ESP-IDF: https://docs.espressif.com/projects/esp-idf/en/latest/esp32s3/
- ESP32 CSI: https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-guides/wifi.html#wi-fi-channel-state-information
- TFLite Micro: https://github.com/tensorflow/tflite-micro
- Waveshare Wiki: https://www.waveshare.com/wiki/ESP32-S3-Zero
