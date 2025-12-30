# 🛡️ Home Network Management System (HNMS)

<div align="center">

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](VERSION)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Docker Hub](https://img.shields.io/badge/docker-wglabz/hnms-blue.svg?logo=docker)](https://hub.docker.com/r/wglabz/hnms)
[![Vue](https://img.shields.io/badge/frontend-Vue%203-42b883.svg)](ui/)
[![FastAPI](https://img.shields.io/badge/backend-FastAPI-009688.svg)](backend/)

**A professional-grade, web-based network monitoring and security suite for the modern home.**

[Explore Features](#-detailed-usage-guide) • [Quick Start](#️-quick-start-docker) • [Developer Guide](#-manual-development-setup)

</div>

---

![Dashboard Overview](./.img/dashboard.png)

HNMS is designed to give you total visibility over your local network. It combines real-time Nmap scanning with persistent historical tracking to provide a comprehensive security audit of every device in your home.

## 📑 Table of Contents
- [✨ Key Features](#-key-features)
- [🛠️ Tech Stack](#️-tech-stack)
- [📸 Gallery](#-gallery)
- [📘 Detailed Usage Guide](#-detailed-usage-guide)
- [🚀 Quick Start (Docker)](#️-quick-start-docker)
- [💻 Manual Development Setup](#-manual-development-setup)
- [📂 Project Structure](#-project-structure)

---

## ✨ Key Features

| Feature | Description |
| :--- | :--- |
| **Dual-Mode Discovery** | Parallel Scapy ARP + ICMP Ping sweeps for 100% device parity across Docker & Windows. |
| **Dynamic Classification** | Fully editable rules engine in the UI for custom icons and device-type matching. |
| **Integrated SSH** | Direct, secure web-based terminal access to your network devices. |
| **Analytical History** | Immutable scan logs and uptime trends with sub-second precision. |
| **Premium UX** | Modern glassmorphism design with unified notification toasts and custom modals. |
| **Rock-Solid Stability** | Shared-connection logic resolves database locking issues in high-concurrency environments. |
| **Timezone Aware** | Optimized timestamp handling with automatic UTC synchronization. |

---

## 🛠️ Tech Stack

- **Frontend**: [Vue 3](https://vuejs.org/) (Composition API), [Vite](https://vitejs.dev/), [Tailwind CSS](https://tailwindcss.com/), [Luxon](https://moment.github.io/luxon/)
- **Backend**: [FastAPI](https://fastapi.tiangolo.com/), [Uvicorn](https://www.uvicorn.org/)
- **Database**: [DuckDB](https://duckdb.org/) (High-performance analytical storage)
- **Scanning Engine**: [Nmap](https://nmap.org/), [Scapy](https://scapy.net/)
- **Integration**: [MQTT](https://mqtt.org/) (Paho), [Home Assistant Discovery](https://www.home-assistant.io/integrations/mqtt/#mqtt-discovery)

---

## 📸 Gallery

### Device Management
![Device List](./.img/devices.png)
*Granular control over your network inventory with vendor-specific metadata.*

### Intelligent Classification
![Settings Classification](./.img/classification.png)
*Manage how devices are identified with customizable Regex and Port rules.*

### Integrated SSH Terminal
![SSH Terminal](./.img/ssh-terminal.png)
*Direct, secure web-based shell access to your network devices.*

### High-Fidelity Analytics
![Device Identification](./.img/device-details.png)
*Sub-second precision on device availability and deep port audit history.*

### Activity Trends
![Events Log](./.img/events.png)
*Visualize spikes in network movement and monitor hardware stability.*

---

## 📘 Detailed Usage Guide

### 📊 Dashboard & Analytics
The Hub for your network health.
- **Sparklines**: Integrated trend lines within metric cards reveal 24-hour activity patterns.
- **Live Feed**: Pulsing activity log monitors current worker status.

### ⚙️ Rule Management
Located in **Settings**, the classification engine allows you to:
- **Prioritize Identification**: Ensure high-priority rules match before generic ones.
- **Regex Support**: Match devices by Hostname, Vendor, or common local ports.
- **Icon Selector**: Choose from a premium Lucide-based icon library.

### 🔍 Device Management
- **Audit Trigger**: Initiate manual scans to force a directory refresh.
- **Deep Audit**: Probes 1000+ ports; captures banner metadata for precise identification.

### 📡 MQTT Integration & Automation
HNMS acts as a bridge between your network and your smart home.

> [!TIP]
> Use the **Home Assistant Discovery** feature to instantly see network presence as binary sensors in your HA Dashboard.

![Home Assistant Discovery](./.img/HA%20Dsicovery.png)

| Topic Pattern | Description |
| :--- | :--- |
| `{base}/device/{mac}/state` | Broadcasts `home` / `not_home`. |
| `{base}/device/{mac}/attributes` | Rich JSON containing IP, Vendor, and OS details. |

---

## 🐋 Docker Image

The official HNMS Docker image is available on Docker Hub:

```bash
docker pull wglabz/hnms:latest
```

👉 **[View on Docker Hub](https://hub.docker.com/r/wglabz/hnms)**

---

## 🚀 Detailed Docker Setup

### Prerequisites
- **Docker** and **Docker Compose** installed.
- **Linux Host**: Recommended for full Nmap/Scapy performance (`network_mode: host`).

### Environment Variables

Configure the container behavior using these variables:

| Variable | Default | Description |
| :--- | :--- | :--- |
| `APP_ENV` | `production` | Set to `development` for debug logging. |
| `DB_PATH` | `/data/network_scanner.duckdb` | Path to the database file inside the container. |
| `DB_SCHEMA_PATH` | `app/schema.sql` | Path to the schema file inside the container. |
| `WORKERS` | `1` | Number of concurrent scan workers (1 is recommended for Raspberry Pi). |
| `MQTT_ENABLED` | `false` | Set to `true` to enable MQTT publishing. |
| `MQTT_HOST` | `localhost` | IP/Hostname of your MQTT broker. |

### Persistent Storage
To preserve your device history and configuration across container updates, map a local directory to `/data`:

```yaml
volumes:
  - ./hnms_data:/data
```

### Networking Requirements (Linux)
The scanner requires raw socket access to perform ARP requests.
- **Host Mode**: Use `network_mode: host` in `docker-compose.yml`.
- **Bridge Mode**: If using bridge mode, MAC address resolution will be limited to the container virtual interface.

---

## 🚀 Quick Start (Docker Compose)

> [!IMPORTANT]
> For Linux deployments, use `network_mode: host` in `docker-compose.yml` to allow the scanner full access to the network interface.

```bash
docker-compose up -d
```
Access at: [http://localhost:8000](http://localhost:8000)

## 💻 Manual Development Setup

### Backend (FastAPI)
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8001
```

### Frontend (Vue 3)
```bash
cd ui
npm install
npm run dev
```

---

## 🛠️ Windows Troubleshooting

If device discovery is not working on your Windows machine, please check the following:

### 1. Install Npcap
The scanner uses Scapy, which requires a packet capture driver on Windows. 
- Download and install **[Npcap](https://npcap.com/#download)**.
- During installation, ensure the **"Install Npcap in WinPcap API-compatible Mode"** option is checked.

### 2. Run as Administrator
Sending raw network packets (ARP) requires high-level privileges. 
- Open your terminal (PowerShell or CMD) as **Administrator** before running the uvicorn command.

### 3. Automatic Fallback
The system includes a smart fallback. If raw ARP packets are restricted by your security policy, HNMS will automatically pivot to a **Parallel Ping Sweep**. This ensures devices are found even without specialized drivers.

---

## 📂 Project Structure
- `/backend`: Analytical core and scanning workers.
- `/ui`: Modern glassmorphism interface.
- `/.img`: Optimized local asset storage.
- `publish.sh`: Automated CI/CD versioning script.

---

<div align="center">
Built with ❤️ for the Home Automation Community
</div>