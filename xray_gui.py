"""Xray Lite - tiny Tkinter front-end for xray.exe (VLESS + Reality over TCP).
Put this file next to xray.exe (e.g. C:\\xray) and run:  pythonw xray_gui.py
Needs:  pip install pystray pillow
"""
import ctypes
import json
import os
import subprocess
import sys
import tkinter as tk
import winreg
from tkinter import messagebox, ttk
from urllib.parse import parse_qs, unquote, urlparse

import pystray
from PIL import Image, ImageDraw

BASE = os.path.dirname(sys.executable if getattr(sys, "frozen", False) else os.path.abspath(__file__))
XRAY = os.path.join(BASE, "xray.exe")
CFG = os.path.join(BASE, "config.json")
LOG = os.path.join(BASE, "xray.log")
SETTINGS = os.path.join(BASE, "settings.json")
SOCKS_PORT, HTTP_PORT = 20808, 20809
REG = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"
NO_WINDOW = 0x08000000


def build_config(link):
    u = urlparse(link.strip())
    if u.scheme != "vless" or not u.username or not u.hostname or not u.port:
        raise ValueError("Not a valid vless:// link")
    q = {k: v[0] for k, v in parse_qs(u.query).items()}
    if q.get("type", "tcp") != "tcp" or q.get("security") != "reality":
        raise ValueError("Only TCP + Reality links are supported")
    user = {"id": u.username, "encryption": "none"}
    if q.get("flow"):
        user["flow"] = q["flow"]
    return {
        "log": {"loglevel": "warning"},
        "inbounds": [
            {"listen": "127.0.0.1", "port": SOCKS_PORT, "protocol": "socks", "settings": {"udp": True}},
            {"listen": "127.0.0.1", "port": HTTP_PORT, "protocol": "http"},
        ],
        "outbounds": [{
            "protocol": "vless",
            "settings": {"vnext": [{"address": u.hostname, "port": u.port, "users": [user]}]},
            "streamSettings": {
                "network": "tcp",
                "security": "reality",
                "realitySettings": {
                    "serverName": q.get("sni", ""),
                    "fingerprint": q.get("fp", "chrome"),
                    "publicKey": q.get("pbk", ""),
                    "shortId": q.get("sid", ""),
                    "spiderX": unquote(q.get("spx", "/")) or "/",  # handles double-encoded %252F
                },
            },
        }],
    }


def set_system_proxy(on):
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG, 0, winreg.KEY_SET_VALUE) as k:
        winreg.SetValueEx(k, "ProxyEnable", 0, winreg.REG_DWORD, int(on))
        if on:
            winreg.SetValueEx(k, "ProxyServer", 0, winreg.REG_SZ, f"127.0.0.1:{HTTP_PORT}")
    wininet = ctypes.windll.wininet
    wininet.InternetSetOptionW(0, 39, 0, 0)  # settings changed
    wininet.InternetSetOptionW(0, 37, 0, 0)  # refresh


def tray_image(on):
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse((4, 4, 60, 60), fill=(34, 197, 94) if on else (120, 120, 120))
    d.polygon([(35, 10), (20, 36), (31, 36), (28, 54), (44, 26), (33, 26)], fill="white")
    return img


def load_settings():
    try:
        with open(SETTINGS) as fh:
            return json.load(fh)
    except Exception:
        return {}


def trim_memory():
    """Hand this process's idle pages back to Windows (they fault back in if needed)."""
    k32, psapi = ctypes.WinDLL("kernel32"), ctypes.WinDLL("psapi")
    k32.GetCurrentProcess.restype = ctypes.c_void_p
    psapi.EmptyWorkingSet.argtypes = [ctypes.c_void_p]
    psapi.EmptyWorkingSet(k32.GetCurrentProcess())


