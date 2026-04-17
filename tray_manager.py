import threading
import pystray
from pystray import MenuItem as item
from PIL import Image, ImageDraw

def create_image():
    """Generates a default icon for the system tray (cyan circle on dark bg)."""
    image = Image.new('RGB', (64, 64), color=(11, 12, 16))
    d = ImageDraw.Draw(image)
    d.ellipse((16, 16, 48, 48), fill=(102, 252, 241))
    return image

class TrayManager:
    """
    Manages the Windows System Tray icon using pystray.
    Allows Scout to run silently in the background while still protecting files.
    """
    def __init__(self, on_show_callback, on_exit_callback):
        self.on_show = on_show_callback
        self.on_exit = on_exit_callback
        self.icon = None
        self._thread = None

    def _setup_icon(self):
        menu = (
            item('Open Scout Dashboard', self._on_show_clicked, default=True),
            item('Exit Scout', self._on_exit_clicked)
        )
        self.icon = pystray.Icon("Scout", create_image(), "Scout - Active Defense", menu)
        # Blocks the thread, so we run it inside a daemon thread
        self.icon.run()

    def _on_show_clicked(self, icon, item_ref):
        if self.on_show:
            self.on_show()

    def _on_exit_clicked(self, icon, item_ref):
        if self.icon:
            self.icon.stop()
        if self.on_exit:
            self.on_exit()

    def start(self):
        self._thread = threading.Thread(target=self._setup_icon, daemon=True)
        self._thread.start()

    def notify(self, title, message):
        """Sends a stable Windows native notification using the existing Tray Icon loop."""
        if self.icon:
            try:
                self.icon.notify(message, title)
            except Exception:
                pass
        
    def stop(self):
        if self.icon:
            self.icon.stop()

if __name__ == "__main__":
    import time
    def show(): print("Show!")
    def quit(): print("Quit!")
    tm = TrayManager(show, quit)
    tm.start()
    print("Tray icon active. Press Ctrl+C directly to stop testing.")
    while True:
        time.sleep(1)
