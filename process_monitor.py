import logging
import hashlib
import os

try:
    import psutil
    import win32gui
    import win32process
    WIN32_CAPABLE = True
except ImportError:
    WIN32_CAPABLE = False

logger = logging.getLogger("Scout.ProcessMonitor")

class ProcessMonitor:
    """
    Advanced Forensics module. Performs a deep snapshot of the culprit process
    extracting its on-disk origin, checking for networking status, and securing its SHA-256 binary hash.
    """
    
    @staticmethod
    def get_file_hash(filepath: str) -> str:
        """Computes the SHA-256 cryptographic hash of an executable file."""
        if not filepath or not os.path.exists(filepath):
            return "File Unavailable"
        sha256 = hashlib.sha256()
        try:
            with open(filepath, 'rb') as f:
                while chunk := f.read(8192):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except Exception:
            return "Read Error (File Locked/Elevated)"

    @staticmethod
    def snapshot_culprit() -> dict:
        """
        Takes a full forensic snapshot of the active window modifying the file.
        Returns a rich dictionary.
        """
        forensics = {
            "name": "Unknown",
            "pid": 0,
            "location": "N/A",
            "hash": "N/A",
            "network_active": False,
            "status": "Unknown"
        }
        
        if not WIN32_CAPABLE:
            forensics["status"] = "Missing Dependencies (psutil/pywin32)"
            return forensics

        try:
            # 1. Grab Window Handle
            hwnd = win32gui.GetForegroundWindow()
            if not hwnd:
                forensics["status"] = "Background System Process"
                return forensics

            # 2. Extract PID
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            forensics["pid"] = pid
            
            if pid <= 0:
                forensics["name"] = "System"
                forensics["status"] = "OS Level"
                return forensics

            # 3. Analyze Process
            process = psutil.Process(pid)
            forensics["name"] = process.name()
            
            if forensics["name"].lower() == "explorer.exe":
                forensics["status"] = "Manual User Edit (Explorer)"
                return forensics
                
            # 4. Location & Cryptographic Hash
            try:
                forensics["location"] = process.exe()
                forensics["hash"] = ProcessMonitor.get_file_hash(forensics["location"])
            except psutil.AccessDenied:
                # If Scout isn't running as admin and a root process does something
                forensics["location"] = "Access Denied (Requires Admin)"
                forensics["status"] = "Elevated Process"
                
            # 5. Network Activity Scan (Are they exfiltrating data?)
            try:
                conns = process.net_connections(kind='inet')
                forensics["network_active"] = len(conns) > 0
            except psutil.AccessDenied:
                pass
                
            if forensics["status"] == "Unknown":
                forensics["status"] = "Forensics Captured Successfully"
                
            return forensics
            
        except psutil.NoSuchProcess:
            forensics["status"] = "Terminated Instantly (Hit & Run)"
            return forensics
        except Exception as e:
            logger.error(f"Forensic Snapshot failed: {e}")
            forensics["status"] = "Snapshot Error"
            return forensics
