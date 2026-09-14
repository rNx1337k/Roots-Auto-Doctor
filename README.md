<div align="center">

# 🚗 Roots Auto Doctor

**Modern automotive diagnostic software for OBD-II vehicles.**

Connect an ELM327 adapter, talk to your car's ECU, and read real diagnostic
data — fault codes, live sensors, readiness monitors — through a fast,
dark-themed desktop app.

<p>
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/GUI-PySide6%20(Qt)-41CD52?logo=qt&logoColor=white" />
  <img src="https://img.shields.io/badge/Platform-Windows-0078D6?logo=windows&logoColor=white" />
  <img src="https://img.shields.io/badge/OBD--II-ELM327-orange" />
  <img src="https://img.shields.io/badge/License-MIT-lightgrey" />
  <img src="https://img.shields.io/badge/Status-In%20Development-yellow" />
</p>

</div>

---

## 🔧 About

**Roots Auto Doctor** is a Windows diagnostic application that speaks OBD-II
directly to your vehicle through an ELM327-compatible adapter (USB, Bluetooth
or WiFi, over a serial/COM port).

No subscriptions, no cloud accounts — just plug in, connect, and diagnose.
The goal is to give hobbyists and technicians a tool that feels as fast and
clear as the professional scanners, without the professional price tag.

## ⚙️ Features

| | |
|---|---|
| 🔌 **Auto interface detection** | Scans available COM ports and connects to any ELM327-compatible adapter |
| 🧩 **ECU gateway info** | Reads protocol, VIN and ECU name straight from the vehicle |
| ⚠️ **Fault codes (DTC)** | Reads, categorizes (Engine / ABS / Body / Network) and clears trouble codes |
| 🧊 **Freeze frame** | Snapshot of key sensors at the exact moment a fault was recorded |
| 📡 **Live data** | Stream any supported PID in a table or on digital-dash style gauges |
| 📈 **Live graphs** | Multi-sensor overview panel — RPM, speed, coolant temp and throttle at a glance |
| 🛡️ **Readiness monitors** | Emissions-readiness check before a mandatory inspection |
| 🔋 **Battery voltage** | Quick sanity check on connect — is the OBD port actually powered? |
| 🧾 **Communication log** | Every request/response with the ECU, timestamped, for troubleshooting |
| ⬇️ **CSV export** | Export a fault-code report to share or archive |

## 🖥️ Screenshots

> _Add a screenshot or GIF of the Dashboard / Live Data pages here once you
> have one — it's the single biggest thing that makes a README "pop"._

## 🚀 Getting Started

### Requirements

- Windows 10/11
- Python 3.10+
- An ELM327-compatible OBD-II adapter (USB, Bluetooth or WiFi paired as a COM port)

### Install & run

```bash
git clone https://github.com/<your-user>/Roots-Auto-Doctor.git
cd Roots-Auto-Doctor

pip install PySide6 pyserial

python main.py
```

### Connecting to a vehicle

1. Plug the adapter into the vehicle's OBD-II port (usually under the steering wheel).
2. Turn the key to the **"Ignition"** position (engine doesn't need to be running for most reads).
3. Open **Ligação**, pick the adapter's COM port, and hit **Ligar**.
4. Once connected, use **Códigos de Falha**, **Dados em Tempo Real** and **Prontidão** to diagnose.

## 🧠 How it works

```
GUI (PySide6)  →  OBD2 protocol layer  →  ELM327 driver  →  Serial (COM port)  →  Vehicle ECU
```

- `hardware/` — low-level adapter communication (serial + ELM327 AT commands)
- `protocols/` — OBD-II (SAE J1979) request/response logic and PID decoding
- `services/` — DTC & PID databases, VIN → manufacturer lookup, session export
- `core/` — plain data models (Vehicle, DTC, ECU, Session)
- `gui/` — the PySide6 interface, one module per page

## 🗺️ Roadmap

- [ ] Manufacturer-specific protocols (UDS/KWP) for per-module diagnostics (ABS, Airbag, Gearbox…)
- [ ] J2534 pass-thru device support
- [ ] Session recording & playback
- [ ] Packaged Windows installer (no Python required)

## 🛠️ Built With

Python • [PySide6 (Qt)](https://doc.qt.io/qtforpython/) • [pyserial](https://pyserial.readthedocs.io/) • OBD-II / SAE J1979

## ⚠️ Disclaimer

This is a hobbyist diagnostic tool. Clearing fault codes and reading live
data is generally safe, but always exercise caution when connecting any
device to your vehicle's systems. Use at your own risk.

## 📄 License

Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for details.

---

<div align="center">
  <strong>🚗 Roots Auto Doctor</strong><br>
  <sub>Automotive diagnostics, made simple.</sub>
</div>