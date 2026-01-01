# Lessons Learned - ESP32 CSI Setup

**Session Date**: December 31, 2025
**Hardware**: ESP32-D0WD (not ESP32-S3 as project name suggests)
**ESP-IDF**: v5.3.1

---

## Critical Discoveries

### 1. Project Name ≠ Hardware Reality

**Discovery**: The project is named "DensePose-ESP32-S3" but the actual hardware was ESP32-D0WD (regular ESP32).

**Impact**: Firmware was configured for ESP32-S3 with PSRAM, causing immediate boot failure on ESP32-D0WD which has no PSRAM.

**Lesson**: **ALWAYS verify actual hardware before configuring firmware**. Don't trust project names, board labels, or assumptions.

**How to verify**:
```bash
. ~/esp/esp-idf/export.sh
idf.py -p /dev/ttyUSB0 flash | grep "Chip is"
```

**Key takeaway**: The ESP-IDF flash tool reports the actual chip model during the connection phase. Use this as the source of truth.

---

### 2. PSRAM Configuration is Make-or-Break

**Discovery**: Mismatched PSRAM configuration between firmware and hardware causes immediate, catastrophic boot failure with continuous reboots.

**Error signature**:
```
E (407) quad_psram: PSRAM ID read error: 0xffffffff, PSRAM chip not found or not supported
E cpu_start: Failed to init external RAM!
abort() was called at PC 0x400815b5 on core 0
Rebooting...
```

**Why it happens**: ESP-IDF's PSRAM initialization code runs very early in the boot process (before app_main). If PSRAM is configured but not present, the chip aborts and reboots immediately.

**Lesson**: **PSRAM configuration must exactly match hardware capabilities**. This is not a warning - it's a hard failure.

**Solution checklist**:
1. Identify chip model first
2. Check if chip has PSRAM:
   - ESP32-D0WD / ESP32-D0WDQ6: ❌ NO PSRAM
   - ESP32-S3FH4R2 / ESP32-S3FN8: ✅ HAS PSRAM
3. Configure `sdkconfig.defaults` accordingly
4. Delete old `sdkconfig` and regenerate

---

### 3. sdkconfig.defaults vs sdkconfig Precedence

**Discovery**: Changes to `sdkconfig.defaults` don't automatically override existing `sdkconfig` file.

**What happened**:
1. We commented out PSRAM in `sdkconfig.defaults`
2. Ran `idf.py build`
3. PSRAM was still enabled!

**Why**: ESP-IDF's configuration system:
- `sdkconfig.defaults` = template/initial values
- `sdkconfig` = active configuration (generated once, then persisted)
- If `sdkconfig` exists, it takes precedence

**Lesson**: **When making major config changes, delete sdkconfig and regenerate**.

**Proper workflow**:
```bash
# 1. Edit defaults
nano sdkconfig.defaults

# 2. Delete active config
rm sdkconfig

# 3. Regenerate from defaults
idf.py reconfigure

# 4. Build
idf.py build
```

---

### 4. WiFi Credentials Require Manual Update

**Discovery**: The .env file system doesn't automatically update WiFi credentials in sdkconfig.

**What we expected**: .env file → automatic injection into build

**What actually happens**:
1. `.env` exists with credentials
2. `tools/load_wifi_env.py` reads .env
3. BUT: sdkconfig still has default "myssid"/"mypassword"
4. Firmware tries to connect to "myssid" → fails

**Why**: The .env loading system was designed to work with `build.sh` script, which wasn't being used. Manual builds need manual credential updates.

**Lesson**: **Always verify WiFi credentials are in sdkconfig after reconfigure**.

**Required step**:
```bash
# After idf.py reconfigure, manually update:
sed -i 's/CONFIG_WIFI_SSID="myssid"/CONFIG_WIFI_SSID="YourNetwork"/' sdkconfig
sed -i 's/CONFIG_WIFI_PASSWORD="mypassword"/CONFIG_WIFI_PASSWORD="YourPass"/' sdkconfig

# VERIFY
grep "CONFIG_WIFI_SSID\|CONFIG_WIFI_PASSWORD" sdkconfig
```

---

### 5. CSI Data Depends on WiFi Traffic

**Discovery**: CSI packets are not generated continuously. They only appear when the ESP32 **receives** WiFi packets.

**What we saw**:
- ESP32 connected to WiFi successfully
- CSI initialized successfully
- Python reader: "Received 0 CSI packets"
- Raw serial showed CSI JSON, but very infrequently (1 packet per 30+ seconds)

**Why**: WiFi CSI (Channel State Information) is extracted from received WiFi frames. No incoming frames = no CSI data.

