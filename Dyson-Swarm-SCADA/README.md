# Dyson Swarm SCADA - Stellar Energy Management Simulation

A high-fidelity, systems-engineering approach to simulating a **Type II Civilization** energy grid. This simulation models an **Active Dyson Swarm** using hard-science principles of orbital mechanics, solar electric propulsion, and industrial-grade telemetry.


## The "Active Swarm" Concept

Unlike passive "Dyson Bubble" models that rely on thin solar sails, this simulation models a **Managed Industrial Swarm**. 

### Key Engineering Principles:
*   **Active Propulsion (SEP)**: Each swarm vehicle is equipped with **Ion Thrusters** (Solar Electric Propulsion). This allows the fleet to maintain stable orbits, avoid solar flares, and perform maintenance maneuvers.
*   **Inverse-Square Flux Harvesting**: Energy yield is calculated based on real-world physics ($1/r^2$). Vehicles "dive" deep into the Sun's gravity well (down to **0.3 AU**) to harvest maximum solar flux (~15,000 W/m²).
*   **The Oberth Effect**: Propulsion is optimized by firing Ion Drives at the perihelion (closest point to the Sun), maximizing orbital energy recovery and allowing vehicles to "kick" back to higher orbits for storage.
*   **Lunar Buffer Storage**: Harvested energy is transmitted to a **Planetary-Scale Buffer** on the Moon. This Exajoule-scale battery balances the dynamic output of the swarm against global grid demand.

## Features

*   **SCADA Interface**: Industrial-grade telemetry and control system (SIT-OS v6.2).
*   **Real-Time Diagnostics**: Monitor individual vehicle kinematics, bus voltage, magnetic flux, and ion core temperatures.
*   **Grid Control**: Adjust global demand in Terawatts (TW) and observe how the swarm adjusts its "Propulsion Tax" and storage rates.
*   **Trend Analysis**: Live graphing of Output vs. Demand.
*   **Visual Simulation**: Real-time canvas rendering with ion plume animations and energy transfer beams.

## Technical Specs (Hard Science)

| Metric | Simulation Value | Realistic Basis |
| :--- | :--- | :--- |
| **Solar Constant** | 1.36 kW/m² | Earth-Orbit Standard |
| **Harvest Radius** | 0.3 - 0.8 AU | Mercury-scale proximity |
| **Storage Type** | Lunar Buffer (PJ/EJ) | Planetary Regolith Heat-Sink |
| **Propulsion** | Ion Drive (62% Eff) | Solar-Electric Propulsion (SEP) |
| **Grid Capacity** | 100 TW | 5x Current Earth Consumption |

## Installation

1.  **Requirements**: Python 3.x, Tkinter (usually included with Python).
2.  **Run**:
    ```bash
    python dyson_scada.py
    ```

## How it Works (The "Dive & Kick" Loop)

1.  **The Dive**: Vehicles decay toward the Sun, building velocity and increasing solar flux exposure.
2.  **The Harvest**: At peak proximity, vehicles harvest maximum power, filling the grid and the Lunar Buffer.
3.  **The Kick**: Using a fraction of harvested power, the vehicle fires its **Ion Thrusters** at the perihelion (Oberth Effect), boosting itself back to the outer swarm ring.
4.  **Load Balancing**: The **Lunar Buffer** automatically discharges EJ-scale energy when the swarm is in its "climb" phase or when demand spikes.

---