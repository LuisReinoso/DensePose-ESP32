# DensePose-ESP32 Firmware

## Quick Start

```bash
# 1. Install ESP-IDF (one time)
git clone --recursive https://github.com/espressif/esp-idf.git ~/esp/esp-idf
cd ~/esp/esp-idf && ./install.sh esp32s3 && source export.sh

# 2. Configure WiFi (run from firmware/ directory)
idf.py menuconfig  # Set WiFi SSID and password under "DensePose WiFi Configuration"

# 3. Build and flash
./build.sh
```

## Serial Output

CSI data streams as JSON:
```json
{"ts":12345,"rssi":-45,"num":64,"amp":[...],"phase":[...]}
```
