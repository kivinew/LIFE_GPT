---
name: monitor-control
category: productivity
description: Turn off Windows monitor using nircmd, powercfg, or Windows API methods
---

# Monitor Control Skill

## Description
Turn off the Windows monitor using various methods: nircmd executable, Windows powercfg settings, or Windows API SendMessage. Provides fallback options when primary method fails.

## Trigger Conditions
Use when user says "turn off monitor", "отключи монитор", or requests monitor control.

## Methods (in order of preference)

### 1. nircmd (recommended — best UX)
Requires nircmd.exe installed at `%LOCALAPPDATA%\nircmd.exe`.

**Download nircmd:**
```powershell
# PowerShell (run once)
Invoke-WebRequest -Uri 'https://nirsoft.net/utils/nircmd.exe' -OutFile '$env:LOCALAPPDATA\nircmd.exe'

# Or via curl
curl -L -o '$env:LOCALAPPDATA\nircmd.exe' https://nirsoft.net/utils/nircmd.exe
```

**Usage:**
```bash
# Via script (once nircmd installed)
"%LOCALAPPDATA%\nircmd.exe" monitor off

# Via created monitor_ctl.sh
~/monitor_ctl.sh off     # contains: "%LOCALAPPDATA%\nircmd.exe" monitor off
```

### 2. Windows powercfg (no extra tools needed, always available)
Sets monitor timeout to 0 seconds (immediate turn off after inactivity).

```bash
# Set monitor timeout to 0 (AC power)
powercfg /setacvalueindex SCHEME_MIN SUB_VIDEO 0

# Set monitor timeout to 0 (DC power)
powercfg /setdcvalueindex SCHEME_MIN SUB_VIDEO 0

# Query current monitor settings
powercfg /query 2>&1 | findstr /i monitor
```

### 3. Windows API (Python, no admin needed)
Works without installing additional tools. Sends broadcast message to all windows.

```python
import ctypes

user32 = ctypes.windll.user32
HWND_BROADCAST = 0xFFFF
WM_SYSCOMMAND = 0x0112
SC_MONITORPOWER = 0xF170

# 2 = turn off, 1 = turn on, -1 = power save mode
result = user32.SendMessageW(HWND_BROADCAST, WM_SYSCOMMAND, SC_MONITORPOWER, 2)
print(f"Monitor off result: {result}")
```

**Usage:**
```bash
python -c "import ctypes; ctypes.windll.user32.SendMessageW(0xFFFF, 0x0112, 0xF170, 2)"
```

### 4. Keyboard shortcuts (built-in, no code needed)
- **Win+P** → Select "PC screen only" (extends display then turns off)
- **Fn+F4** (laptop) or **Fn+F7/F8** (display toggle key)
- **Right-click desktop** → Graphics options → Quick Shell Launch → Switch off

## Verification
Test that monitor is off by:
- Moving mouse (should not wake immediately — depends on power settings)
- Pressing any key (may wake after monitor timeout)
- Checking power LED on monitor is off

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| `nircmd not found` | Executable not downloaded | Run download command above |
| `Access denied` (powercfg) | Insufficient permissions | Run cmd as Administrator |
| Monitor turns back on | Power settings too high | Set both AC/DC timeout to 0 |
| API method fails | Windows version incompatible | Use powercfg or keyboard shortcut instead |
| `monitor_ctl.sh` not found | Script not created | Create with: `echo "%LOCALAPPDATA%\nircmd.exe" monitor off > ~/monitor_ctl.sh` |

## Usage Examples

```bash
# Method 1: nircmd (once installed)
%LOCALAPPDATA%\nircmd.exe monitor off

# Method 2: powercfg (always works)
powercfg /setacvalueindex SCHEME_MIN SUB_VIDEO 0
powercfg /setdcvalueindex SCHEME_MIN SUB_VIDEO 0

# Method 3: Python (no admin, no download)
python -c "import ctypes; ctypes.windll.user32.SendMessageW(0xFFFF, 0x0112, 0xF170, 2)"

# Method 4: Keyboard shortcut
# Win+P then ↓ twice → Enter (PC screen only)
```

## Dependencies
- nircmd.exe (optional — method 1)
- Admin privileges (optional — method 2 may need for some schemes)
- Python 3.x with ctypes (optional — method 3)

## Installation
1. **One-time nircmd download** (run as Administrator or user):
   ```powershell
   Invoke-WebRequest -Uri 'https://nirsoft.net/utils/nircmd.exe' -OutFile '$env:LOCALAPPDATA\nircmd.exe'
   ```

2. **Create monitor_ctl.sh** (for bash compatibility):
   ```bash
   echo "%LOCALAPPDATA%\nircmd.exe" monitor off > ~/monitor_ctl.sh
   chmod +x ~/monitor_ctl.sh
   ```

3. **Skill auto-loads** — no manual installation needed for Hermes Agent