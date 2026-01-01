# Documentation Index

Quick navigation guide for all DensePose-ESP32 documentation.

---

## Quick Links by User Type

### 🚀 I'm New - Just Want CSI Data Working
**Start here**: [`../QUICK-START.md`](../QUICK-START.md)
- 5-minute setup
- Minimal explanation
- Get running fast

### 🔧 I'm Setting Up Multiple ESP32s
**Best guide**: [`ESP32-Setup-Guide.md`](ESP32-Setup-Guide.md)
- Complete walkthrough
- Hardware identification
- All configuration steps
- Testing procedures

### 🐛 Something's Not Working
**Troubleshooting**: [`Troubleshooting-Checklist.md`](Troubleshooting-Checklist.md)
- Diagnostic flowchart
- Pre-flash checklist
- Common errors & fixes
- Quick commands

### 📚 I Want to Understand What Happened
**Context**: [`LESSONS-LEARNED.md`](LESSONS-LEARNED.md)
- Critical discoveries
- Why things failed
- Best practices
- Debugging methodology

---

## Documentation Structure

```
DensePose-ESP32/
│
├── QUICK-START.md              ⚡ START HERE (5 min)
├── README.md                    📖 Project overview
├── SESSION-SUMMARY.md           📊 What was accomplished
│
└── docs/
    ├── INDEX.md                 📑 This file
    │
    ├── ESP32-Setup-Guide.md     📘 Complete setup (30 min read)
    ├── Troubleshooting-Checklist.md  🔍 Diagnostic steps
    ├── LESSONS-LEARNED.md       🎓 Session insights
    │
    ├── DensePose-WiFi-Paper.md  📄 Research background
    ├── ESP32-S3-Hardware-Reference.md  🔧 Hardware specs
    └── WiFi-Configuration.md    📡 WiFi setup details
```

---

## Documentation by Task

### Setting Up a New ESP32

1. **Quick setup** (experienced users)
   - [`../QUICK-START.md`](../QUICK-START.md)
   - Time: 5 minutes

2. **Detailed setup** (first time or issues)
   - [`ESP32-Setup-Guide.md`](ESP32-Setup-Guide.md)
   - Time: 30 minutes

### Troubleshooting Issues

