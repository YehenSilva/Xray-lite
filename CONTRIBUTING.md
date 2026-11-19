# Contributing to Xray Lite

Thank you for your interest in contributing to **Xray Lite**!

Our primary design philosophy is **extreme minimalism and low resource usage**. Any PR or feature should keep RAM consumption minimal (< 25MB combined) and avoid bloated dependencies.

## Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/YehenSilva/Xray-lite.git
   cd Xray-lite
   ```

2. Set up Python (3.10+ recommended):
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Ensure `xray.exe` is in the project root directory.

4. Run from source:
   ```bash
   pythonw xray_gui.py
   ```

## Building Executables

Build the standalone binary with PyInstaller:
```bash
pyinstaller XrayLite.spec
```
The output binary will be generated in `dist/XrayLite.exe`.

## Guidelines
- Avoid heavy UI frameworks (e.g. Electron, Qt, PyQt, Chromium webviews).
- Always ensure Windows memory trimming (`EmptyWorkingSet`) is preserved when minimizing.
- Keep `GOGC=50` tuning enabled for `xray.exe`.
- Do not commit sensitive keys, links, or personal `config.json` / `settings.json` files.
