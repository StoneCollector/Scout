import subprocess
import os
import sys

def build_executable():
    """Packages the Scout application into a single standalone .exe file."""
    print("Starting Scout build process...")
    print("This may take a few minutes as it bundles Python and all libraries.")
    
    # flet pack is only available in Flet >= 0.21 CLI—which our pinned 0.23.2 doesn't expose.
    # We call PyInstaller directly instead.
    command = [
        sys.executable, "-m", "PyInstaller",
        "app.py",
        "--name", "Scout",
        "--onefile",            # Single EXE
        "--windowed",           # No console window
        "--uac-admin",          # UAC elevation prompt (needed for Win32 locking)
        "--hidden-import", "win32file",
        "--hidden-import", "win32api",
        "--hidden-import", "win32con",
        "--hidden-import", "pywintypes",
        "--hidden-import", "watchdog",
        "--hidden-import", "watchdog.observers",
        "--hidden-import", "watchdog.events",
        "--hidden-import", "flet",
        "--hidden-import", "flet_core",
        "--hidden-import", "psutil",
        "--hidden-import", "pystray",
        "--hidden-import", "plyer",
        "--hidden-import", "requests",
        "--collect-all", "flet",
        "--collect-all", "flet_core",
        "--collect-all", "flet_runtime",
        "--noconfirm",
    ]
    
    try:
        subprocess.run(command, check=True)
        print("\n\n✅ BUILD SUCCESSFUL!")
        print(f"Your executable is located in: {os.path.abspath('dist/Scout.exe')}")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ BUILD FAILED: {e}")
        print("Ensure 'pyinstaller' is installed:  pip install pyinstaller")

if __name__ == "__main__":
    build_executable()
