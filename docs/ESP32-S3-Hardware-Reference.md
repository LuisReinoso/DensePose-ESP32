# ESP32-S3FH4R2 Hardware Reference

## Datasheet

The official ESP32-S3 Series Datasheet is available from Espressif:
- **Download**: https://www.espressif.com/sites/default/files/documentation/esp32-s3_datasheet_en.pdf
- **Documentation Portal**: https://docs.espressif.com/projects/esp-idf/en/latest/esp32s3/

## ESP32-S3FH4R2 Chip Specifications

| Specification | Value |
|---------------|-------|
| **CPU** | Xtensa 32-bit LX7 dual-core |
| **Clock Speed** | Up to 240 MHz |
| **Flash** | 4 MB (in-package) |
| **PSRAM** | 2 MB (in-package) |
| **SRAM** | 512 KB |
| **ROM** | 384 KB |
| **RTC SRAM** | 16 KB |
| **Package** | QFN 56-pin, 7×7 mm |

## Waveshare ESP32-S3-Zero Development Board

**Product**: [Waveshare ESP32-S3-Zero](https://www.waveshare.com/esp32-s3-zero.htm)
**Wiki**: https://www.waveshare.com/wiki/ESP32-S3-Zero

### Key Features

- 24 × GPIO pins with flexible configuration
- USB Type-C (native USB, no UART-to-USB chip)
- WS2812 RGB LED on GPIO21
- 2.4G ceramic antenna
- Castellated holes for integration
- ME6217C33M5G LDO (800mA max output)

### Power Requirements

- **Input Voltage**: 3.7V - 6V
- **Recommended**: 5V @ 500mA minimum
- **Operating Voltage**: 3.3V (regulated)

### Pin Assignments

| Pin | Function | Notes |
|-----|----------|-------|
| GPIO0 | BOOT | Boot button |
| GPIO21 | WS2812 | RGB LED |
| GPIO43 | TX | UART0 default |
| GPIO44 | RX | UART0 default |
| GPIO33-37 | Internal | Octal PSRAM (do not use) |

### Peripheral Interfaces

- 4 × SPI controllers
- 2 × I2C interfaces
- 3 × UART interfaces
- 2 × I2S interfaces (audio)
- 2 × ADC (12-bit SAR ADC)
- 2 × MCPWM (motor control)
- Touch-capable pins
- USB OTG

## Connectivity

### WiFi
- 802.11 b/g/n (2.4 GHz)
- Station, SoftAP, and Station+SoftAP modes
- WPA3 support

### Bluetooth
- Bluetooth 5.0 LE
- Long Range (Coded PHY)
- 2 Mbps PHY

## Development Environment

### ESP-IDF (Recommended for this project)
```bash
# Install ESP-IDF
git clone --recursive https://github.com/espressif/esp-idf.git
cd esp-idf
./install.sh esp32s3
source export.sh
```

### Arduino IDE
- Board: "ESP32S3 Dev Module" or "Waveshare ESP32-S3-Zero"
- USB Mode: "USB-OTG (TinyUSB)" or "Hardware CDC and JTAG"

## WiFi CSI (Channel State Information)

The ESP32-S3 supports WiFi CSI extraction, which is critical for the DensePose from WiFi implementation:

- **CSI Callback**: Available via `esp_wifi_set_csi_config()` and `esp_wifi_set_csi_rx_cb()`
- **Subcarriers**: Up to 52 subcarriers for 20 MHz bandwidth
- **Data Format**: Complex values (amplitude + phase) per subcarrier
- **Reference**: https://docs.espressif.com/projects/esp-idf/en/latest/esp32s3/api-reference/network/esp_wifi.html

### CSI Configuration Example
```c
wifi_csi_config_t csi_config = {
    .lltf_en = true,           // Enable L-LTF
    .htltf_en = true,          // Enable HT-LTF
    .stbc_htltf2_en = true,    // Enable STBC HT-LTF2
    .ltf_merge_en = true,      // Merge LTF
    .channel_filter_en = true, // Enable channel filter
    .manu_scale = false,       // Automatic scaling
    .shift = false,            // No shift
};
```

## Memory Considerations for ML Inference

| Memory Type | Size | Use Case |
|-------------|------|----------|
| Internal SRAM | 512 KB | Fast buffers, model weights |
| PSRAM | 2 MB | Large tensors, CSI buffers |
| Flash | 4 MB | Model storage, firmware |

**Note**: PSRAM access is slower than internal SRAM. Critical inference paths should use internal SRAM when possible.

## References

1. [ESP32-S3 Technical Reference Manual](https://www.espressif.com/sites/default/files/documentation/esp32-s3_technical_reference_manual_en.pdf)
2. [ESP-IDF Programming Guide](https://docs.espressif.com/projects/esp-idf/en/latest/esp32s3/)
3. [ESP32 WiFi CSI Guide](https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-guides/wifi.html#wi-fi-channel-state-information)
4. [Waveshare ESP32-S3-Zero Wiki](https://www.waveshare.com/wiki/ESP32-S3-Zero)