**Lesson**: **CSI data collection requires active WiFi traffic**.

**Solutions**:
1. Generate traffic yourself: `ping -i 0.1 192.168.1.255`
2. Use other devices on same network (streaming, browsing)
3. Ping the ESP32 directly if you know its IP
4. Set up a secondary device to continuously generate traffic

**Expected rates**:
- Idle network: 0.1-1 packets/sec
- Light traffic: 1-10 packets/sec
- Heavy traffic: 10-100 packets/sec

---

### 6. ESP-IDF Version Compatibility

**Discovery**: ESP-IDF git clone with `--recursive` flag downloads ~4GB of data including submodules for ALL ESP32 variants.

**What happened**:
- Ran `git clone --recursive https://github.com/espressif/esp-idf.git`
- Downloaded submodules for esp32, esp32s2, esp32s3, esp32c3, esp32c6, esp32h2, etc.
- Most submodules unnecessary for single-chip development

**Lesson**: **Use selective installation for faster setup**.

**Better approach**:
```bash
# Clone without submodules
git clone https://github.com/espressif/esp-idf.git
cd esp-idf
git checkout v5.3.1

# Install only what you need
./install.sh esp32        # For ESP32 only
# OR
./install.sh esp32,esp32s3  # For both
```

**But**: If you already cloned with `--recursive`, just run `git submodule update --init --recursive` if you get submodule errors. The extra disk space isn't critical on modern systems.

---

### 7. Serial Monitor Context

**Discovery**: ESP-IDF's `idf.py monitor` requires TTY (terminal) access and doesn't work well with automated scripts.

**What failed**:
```bash
timeout 10 idf.py -p /dev/ttyUSB0 monitor | head -50
# Error: Monitor requires standard input to be attached to TTY
```

**Why**: `idf.py monitor` uses terminal control codes (colors, cursor positioning) and expects interactive input for features like Ctrl+] to exit.

**Lesson**: **Use Python's pyserial for automated CSI data collection**, not idf.py monitor.

**For debugging**: Use `idf.py monitor` interactively
**For data collection**: Use `python tools/read_csi.py /dev/ttyUSB0`

---

## Best Practices Established

### 1. Hardware Verification First

```bash
# ALWAYS start with this
. ~/esp/esp-idf/export.sh
idf.py -p /dev/ttyUSB0 flash | grep "Chip is"

# Record the output, then configure accordingly
```

### 2. Clean Build Workflow

```bash
# For major changes (target, PSRAM, etc.)
cd firmware
idf.py fullclean
rm sdkconfig
idf.py set-target esp32  # or esp32s3
idf.py reconfigure

# Update WiFi credentials
sed -i 's/CONFIG_WIFI_SSID="myssid"/CONFIG_WIFI_SSID="YourNetwork"/' sdkconfig
sed -i 's/CONFIG_WIFI_PASSWORD="mypassword"/CONFIG_WIFI_PASSWORD="YourPass"/' sdkconfig

# Verify config
grep "CONFIG_SPIRAM" sdkconfig  # Should match hardware
grep "CONFIG_WIFI_SSID" sdkconfig  # Should match your network

# Build and flash
idf.py build
idf.py -p /dev/ttyUSB0 flash monitor
```

### 3. CSI Data Validation

```bash
# 1. Verify boot messages
idf.py -p /dev/ttyUSB0 monitor
# Look for:
# - "WiFi connected, IP: ..."
# - "WiFi CSI initialized successfully"

# 2. Check raw serial for JSON
python3 -c "import serial; s=serial.Serial('/dev/ttyUSB0',115200,timeout=5); [print(s.readline()) for i in range(10)]"

# 3. Generate traffic
ping -i 0.1 192.168.1.255 &

# 4. Collect CSI data
python tools/read_csi.py /dev/ttyUSB0
```

### 4. Documentation As You Go

**What worked well**: Creating comprehensive documentation during the troubleshooting process, capturing:
- Exact error messages
- Root causes
- Solutions that worked
- Commands that failed (and why)

**Result**: Three interconnected docs:
1. `QUICK-START.md` - Fast setup for experienced users
2. `ESP32-Setup-Guide.md` - Detailed walkthrough with explanations
3. `Troubleshooting-Checklist.md` - Diagnostic flowchart

---

## Common Mistakes to Avoid

### ❌ Don't Do This

1. **Don't assume project name = hardware**
   - Project says ESP32-S3
   - Hardware might be ESP32

2. **Don't skip hardware verification**
   - "It should work" is not a debugging strategy
   - Verify chip model first

