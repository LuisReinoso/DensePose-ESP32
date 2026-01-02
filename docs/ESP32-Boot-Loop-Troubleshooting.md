# ESP32 Boot Loop & CSI Output Troubleshooting Guide

**Date**: January 1, 2026
**Issue**: ESP32 stuck in boot loop, outputting garbage characters, no CSI data

---

## Symptoms Observed

### 1. Garbage Serial Output
```
|p| ppppp|ppp|| p||p |p| ppppp|ppp|| p||p |p| ppppp|ppp|| p||p
```

**What this means**:
- Baud rate mismatch, OR
- ESP32 in continuous reboot loop, OR
- Hardware/power issue

### 2. Intermittent "Free heap" Messages
```
I (373883) main: Free heap: 211936, min ever: 206920
```

**What this means**:
- ESP32 is running the firmware
- Main loop is executing
- But WiFi/CSI subsystem not initializing

### 3. No CSI JSON Data
- Expected: `{"ts":123,"rssi":-45,"amp":[...],"phase":[...]}`
- Actual: Nothing or garbage

---

## Root Cause Analysis

### Most Likely Causes (In Order)

#### 1. **Boot Loop Due to WiFi Connection Failure**
**Probability**: HIGH
**Why**: ESP32 may be crashing when trying to connect to WiFi

**Evidence**:
- Garbage characters (typical of repeated reboots)
- "Free heap" messages appear briefly then restart
- No WiFi connection messages seen

**Fix**:
```bash
# Check WiFi credentials
cd firmware
grep "CONFIG_WIFI_SSID\|CONFIG_WIFI_PASSWORD" sdkconfig

# If wrong, update:
sed -i 's/CONFIG_WIFI_SSID=".*"/CONFIG_WIFI_SSID="YourNetwork"/' sdkconfig
sed -i 's/CONFIG_WIFI_PASSWORD=".*"/CONFIG_WIFI_PASSWORD="YourPass"/' sdkconfig

# Rebuild and reflash
. ~/esp/esp-idf/export.sh
idf.py build
idf.py -p /dev/ttyUSB0 flash
```

#### 2. **PSRAM Configuration Mismatch**
**Probability**: MEDIUM
**Why**: Firmware expects PSRAM but hardware doesn't have it (or vice versa)

**Evidence**:
- We disabled PSRAM in sdkconfig.defaults
- But fullclean + rebuild may have reset this

**Fix**:
```bash
cd firmware

# Check PSRAM config
grep "CONFIG_SPIRAM" sdkconfig

# If enabled but chip has no PSRAM:
rm sdkconfig
idf.py reconfigure
grep "CONFIG_SPIRAM" sdkconfig  # Should show "# CONFIG_SPIRAM is not set"
idf.py build
idf.py -p /dev/ttyUSB0 flash
```

#### 3. **Hardware Issues**
**Probability**: MEDIUM
**Why**: USB cable, power, or board fault

**Symptoms**:
- Garbage output at all baud rates
- Inconsistent behavior after reconnecting
- LED behavior abnormal

**Fix**:
- Try different USB cable (must support data transfer)
- Try different USB port
- Check for physical damage on ESP32
- Test with different ESP32 board if available

#### 4. **Corrupted Flash/Partition Table**
**Probability**: LOW-MEDIUM
**Why**: Flash corruption from incomplete writes

**Fix**:
```bash
cd firmware
. ~/esp/esp-idf/export.sh

# Erase entire flash
idf.py -p /dev/ttyUSB0 erase-flash

# Rebuild from scratch
idf.py fullclean
idf.py build
idf.py -p /dev/ttyUSB0 flash
```

---

## Step-by-Step Troubleshooting Procedure

### Phase 1: Basic Diagnostics

#### 1.1 Check Hardware Connection
```bash
# Verify device is detected
ls -l /dev/ttyUSB*
# Expected: crw-rw-rw- ... /dev/ttyUSB0

# Check permissions
sudo chmod 666 /dev/ttyUSB0
```

