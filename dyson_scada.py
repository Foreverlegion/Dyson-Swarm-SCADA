import tkinter as tk
from tkinter import ttk
import math
import random
from collections import deque

AU_SCALE = 350
TRACK_RADIUS_AU = 0.3
TOTAL_VEHICLES = 150000
TOTAL_STATIONS = 3000
MAX_DEMAND_TW = 100.0
SIM_VEHICLES = 300
SIM_STATIONS = 400

class SIT_Master_SCADA:
    def __init__(self, root):
        self.root = root
        self.root.title("SIT-OS v6.2 | FULL SYSTEM TELEMETRY & CONTROL")
        self.root.geometry("1600x950")
        self.root.configure(bg="#050505")

        self.zoom = 1.0
        self.offset_x, self.offset_y = 0, 0
        self.selected_asset = None
        self.asset_type = "VEHICLE"
        self.vehicles = []
        self.stations = []
        
        self.power_history = deque([0.0]*100, maxlen=100)
        self.demand_history = deque([0.0]*100, maxlen=100)
        
        self.total_ticks = 0
        self.cum_output = 0.0
        self.cum_demand = 0.0
        self.cum_kin = 0.0
        self.cum_thm = 0.0
        self.cum_eff = 0.0
        
        self.uptime = 99.9998
        self.grid_demand = 0.0
        self.lunar_buffer_pj = 0.0
        self.lunar_capacity_pj = 1000000.0 # 1000 EJ
        self.moon_theta = random.uniform(0, 6.28)
        self.sim_time = 0.0

        self.setup_ui()
        self.init_infrastructure()
        self.run_sim()

    def setup_ui(self):
        self.frame_roster = tk.Frame(self.root, bg="#0a0a0a", width=250, highlightbackground="#222", highlightthickness=1)
        self.frame_roster.pack(side=tk.LEFT, fill=tk.Y)
        
        tk.Label(self.frame_roster, text="ASSET INVENTORY", fg="#00ffcc", bg="#0a0a0a", font=("Courier", 12, "bold")).pack(pady=10)
        
        btn_frame = tk.Frame(self.frame_roster, bg="#0a0a0a")
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        self.btn_v = tk.Button(btn_frame, text="SWARM", bg="#222", fg="#fff", command=lambda: self.switch_roster("VEHICLE"), relief=tk.FLAT)
        self.btn_v.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        self.btn_s = tk.Button(btn_frame, text="STATIONS", bg="#111", fg="#777", command=lambda: self.switch_roster("STATION"), relief=tk.FLAT)
        self.btn_s.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        self.btn_l = tk.Button(btn_frame, text="LUNAR", bg="#111", fg="#777", command=lambda: self.switch_roster("LUNAR"), relief=tk.FLAT)
        self.btn_l.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)

        self.listbox = tk.Listbox(self.frame_roster, bg="#000", fg="#00ffcc", font=("Courier", 10), borderwidth=0, highlightthickness=0, selectbackground="#333")
        self.listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.listbox.bind('<<ListboxSelect>>', self.on_select)

        self.frame_diag_container = tk.Frame(self.root, bg="#0a0a0a", width=420, highlightbackground="#222", highlightthickness=1)
        self.frame_diag_container.pack(side=tk.RIGHT, fill=tk.Y)

        style = ttk.Style()
        style.theme_use('default')
        style.configure('TNotebook', background='#0a0a0a', borderwidth=0)
        style.configure('TNotebook.Tab', background='#111', foreground='#888', padding=[15, 5], font=("Courier", 10, "bold"))
        style.map('TNotebook.Tab', background=[('selected', '#222')], foreground=[('selected', '#ffcc00')])

        self.notebook = ttk.Notebook(self.frame_diag_container)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.frame_diag = tk.Frame(self.notebook, bg="#0a0a0a")
        self.notebook.add(self.frame_diag, text="NODE DIAG")

        self.frame_energy = tk.Frame(self.notebook, bg="#0a0a0a")
        self.notebook.add(self.frame_energy, text="ENERGY ANALYSIS")
        
        self.diag_labels = {}
        self.build_diag_section("IDENTIFICATION", ["ID", "TYPE", "STATUS"])
        self.build_diag_section("KINEMATICS / POSITION", ["RADIAL (AU)", "VELOCITY", "LATENCY (ms)"])
        self.build_diag_section("ELECTROMAGNETICS", ["MAG FLUX", "BUS VOLTAGE", "LAST YIELD"])
        self.build_diag_section("THERMAL / STRUCTURAL", ["HULL/COIL TEMP", "COOLING SYS", "INTEGRITY"])

        self.energy_labels = {}
        self.build_energy_section("SYSTEM LOAD PROFILES", ["TARGET DEMAND", "AVG OUTPUT (CUMULATIVE)", "AVG SURPLUS/DEFICIT"])
        self.build_energy_section("STORAGE & RESERVES", ["LUNAR BUFFER (PJ)", "SWARM KINETIC (EJ)", "ION PROPELLANT (kT)"])
        self.build_energy_section("EFFICIENCY METRICS", ["SOLAR FLUX (W/m2)", "ION DRIVE EFFICIENCY", "OVERALL YIELD"])

        tk.Label(self.frame_diag_container, text="GRID DEMAND (TW)", fg="#666", bg="#0a0a0a", font=("Courier", 10)).pack(anchor="w", padx=15, pady=(10, 0))
        self.demand_slider = tk.Scale(self.frame_diag_container, from_=0.0, to=MAX_DEMAND_TW, resolution=1.0, orient=tk.HORIZONTAL, bg="#0a0a0a", fg="#00ffcc", highlightthickness=0)
        self.demand_slider.set(0.0)
        self.demand_slider.pack(fill=tk.X, padx=15)

        tk.Label(self.frame_diag_container, text="TIME COMPRESSION", fg="#666", bg="#0a0a0a", font=("Courier", 10)).pack(anchor="w", padx=15, pady=(5, 0))
        self.time_slider = tk.Scale(self.frame_diag_container, from_=0.1, to=5.0, resolution=0.1, orient=tk.HORIZONTAL, bg="#0a0a0a", fg="#ffcc00", highlightthickness=0)
        self.time_slider.set(1.0)
        self.time_slider.pack(fill=tk.X, padx=15, pady=(0, 15))

        self.frame_global = tk.Frame(self.root, bg="#050505", height=100, highlightbackground="#222", highlightthickness=1)
        self.frame_global.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.lbl_timer = tk.Label(self.frame_global, text="T+ 000d 00h 00m", fg="#ffcc00", bg="#050505", font=("Courier", 12, "bold"))
        self.lbl_timer.pack(side=tk.LEFT, padx=(20, 10), pady=20)
        
        self.lbl_grid = tk.Label(self.frame_global, text="SYNCING...", fg="#00ff00", bg="#050505", font=("Courier", 12, "bold"))
        self.lbl_grid.pack(side=tk.LEFT, padx=10, pady=20)
        
        self.canvas_trend = tk.Canvas(self.frame_global, width=300, height=60, bg="#000", highlightthickness=1, highlightbackground="#333")
        self.canvas_trend.pack(side=tk.RIGHT, padx=20, pady=10)

        self.canvas = tk.Canvas(self.root, bg="#000", highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
        self.canvas.bind("<MouseWheel>", self.handle_zoom)
        self.canvas.bind("<B1-Motion>", self.handle_drag)
        self.last_x, self.last_y = 0, 0

    def build_diag_section(self, title, fields):
        tk.Frame(self.frame_diag, height=1, bg="#222").pack(fill=tk.X, pady=10, padx=15)
        tk.Label(self.frame_diag, text=title, fg="#555", bg="#0a0a0a", font=("Courier", 10, "bold")).pack(anchor="w", padx=15)
        for f in fields:
            row = tk.Frame(self.frame_diag, bg="#0a0a0a")
            row.pack(fill=tk.X, padx=20, pady=2)
            tk.Label(row, text=f, fg="#888", bg="#0a0a0a", font=("Courier", 9)).pack(side=tk.LEFT)
            val = tk.Label(row, text="---", fg="#fff", bg="#0a0a0a", font=("Courier", 10, "bold"))
            val.pack(side=tk.RIGHT)
            self.diag_labels[f] = val

    def build_energy_section(self, title, fields):
        tk.Frame(self.frame_energy, height=1, bg="#222").pack(fill=tk.X, pady=10, padx=15)
        tk.Label(self.frame_energy, text=title, fg="#00ffcc", bg="#0a0a0a", font=("Courier", 10, "bold")).pack(anchor="w", padx=15)
        for f in fields:
            row = tk.Frame(self.frame_energy, bg="#0a0a0a")
            row.pack(fill=tk.X, padx=20, pady=5)
            tk.Label(row, text=f, fg="#aaa", bg="#0a0a0a", font=("Courier", 9)).pack(side=tk.LEFT)
            val = tk.Label(row, text="---", fg="#fff", bg="#0a0a0a", font=("Courier", 10, "bold"))
            val.pack(side=tk.RIGHT)
            self.energy_labels[f] = val

    def switch_roster(self, mode):
        self.asset_type = mode
        self.selected_asset = None
        self.listbox.delete(0, tk.END)
        
        for key in self.diag_labels:
            self.diag_labels[key].config(text="---", fg="#fff")

        if mode == "VEHICLE":
            self.btn_v.config(bg="#222", fg="#fff")
            self.btn_s.config(bg="#111", fg="#777")
            self.btn_l.config(bg="#111", fg="#777")
            for v in self.vehicles: self.listbox.insert(tk.END, f" {v['id']}")
        elif mode == "STATION":
            self.btn_s.config(bg="#222", fg="#fff")
            self.btn_v.config(bg="#111", fg="#777")
            self.btn_l.config(bg="#111", fg="#777")
            for s in self.stations: self.listbox.insert(tk.END, f" {s['id']}")
        else:
            self.btn_l.config(bg="#222", fg="#fff")
            self.btn_v.config(bg="#111", fg="#777")
            self.btn_s.config(bg="#111", fg="#777")
            self.listbox.insert(tk.END, " LUNAR-BUFFER-01")

    def init_infrastructure(self):
        for i in range(SIM_STATIONS):
            angle = (i / SIM_STATIONS) * 2 * math.pi
            self.stations.append({
                "type": "STATION", "id": f"STN-{1000+i}", "theta": angle, "r": TRACK_RADIUS_AU,
                "temp": 42.0, "flux": 0.0, "health": 100.0, "status": "STANDBY", "yield": 0.0
            })
            
        for i in range(SIM_VEHICLES):
            self.vehicles.append({
                "type": "VEHICLE", "id": f"SIT-V{random.randint(10000, 99999)}", "r": random.uniform(0.35, 0.8), 
                "theta": random.uniform(0, 6.28), "v": random.uniform(1.2, 1.8),
                "temp": 280, "health": 100.0, "status": "DIVE", "yield": 0.0
            })
        self.switch_roster("VEHICLE")

    def on_select(self, event):
        selection = event.widget.curselection()
        if not selection: return
        idx = selection[0]
        if self.asset_type == "VEHICLE":
            self.selected_asset = self.vehicles[idx]
        elif self.asset_type == "STATION":
            self.selected_asset = self.stations[idx]
        else:
            self.selected_asset = {
                "type": "LUNAR", "id": "LUNAR-BUFFER-01", "status": "ACTIVE",
                "r": 1.1, "health": 100.0, "cap": self.lunar_capacity_pj
            }

    def handle_zoom(self, event):
        self.zoom *= 1.1 if event.delta > 0 else 0.9
        
    def handle_drag(self, event):
        self.offset_x += event.x - self.last_x
        self.offset_y += event.y - self.last_y
        self.last_x, self.last_y = event.x, event.y

    def update_diagnostics(self):
        if not self.selected_asset: return
        a = self.selected_asset
        
        self.diag_labels["ID"].config(text=a['id'])
        self.diag_labels["TYPE"].config(text=a['type'])
        self.diag_labels["STATUS"].config(text=a['status'], fg="#00ff00" if a['status'] in ["DIVE", "STANDBY"] else "#ff00ff")
        self.diag_labels["RADIAL (AU)"].config(text=f"{a['r']:.4f}")
        self.diag_labels["INTEGRITY"].config(text=f"{a['health']:.1f}%", fg="#00ff00")
        self.diag_labels["LATENCY (ms)"].config(text=f"{random.uniform(12, 18):.1f}")
        
        if a['type'] == "VEHICLE":
            temp = 390 / math.sqrt(a['r'])
            flux = 1361 / (a['r']**2)
            self.diag_labels["VELOCITY"].config(text=f"{a['v']*48.2:.2f} km/s")
            self.diag_labels["MAG FLUX"].config(text=f"{flux:,.0f} W/m2")
            self.diag_labels["BUS VOLTAGE"].config(text=f"{int(a['v'] * 450)} kV")
            self.diag_labels["HULL/COIL TEMP"].config(text=f"{int(temp)} K", fg="#ff6600" if temp > 600 else "#fff")
            self.diag_labels["COOLING SYS"].config(text="ION CORE COOLANT")
            self.diag_labels["LAST YIELD"].config(text=f"{a['yield']:.2f} GW")
        elif a['type'] == "STATION":
            self.diag_labels["VELOCITY"].config(text="STATITE (0.0 km/s)")
            self.diag_labels["MAG FLUX"].config(text=f"{a['flux']:.2f} T", fg="#00ccff" if a['flux'] > 0 else "#555")
            self.diag_labels["BUS VOLTAGE"].config(text="1,200 kV (GRID)")
            self.diag_labels["HULL/COIL TEMP"].config(text=f"{a['temp']:.1f} K", fg="#ff0000" if a['temp'] > 80 else "#00ff00")
            self.diag_labels["COOLING SYS"].config(text="ACTIVE CRYOGENIC")
            self.diag_labels["LAST YIELD"].config(text=f"{a['yield']:.2f} GW")
        elif a['type'] == "LUNAR":
            self.diag_labels["VELOCITY"].config(text="1.02 km/s (ORBIT)")
            self.diag_labels["MAG FLUX"].config(text="850.0 mT")
            self.diag_labels["BUS VOLTAGE"].config(text="5,000 kV (BUFFER)")
            self.diag_labels["HULL/COIL TEMP"].config(text="142.5 K")
            self.diag_labels["COOLING SYS"].config(text="REGOLITH HEAT SINK")
            self.diag_labels["LAST YIELD"].config(text=f"{self.lunar_buffer_pj/1000:.2f} EJ")

    def run_sim(self):
        dt = self.time_slider.get() * 0.02
        
        self.sim_time += dt * 432000
        days = int(self.sim_time // 86400)
        hours = int((self.sim_time % 86400) // 3600)
        mins = int((self.sim_time % 3600) // 60)
        self.lbl_timer.config(text=f"T+ {days:03d}d {hours:02d}h {mins:02d}m")

        self.canvas.delete("all")
        cx, cy = 400 + self.offset_x, 400 + self.offset_y
        
        # DRAW SUN
        s_rad = 20 * self.zoom
        self.canvas.create_oval(cx-s_rad, cy-s_rad, cx+s_rad, cy+s_rad, fill="#ffcc00", outline="#ff6600", width=2)
        
        # DRAW MOON
        self.moon_theta += 0.005 * dt
        mx = cx + math.cos(self.moon_theta) * (1.1 * AU_SCALE * self.zoom)
        my = cy + math.sin(self.moon_theta) * (1.1 * AU_SCALE * self.zoom)
        m_rad = 8 * self.zoom
        
        charge_pct = self.lunar_buffer_pj / self.lunar_capacity_pj
        m_color = f"#{int(50 + 205*charge_pct):02x}{int(50 + 100*charge_pct):02x}ff" if charge_pct > 0 else "#444"
        self.canvas.create_oval(mx-m_rad, my-m_rad, mx+m_rad, my+m_rad, fill=m_color, outline="#888")
        self.canvas.create_text(mx, my+m_rad+10, text="LUNAR BUFFER", fill="#888", font=("Courier", int(8*self.zoom)))

        for s in self.stations:
            s['status'] = "STANDBY"
            s['flux'] *= 0.8
            s['temp'] = max(42.0, s['temp'] - 1.0)

        power_sum = 0
        target_demand = self.demand_slider.get()
        harvest_factor = target_demand / MAX_DEMAND_TW
        
        for v in self.vehicles:
            # Physics: Inverse square gravity and orbital decay
            v['v'] += (0.0065 / (v['r']**2)) * dt
            v['theta'] += (v['v'] / v['r']) * dt
            v['r'] -= 0.0015 * dt
            
            # Harvesting: Solar Flux (1/r^2)
            solar_flux = 1.36 / (v['r']**2) # kW/m2
            v['yield'] = solar_flux * 45.0 * harvest_factor # PV Yield
            power_sum += v['yield']
            
            v['status'] = "SOLAR HARVEST"
            color = "#ffcc00"
            thruster_active = False

            # The "Slingshot" Maneuver (Oberth Effect)
            if v['r'] < TRACK_RADIUS_AU + 0.05:
                # Use Ion Thrusters to "kick" back to high orbit
                propulsion_tax = 0.25 # 25% of yield diverted to ion drives
                thrust_force = (v['yield'] * propulsion_tax) * 0.15
                v['v'] += thrust_force * dt
                v['r'] += 0.05 # Immediate radial lift from thrust
                
                v['status'] = "ION THRUST (OBERTH)"
                color = "#00ffff"
                thruster_active = True
                
                # Update station as relay
                closest_s = min(self.stations, key=lambda s: abs(s['theta'] - (v['theta'] % (2*math.pi))))
                closest_s['status'] = "RELAY ACTIVE"
                closest_s['yield'] = v['yield']

            vx = cx + math.cos(v['theta']) * (v['r'] * AU_SCALE * self.zoom)
            vy = cy + math.sin(v['theta']) * (v['r'] * AU_SCALE * self.zoom)
            
            if thruster_active:
                # Draw ion plume
                self.canvas.create_line(vx, vy, vx - math.cos(v['theta'])*15, vy - math.sin(v['theta'])*15, fill="#00ffff", width=2)
            
            if self.selected_asset and v['id'] == self.selected_asset['id']:
                self.canvas.create_oval(vx-8, vy-8, vx+8, vy+8, outline="#ffcc00", width=1, dash=(2,2))
            self.canvas.create_oval(vx-3, vy-3, vx+3, vy+3, fill=color, outline="")

        t_rad = TRACK_RADIUS_AU * AU_SCALE * self.zoom
        for s in self.stations:
            sx = cx + math.cos(s['theta']) * t_rad
            sy = cy + math.sin(s['theta']) * t_rad
            
            s_color = "#ff00ff" if s['status'] == "ACTIVE HARVEST" else "#004400"
            s_out = "#fff" if s['status'] == "ACTIVE HARVEST" else "#00ff00"
            
            if self.selected_asset and s['id'] == self.selected_asset['id']:
                self.canvas.create_rectangle(sx-6, sy-6, sx+6, sy+6, outline="#ffcc00", width=2)
            self.canvas.create_rectangle(sx-3, sy-3, sx+3, sy+3, fill=s_color, outline=s_out)

        scaled_tw = (power_sum / SIM_VEHICLES) * (TOTAL_VEHICLES / 1200)
        self.power_history.append(scaled_tw)
        self.demand_history.append(target_demand)

        self.total_ticks += 1
        self.cum_output += scaled_tw
        self.cum_demand += target_demand

        deficit = scaled_tw - target_demand
        
        # Buffer logic with visualization
        if deficit > 0: # Charging
            self.lunar_buffer_pj = min(self.lunar_capacity_pj, self.lunar_buffer_pj + deficit * (dt * 0.5))
            # Draw charging beams from stations to moon
            if self.total_ticks % 5 == 0:
                for _ in range(3):
                    s = random.choice(self.stations)
                    sx = cx + math.cos(s['theta']) * (TRACK_RADIUS_AU * AU_SCALE * self.zoom)
                    sy = cy + math.sin(s['theta']) * (TRACK_RADIUS_AU * AU_SCALE * self.zoom)
                    self.canvas.create_line(sx, sy, mx, my, fill="#00ffcc", dash=(4,4), width=1)
        else: # Discharging
            drain = min(abs(deficit), self.lunar_buffer_pj / (dt * 0.5 + 1e-9))
            self.lunar_buffer_pj = max(0.0, self.lunar_buffer_pj - abs(deficit) * (dt * 0.5))
            if deficit < -1.0 and self.lunar_buffer_pj > 0:
                # Draw discharging beams to "The Grid" (off-screen)
                self.canvas.create_line(mx, my, cx + 2000, cy + 2000, fill="#ff3333", width=2, arrow=tk.LAST)

        self.lbl_grid.config(text=f"DEMAND: {target_demand:.1f} TW | OUTPUT: {scaled_tw:.2f} TW | LUNAR BUFFER: {self.lunar_buffer_pj/1000:.2f} EJ")
        
        self.canvas_trend.delete("all")
        w, h = 300, 60
        max_p = max(100.0, max(self.power_history), max(self.demand_history))
        pts_actual = []
        pts_target = []
        for i in range(len(self.power_history)):
            x = (i / 100) * w
            ya = h - ((self.power_history[i] / max_p) * h)
            yt = h - ((self.demand_history[i] / max_p) * h)
            pts_actual.extend([x, ya])
            pts_target.extend([x, yt])
            
        if len(pts_target) >= 4:
            self.canvas_trend.create_line(pts_target, fill="#ff3333", width=1, dash=(2,2))
        if len(pts_actual) >= 4:
            self.canvas_trend.create_line(pts_actual, fill="#00ffcc", width=2, smooth=True)

        self.update_diagnostics()
        self.update_energy_analysis(target_demand, scaled_tw, deficit)
        self.root.after(30, self.run_sim)

    def update_energy_analysis(self, target, actual, deficit):
        self.energy_labels["TARGET DEMAND"].config(text=f"{target:.2f} TW", fg="#ff3333")
        
        avg_output = self.cum_output / self.total_ticks
        avg_demand = self.cum_demand / self.total_ticks
        avg_deficit = avg_output - avg_demand

        self.energy_labels["AVG OUTPUT (CUMULATIVE)"].config(text=f"{avg_output:.2f} TW", fg="#00ffcc")
        
        def_color = "#00ff00" if avg_deficit >= 0 else "#ff0000"
        self.energy_labels["AVG SURPLUS/DEFICIT"].config(text=f"{avg_deficit:+.2f} TW", fg=def_color)

        self.energy_labels["LUNAR BUFFER (PJ)"].config(text=f"{self.lunar_buffer_pj:,.1f}")

        kin_ej = sum([0.5 * 1200 * ((v['v']*48200)**2) for v in self.vehicles]) * (TOTAL_VEHICLES/SIM_VEHICLES) / 1e18
        self.cum_kin += kin_ej
        avg_kin = self.cum_kin / self.total_ticks
        self.energy_labels["SWARM KINETIC (EJ)"].config(text=f"{avg_kin:,.2f}")

        prop_kt = (1.0 - (self.total_ticks % 1000) / 1000) * 850.0
        self.energy_labels["ION PROPELLANT (kT)"].config(text=f"{prop_kt:,.1f}")

        avg_flux = 1361 / (TRACK_RADIUS_AU**2)
        self.energy_labels["SOLAR FLUX (W/m2)"].config(text=f"{avg_flux:,.0f}")
        self.energy_labels["ION DRIVE EFFICIENCY"].config(text="62.4%")
        
        inst_eff = min(99.9, max(0.1, (actual / (actual + (abs(deficit)*0.2) + 0.001)) * 100))
        self.cum_eff += inst_eff
        avg_eff = self.cum_eff / self.total_ticks
        self.energy_labels["OVERALL YIELD"].config(text=f"{avg_eff - 1.42:.2f}%")

if __name__ == "__main__":
    root = tk.Tk()
    app = SIT_Master_SCADA(root)
    root.mainloop()
