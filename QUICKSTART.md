# Quick Start Guide

Get your ESP32-S3 streaming CSI data in under 10 minutes!

## Prerequisites

- ESP32-S3-Zero board (or compatible ESP32-S3)
- USB cable
- WiFi network (2.4GHz)
- Linux/macOS/Windows with Python 3

## Step 1: Install ESP-IDF (One Time Setup)

```bash
# Clone ESP-IDF
git clone --recursive https://github.com/espressif/esp-idf.git ~/esp/esp-idf
cd ~/esp/esp-idf

# Install for ESP32-S3 (takes 5-10 minutes)
./install.sh esp32s3

# Set up environment (run this in every new terminal)
source export.sh
```

Add this to your `~/.bashrc` or `~/.zshrc` for convenience:
```bash
alias get_idf='source ~/esp/esp-idf/export.sh'
```

## Step 2: Configure WiFi

Edit `firmware/main/main.c` and update lines 33-34:

```c
#define WIFI_SSID      "YourNetworkName"    // Change this
#define WIFI_PASSWORD  "YourPassword"        // Change this
```

**Important**: Your WiFi must be 2.4GHz (ESP32 doesn't support 5GHz).

## Step 3: Build and Flash

```bash
# Navigate to firmware directory
cd /path/to/DensePose-ESP32/firmware

# Set target (first time only)
idf.py set-target esp32s3

# Build the firmware
idf.py build

# Find your serial port
# Linux: /dev/ttyUSB0 or /dev/ttyACM0
# macOS: /dev/cu.usbserial-* or /dev/cu.usbmodem-*
# Windows: COM3, COM4, etc.
ls /dev/tty* | grep -i usb

# Flash and monitor (replace /dev/ttyUSB0 with your port)
idf.py -p /dev/ttyUSB0 flash monitor
```

## Step 4: Verify CSI Data

You should see output like:

```
I (2345) main: WiFi started, connecting to AP...
I (3456) main: Connected! IP: 192.168.1.42
I (3457) wifi_csi: CSI collection initialized successfully
I (3458) main: Initialization complete. Collecting CSI data...
I (3459) main: Streaming CSI data over serial (JSON format)...
{"ts":3459,"rssi":-45,"num":64,"amp":[12.3,15.7,...],"phase":[0.12,-1.45,...]}
{"ts":3559,"rssi":-46,"num":64,"amp":[11.8,16.2,...],"phase":[0.15,-1.42,...]}
```

If you see the JSON lines, **you're streaming CSI data!** 🎉

## Step 5: Analyze CSI Data (Optional)

### Option A: Use Python Script

```bash
# Install pyserial
pip3 install pyserial

# Run the CSI reader
python3 tools/read_csi.py /dev/ttyUSB0

# Save data to file for later analysis
python3 tools/read_csi.py /dev/ttyUSB0 -o csi_data.jsonl

# Verbose mode (shows full arrays)
python3 tools/read_csi.py /dev/ttyUSB0 -v
```

### Option B: Use ESP-IDF Monitor

Already running from Step 3! Press `Ctrl+]` to exit.

### Option C: Any Serial Terminal

- **Linux**: `screen /dev/ttyUSB0 115200`
- **macOS**: `screen /dev/cu.usbserial-* 115200`
- **Windows**: Use PuTTY or Arduino Serial Monitor

## Troubleshooting

### "Permission denied" on serial port

**Linux**:
```bash
sudo usermod -a -G dialout $USER
# Then log out and back in
```

**macOS/Windows**: Run terminal as administrator

### WiFi connection fails

1. Double-check SSID and password in `main.c`
2. Verify your WiFi is 2.4GHz (not 5GHz)
3. Check router allows new device connections
4. Look for error messages in serial output

### No CSI data appearing

1. Verify "CSI collection initialized successfully" message appears
2. Make sure WiFi is connected (check for IP address in logs)
3. Generate some WiFi traffic (ping another device, browse the web)
4. Try moving closer to the router

### Build errors

1. Make sure ESP-IDF is properly installed: `idf.py --version`
2. Verify you ran `source ~/esp/esp-idf/export.sh`
3. Delete build directory and try again: `rm -rf build && idf.py build`

### Flash fails

1. Disconnect and reconnect USB cable
2. Try a different USB cable (some are power-only)
3. Hold the BOOT button while running `idf.py flash`
4. Verify correct serial port with `ls /dev/tty*`

## What to Try Next

1. **Test CSI sensitivity**: Walk around the room and watch amplitude values change
2. **Record baseline data**: Run `read_csi.py -o baseline.jsonl` with empty room
3. **Test with presence**: Record again with person in room, compare the data
4. **Experiment with distance**: Move closer/farther from router
5. **Try different positions**: Change ESP32 orientation and location

## Next Steps

See [PHASE2_SUMMARY.md](PHASE2_SUMMARY.md) for:
- Detailed testing checklist
- Data validation procedures
- Future improvements (web visualization)

See [firmware/README.md](firmware/README.md) for:
- Detailed ESP-IDF setup
- CSI data format specification
- Advanced troubleshooting

## Need Help?

Check the documentation:
- `AGENTS.md` - Project overview and development guide
- `TODO.md` - Project roadmap
- `firmware/README.md` - Firmware details
- `PHASE2_SUMMARY.md` - Phase 2 implementation notes

Or review the code:
- `firmware/main/wifi_csi.c` - CSI collection logic
- `firmware/main/main.c` - Application entry point
- `tools/read_csi.py` - Python CSI reader
