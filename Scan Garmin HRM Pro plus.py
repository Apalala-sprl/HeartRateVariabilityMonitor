# HRV Real-Time Visual App with BLE Device Selection and Enhanced UI
# ---------------------------------------------------
# This application detects BLE HR monitors (e.g., Garmin HRM), displays live RR data,
# a real-time HR graph, and a dynamic RMSSD chart. It includes UI elements to scan, connect,
# view status messages, and export data.

import asyncio
import threading
import tkinter as tk
from tkinter import ttk, filedialog
import numpy as np
from bleak import BleakScanner, BleakClient
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import pandas as pd
import datetime

HR_CHAR_UUID = "00002a37-0000-1000-8000-00805f9b34fb"
TARGET_KEYWORDS = ["HRM", "Garmin"]

class HRVApp:
    def __init__(self, root):
        self.root = root
        self.root.title("HRV Live Monitor")
        self.root.geometry("1400x900")
        self.root.configure(bg="#f0f0f0")

        self.devices = []
        self.selected_device = tk.StringVar()
        self.running = False
        self.client = None
        self.rr_data = []
        self.bpm_data = []
        self.timestamp_data = []
        self.rmssd_history = []
        self.df = pd.DataFrame(columns=["timestamp", "RR", "BPM"])

        self.create_widgets()
        threading.Thread(target=asyncio.run, args=(self.scan_devices(),), daemon=True).start()

    def create_widgets(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TButton", padding=6, relief="flat", background="#4a90e2", foreground="white")
        style.configure("TCombobox", padding=5, font=("Arial", 12))

        top_frame = tk.Frame(self.root, height=100, bg='#ffffff')
        top_frame.pack(fill='x', side='top')

        tk.Label(top_frame, text="Capteur HRM:", font=("Arial", 16), bg='#ffffff').pack(side='left', padx=10)
        self.device_menu = ttk.Combobox(top_frame, textvariable=self.selected_device, font=("Arial", 14), width=40)
        self.device_menu.pack(side='left')

        ttk.Button(top_frame, text="🔄 Scanner", command=lambda: threading.Thread(target=asyncio.run, args=(self.scan_devices(),), daemon=True).start()).pack(side='left', padx=10)
        ttk.Button(top_frame, text="✅ Connecter", command=self.start_monitoring).pack(side='left', padx=10)
        self.start_stop_btn = ttk.Button(top_frame, text="▶ Démarrer", command=self.toggle_run)
        self.start_stop_btn.pack(side='left', padx=10)
        ttk.Button(top_frame, text="⛔ Déconnecter", command=self.disconnect).pack(side='left', padx=10)
        ttk.Button(top_frame, text="💾 Export CSV", command=self.export_csv).pack(side='left', padx=10)

        middle_frame = tk.Frame(self.root, bg='#f0f0f0')
        middle_frame.pack(fill='both', expand=True)

        graph_frame = tk.Frame(middle_frame)
        graph_frame.pack(side='left', fill='both', expand=True, padx=5, pady=5)

        self.fig = Figure(figsize=(8, 5), dpi=100)
        self.ax_bpm = self.fig.add_subplot(211)
        self.ax_rmssd = self.fig.add_subplot(212)
        self.line_bpm, = self.ax_bpm.plot([], [], lw=2, color='blue')
        self.line_rmssd, = self.ax_rmssd.plot([], [], lw=2, color='green')

        self.ax_bpm.set_title("Fréquence cardiaque estimée (BPM)")
        self.ax_bpm.set_ylabel("BPM")
        self.ax_rmssd.set_title("RMSSD (moyenne mobile 15s)")
        self.ax_rmssd.set_ylabel("ms")

        self.canvas = FigureCanvasTkAgg(self.fig, master=graph_frame)
        self.canvas.get_tk_widget().pack(fill='both', expand=True)

        self.text_log = tk.Text(middle_frame, width=50, font=("Consolas", 11), bg="#1e1e1e", fg="#00ff00")
        self.text_log.pack(side='right', fill='y', padx=5, pady=5)

    async def scan_devices(self):
        self.log("🔍 Recherche des périphériques BLE...")
        devices = await BleakScanner.discover(timeout=5.0)
        self.devices = [d for d in devices if d.name and any(k in d.name for k in TARGET_KEYWORDS)]
        self.device_menu['values'] = [f"{d.name} @ {d.address}" for d in self.devices]
        if self.devices:
            self.device_menu.set(f"{self.devices[0].name} @ {self.devices[0].address}")
            self.log(f"✅ {len(self.devices)} capteur(s) trouvé(s). Prêt à connecter.")
        else:
            self.device_menu.set('')
            self.log("❌ Aucun capteur trouvé.")

    def log(self, message):
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.text_log.insert('end', f"[{timestamp}] {message}\n")
        self.text_log.see('end')

    def start_monitoring(self):
        selection = self.device_menu.current()
        if selection >= 0:
            device = self.devices[selection]
            self.log(f"🔗 Connexion au capteur : {device.name}")
            threading.Thread(target=asyncio.run, args=(self.connect_ble(device),), daemon=True).start()
            self.update_graph_loop()

    async def connect_ble(self, device):
        self.client = BleakClient(device)
        await self.client.__aenter__()
        await self.client.start_notify(HR_CHAR_UUID, self.handle_data)
        self.log("✅ Connecté. En attente de données...")
        while True:
            await asyncio.sleep(1)

    def handle_data(self, _, data):
        if not self.running:
            return
        flags = data[0]
        index = 1 if not flags & 0x01 else 2
        index += 1
        while index + 1 < len(data):
            rr = int.from_bytes(data[index:index+2], byteorder='little') / 1024.0
            bpm = 60.0 / rr if rr > 0 else 0
            now = datetime.datetime.now()
            self.rr_data.append(rr)
            self.bpm_data.append(bpm)
            self.timestamp_data.append(now)
            self.df.loc[len(self.df)] = [now.strftime("%H:%M:%S"), rr, bpm]
            self.log(f"{now.strftime('%H:%M:%S')} | RR: {rr:.3f} s | BPM: {bpm:.1f}")
            index += 2

    def toggle_run(self):
        self.running = not self.running
        self.start_stop_btn.config(text="⏸ Arrêter" if self.running else "▶ Démarrer")

    def disconnect(self):
        if self.client:
            asyncio.run(self.client.disconnect())
            self.client = None
            self.running = False
            self.start_stop_btn.config(text="▶ Démarrer")
            self.log("🔌 Déconnexion effectuée.")

    def update_graph_loop(self):
        if self.rr_data and self.running:
            bpm_values = self.bpm_data[-60:]
            x = list(range(len(bpm_values)))
            self.line_bpm.set_data(x, bpm_values)
            self.ax_bpm.set_xlim(0, max(60, len(bpm_values)))
            self.ax_bpm.set_ylim(min(bpm_values)*0.95, max(bpm_values)*1.05)

            # Update RMSSD every 15s
            if len(self.rr_data) >= 15:
                recent_rr = self.rr_data[-15:]
                rmssd = self.compute_rmssd(recent_rr) * 1000
                self.rmssd_history.append(rmssd)

            rmssd_x = list(range(len(self.rmssd_history)))
            self.line_rmssd.set_data(rmssd_x, self.rmssd_history)
            self.ax_rmssd.set_xlim(0, max(60, len(self.rmssd_history)))
            self.ax_rmssd.set_ylim(10, 150)
            self.canvas.draw()

        self.root.after(1000, self.update_graph_loop)

    def compute_rmssd(self, values):
        if len(values) < 2:
            return 0
        diff = np.diff(values)
        return np.sqrt(np.mean(diff**2))

    def export_csv(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if file_path:
            self.df.to_csv(file_path, index=False)
            self.log(f"💾 Données sauvegardées : {file_path}")

if __name__ == "__main__":
    root = tk.Tk()
    app = HRVApp(root)
    root.mainloop()
