# ⚡ Xray Lite

<div align="center">

**The ultra-lightweight, zero-bloat Windows front-end for [Xray-core](https://github.com/XTLS/Xray-core) (VLESS + Reality over TCP).**

[![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011-0078D6?logo=windows&logoColor=white)](https://github.com/YehenSilva/Xray-lite)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![License: MPL 2.0](https://img.shields.io/badge/License-MPL%202.0-blue.svg)](LICENSE)
[![Memory Footprint](https://img.shields.io/badge/RAM%20Footprint-%7E22%20MB%20Total-success?logo=speedtest&logoColor=white)](assets/memory_comparison_chart.png)
[![Idle CPU](https://img.shields.io/badge/Idle%20CPU-0.0%25-brightgreen)](assets/taskmanager_comparison.png)
[![Bloatware](https://img.shields.io/badge/Bloatware%20%26%20Ads-0%25-green)](https://github.com/YehenSilva/Xray-lite)

<p align="center">
  <a href="#-why-xray-lite-the-problem-with-netmod--incy">Why Xray Lite?</a> •
  <a href="#-interface-overview">Interface Overview</a> •
  <a href="#-resource-benchmarks">Resource Benchmarks</a> •
  <a href="#-features">Features</a> •
  <a href="#-quick-start">Quick Start</a> •
  <a href="#-how-it-works">How It Works</a> •
  <a href="#-building-from-source">Build</a>
</p>

![Xray Lite Preview](assets/app_ui_preview.png)

</div>

---

## 🖥️ Interface Overview

Xray Lite provides a clean, native Windows Tkinter interface with zero unnecessary graphics rendering overhead:

* **Connected State (Active)**: Displays active connection status, listening ports (SOCKS5 `20808` / HTTP `20809`), and one-click disconnection.
* **Disconnected State (Ready)**: Stores your connection URI securely in `settings.json` and supports instant one-click connection.
* **Windows System Tray Integration**: Minimizes silently to the Windows notification tray with an active status icon (`Green` = Connected, `Grey` = Disconnected) and context menu (`Show`, `Disconnect`, `Quit`).
* **Instant Memory Trim**: Automatically trims working set memory pages down to **~4.1 MB** whenever minimized to the tray.

---

## 🧐 Why Xray Lite? (The Problem with NetMod & INCY)

Most modern proxy clients have become bloated, sluggish resource hogs. If you've used clients like **NetMod (NetMod Syna)**, **INCY**, or heavy Electron/Chromium-based wrappers, you have probably noticed high memory usage, background clutter, and battery drain:

* 🐢 **NetMod (NetMod Syna)**:
  * Packed with a heavy .NET runtime and persistent background services.
  * Consistently drains **150 MB – 260 MB+ of RAM** just idling in the background.
  * Spikes CPU usage during connection handshakes and ping loops.
  * Lacks active memory-trimming routines—it hoards allocated memory even when hidden in the system tray.
  * Contains ads, donation banners, and complex, confusing menus.

* 📦 **INCY & Electron Clients (v2rayN / Mihomo Party / Clash Verge)**:
  * Run entire multi-process Chromium rendering engines and NodeJS runtimes merely to toggle a proxy switch.
  * Idle memory footprint sits at **180 MB – 380 MB+ RAM** across multiple renderer and helper processes.
  * Causes thermal throttling and accelerates battery drain on laptops.

### 💡 The Solution: Xray Lite
**Xray Lite was engineered from the ground up for maximum performance and zero overhead:**
1. **Total Combined Footprint: ~22.3 MB**: The entire application (native GUI + backend `xray.exe`) runs in less than **25 MB RAM total**—over **90% less memory** than NetMod or INCY.
2. **0.0% Idle CPU**: Pure event-driven native Win32 system tray loop with no background polling spikes.
3. **Instant Launch (< 0.4s)**: No Electron startup delay, no .NET JIT initialization delay.
4. **Zero Bloat & Zero Telemetry**: Clean native GUI, no ads, no trackers, no extraneous background daemons.

---

## 📊 Resource Benchmarks

### 1. Windows Task Manager Comparison
Verified on Windows 11 x64 under active VLESS + Reality traffic:

![Task Manager Comparison](assets/taskmanager_comparison.png)

### 2. RAM Consumption Comparison (Lower is Better)

![RAM Footprint Chart](assets/memory_comparison_chart.png)

### 3. Detailed Metrics Table

| Metric | ⚡ **Xray Lite** (This App) | 📱 **INCY Client** | ⚙️ **NetMod Syna** | 🖥️ **v2rayN (.NET)** | 🌐 **Electron Clients** |
|:---|:---:|:---:|:---:|:---:|:---:|
| **RAM (Minimized to Tray)** | **~22.3 MB** *(4.1 MB GUI + 18.2 MB Core)* | ~188.4 MB | ~245.8 MB | ~164.2 MB | ~385.0 MB |
| **RAM (Active Window)** | **~29.5 MB** | ~210.0 MB | ~260.0 MB | ~195.0 MB | ~410.0 MB |
| **Idle CPU Usage** | **0.0%** | 0.8% – 1.5% | 1.2% – 2.5% | 0.4% – 1.0% | 1.5% – 3.2% |
| **Cold Startup Time** | **< 0.4 seconds** | 3.5 – 6.0 s | 4.0 – 7.0 s | 2.5 – 4.5 s | 5.0 – 9.0 s |
| **Framework / Stack** | Pure Tkinter + Win32 API | Electron / WebView | .NET / Mixed | .NET 8 WPF + WebView2 | Chromium / Node.js |
| **OS Memory Trimming** | **Yes (`EmptyWorkingSet`)** | ❌ No | ❌ No | ⚠️ Partial | ❌ No |
| **Adware / Banners** | **None (100% Clean)** | None | ⚠️ High (Banners/Ads) | None | Varies |
| **Background Processes** | **Only 2 (`XrayLite` + `xray`)** | 4 – 6 Processes | 3 – 5 Services | 3 – 4 Processes | 6 – 10 Processes |

---

## ⚙️ How Xray Lite Stays Under 25MB

Xray Lite achieves its ultra-compact memory footprint through two intentional low-level optimizations:

1. **Windows Working Set Memory Trimming (`psapi.EmptyWorkingSet`)**:
   ```python
   def trim_memory():
       """Hand this process's idle pages back to Windows kernel."""
       k32, psapi = ctypes.WinDLL("kernel32"), ctypes.WinDLL("psapi")
       k32.GetCurrentProcess.restype = ctypes.c_void_p
       psapi.EmptyWorkingSet.argtypes = [ctypes.c_void_p]
       psapi.EmptyWorkingSet(k32.GetCurrentProcess())
   ```
   Whenever Xray Lite minimizes to the system tray, it instructs the Windows memory manager to reclaim any unused heap pages, shrinking the GUI process footprint to **~4.1 MB**.

2. **Aggressive Go Garbage Collection (`GOGC=50`)**:
   ```python
   self.proc = subprocess.Popen(
       [XRAY, "run", "-c", CFG],
       env=dict(os.environ, GOGC="50")  # tighter Go GC -> less RAM
   )
   ```
   By default, Go runtimes hoard memory heap until footprint doubles (`GOGC=100`). Setting `GOGC=50` commands the Go runtime inside `xray.exe` to trigger garbage collection twice as aggressively, keeping core engine RAM down to **~18.2 MB**.

---

## ✨ Features

- **⚡ VLESS + Reality over TCP**: Built specifically for modern, censorship-resistant anti-censorship protocols.
- **🔗 Instant Link Import**: Paste your standard `vless://` configuration link directly.
- **🛡️ 1-Click System Proxy**: Automatically toggles Windows Internet Settings (`ProxyEnable` and `ProxyServer`) with instant `wininet` broadcast updates.
- **🔕 System Tray Integration**: Minimizes silently to the Windows notification tray with color-coded status badges (Green = Connected, Grey = Disconnected).
- **🚀 Auto-Connect on Launch**: Configure it once, check *Auto-connect on launch*, and have it start silently minimized on boot.
- **🔒 Single-Instance Protection**: Uses a native Windows Kernel Mutex (`XrayLiteSingleInstance`) to prevent duplicate instances from conflicting.
- **🔌 Dual Inbound Ports**:
  - **SOCKS5**: `127.0.0.1:20808` (with full UDP support)
  - **HTTP Proxy**: `127.0.0.1:20809`
- **📝 Automatic Diagnostics**: Redirects runtime events and connection errors directly to `xray.log` for instant troubleshooting.

---

## 🚀 Quick Start

### Option 1: Use Pre-Built Binary (Recommended)

1. Download `XrayLite.exe` from the [Releases](https://github.com/YehenSilva/Xray-lite/releases) page.
2. Download official `xray.exe` from the [XTLS/Xray-core releases](https://github.com/XTLS/Xray-core/releases) (or extract from your existing Xray folder).
3. Place `xray.exe` in the same directory as `XrayLite.exe`:
   ```text
   C:\xray\
   ├── XrayLite.exe
   ├── xray.exe
   └── icon.ico (optional)
   ```
4. Double-click `XrayLite.exe`.
5. Paste your `vless://` link and click **Connect**.

---

### Option 2: Run from Python Source

#### Prerequisites
- Windows 10 or Windows 11
- Python 3.10 or higher
- Official `xray.exe` binary in the repository folder

#### Installation Steps
```bash
# 1. Clone repository
git clone https://github.com/YehenSilva/Xray-lite.git
cd Xray-lite

# 2. Create virtual environment
python -m venv .venv
.venv\Scripts\activate

# 3. Install lightweight dependencies
pip install -r requirements.txt

# 4. Run application without terminal window
pythonw xray_gui.py
```

---

## 🛠️ Building the Standalone Executable

You can compile `XrayLite.exe` yourself using PyInstaller and the provided specification file:

```bash
# Install PyInstaller
pip install pyinstaller

# Build executable
pyinstaller XrayLite.spec
```

The compiled standalone executable will be available in `dist/XrayLite.exe`.

---

## 📋 Supported Link Format

Xray Lite parses standard `vless://` URI formats configured for TCP + Reality:

```text
vless://<UUID>@<SERVER_HOST>:<PORT>?security=reality&type=tcp&fp=chrome&sni=<SNI>&pbk=<PUBLIC_KEY>&sid=<SHORT_ID>&spx=%2F&flow=xtls-rprx-vision#MyNode
```

### Supported Parameters:
* `security`: Must be `reality`
* `type`: Must be `tcp`
* `sni`: Server Name Indication (e.g. `www.microsoft.com`)
* `pbk`: Reality Public Key
* `sid`: Short ID
* `fp`: TLS Client Fingerprint (defaults to `chrome`)
* `spx`: SpiderX path (defaults to `/`)
* `flow`: (Optional) e.g. `xtls-rprx-vision`

---

## ❓ Frequently Asked Questions (FAQ)

<details>
<summary><b>Why did my connection fail with "Missing file: xray.exe not found"?</b></summary>
Xray Lite is a GUI front-end. It needs the official <code>xray.exe</code> core binary located in the same directory as <code>XrayLite.exe</code> (or <code>xray_gui.py</code>). Download it from <a href="https://github.com/XTLS/Xray-core/releases">Xray-core Releases</a>.
</details>

<details>
<summary><b>Does Xray Lite work with WebSocket (ws) or gRPC?</b></summary>
By design, Xray Lite is strictly focused on <b>VLESS + TCP + Reality</b> for maximum speed, resistance against DPI censorship, and minimal overhead.
</details>

<details>
<summary><b>How do I make Xray Lite start automatically with Windows?</b></summary>
1. Check the <b>Auto-connect on launch (starts in tray)</b> option in the GUI.<br>
2. Press <code>Win + R</code>, type <code>shell:startup</code>, and press Enter.<br>
3. Create a shortcut to <code>XrayLite.exe</code> in that startup folder. It will launch silently straight into your system tray on boot!
</details>

<details>
<summary><b>Can I route individual applications through the proxy?</b></summary>
Yes! You can configure any app (e.g. Telegram, Discord, Git, Firefox) to use either:
- <b>SOCKS5:</b> <code>127.0.0.1:20808</code>
- <b>HTTP:</b> <code>127.0.0.1:20809</code>
</details>

---

## 📄 License

This project is licensed under the [Mozilla Public License Version 2.0 (MPL-2.0)](LICENSE).

Third-party core components:
- [Xray-core](https://github.com/XTLS/Xray-core) — MPL-2.0
- [Wintun](https://www.wintun.net/) — WireGuard LLC (Optional TUN driver)

---

<div align="center">
  <sub>Engineered with minimalism in mind • Fast, Silent, & Lightweight</sub>
</div>
