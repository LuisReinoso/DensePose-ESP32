# ESP32 Setup Guide for DensePose-ESP32

**Last Updated**: December 31, 2025
**Tested Hardware**: ESP32-D0WD (regular ESP32, NOT ESP32-S3)
**ESP-IDF Version**: v5.3.1

---

## Table of Contents

1. [Hardware Identification](#hardware-identification)
2. [Common Issues & Solutions](#common-issues--solutions)
3. [Quick Setup Steps](#quick-setup-steps)
4. [Detailed Setup Guide](#detailed-setup-guide)
5. [Troubleshooting](#troubleshooting)
6. [Testing & Validation](#testing--validation)

---

## Hardware Identification

### CRITICAL: Verify Your ESP32 Chip Model

**Before you start**, identify your actual ESP32 chip model:

```bash
# Connect ESP32 via USB and check dmesg
sudo dmesg | tail -20

# Look for lines like:
# "cp210x converter now attached to ttyUSB0"  → CP2102 USB bridge
# OR
# "ch341-uart converter now attached to ttyUSB0"  → CH340 USB bridge

# Then check the chip type during flash:
. ~/esp/esp-idf/export.sh
idf.py -p /dev/ttyUSB0 flash

# Look for output:
# "Chip is ESP32-D0WD"  → Regular ESP32 (NO PSRAM)
# "Chip is ESP32-S3"    → ESP32-S3 (HAS PSRAM)
```

### Known Chip Variants

| Chip Model | PSRAM | CPU Cores | Flash | RAM | WiFi CSI Support |
|------------|-------|-----------|-------|-----|------------------|
| ESP32-D0WD | ❌ NO | Dual Xtensa LX6 | 2-4MB | 520KB | ✅ YES |
| ESP32-D0WDQ6 | ❌ NO | Dual Xtensa LX6 | 2-4MB | 520KB | ✅ YES |
| ESP32-S3FH4R2 | ✅ YES (2MB) | Dual Xtensa LX7 | 4MB | 512KB + 2MB PSRAM | ✅ YES |

**Important**: Project name says "ESP32-S3" but hardware may be regular ESP32!

---

## Common Issues & Solutions

### Issue 1: PSRAM Boot Loop (CRITICAL)

**Symptoms**:
```
E (407) quad_psram: PSRAM ID read error: 0xffffffff, PSRAM chip not found
E cpu_start: Failed to init external RAM!
abort() was called at PC 0x400815b5 on core 0
Rebooting...
```

**Root Cause**: Firmware configured for PSRAM, but chip doesn't have it.

**Solution**:

1. **Check chip model** (see above) - if it's ESP32-D0WD, it has NO PSRAM
2. **Disable PSRAM in configuration**:

```bash
cd firmware

# Edit sdkconfig.defaults
nano sdkconfig.defaults

# Comment out PSRAM lines:
# PSRAM configuration for ESP32-S3
# DISABLED: Current chip is ESP32-D0WD which does not have PSRAM
# CONFIG_ESP32S3_SPIRAM_SUPPORT=y
# CONFIG_SPIRAM=y
# CONFIG_SPIRAM_MODE_QUAD=y
# CONFIG_SPIRAM_SPEED_80M=y
```

3. **Delete old sdkconfig and rebuild**:

```bash
rm sdkconfig
. ~/esp/esp-idf/export.sh
idf.py reconfigure
idf.py build
idf.py -p /dev/ttyUSB0 flash
```

4. **Verify PSRAM is disabled**:

```bash
grep "CONFIG_SPIRAM" sdkconfig
# Should show:
# # CONFIG_SPIRAM is not set
# # CONFIG_SPIRAM_SUPPORT is not set
```

---

### Issue 2: Wrong WiFi Credentials

**Symptoms**:
```
E (15254) main: Failed to connect after 5 attempts
E (15254) main: Failed to connect to SSID: myssid
E (15254) main: WiFi initialization failed!
```

**Root Cause**: WiFi credentials not loaded from .env file into sdkconfig.

**Solution**:

1. **Verify .env file exists and has correct credentials**:

```bash
cat .env
# Should show:
# WIFI_SSID=Your-Network-Name
# WIFI_PASSWORD=YourPassword123
```

2. **Update sdkconfig manually**:

```bash
cd firmware

# Edit WiFi credentials in sdkconfig
sed -i 's/CONFIG_WIFI_SSID="myssid"/CONFIG_WIFI_SSID="Your-Network-Name"/' sdkconfig
sed -i 's/CONFIG_WIFI_PASSWORD="mypassword"/CONFIG_WIFI_PASSWORD="YourPassword123"/' sdkconfig

# Verify changes
grep "CONFIG_WIFI_SSID\|CONFIG_WIFI_PASSWORD" sdkconfig
```

3. **Rebuild and flash**:

```bash
. ~/esp/esp-idf/export.sh
idf.py build
idf.py -p /dev/ttyUSB0 flash
```

---

### Issue 3: Serial Port Permissions

**Symptoms**:
```
serial.serialutil.SerialException: [Errno 13] could not open port /dev/ttyUSB0: [Errno 13] Permission denied
```

**Solution**:

```bash
# Temporary fix (until reboot):
sudo chmod 666 /dev/ttyUSB0

# Permanent fix (add user to dialout group):
sudo usermod -a -G dialout $USER
# Log out and log back in for this to take effect
```

---

### Issue 4: Wrong Chip Target

**Symptoms**:
```
A fatal error occurred: This chip is ESP32, not ESP32-S3. Wrong --chip argument?
```

**Solution**:

```bash
cd firmware
. ~/esp/esp-idf/export.sh

# Clean and set correct target
idf.py fullclean
idf.py set-target esp32   # Use 'esp32s3' if you actually have ESP32-S3

# Rebuild
idf.py build
idf.py -p /dev/ttyUSB0 flash
```

---

## Quick Setup Steps

### For Regular ESP32 (ESP32-D0WD/ESP32-D0WDQ6)

```bash
# 1. Clone or navigate to project
cd ~/proyectos/DensePose-ESP32

# 2. Create WiFi credentials
cp .env.example .env
nano .env
# Edit: WIFI_SSID and WIFI_PASSWORD

# 3. Disable PSRAM
cd firmware
nano sdkconfig.defaults
# Comment out all CONFIG_SPIRAM lines

# 4. Clean and configure
rm sdkconfig
. ~/esp/esp-idf/export.sh
idf.py set-target esp32
idf.py reconfigure

# 5. Update WiFi credentials in sdkconfig
sed -i 's/CONFIG_WIFI_SSID="myssid"/CONFIG_WIFI_SSID="YourNetworkName"/' sdkconfig
sed -i 's/CONFIG_WIFI_PASSWORD="mypassword"/CONFIG_WIFI_PASSWORD="YourPassword123"/' sdkconfig

# 6. Build and flash
idf.py build
sudo chmod 666 /dev/ttyUSB0  # If needed
idf.py -p /dev/ttyUSB0 flash monitor
```

### For ESP32-S3 with PSRAM

```bash
# 1-2. Same as above

# 3. Enable PSRAM (should be enabled by default)
cd firmware
nano sdkconfig.defaults
# Uncomment:
# CONFIG_ESP32S3_SPIRAM_SUPPORT=y
# CONFIG_SPIRAM=y
# CONFIG_SPIRAM_MODE_QUAD=y
# CONFIG_SPIRAM_SPEED_80M=y

# 4. Clean and configure
rm sdkconfig
. ~/esp/esp-idf/export.sh
idf.py set-target esp32s3
idf.py reconfigure

# 5-6. Same as above
```

---

## Detailed Setup Guide

### Step 1: ESP-IDF Installation (One-Time Setup)

```bash
# Install prerequisites
sudo apt-get update
sudo apt-get install git wget flex bison gperf python3 python3-pip \
  python3-venv cmake ninja-build ccache libffi-dev libssl-dev \
  dfu-util libusb-1.0-0

# Clone ESP-IDF
mkdir -p ~/esp
cd ~/esp
git clone --recursive https://github.com/espressif/esp-idf.git
cd esp-idf
git checkout v5.3.1  # Use stable version

# Install ESP32 tools
./install.sh esp32,esp32s3

# Add to ~/.bashrc for convenience (optional)
echo 'alias get_idf=". ~/esp/esp-idf/export.sh"' >> ~/.bashrc
source ~/.bashrc
```

### Step 2: Project Setup

```bash
cd ~/proyectos/DensePose-ESP32

# Install Python dependencies
pip install -r tools/requirements.txt
# Should install: pyserial>=3.5

# Create WiFi credentials
cp .env.example .env
nano .env
```

Edit `.env`:
```
WIFI_SSID=Your-2.4GHz-Network-Name
WIFI_PASSWORD=YourSecurePassword
```

**Important WiFi Requirements**:
- Must be 2.4GHz network (ESP32 doesn't support 5GHz)
- WPA2 or WPA3 security (no open networks)
- Good signal strength at ESP32 location

### Step 3: Configure Firmware for Your Hardware

#### Option A: Regular ESP32 (NO PSRAM)

```bash
cd firmware
nano sdkconfig.defaults
```

Ensure PSRAM lines are commented:
```
# PSRAM configuration for ESP32-S3
# DISABLED: Current chip is ESP32-D0WD which does not have PSRAM
# CONFIG_ESP32S3_SPIRAM_SUPPORT=y
# CONFIG_SPIRAM=y
# CONFIG_SPIRAM_MODE_QUAD=y
# CONFIG_SPIRAM_SPEED_80M=y
```

#### Option B: ESP32-S3 (WITH PSRAM)

```bash
cd firmware
nano sdkconfig.defaults
```

Ensure PSRAM lines are uncommented:
```
# PSRAM configuration for ESP32-S3
CONFIG_ESP32S3_SPIRAM_SUPPORT=y
CONFIG_SPIRAM=y
CONFIG_SPIRAM_MODE_QUAD=y
CONFIG_SPIRAM_SPEED_80M=y
```

### Step 4: Build Firmware

```bash
cd firmware
. ~/esp/esp-idf/export.sh

# Set target (IMPORTANT: Use correct target for your chip!)
idf.py set-target esp32      # For ESP32-D0WD
# OR
idf.py set-target esp32s3    # For ESP32-S3

# Configure (this generates sdkconfig from sdkconfig.defaults)
idf.py reconfigure

# Update WiFi credentials in sdkconfig
# Replace with YOUR credentials from .env
sed -i 's/CONFIG_WIFI_SSID="myssid"/CONFIG_WIFI_SSID="YourNetworkName"/' sdkconfig
sed -i 's/CONFIG_WIFI_PASSWORD="mypassword"/CONFIG_WIFI_PASSWORD="YourPassword123"/' sdkconfig

# Verify WiFi credentials
grep "CONFIG_WIFI_SSID\|CONFIG_WIFI_PASSWORD" sdkconfig

# Build
idf.py build
```

### Step 5: Flash to ESP32

```bash
# Connect ESP32 via USB
# Check which port it appears on
ls /dev/ttyUSB* /dev/ttyACM*

# Set permissions (if needed)
sudo chmod 666 /dev/ttyUSB0

# Flash and monitor
idf.py -p /dev/ttyUSB0 flash monitor

# Press Ctrl+] to exit monitor
```

### Step 6: Verify CSI Data Collection

```bash
# In a new terminal
cd ~/proyectos/DensePose-ESP32

# Run CSI reader
python tools/read_csi.py /dev/ttyUSB0

# You should see:
# Connected to /dev/ttyUSB0 at 115200 baud
# Waiting for CSI data... (Ctrl+C to exit)
#
# [20:00:55] Packet #1 | ts=490666ms | RSSI=-45dBm | subcarriers=64 | ...
```

---

## Troubleshooting

### No CSI Packets Received

**Symptoms**: Python tool connects but shows "Received 0 CSI packets"

**Cause**: CSI is only generated when ESP32 **receives** WiFi packets from other devices.

**Solution**: Generate WiFi traffic

```bash
# Option 1: Ping broadcast address (run in another terminal)
ping -i 0.1 192.168.1.255

# Option 2: Ping ESP32 directly (if you know its IP)
ping -i 0.1 <ESP32_IP_ADDRESS>

# Option 3: Use another device on the same WiFi network
# - Browse websites
# - Stream video
# - Download files
```

**Expected CSI Rate**:
- Idle network: 0.1-1 packets/sec
- Light traffic: 1-10 packets/sec
- Heavy traffic: 10-100 packets/sec

### ESP32 Won't Enter Flash Mode

**Symptoms**: "Connecting..." appears but never connects

**Solution**:

1. **Hold BOOT button** while connecting USB
2. Or **press and hold BOOT**, then press and release RESET
3. Try different USB cable (some cables are power-only)
4. Check USB drivers:
   - CP2102: `sudo modprobe cp210x`
   - CH340: `sudo modprobe ch341`

### Monitor Shows Garbled Text

**Cause**: Wrong baud rate

**Solution**: ESP32 uses 115200 baud by default

```bash
# Ensure baud rate is correct
idf.py -p /dev/ttyUSB0 -b 115200 monitor

# Or with Python tool
python tools/read_csi.py /dev/ttyUSB0 -b 115200
```

### Build Warnings About Unknown Kconfig Symbols

**Warning**: `unknown kconfig symbol 'ESP32S3_SPIRAM_SUPPORT'`

**Cause**: sdkconfig.defaults has ESP32-S3 options but target is ESP32

**Solution**: This is expected when building for ESP32 (without PSRAM). Comment out those lines or ignore the warning.

---

## Testing & Validation

### 1. Basic Boot Test

After flashing, monitor should show:

```
I (31) boot: ESP-IDF v5.3.1 2nd stage bootloader
I (35) boot: chip revision: v1.1
I (48) boot.esp32: SPI Flash Size : 2MB
...
I (xxx) main: DensePose WiFi CSI - ESP32
I (xxx) main: Connecting to WiFi SSID: Your-Network-Name
I (xxx) main: WiFi connected, IP: 192.168.x.x
I (xxx) wifi_csi: WiFi CSI initialized successfully
```

**✅ PASS**: If you see "WiFi connected" and "CSI initialized"
**❌ FAIL**: If you see errors or continuous rebooting

### 2. CSI Data Format Test

CSI data should be valid JSON:

```json
{
  "ts": 490666,
  "rssi": -45,
  "num": 64,
  "amp": [104.18, 18.00, 20.81, ...],
  "phase": [1.1974, 0.0000, 0.9561, ...]
}
```

**Validation**:
- `ts`: Timestamp in milliseconds (increasing)
- `rssi`: -30 to -90 dBm (typical range)
- `num`: 52-64 subcarriers (20MHz bandwidth)
- `amp`: Positive values, typically 0-150
- `phase`: -π to +π (-3.14 to 3.14)

### 3. Signal Quality Test

**Good CSI Quality**:
- RSSI: -30 to -60 dBm (excellent to good)
- Amplitude: Mean > 5, Max > 50
- Packet rate: > 1 packet/sec with traffic

**Poor CSI Quality**:
- RSSI: < -80 dBm (very weak signal)
- Amplitude: All values near 0
- Packet rate: < 0.1 packet/sec

**Fix**: Move ESP32 closer to WiFi router or use WiFi extender

### 4. Movement Detection Test

```bash
# Start CSI collection with verbose output
python tools/read_csi.py /dev/ttyUSB0 --verbose

# Baseline: Stand still for 30 seconds
# Observe amplitude values stabilize

# Movement: Walk between router and ESP32
# Observe amplitude values change (typically decrease)

# Movement: Wave arms near ESP32
# Observe rapid fluctuations in amplitude and phase
```

**Expected Behavior**:
- **No movement**: Amplitude values relatively stable (±10%)
- **Person passing**: Amplitude dips 20-50%
- **Active movement**: Rapid changes in both amplitude and phase

---

## Quick Reference Commands

```bash
# Source ESP-IDF environment
. ~/esp/esp-idf/export.sh

# Check chip type
idf.py -p /dev/ttyUSB0 flash  # Look at chip detection

# Build for ESP32
idf.py set-target esp32
idf.py build

# Build for ESP32-S3
idf.py set-target esp32s3
idf.py build

# Flash and monitor
idf.py -p /dev/ttyUSB0 flash monitor

# Clean build
idf.py fullclean

# Read CSI data
python tools/read_csi.py /dev/ttyUSB0

# Save CSI data to file
python tools/read_csi.py /dev/ttyUSB0 --output data.json

# Generate WiFi traffic for CSI
ping -i 0.1 192.168.1.255
```

---

## Configuration Files Reference

### Key Files Modified for Each ESP32

| File | Purpose | Action |
|------|---------|--------|
| `.env` | WiFi credentials | **CREATE** - copy from .env.example |
| `firmware/sdkconfig.defaults` | Default config | **EDIT** - enable/disable PSRAM |
| `firmware/sdkconfig` | Active config | **AUTO-GENERATED** - update WiFi credentials |

### Files That Should NOT Be Modified

- `firmware/main/main.c` - Application entry point
- `firmware/main/wifi_csi.c` - CSI implementation
- `firmware/main/wifi_csi.h` - CSI API
- `tools/read_csi.py` - CSI data reader

---

## Lessons Learned

### 1. Always Verify Hardware Before Configuring

Don't assume hardware matches project name. The "DensePose-ESP32-S3" project worked on regular ESP32-D0WD after disabling PSRAM.

### 2. PSRAM Configuration is Critical

Mismatch between PSRAM config and hardware causes immediate boot failure. Always check chip model first.

### 3. WiFi Credentials Need Manual Update

The .env file doesn't automatically update sdkconfig. You must manually update WiFi credentials in sdkconfig after running `idf.py reconfigure`.

### 4. CSI Requires WiFi Traffic

CSI packets are only generated when ESP32 receives WiFi packets. Generate traffic by pinging or using other network devices.

### 5. Clean Builds Prevent Stale Config Issues

When changing major settings (target, PSRAM), always run:
```bash
idf.py fullclean
rm sdkconfig
idf.py reconfigure
```

---

## Support & Resources

- **ESP-IDF Documentation**: https://docs.espressif.com/projects/esp-idf/
- **ESP32 WiFi CSI**: https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-guides/wifi.html#wi-fi-channel-state-information
- **Project Issues**: https://github.com/anthropics/claude-code/issues (for Claude Code setup help)
- **Hardware Datasheets**: See `docs/ESP32-S3-Hardware-Reference.md`

---

**Document Version**: 1.0
**Last Tested**: December 31, 2025
**ESP-IDF**: v5.3.1
**Hardware**: ESP32-D0WD (CP2102 USB bridge)
