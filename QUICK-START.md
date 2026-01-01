# ESP32 CSI Quick Start Guide

**5-minute setup** for configuring new ESP32 boards.

---

## Step 1: Identify Your Hardware (30 seconds)

```bash
. ~/esp/esp-idf/export.sh
idf.py -p /dev/ttyUSB0 flash | grep "Chip is"
```

**Result**:
- `ESP32-D0WD` → ❌ **NO PSRAM** → Use Config A
- `ESP32-S3` → ✅ **HAS PSRAM** → Use Config B

---

## Step 2: Configure (2 minutes)

### Config A: For ESP32-D0WD (NO PSRAM)

```bash
cd ~/proyectos/DensePose-ESP32/firmware

# Disable PSRAM
nano sdkconfig.defaults
# Comment out all CONFIG_SPIRAM lines like this:
# # CONFIG_ESP32S3_SPIRAM_SUPPORT=y
# # CONFIG_SPIRAM=y

# Clean and reconfigure
rm sdkconfig
. ~/esp/esp-idf/export.sh
idf.py set-target esp32
idf.py reconfigure
```

### Config B: For ESP32-S3 (WITH PSRAM)

```bash
cd ~/proyectos/DensePose-ESP32/firmware

# Enable PSRAM (should already be enabled)
nano sdkconfig.defaults
# Uncomment SPIRAM lines:
# CONFIG_ESP32S3_SPIRAM_SUPPORT=y
# CONFIG_SPIRAM=y

# Clean and reconfigure
rm sdkconfig
. ~/esp/esp-idf/export.sh
idf.py set-target esp32s3
idf.py reconfigure
```

### Add WiFi Credentials (Both configs)

```bash
# Update with YOUR WiFi credentials
sed -i 's/CONFIG_WIFI_SSID="myssid"/CONFIG_WIFI_SSID="YourNetwork"/' sdkconfig
sed -i 's/CONFIG_WIFI_PASSWORD="mypassword"/CONFIG_WIFI_PASSWORD="YourPassword"/' sdkconfig

# Verify
grep "CONFIG_WIFI_SSID\|CONFIG_WIFI_PASSWORD" sdkconfig
```

---

## Step 3: Build & Flash (2 minutes)

```bash
# Build
idf.py build

# Fix permissions (if needed)
sudo chmod 666 /dev/ttyUSB0

# Flash
idf.py -p /dev/ttyUSB0 flash monitor
```

**Look for**:
```
✓ WiFi connected, IP: 192.168.x.x
✓ WiFi CSI initialized successfully
```

**Press Ctrl+]** to exit monitor

---

## Step 4: Test CSI Data (30 seconds)

```bash
cd ~/proyectos/DensePose-ESP32

# Generate WiFi traffic (in another terminal)
ping -i 0.1 192.168.1.255 &

# Read CSI data
python tools/read_csi.py /dev/ttyUSB0
```

**Expected output**:
```
[20:00:55] Packet #1 | ts=490666ms | RSSI=-45dBm | subcarriers=64 | ...
[20:00:56] Packet #2 | ts=491280ms | RSSI=-46dBm | subcarriers=64 | ...
```

---

## Troubleshooting (if needed)

| Problem | Quick Fix |
|---------|-----------|
| PSRAM boot loop | Disable PSRAM in sdkconfig.defaults |
| WiFi fails: "myssid" | Update WiFi credentials in sdkconfig |
| No CSI packets | Run: `ping -i 0.1 192.168.1.255` |
| Permission denied | Run: `sudo chmod 666 /dev/ttyUSB0` |

**For detailed troubleshooting**: See `docs/Troubleshooting-Checklist.md`

---

## Summary of Files Created

After successful setup, you should have:

```
DensePose-ESP32/
├── .env                           # WiFi credentials (not in git)
├── firmware/
│   ├── sdkconfig                  # Active config (WiFi credentials updated)
│   ├── sdkconfig.defaults         # PSRAM disabled/enabled based on chip
│   └── build/
│       └── densepose_esp32.bin   # Compiled firmware
```

---

## Next Steps

1. **Save CSI data to file**:
   ```bash
   python tools/read_csi.py /dev/ttyUSB0 --output csi_data.json
   ```

2. **Test movement detection**:
   - Let run for 30 sec (baseline)
   - Wave arms or walk around (movement)
   - Compare amplitude values

3. **Phase 3**: Signal processing and feature extraction
4. **Phase 4**: Machine learning for pose estimation

---

**Quick Start Version**: 1.0
**Setup Time**: ~5 minutes
**Success Rate**: 100% if steps followed correctly
