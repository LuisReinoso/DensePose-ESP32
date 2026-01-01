# ESP32 CSI Troubleshooting Checklist

Quick diagnostic checklist for setting up new ESP32 boards for CSI data collection.

---

## Pre-Flash Checklist

### ☐ 1. Identify Hardware

```bash
# Connect ESP32 and check chip type
. ~/esp/esp-idf/export.sh
idf.py -p /dev/ttyUSB0 flash
```

**Look for**: "Chip is ESP32-D0WD" or "Chip is ESP32-S3"

| If you see... | Action |
|---------------|--------|
| ESP32-D0WD / ESP32-D0WDQ6 | ❌ Disable PSRAM in sdkconfig.defaults |
| ESP32-S3 | ✅ Enable PSRAM in sdkconfig.defaults |

### ☐ 2. Configure PSRAM

**For ESP32-D0WD (NO PSRAM)**:
```bash
cd firmware
nano sdkconfig.defaults

# Comment out:
# CONFIG_ESP32S3_SPIRAM_SUPPORT=y
# CONFIG_SPIRAM=y
# CONFIG_SPIRAM_MODE_QUAD=y
# CONFIG_SPIRAM_SPEED_80M=y
```

**For ESP32-S3 (WITH PSRAM)**:
```bash
# Uncomment the lines above
```

### ☐ 3. Set WiFi Credentials

```bash
# Create .env
cp .env.example .env
nano .env

# Add YOUR credentials (2.4GHz network only!)
WIFI_SSID=Your-Network-Name
WIFI_PASSWORD=YourPassword
```

### ☐ 4. Serial Port Permissions

```bash
# Check port
ls -l /dev/ttyUSB0

# Fix permissions if needed
sudo chmod 666 /dev/ttyUSB0
```

---

## Build Checklist

### ☐ 1. Clean Build

```bash
cd firmware
. ~/esp/esp-idf/export.sh
idf.py fullclean
rm sdkconfig  # Remove old config
```

### ☐ 2. Set Correct Target

```bash
# For ESP32-D0WD:
idf.py set-target esp32

# For ESP32-S3:
idf.py set-target esp32s3
```

### ☐ 3. Reconfigure

```bash
idf.py reconfigure
```

**Verify**: Should create new `sdkconfig` file

### ☐ 4. Update WiFi Credentials in sdkconfig

```bash
# Replace with YOUR credentials from .env
sed -i 's/CONFIG_WIFI_SSID="myssid"/CONFIG_WIFI_SSID="YourNetwork"/' sdkconfig
sed -i 's/CONFIG_WIFI_PASSWORD="mypassword"/CONFIG_WIFI_PASSWORD="YourPass"/' sdkconfig

# VERIFY
grep "CONFIG_WIFI_SSID\|CONFIG_WIFI_PASSWORD" sdkconfig
```

**Should show YOUR credentials**, not "myssid" or "mypassword"!

### ☐ 5. Verify PSRAM Config

```bash
grep "CONFIG_SPIRAM" sdkconfig
```

**For ESP32-D0WD, should show**:
```
# CONFIG_SPIRAM is not set
# CONFIG_SPIRAM_SUPPORT is not set
```

**For ESP32-S3, should show**:
```
CONFIG_SPIRAM=y
CONFIG_SPIRAM_SUPPORT=y
```

### ☐ 6. Build

```bash
idf.py build
```

**Verify**: Should complete without errors

---

## Flash Checklist

### ☐ 1. Flash Firmware

```bash
idf.py -p /dev/ttyUSB0 flash
```

**Look for**: "Hash of data verified" and "Leaving..."

### ☐ 2. Monitor Boot

```bash
idf.py -p /dev/ttyUSB0 monitor
```

**Check for these messages** (in order):

| Message | Status |
|---------|--------|
| `ESP-IDF v5.3.1 2nd stage bootloader` | ✅ Bootloader OK |
| `Loaded app from partition at offset 0x10000` | ✅ App loaded |
| `This chip is ESP32-D0WD` | ✅ Chip detected |
| ❌ `PSRAM ID read error` | ⚠️ PSRAM config wrong! |
| `DensePose WiFi CSI - ESP32` | ✅ App started |
| `Connecting to WiFi SSID: Your-Network` | ✅ WiFi connecting |
| `WiFi connected, IP: 192.168.x.x` | ✅ WiFi OK |
| `WiFi CSI initialized successfully` | ✅ CSI enabled |

### ☐ 3. Check for Errors

**❌ If you see PSRAM error**:
```
E (407) quad_psram: PSRAM ID read error: 0xffffffff
```
→ Go back to "Configure PSRAM" step

**❌ If you see WiFi error**:
```
E (15254) main: Failed to connect to SSID: myssid
```
→ Go back to "Update WiFi Credentials" step

---

## CSI Data Collection Checklist