#### 1.2 Test Serial Output
```bash
# Read raw output for 5 seconds
timeout 5 cat /dev/ttyUSB0

# If you see readable text → Good
# If you see garbage (|p|ppp) → Bad (boot loop or baud mismatch)
# If you see nothing → Very bad (hardware issue)
```

#### 1.3 Check Boot Messages
```bash
# Unplug ESP32, wait 3 seconds, plug back in
# Immediately run:
python3 -c "
import serial
ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)
for i in range(50):
    print(ser.readline().decode('utf-8', errors='ignore').strip())
ser.close()
"
```

**Look for**:
- `ESP-ROM:` lines (early boot)
- `I (xx) boot:` messages (bootloader)
- `I (xx) cpu_start:` (app starting)
- `I (xx) wifi:` (WiFi init)
- `E (xx)` ERROR messages (crashes)

---

### Phase 2: Configuration Fixes

#### 2.1 Verify and Fix WiFi Credentials
```bash
cd /home/luis/proyectos/DensePose-ESP32/firmware

# Check current config
echo "Current WiFi config:"
grep "CONFIG_WIFI_SSID\|CONFIG_WIFI_PASSWORD" sdkconfig

# Update if needed (replace with your network)
sed -i 's/CONFIG_WIFI_SSID=".*"/CONFIG_WIFI_SSID="CNT-INTERNET"/' sdkconfig
sed -i 's/CONFIG_WIFI_PASSWORD=".*"/CONFIG_WIFI_PASSWORD="rrSVPSP.DLL1"/' sdkconfig

# Verify update
grep "CONFIG_WIFI_SSID\|CONFIG_WIFI_PASSWORD" sdkconfig

# Rebuild and flash
. ~/esp/esp-idf/export.sh
idf.py build
idf.py -p /dev/ttyUSB0 flash
```

#### 2.2 Disable PSRAM (ESP32-D0WD has no PSRAM)
```bash
cd firmware

# Method 1: Edit sdkconfig.defaults
nano sdkconfig.defaults
# Comment out all PSRAM lines:
# # CONFIG_SPIRAM=y
# # CONFIG_SPIRAM_MODE_QUAD=y
# etc.

# Method 2: Clean rebuild
rm sdkconfig sdkconfig.old
. ~/esp/esp-idf/export.sh
idf.py reconfigure

# Verify PSRAM is disabled
grep "CONFIG_SPIRAM" sdkconfig
# Should show: # CONFIG_SPIRAM is not set

# Build and flash
idf.py build
idf.py -p /dev/ttyUSB0 flash
```

#### 2.3 Check CSI Configuration
```bash
cd firmware

# Verify CSI is enabled
grep "CONFIG_ESP_WIFI_CSI_ENABLED" sdkconfig
# Should show: CONFIG_ESP_WIFI_CSI_ENABLED=y

# If not enabled:
idf.py menuconfig
# Navigate to: Component config → Wi-Fi → WiFi CSI(Channel State Information)
# Enable it, save, exit

idf.py build
idf.py -p /dev/ttyUSB0 flash
```

---

### Phase 3: Nuclear Options

#### 3.1 Complete Flash Erase
```bash
cd firmware
. ~/esp/esp-idf/export.sh

# Erase everything
idf.py -p /dev/ttyUSB0 erase-flash

# Wait for completion, then rebuild from scratch
idf.py fullclean
idf.py build
idf.py -p /dev/ttyUSB0 flash
```

#### 3.2 Bootloader Mode Check
```bash
# Try entering bootloader manually
# 1. Unplug ESP32
# 2. Hold BOOT button (if available)
# 3. Plug in ESP32 while holding BOOT
# 4. Release BOOT after 2 seconds

# Then flash
idf.py -p /dev/ttyUSB0 flash
```