1. **Pre-flash problems** (won't flash, boot loop)
   - [`Troubleshooting-Checklist.md`](Troubleshooting-Checklist.md) → Pre-Flash Checklist

2. **WiFi problems** (won't connect)
   - [`Troubleshooting-Checklist.md`](Troubleshooting-Checklist.md) → WiFi Section
   - [`ESP32-Setup-Guide.md`](ESP32-Setup-Guide.md) → "Wrong WiFi Credentials"

3. **No CSI data**
   - [`Troubleshooting-Checklist.md`](Troubleshooting-Checklist.md) → CSI Checklist
   - [`ESP32-Setup-Guide.md`](ESP32-Setup-Guide.md) → "No CSI Packets Received"

### Understanding the System

1. **How CSI works**
   - [`DensePose-WiFi-Paper.md`](DensePose-WiFi-Paper.md)
   - [`../README.md`](../README.md) → "How It Works"

2. **Hardware capabilities**
   - [`ESP32-S3-Hardware-Reference.md`](ESP32-S3-Hardware-Reference.md)

3. **WiFi configuration system**
   - [`WiFi-Configuration.md`](WiFi-Configuration.md)

### Learning from This Project

1. **What we learned debugging**
   - [`LESSONS-LEARNED.md`](LESSONS-LEARNED.md)

2. **Session summary**
   - [`../SESSION-SUMMARY.md`](../SESSION-SUMMARY.md)

---

## Common Questions

**Q: My ESP32 keeps rebooting, what do I do?**
→ [`ESP32-Setup-Guide.md`](ESP32-Setup-Guide.md) → "PSRAM Boot Loop"

**Q: How do I set up a new ESP32 quickly?**
→ [`../QUICK-START.md`](../QUICK-START.md)

**Q: WiFi won't connect, tried everything**
→ [`Troubleshooting-Checklist.md`](Troubleshooting-Checklist.md) → Build Checklist → Step 4

**Q: I get no CSI data packets**
→ [`ESP32-Setup-Guide.md`](ESP32-Setup-Guide.md) → "No CSI Packets Received"

**Q: What hardware do I need?**
→ [`ESP32-S3-Hardware-Reference.md`](ESP32-S3-Hardware-Reference.md)

**Q: How do I verify my chip type?**
→ [`ESP32-Setup-Guide.md`](ESP32-Setup-Guide.md) → "Hardware Identification"

**Q: What did you learn from debugging this?**
→ [`LESSONS-LEARNED.md`](LESSONS-LEARNED.md)

**Q: Where's the code?**
→ [`../firmware/`](../firmware/) - ESP-IDF project
→ [`../tools/`](../tools/) - Python CSI reader

---

## Documentation Symbols

| Symbol | Meaning |
|--------|---------|
| ⚡ | Quick start - minimal reading |
| 📘 | Comprehensive guide - detailed |
| 🔍 | Diagnostic/troubleshooting |
| 🎓 | Learning/insights |
| 📖 | Overview/reference |
| 🔧 | Hardware/technical specs |
| 📡 | WiFi/networking |
| 📄 | Research/background |

---

## Recommended Reading Order

### For First-Time Setup

1. [`../QUICK-START.md`](../QUICK-START.md) - Get overview (2 min)
2. [`ESP32-Setup-Guide.md`](ESP32-Setup-Guide.md) → "Hardware Identification" (5 min)
3. [`ESP32-Setup-Guide.md`](ESP32-Setup-Guide.md) → "Quick Setup Steps" (15 min)
4. [`Troubleshooting-Checklist.md`](Troubleshooting-Checklist.md) - Keep handy

### For Understanding the System

1. [`../README.md`](../README.md) - Project overview
2. [`DensePose-WiFi-Paper.md`](DensePose-WiFi-Paper.md) - Research background
3. [`ESP32-S3-Hardware-Reference.md`](ESP32-S3-Hardware-Reference.md) - Hardware
4. [`LESSONS-LEARNED.md`](LESSONS-LEARNED.md) - Real-world insights

### For Debugging Issues

1. Identify symptom
2. Check [`Troubleshooting-Checklist.md`](Troubleshooting-Checklist.md) - Find symptom
3. Follow steps in checklist
4. If needed, see [`ESP32-Setup-Guide.md`](ESP32-Setup-Guide.md) for detailed explanation
5. If still stuck, review [`LESSONS-LEARNED.md`](LESSONS-LEARNED.md) for similar issues

---

## File Modification History

**Created December 31, 2025**:
- `../QUICK-START.md`
- `ESP32-Setup-Guide.md`
- `Troubleshooting-Checklist.md`
- `LESSONS-LEARNED.md`
- `../SESSION-SUMMARY.md`
- `INDEX.md` (this file)

**Updated December 31, 2025**:
- `../README.md` - Added troubleshooting and doc links
- `../firmware/sdkconfig.defaults` - Disabled PSRAM
- `../firmware/sdkconfig` - Updated WiFi credentials

---

## External References

- **ESP-IDF Documentation**: https://docs.espressif.com/projects/esp-idf/en/v5.3.1/esp32/
- **WiFi CSI Guide**: https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-guides/wifi.html#wi-fi-channel-state-information
- **DensePose Paper**: https://arxiv.org/abs/2301.00250
- **Waveshare ESP32-S3-Zero**: https://www.waveshare.com/wiki/ESP32-S3-Zero

---

## Contributing to Documentation

If you find issues or have improvements:

1. Note the specific doc file and section
2. Describe the issue or improvement
3. If possible, suggest the fix
4. Update the doc (if you have access)
5. Update "Last Updated" date

**Documentation Standard**:
- Clear, concise language
- Step-by-step instructions
- Command examples with expected output
- Screenshots where helpful
- Version information

---

**Index Version**: 1.0
**Last Updated**: December 31, 2025
**Covers**: DensePose-ESP32 Phase 2 completion