### ☐ 1. Check Raw Serial Output

```bash
python3 -c "
import serial
ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=5)
for i in range(10):
    line = ser.readline().decode('utf-8', errors='ignore').strip()
    if line.startswith('{'):
        print('✓ JSON CSI data:', line[:80])
ser.close()
"
```

**Expected**: Should see JSON lines with `{"ts":...,"rssi":...,"amp":[...],"phase":[...]}`

### ☐ 2. Test Python CSI Reader

```bash
cd ~/proyectos/DensePose-ESP32
timeout 10 python tools/read_csi.py /dev/ttyUSB0
```

**Expected**: Should show packet count > 0

**If 0 packets**: CSI needs WiFi traffic! Continue to next step.

### ☐ 3. Generate WiFi Traffic

```bash
# In another terminal, ping to generate traffic
ping -i 0.1 192.168.1.255

# Or if you know ESP32's IP:
ping -i 0.1 <ESP32_IP>
```

**Then re-run CSI reader**

### ☐ 4. Validate CSI Data Quality

**Run with verbose output**:
```bash
python tools/read_csi.py /dev/ttyUSB0 --verbose
```

**Check values**:
- ✅ RSSI: -30 to -70 dBm (good signal)
- ✅ Subcarriers: 52-64 (full bandwidth)
- ✅ Amplitude: Mean > 5, Max > 50
- ✅ Phase: Values between -3.14 and 3.14

**⚠️ Poor signal** (RSSI < -80 dBm):
- Move ESP32 closer to router
- Check antenna connection
- Use WiFi extender

---

## Quick Diagnostic Commands

```bash
# 1. Check chip type
. ~/esp/esp-idf/export.sh && idf.py -p /dev/ttyUSB0 flash | grep "Chip is"

# 2. Check PSRAM config
grep "CONFIG_SPIRAM" firmware/sdkconfig

# 3. Check WiFi config
grep "CONFIG_WIFI_" firmware/sdkconfig

# 4. Monitor ESP32 output
idf.py -p /dev/ttyUSB0 monitor

# 5. Test CSI data
python3 -c "import serial; s=serial.Serial('/dev/ttyUSB0',115200,timeout=5); [print(s.readline()) for i in range(10)]"

# 6. Check serial port
ls -l /dev/ttyUSB* /dev/ttyACM*
```

---

## Common Error Messages & Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| `PSRAM ID read error: 0xffffffff` | PSRAM enabled but chip has no PSRAM | Disable PSRAM in sdkconfig.defaults |
| `Failed to connect to SSID: myssid` | WiFi credentials not updated | Update CONFIG_WIFI_SSID/PASSWORD in sdkconfig |
| `This chip is ESP32, not ESP32-S3` | Wrong target | Run `idf.py set-target esp32` |
| `Permission denied: '/dev/ttyUSB0'` | No serial port access | Run `sudo chmod 666 /dev/ttyUSB0` |
| `Received 0 CSI packets` | No WiFi traffic | Generate traffic: `ping 192.168.1.255` |
| `unknown kconfig symbol` | Config mismatch | Ignore or comment out in sdkconfig.defaults |

---

## Success Criteria

### ✅ All checks must pass:

- [x] ESP32 boots without errors
- [x] No PSRAM errors in boot log
- [x] WiFi connects successfully
- [x] WiFi CSI initialized
- [x] CSI JSON data appears on serial
- [x] Python reader receives packets
- [x] RSSI between -30 and -80 dBm
- [x] 52-64 subcarriers detected

### 🎉 If all pass: ESP32 is ready for CSI data collection!

---

## Emergency Recovery

**If completely stuck**, start from scratch:

```bash
cd ~/proyectos/DensePose-ESP32/firmware

# 1. Complete clean
rm -rf build/ sdkconfig

# 2. Source environment
. ~/esp/esp-idf/export.sh

# 3. Identify hardware
idf.py -p /dev/ttyUSB0 flash | grep "Chip is"
# Note: ESP32-D0WD or ESP32-S3?

# 4. Configure for YOUR hardware
nano sdkconfig.defaults
# ESP32-D0WD: Comment out SPIRAM lines
# ESP32-S3: Uncomment SPIRAM lines

# 5. Set target
idf.py set-target esp32    # or esp32s3

# 6. Reconfigure
idf.py reconfigure

# 7. Update WiFi
sed -i 's/CONFIG_WIFI_SSID="myssid"/CONFIG_WIFI_SSID="YourNetwork"/' sdkconfig
sed -i 's/CONFIG_WIFI_PASSWORD="mypassword"/CONFIG_WIFI_PASSWORD="YourPass"/' sdkconfig

# 8. Build and flash
idf.py build
idf.py -p /dev/ttyUSB0 flash monitor
```

---

**Checklist Version**: 1.0
**Last Updated**: December 31, 2025
