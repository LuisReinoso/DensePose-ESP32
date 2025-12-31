# AGENTS.md - Development Guidelines

## Project Context

This is an ESP32-S3 firmware project implementing WiFi-based pose estimation. The developer is returning to firmware development after 2 years, so explanations should be clear and educational.

## ESP-IDF Firmware Development Guide

### Project Structure

ESP-IDF uses CMake-based build system:

```
firmware/
├── CMakeLists.txt          # Top-level CMake (defines project)
├── main/
│   ├── CMakeLists.txt      # Component CMake (lists source files)
│   ├── main.c              # Entry point (app_main function)
│   ├── Kconfig.projbuild   # Optional: project-specific menuconfig
│   └── *.c/*.h             # Your source files
├── components/             # Custom reusable components
│   └── my_component/
│       ├── CMakeLists.txt
│       ├── include/
│       └── src/
└── sdkconfig               # Generated config (don't edit directly)
```

### Key Concepts

#### 1. FreeRTOS Tasks
ESP-IDF uses FreeRTOS. Code runs in tasks, not a main loop:

```c
void my_task(void *pvParameters) {
    while (1) {
        // Do work
        vTaskDelay(pdMS_TO_TICKS(100));  // Yield for 100ms
    }
}

// Create task (usually in app_main)
xTaskCreate(my_task, "my_task", 4096, NULL, 5, NULL);
//          function, name,     stack, param, priority, handle
```

#### 2. Event-Driven WiFi
WiFi uses event handlers, not polling:

```c
static void wifi_event_handler(void* arg, esp_event_base_t event_base,
                               int32_t event_id, void* event_data) {
    if (event_id == WIFI_EVENT_STA_START) {
        esp_wifi_connect();
    } else if (event_id == WIFI_EVENT_STA_DISCONNECTED) {
        esp_wifi_connect();  // Reconnect
    }
}

// Register handler
esp_event_handler_register(WIFI_EVENT, ESP_EVENT_ANY_ID,
                          &wifi_event_handler, NULL);
```

#### 3. Memory Management
```c
// Internal RAM (fast, limited ~300KB usable)
uint8_t *fast_buf = malloc(1024);

// PSRAM (slower, 2MB available)
uint8_t *large_buf = heap_caps_malloc(1024*1024, MALLOC_CAP_SPIRAM);

// Check available memory
ESP_LOGI(TAG, "Free heap: %lu", esp_get_free_heap_size());
ESP_LOGI(TAG, "Free PSRAM: %lu", heap_caps_get_free_size(MALLOC_CAP_SPIRAM));
```

#### 4. Logging
```c
#define TAG "my_module"

ESP_LOGE(TAG, "Error: %s", error_msg);    // Error (always shown)
ESP_LOGW(TAG, "Warning: %d", value);       // Warning
ESP_LOGI(TAG, "Info message");             // Info (default level)
ESP_LOGD(TAG, "Debug: buf=%p", buf);       // Debug (enable in menuconfig)
ESP_LOGV(TAG, "Verbose trace");            // Verbose
```

### Build Commands

```bash
# First time setup
idf.py set-target esp32s3

# Configure (opens ncurses menu)
idf.py menuconfig

# Build
idf.py build

# Flash and monitor (combined)
idf.py -p /dev/ttyUSB0 flash monitor

# Just monitor (Ctrl+] to exit)
idf.py -p /dev/ttyUSB0 monitor

# Clean build
idf.py fullclean
```

### Common Gotchas

1. **Task stack overflow**: Default 4096 bytes may be too small. Increase if you see random crashes or "Stack canary" errors.

2. **PSRAM not working**: Enable in menuconfig: Component config → ESP32S3-Specific → Support for external, SPI-connected RAM

3. **WiFi CSI not receiving**: Must be connected to an AP, or use promiscuous mode

4. **USB port not showing**: On ESP32-S3-Zero, hold BOOT button while connecting, or use GPIO0 to enter bootloader

5. **Watchdog resets**: Long operations block the idle task. Use `vTaskDelay()` or `esp_task_wdt_reset()`

## Code Style Guidelines

### C Code
- Use ESP-IDF naming conventions: `esp_*` for APIs, `ESP_*` for macros
- Prefix module functions: `wifi_csi_init()`, `pose_inference_run()`
- Use `static` for file-local functions
- Always check return values: `ESP_ERROR_CHECK(esp_wifi_init(&cfg));`

### Header Guards
```c
#ifndef WIFI_CSI_H
#define WIFI_CSI_H

#ifdef __cplusplus
extern "C" {
#endif

// Declarations

#ifdef __cplusplus
}
#endif

#endif // WIFI_CSI_H
```

### Error Handling
```c
esp_err_t my_function(void) {
    esp_err_t ret;

    ret = some_operation();
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Operation failed: %s", esp_err_to_name(ret));
        return ret;
    }

    return ESP_OK;
}
```

## WiFi CSI Specifics

### CSI Data Format
CSI buffer contains interleaved I/Q values:
```
[I0, Q0, I1, Q1, I2, Q2, ...]
```

Each I/Q pair represents one subcarrier. For 20MHz bandwidth: ~52 subcarriers.

### Processing Pipeline
```
CSI Raw Data → Amplitude/Phase Extraction → Noise Filtering →
Feature Extraction → ML Inference → Pose Output
```

### Amplitude and Phase
```c
// From I/Q to amplitude and phase
int8_t I = csi_buf[i*2];
int8_t Q = csi_buf[i*2 + 1];
float amplitude = sqrt(I*I + Q*Q);
float phase = atan2(Q, I);
```

## ML on ESP32

### TensorFlow Lite Micro
```c
#include "tensorflow/lite/micro/micro_interpreter.h"
#include "tensorflow/lite/micro/micro_mutable_op_resolver.h"

// Load model from flash
extern const unsigned char model_data[];
extern const unsigned int model_data_len;

// Create interpreter
const tflite::Model* model = tflite::GetModel(model_data);
tflite::MicroInterpreter interpreter(model, resolver, tensor_arena,
                                     kTensorArenaSize, &error_reporter);
interpreter.AllocateTensors();

// Run inference
interpreter.Invoke();
```

### Model Size Constraints
- **Target**: <500KB for model weights
- **Tensor arena**: ~100-200KB (internal SRAM preferred)
- **Quantization**: INT8 required for speed and size

## Beads Task Tracking

Use beads for task management:
```bash
# View tasks
bd list
bd ready

# Create task
bd create "Implement CSI callback handler"

# Add dependency
bd dep add <child-id> <parent-id>

# Complete task
bd done <id>
```

## Testing Strategy

1. **Unit tests**: ESP-IDF Unity framework
2. **Hardware tests**: LED blink, serial output
3. **CSI validation**: Compare with known good implementations
4. **ML validation**: Test model accuracy on PC before deployment

## Resources

- [ESP-IDF Programming Guide](https://docs.espressif.com/projects/esp-idf/en/latest/esp32s3/)
- [FreeRTOS Documentation](https://www.freertos.org/Documentation/RTOS_book.html)
- [ESP32 WiFi CSI Tool](https://github.com/espressif/esp-csi)
- [TFLite Micro ESP32](https://github.com/espressif/tflite-micro-esp-examples)