class App:
    def __init__(self, root):
        self.root, self.proc, self.log, self.proxy_on = root, None, None, False
        root.title("Xray Lite")
        root.resizable(False, False)
        icon_path = os.path.join(BASE, "icon.ico")
        if os.path.exists(icon_path):
            try:
                root.iconbitmap(icon_path)
            except Exception:
                pass
        f = ttk.Frame(root, padding=12)
        f.pack()
        ttk.Label(f, text="vless:// link").grid(sticky="w")
        s = load_settings()
        self.link = tk.StringVar(value=s.get("link", ""))
        ttk.Entry(f, textvariable=self.link, width=46, show="\u2022").grid(pady=4)
        self.use_proxy = tk.BooleanVar(value=True)
        ttk.Checkbutton(f, text="Set Windows system proxy", variable=self.use_proxy).grid(sticky="w")
        self.auto = tk.BooleanVar(value=bool(s.get("auto")))
        ttk.Checkbutton(f, text="Auto-connect on launch (starts in tray)", variable=self.auto,
                        command=self.save).grid(sticky="w")
        self.btn = ttk.Button(f, text="Connect", command=self.toggle)
        self.btn.grid(pady=8, sticky="we")
        self.status = ttk.Label(f, text="Disconnected")
        self.status.grid()
        root.protocol("WM_DELETE_WINDOW", self.hide)  # X button -> tray
        self.tray = pystray.Icon("xraylite", tray_image(False), "Xray Lite - Disconnected", pystray.Menu(
            pystray.MenuItem("Show", lambda: root.after(0, self.show), default=True),
            pystray.MenuItem(lambda item: "Disconnect" if self.proc else "Connect",
                             lambda: root.after(0, self.toggle)),
            pystray.MenuItem("Quit", lambda: root.after(0, self.quit)),
        ))
        self.tray.run_detached()
        if self.auto.get() and self.link.get().strip():
            root.withdraw()
            root.after(300, self.connect)

    def save(self):
        with open(SETTINGS, "w") as fh:
            json.dump({"link": self.link.get().strip(), "auto": self.auto.get()}, fh)

    def hide(self):
        self.root.withdraw()
        self.root.after(500, trim_memory)

    def show(self):
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def refresh(self, on):
        self.tray.icon = tray_image(on)
        self.tray.title = "Xray Lite - " + ("Connected" if on else "Disconnected")
        self.tray.update_menu()

    def toggle(self):
        self.disconnect() if self.proc else self.connect()

    def connect(self):
        if not os.path.exists(XRAY):
            return messagebox.showerror("Missing file", f"xray.exe not found in:\n{BASE}")
        try:
            cfg = build_config(self.link.get())
        except Exception as e:
            return messagebox.showerror("Bad link", str(e))
        with open(CFG, "w") as fh:
            json.dump(cfg, fh, indent=2)
        self.save()
        self.log = open(LOG, "w")
        self.proc = subprocess.Popen([XRAY, "run", "-c", CFG], cwd=BASE, stdout=self.log,
                                     stderr=self.log, creationflags=NO_WINDOW,
                                     env=dict(os.environ, GOGC="50"))  # tighter Go GC -> less RAM
        self.status.config(text="Connecting...")
        self.root.after(800, self.verify)

    def verify(self):
        if self.proc and self.proc.poll() is not None:
            self.cleanup()
            try:
                tail = "".join(open(LOG).readlines()[-6:])
            except Exception:
                tail = "unknown error"
            return messagebox.showerror("Xray failed to start", tail)
        if self.use_proxy.get():
            set_system_proxy(True)
            self.proxy_on = True
        self.btn.config(text="Disconnect")
        self.status.config(text=f"Connected  (SOCKS {SOCKS_PORT} / HTTP {HTTP_PORT})")
        self.refresh(True)
        if not self.root.winfo_viewable():  # started hidden (auto-connect)
            self.root.after(500, trim_memory)
        self.root.after(3000, self.watch)

    def watch(self):
        if self.proc and self.proc.poll() is not None:
            self.disconnect()
            messagebox.showwarning("Xray stopped", "The Xray process exited unexpectedly.")
        elif self.proc:
            self.root.after(3000, self.watch)

    def cleanup(self):
        if self.proxy_on:
            set_system_proxy(False)
            self.proxy_on = False
        if self.log:
            self.log.close()
            self.log = None
        self.proc = None
        self.btn.config(text="Connect")
        self.status.config(text="Disconnected")
        self.refresh(False)

    def disconnect(self):
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(2)
            except subprocess.TimeoutExpired:
                self.proc.kill()
        self.cleanup()

    def quit(self):
        self.disconnect()
        self.tray.stop()
        self.root.destroy()


if __name__ == "__main__":
    _mutex = ctypes.windll.kernel32.CreateMutexW(None, False, "XrayLiteSingleInstance")
    if ctypes.windll.kernel32.GetLastError() == 183:  # already running
        sys.exit(0)
    root = tk.Tk()
    App(root)
    root.mainloop()