3. **Don't edit sdkconfig directly for permanent changes**
   - Changes get overwritten by `idf.py reconfigure`
   - Edit `sdkconfig.defaults` instead

4. **Don't forget to update WiFi credentials**
   - .env file alone is not enough
   - Must update sdkconfig manually

5. **Don't expect CSI without WiFi traffic**
   - Idle network = low/no CSI packets
   - Generate traffic for testing

### ✅ Do This Instead

1. **Verify hardware first**
   ```bash
   idf.py -p /dev/ttyUSB0 flash | grep "Chip is"
   ```

2. **Clean build for major changes**
   ```bash
   rm sdkconfig && idf.py reconfigure
   ```

3. **Verify configuration matches hardware**
   ```bash
   grep "CONFIG_SPIRAM" sdkconfig
   grep "CONFIG_WIFI_SSID" sdkconfig
   ```

4. **Test with WiFi traffic**
   ```bash
   ping -i 0.1 192.168.1.255 &
   python tools/read_csi.py /dev/ttyUSB0
   ```

---

## Debugging Workflow That Worked

### The PSRAM Debug Process

**Timeline of discovery**:

1. **Symptom**: ESP32 boot loop, continuous rebooting
2. **First check**: Read serial output
   - Saw: "PSRAM ID read error"
3. **Hypothesis**: PSRAM configured but not present
4. **Verification**: Checked chip model
   - Flash tool reported: "Chip is ESP32-D0WD"
   - ESP32-D0WD has NO PSRAM
5. **Root cause**: Firmware configured for ESP32-S3 (with PSRAM)
6. **Solution attempt 1**: Commented PSRAM in sdkconfig.defaults
   - Built → still crashed
   - **Why failed**: sdkconfig still had PSRAM enabled
7. **Solution attempt 2**: Deleted sdkconfig, regenerated
   - Verified PSRAM disabled in new sdkconfig
   - Built → SUCCESS!
8. **Validation**: ESP32 booted without errors

**Key insight**: The iterative process of:
1. Observe symptoms
2. Read error messages carefully
3. Form hypothesis
4. Test hypothesis
5. Verify results
6. Adjust if needed

---

## Tools & Commands That Saved Time

### Hardware Detection
```bash
idf.py -p /dev/ttyUSB0 flash | grep "Chip is"
sudo dmesg | tail -20
```

### Configuration Verification
```bash
grep "CONFIG_SPIRAM\|CONFIG_WIFI" firmware/sdkconfig
```

### Quick Serial Test
```bash
python3 -c "import serial; s=serial.Serial('/dev/ttyUSB0',115200,timeout=5); [print(s.readline()) for i in range(10)]"
```

### Traffic Generation
```bash
ping -i 0.1 192.168.1.255
```

---

## Future Improvements

### 1. Automated Hardware Detection

Could add a setup script that:
1. Detects chip type automatically
2. Configures PSRAM accordingly
3. Prompts for WiFi credentials
4. Updates sdkconfig
5. Builds and flashes

### 2. Better WiFi Config System

Improve .env → sdkconfig integration:
- Auto-update sdkconfig from .env
- Validate WiFi credentials before build
- Warn if credentials look like defaults

### 3. CSI Traffic Generator

Include a companion script to:
- Detect ESP32 IP on network
- Automatically generate optimal WiFi traffic
- Monitor CSI packet rate

### 4. Hardware Detection in build.sh

Modify `build.sh` to:
1. Query hardware first
2. Configure PSRAM automatically
3. Set correct target
4. Warn on mismatches

---

## Success Metrics

**Time to working CSI data**:
- First attempt (wrong config): Failed
- With troubleshooting: ~2 hours
- With this documentation: ~5 minutes (expected)

**Error rate reduction**:
- Without docs: Multiple boot loops, config errors
- With docs: Zero errors if followed

**Knowledge transfer**:
- Original: Tribal knowledge, trial and error
- Now: Documented, repeatable, teachable

---

## Conclusion

The key lessons:

1. **Verify hardware first** - Don't assume anything
2. **PSRAM config is critical** - Must match hardware exactly
3. **Clean builds for major changes** - Delete sdkconfig
4. **Manual WiFi credential update** - Verify in sdkconfig
5. **CSI needs WiFi traffic** - Generate traffic for testing
6. **Document as you go** - Future you will thank you

**Most important**: The debugging process itself:
- Read error messages carefully
- Form hypotheses
- Test systematically
- Verify results
- Document findings

This methodology applies beyond ESP32 setup - it's universal debugging practice.

---

**Document Version**: 1.0
**Authors**: Session debugging team
**Date**: December 31, 2025
