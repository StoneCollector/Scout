import subprocess
import os
import sys

def build_executable():
    """Packages the Scout application into a single standalone .exe file."""
    print("Starting Scout build process...")
    print("This may take a few minutes as it bundles Python and all libraries.")
    
    # We use flet pack, passing --uac-admin so Windows prompts for Administrator
    # privileges automatically upon launching the EXE (needed for Enforced Mode).
    command = [
        sys.executable, "-m", "flet", "pack", "app.py",
        "--name", "Scout",
        "--hidden-import", "win32file",
        "--hidden-import", "pywintypes",
        "--hidden-import", "watchdog",
        "--uac-admin",         # Trigger UAC prompt
        "--windowed"           # Hide the console window
    ]
    
    try:
        # Run the build command
        subprocess.run(command, check=True)
        print("\n\n✅ BUILD SUCCESSFUL!")
        print(f"Your executable is located in: {os.path.abspath('dist/Scout.exe')}")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ BUILD FAILED: {e}")
        print("Ensure 'flet' and 'pyinstaller' are installed.")

if __name__ == "__main__":
    build_executable()
