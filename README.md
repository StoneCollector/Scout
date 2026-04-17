# Scout — Active Defense System

> **A professional-grade, real-time File Integrity Monitor and Active Defense platform for Windows.**  
> Scout watches your critical files and folders and fights back — automatically healing tampering, annihilating unauthorized creations, and dispatching forensic alerts in real time.

---

## ✨ Feature Overview

| Feature | Description |
|---|---|
| 🛡️ **Zero-Trust STRICT Mode** | OS-level write locks prevent any process from modifying protected files |
| 🔥 **Kill-on-Arrival** | Unauthorized files/folders created in protected paths are instantly annihilated |
| 🔁 **Self-Healing** | Modified or deleted files are automatically restored from the vault |
| 🔬 **OpCode Forensic Diff** | Side-by-side viewer that shows exactly what changed, using a SequenceMatcher sync-map engine |
| 🧬 **Deep Process Forensics** | Captures the culprit process name, PID, disk location, SHA-256 hash, and network activity at the moment of intrusion |
| ✅ **Administrative Vetting** | Approve legitimate changes with one click to reset the forensic baseline |
| 🔔 **Discord Webhooks** | Instant security alerts with full forensic embeds dispatched to your Discord server |
| 💾 **Encrypted Vault** | Baselines are XOR-encoded and stored in a hidden system directory |
| 🖥️ **System Tray Integration** | Minimises to the system tray and delivers native Windows toast notifications |
| 📋 **Forensic History Log** | Full audit trail of every security event with timestamps and diffs |
| 🔑 **Checkout Workflow** | Temporarily unlock a file or folder for authorized editing, then re-lock in one click |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Scout Active Defense                    │
│                                                             │
│  ┌──────────┐    ┌─────────────────┐    ┌───────────────┐  │
│  │ watchdog │───▶│  ScoutEngine    │───▶│  SecurityMgr  │  │
│  │ Observer │    │  (Orchestrator) │    │  (Win32 Locks)│  │
│  └──────────┘    └────────┬────────┘    └───────────────┘  │
│                           │                                 │
│              ┌────────────┼────────────┐                    │
│              ▼            ▼            ▼                    │
│    ┌──────────────┐ ┌──────────┐ ┌──────────────────────┐  │
│    │ProcessMonitor│ │ Recovery │ │   Forensic Sync Map  │  │
│    │(PID/Hash/Net)│ │  Vault   │ │  (OpCode Diff Engine)│  │
│    └──────────────┘ └──────────┘ └──────────────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Flet UI (app.py)                        │  │
│  │  Dashboard | Target Explorer | Forensic Diff Viewer  │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
file-integrity-monitor-main/
│
├── app.py                  # Main UI entry point (Flet application)
├── scout_engine.py         # Core orchestration engine (events, policy, healing)
├── security_manager.py     # OS-level file locking via Win32 API
├── recovery_vault.py       # XOR-encoded vault for pristine file storage
├── process_monitor.py      # Deep-dive culprit forensics (PID, hash, network)
├── tray_manager.py         # System tray icon and toast notification manager
├── fim.py                  # Legacy/standalone FIM module (reference)
├── build.py                # PyInstaller build script
├── requirements.txt        # All Python dependencies
└── test_fim.py             # Engine unit tests
```

---

## 🚀 Quick Start

### Prerequisites

- **Windows 10/11** (Win32 API is required for file locking)
- **Python 3.11+**

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/your-username/scout-active-defense.git
cd scout-active-defense

# 2. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
```

### Run Scout

```bash
python app.py
```

---

## 🔒 How It Works: Protection Modes

Scout operates in two protection modes per target:

### 🟡 MONITORING Mode
- Watchdog detects all file system events.
- Deep forensic data (process name, hash, diff) is captured.
- Discord alerts are dispatched.
- **Files are NOT reverted.** Changes are observed and logged.

### 🔴 STRICT Mode (Zero-Trust)
Scout enforces a full lock-down policy:

| Event | Response |
|---|---|
| **File Modified** | Reverted instantly from the vault. Culprit logged. |
| **File Created** | Annihilated via `Kill-on-Arrival`. No baseline created. |
| **Folder Created** | Recursively destroyed by `shutil.rmtree` |
| **File Deleted** | Restored from vault. Re-locked immediately. |
| **Folder Deleted** | Recreated with `os.makedirs` |

#### Authorizing Legitimate Changes (Checkout Workflow)
1. Click **"Checkout"** on a file or folder in the UI.
2. Make your authorized changes (edit, add, delete).
3. Click **"Check-In"** — Scout re-locks everything and updates the vault baseline.

---

## ✅ Administrative Vetting

If you've already made a change and want to "bless" the current state as the new baseline:

1. Navigate to the target in the **Targets** panel.
2. Click the **Green Shield (✅ Vet)** icon next to the file.
3. Scout captures the current version as the new "Last Known Good."
4. All future forensic diffs will compare against this vetted state.

---

## 🔔 Discord Webhooks

Scout can dispatch real-time forensic alerts to a Discord channel:

1. Go to **Settings** in the Scout UI.
2. Paste your Discord Webhook URL and click **Add**.
3. Every security event will be dispatched as an embedded forensic report containing:
   - Culprit Process Name & PID
   - SHA-256 hash of the culprit executable
   - Whether the process had active network connections
   - The file path and event type

---

## 🧬 Forensic Diff Viewer

Scout uses a binary **OpCode Sync-Map Engine** (backed by Python's `SequenceMatcher`) to generate perfectly aligned, side-by-side forensic diffs:

- **Left panel**: Previous (Vault) version with line numbers
- **Right panel**: Current (Modified) version with line numbers
- **Color coding**:
  - 🔴 Red background — Deleted line
  - 🟢 Green background — Inserted line  
  - 🟡 Amber background — Changed line
  - Neutral — Unchanged line

---

## 🏗️ Building a Standalone Executable

```bash
python build.py
```

This will use PyInstaller to create a single `Scout.exe` in the `dist/` directory.

---

## ⚙️ Dependencies

| Package | Purpose |
|---|---|
| `flet` | Cross-platform desktop UI framework |
| `watchdog` | Real-time file system event monitoring |
| `pywin32` | Win32 API bindings for OS-level file locking |
| `psutil` | Process inspection and culprit identification |
| `pystray` | System tray icon management |
| `Pillow` | Tray icon image rendering |
| `requests` | Discord Webhook HTTP dispatch |
| `plyer` | Native desktop notifications |

---

## ⚠️ Important Notes

- **Windows Only**: Scout's file-locking engine relies on Win32 `CreateFileW` with `FILE_SHARE_READ`. It will not run on Linux/macOS.
- **Run as Administrator**: For locking files in system directories, run Scout as an administrator.
- **Vault Security**: The `.scout_vault/` directory is hidden and XOR-encoded, but should not be committed to version control.
- **Webhook URLs**: Store Discord Webhook URLs securely. They are saved to `scout_config.json` which is also excluded from git.

---

## 📜 License

MIT License — see [LICENSE](LICENSE) for details.