#### 3.3 Hardware Swap
If all else fails:
- Try different USB cable (must support data, not just charging)
- Try different USB port on computer
- Try different ESP32 board (if available)
- Check for visible damage on board

---

## Monitoring and Validation

### Test 1: Basic Serial Communication
```bash
timeout 5 python3 -c "
import serial
ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)
lines = []
for i in range(30):
    line = ser.readline().decode('utf-8', errors='ignore').strip()
    if line and 'I (' in line:  # ESP-IDF log format
        lines.append(line)
ser.close()
print(f'Readable lines: {len(lines)}')
for line in lines[:10]:
    print(line)
"
```

**Success criteria**: See `I (timestamp)` formatted log messages

---

### Test 2: WiFi Connection Check
```bash
timeout 10 python3 -c "
import serial
ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)
wifi_connected = False
for i in range(100):
    line = ser.readline().decode('utf-8', errors='ignore').strip()
    if 'wifi' in line.lower() or 'connected' in line.lower():
        print(line)
        if 'connected' in line.lower() or 'got ip' in line.lower():
            wifi_connected = True
            break
ser.close()
print(f'WiFi connected: {wifi_connected}')
"
```

**Success criteria**: See "WiFi connected" or "got ip" messages

---

### Test 3: CSI Data Flow Check
```bash
# Generate WiFi traffic
ping -i 0.1 192.168.1.255 >/dev/null 2>&1 &
PING_PID=$!

# Monitor for CSI data
timeout 10 python3 -c "
import serial, json
ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)
csi_count = 0
for i in range(100):
    line = ser.readline().decode('utf-8', errors='ignore').strip()
    if line.startswith('{'):
        try:
            data = json.loads(line)
            if 'rssi' in data and 'amp' in data:
                csi_count += 1
                print(f'CSI packet {csi_count}: RSSI={data[\"rssi\"]}')
                if csi_count >= 5:
                    break
        except: pass
ser.close()
print(f'Total CSI packets: {csi_count}')
"

# Stop ping
kill $PING_PID
```

**Success criteria**: Receive 5+ CSI packets with valid JSON format

---

## Known Issues and Workarounds

### Issue 1: Permissions Reset After Reconnect
**Symptom**: `Permission denied: /dev/ttyUSB0`

**Workaround**:
```bash
# Quick fix (temporary)
sudo chmod 666 /dev/ttyUSB0

# Permanent fix (add user to dialout group)
sudo usermod -a -G dialout $USER
# Then logout and login again
```

---

### Issue 2: No CSI Packets Despite WiFi Connected
**Symptom**: WiFi connects but no CSI JSON output

**Causes**:
- No WiFi traffic (CSI only generated on packet reception)
- CSI not enabled in firmware
- Wrong CSI configuration

**Fix**:
```bash
# 1. Generate WiFi traffic
ping -i 0.1 192.168.1.255 &

# 2. Check firmware has CSI enabled
cd firmware
grep "CONFIG_ESP_WIFI_CSI_ENABLED" sdkconfig

# 3. Check CSI callback is registered (in code)
grep "esp_wifi_set_csi_rx_cb" main/wifi_csi.c
```

---

### Issue 3: CSI Packet Rate Too Low
**Symptom**: Only 1 packet every 30+ seconds

**Cause**: Insufficient WiFi traffic

**Fix**:
```bash
# Generate more aggressive WiFi traffic
for i in {1..5}; do
    ping -i 0.05 192.168.1.255 &
done

# Or ping specific device
ping -i 0.05 192.168.1.1 &  # Router
```

---

## Diagnostic Commands Reference

