import os
import logging

try:
    import win32file
    import pywintypes
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False
    print("Warning: win32file not found. Locking mechanics will not work on non-Windows platforms.")

logger = logging.getLogger("Scout.SecurityManager")
if not logger.handlers:
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter("%(asctime)s | SECURITY | %(levelname)s | %(message)s"))
    logger.addHandler(ch)

class SecurityManager:
    """
    Manages active locks on files to prevent tampering.
    Uses Win32 Exclusive Handles (FILE_SHARE_READ only).
    """
    def __init__(self):
        self._active_locks = {}  # filepath: handle

    def lock_file(self, target_filepath: str) -> bool:
        """Applies an OS-level write lock to the file."""
        if not WIN32_AVAILABLE:
            logger.error("Cannot lock file: win32file is not available.")
            return False
            
        abs_path = os.path.abspath(target_filepath)
        if abs_path in self._active_locks:
            logger.info(f"File is already locked: {abs_path}")
            return True

        if not os.path.exists(abs_path):
            logger.error(f"Cannot lock non-existent file: {abs_path}")
            return False

        try:
            # We open for GENERIC_READ, but only allow others to FILE_SHARE_READ.
            # We explicitly exclude FILE_SHARE_WRITE and FILE_SHARE_DELETE.
            handle = win32file.CreateFileW(
                abs_path,
                win32file.GENERIC_READ,
                win32file.FILE_SHARE_READ,  # Allow reading, block writing/deleting
                None,
                win32file.OPEN_EXISTING,
                win32file.FILE_ATTRIBUTE_NORMAL,
                None
            )
            self._active_locks[abs_path] = handle
            logger.info(f"File LOCKED successfully: {abs_path}")
            return True
        except pywintypes.error as e:
            # Check if file is in use by someone else
            if e.winerror == 32:  # ERROR_SHARING_VIOLATION
                logger.error(f"Cannot lock file, it is already open by another process: {abs_path}")
            else:
                logger.error(f"Windows API Error locking {abs_path}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error locking {abs_path}: {e}")
            return False

    def unlock_file(self, target_filepath: str) -> bool:
        """Releases the lock on the file for On-Demand Checkout."""
        if not WIN32_AVAILABLE:
            return False

        abs_path = os.path.abspath(target_filepath)
        handle = self._active_locks.get(abs_path)
        
        if handle:
            try:
                win32file.CloseHandle(handle)
                del self._active_locks[abs_path]
                logger.info(f"File UNLOCKED (Checkout): {abs_path}")
                return True
            except Exception as e:
                logger.error(f"Error releasing lock for {abs_path}: {e}")
                return False
        else:
            return True

    def lock_path(self, target_path: str) -> bool:
        """Recursively locks a file or all files in a folder."""
        abs_path = os.path.abspath(target_path)
        if os.path.isfile(abs_path):
            return self.lock_file(abs_path)
        elif os.path.isdir(abs_path):
            success = True
            for root, _, files in os.walk(abs_path):
                for f in files:
                    if not self.lock_file(os.path.join(root, f)):
                        success = False
            return success
        return False

    def unlock_path(self, target_path: str) -> bool:
        """Unlocks a file or all files tracked within a folder tree."""
        abs_path = os.path.abspath(target_path)
        if os.path.isfile(abs_path):
            return self.unlock_file(abs_path)
        
        # Unlock all files that belong to this path tree
        to_unlock = [p for p in self._active_locks.keys() if p.startswith(abs_path)]
        success = True
        for p in to_unlock:
            if not self.unlock_file(p):
                success = False
        return success

    def is_locked(self, target_filepath: str) -> bool:
        """Check if Scout is currently holding a lock on the file."""
        return os.path.abspath(target_filepath) in self._active_locks

    def unlock_all(self):
        """Emergency release of all file locks."""
        for path in list(self._active_locks.keys()):
            self.unlock_file(path)


if __name__ == "__main__":
    # Test strict mode locking capability
    manager = SecurityManager()
    
    test_file = "lock_test.txt"
    with open(test_file, "w") as f:
        f.write("Some configuration data.")
        
    print("Locking...")
    manager.lock_file(test_file)
    
    print("Attempting to write while locked...")
    try:
        with open(test_file, "a") as f:
            f.write("\nHacked data")
        print("FAIL: Managed to write to locked file!")
    except PermissionError:
        print("SUCCESS: File write blocked by OS (PermissionError).")
        
    print("Unlocking...")
    manager.unlock_file(test_file)
    
    print("Attempting to write while unlocked...")
    try:
        with open(test_file, "a") as f:
            f.write("\nAuthorized edit")
        print("SUCCESS: Wrote to unlocked file.")
    except Exception as e:
        print(f"FAIL: {e}")
        
    os.remove(test_file)
