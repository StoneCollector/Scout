import os
import ctypes
import shutil
import logging
from pathlib import Path

# Setup simple logger for the vault
logger = logging.getLogger("Scout.Vault")
if not logger.handlers:
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter("%(asctime)s | VAULT | %(levelname)s | %(message)s"))
    logger.addHandler(ch)

class RecoveryVault:
    def __init__(self, vault_path: str = ".scout_vault"):
        self.vault_path = os.path.abspath(vault_path)
        self.xor_key = 0x55 # Simple salt/key for obfuscation
        self._initialize_vault()

    def _encode_data(self, data: bytes) -> bytes:
        import base64
        # XOR every byte
        encoded = bytes([b ^ self.xor_key for b in data])
        return base64.b64encode(encoded)

    def _decode_data(self, data: bytes) -> bytes:
        import base64
        decoded = base64.b64decode(data)
        return bytes([b ^ self.xor_key for b in decoded])

    def _initialize_vault(self):
        """Creates the vault directory and sets it to Hidden on Windows."""
        if not os.path.exists(self.vault_path):
            try:
                os.makedirs(self.vault_path)
                logger.info(f"Initialized new Recovery Vault at: {self.vault_path}")
            except PermissionError:
                logger.error(f"CRITICAL: Permission Denied while creating vault at {self.vault_path}. "
                             "Ensure the application has write access to the project directory.")
                return
            except Exception as e:
                logger.error(f"Failed to create vault directory: {e}")
                return

        # Hide the directory on Windows
        try:
            FILE_ATTRIBUTE_HIDDEN = 0x02
            ret = ctypes.windll.kernel32.SetFileAttributesW(self.vault_path, FILE_ATTRIBUTE_HIDDEN)
            if not ret:
                logger.warning("Failed to hide the vault directory.")
        except Exception as e:
            logger.warning(f"Could not hide vault directory: {e}")

    def _get_vault_file_path(self, target_filepath: str) -> str:
        """Translates a real file path into its vault counterpart."""
        abs_target = os.path.abspath(target_filepath)
        # Strip the drive letter and colon (e.g., "C:\") safely
        drive, path_tail = os.path.splitdrive(abs_target)
        if path_tail.startswith("\\") or path_tail.startswith("/"):
            path_tail = path_tail[1:]
        
        return os.path.join(self.vault_path, "cache", drive.replace(":", ""), path_tail)

    def get_pristine_path(self, target_filepath: str) -> str:
        """Public accessor for the physical vault copy path."""
        return self._get_vault_file_path(target_filepath)

    def load_pristine_content(self, target_filepath: str) -> list:
        """Reads encoded file from vault and returns decoded list of strings (lines)."""
        vault_src = self._get_vault_file_path(target_filepath)
        if not os.path.exists(vault_src):
            return []
        try:
            with open(vault_src, "rb") as f:
                raw = f.read()
            decoded_bytes = self._decode_data(raw)
            # Use utf-8-sig to handle Windows BOMs consistently across the forensic pipeline
            return decoded_bytes.decode("utf-8-sig", errors="replace").splitlines(keepends=True)
        except Exception:
            return []

    def store_good_version(self, target_filepath: str) -> bool:
        """Encodes and copies the 'Last Known Good' file into the vault."""
        if not os.path.exists(target_filepath):
            logger.error(f"Cannot store baseline. Target does not exist: {target_filepath}")
            return False

        vault_dest = self._get_vault_file_path(target_filepath)
        os.makedirs(os.path.dirname(vault_dest), exist_ok=True)
        
        try:
            if not os.path.exists(target_filepath):
                logger.error(f"Baseline FAILED - Source missing: {target_filepath}")
                return False

            with open(target_filepath, "rb") as f_in:
                data = f_in.read()
            
            logger.info(f"Read {len(data)} bytes from {os.path.basename(target_filepath)}")
            encoded = self._encode_data(data)
            
            with open(vault_dest, "wb") as f_out:
                f_out.write(encoded)
            
            if os.path.exists(vault_dest):
                logger.info(f"Baseline SUCCESS: {target_filepath} -> {vault_dest}")
                return True
            else:
                logger.error(f"Baseline FAILED - File not written to {vault_dest}")
                return False
                
        except Exception as e:
            logger.error(f"Baseline CRITICAL ERROR [{type(e).__name__}]: {e} | Path: {target_filepath}")
            return False

    def heal_file(self, target_filepath: str) -> bool:
        """Decodes and restores a file from the vault."""
        vault_src = self._get_vault_file_path(target_filepath)
        
        if not os.path.exists(vault_src):
            logger.error(f"Cannot heal! No pristine copy exists in vault for: {target_filepath}")
            return False

        try:
            with open(vault_src, "rb") as f_in:
                encoded = f_in.read()
            decoded = self._decode_data(encoded)
            with open(target_filepath, "wb") as f_out:
                f_out.write(decoded)
            logger.critical(f"SELF-HEALING EXECUTED: Decoded and Restored {target_filepath}")
            return True
        except Exception as e:
            logger.error(f"Self-Healing FAILED for {target_filepath}: {e}")
            return False

    def is_tracked(self, target_filepath: str) -> bool:
        """Check if a file is currently backed up in the vault."""
        return os.path.exists(self._get_vault_file_path(target_filepath))

if __name__ == "__main__":
    # Quick test
    vault = RecoveryVault()
    test_file = "test_config.txt"
    with open(test_file, "w") as f:
        f.write("PRISTINE DATA")
    
    vault.store_good_version(test_file)
    
    # Tamper
    with open(test_file, "w") as f:
        f.write("HACKED DATA")
        
    print("Before Healed:")
    with open(test_file, "r") as f: print(f.read())
    
    vault.heal_file(test_file)
    
    print("After Healed:")
    with open(test_file, "r") as f: print(f.read())
    
    os.remove(test_file)