### Quick Health Check
```bash
# All-in-one diagnostic
cd /home/luis/proyectos/DensePose-ESP32/firmware

echo "=== Hardware Check ==="
ls -l /dev/ttyUSB* || echo "No USB device found!"

echo -e "\n=== Config Check ==="
grep "CONFIG_WIFI_SSID\|CONFIG_WIFI_PASSWORD\|CONFIG_SPIRAM\|CONFIG_ESP_WIFI_CSI" sdkconfig | head -10

echo -e "\n=== Serial Test (5 seconds) ==="
timeout 5 python3 -c "
import serial
ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)
count = 0
for i in range(30):
    line = ser.readline().decode('utf-8', errors='ignore').strip()
    if line:
        count += 1
        if 'I (' in line or '{' in line:
            print(line[:100])
ser.close()
print(f'Total lines: {count}')
" 2>&1 || echo "Serial communication failed!"
```

---

## Success Indicators

### ✅ ESP32 is Healthy When:
- Serial output shows clean `I (timestamp) module: message` format
- Boot messages appear without repeating
- WiFi connects within 10 seconds
- CSI JSON data appears when WiFi traffic is present
- No continuous reboots or garbage output

### ❌ ESP32 Has Issues When:
- Garbage characters: `|p| ppppp|ppp||`
- Repeating boot messages (boot loop)
- Error messages: `E (xxx) module: ...`
- No output at all
- "Free heap" messages but nothing else

---

## Emergency Recovery Procedure

If everything else fails, follow this nuclear option:

```bash
cd /home/luis/proyectos/DensePose-ESP32/firmware
. ~/esp/esp-idf/export.sh

# 1. Full erase
idf.py -p /dev/ttyUSB0 erase-flash

# 2. Clean slate
rm -rf build sdkconfig sdkconfig.old

# 3. Reconfigure for ESP32-D0WD (no PSRAM)
idf.py set-target esp32
idf.py reconfigure

# 4. Verify config
echo "Checking critical settings..."
grep "CONFIG_WIFI_SSID" sdkconfig
grep "CONFIG_SPIRAM" sdkconfig  # Should be disabled
grep "CONFIG_ESP_WIFI_CSI_ENABLED" sdkconfig  # Should be enabled

# 5. Update WiFi credentials
sed -i 's/CONFIG_WIFI_SSID=".*"/CONFIG_WIFI_SSID="CNT-INTERNET"/' sdkconfig
sed -i 's/CONFIG_WIFI_PASSWORD=".*"/CONFIG_WIFI_PASSWORD="rrSVPSP.DLL1"/' sdkconfig

# 6. Build and flash
idf.py build
idf.py -p /dev/ttyUSB0 flash monitor
```

---

## Logging This Issue for Future Reference

### What Happened (January 1, 2026)
- ESP32 was working previously with CSI data flowing
- After hardware change/reconnection, ESP32 outputs garbage
- Shows intermittent "Free heap" messages
- No WiFi connection, no CSI data
- Multiple reflash attempts did not resolve

### What Was Tried
1. ✅ Permissions fixed (`sudo chmod 666`)
2. ✅ Multiple reflashes
3. ✅ Full clean rebuild (`idf.py fullclean`)
4. ✅ PSRAM configuration verified
5. ✅ WiFi credentials verified
6. ✅ Different baud rates tested
7. ❌ Issue persists

### Suspected Root Cause
- **Most likely**: Hardware issue (USB cable or ESP32 board fault)
- **Also possible**: Power supply insufficient
- **Less likely**: Firmware corruption requiring complete flash erase

### Recommended Next Steps
1. Try different USB cable (data-capable, not just charging)
2. Try different USB port or computer
3. Test with different ESP32 board if available
4. Full flash erase + rebuild as last software attempt

---

## Contact and Support

**Project**: DensePose-ESP32
**GitHub**: https://github.com/LuisReinoso/DensePose-ESP32
**Documentation**: See `docs/` directory

**Related Documents**:
- `docs/ESP32-Setup-Guide.md` - Complete setup guide
- `docs/Troubleshooting-Checklist.md` - Quick diagnostic checklist
- `QUICK-START.md` - 5-minute setup for working hardware

---

**Last Updated**: January 1, 2026
**Status**: Boot loop issue unresolved, awaiting hardware investigation
