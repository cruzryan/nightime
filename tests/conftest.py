import sys
import pytest
from unittest.mock import MagicMock

# Mock out native extensions before importing our project logic so tests don't crash
# requiring a physical display server or throwing ctypes missing module exceptions.

mock_win32gui = MagicMock()
mock_win32api = MagicMock()
mock_win32con = MagicMock()
mock_pystray = MagicMock()
mock_ctypes = MagicMock()
mock_ctypes.wintypes = MagicMock()
mock_webview = MagicMock()

sys.modules['win32gui'] = mock_win32gui
sys.modules['win32api'] = mock_win32api
sys.modules['win32con'] = mock_win32con
sys.modules['pystray'] = mock_pystray
sys.modules['webview'] = mock_webview

@pytest.fixture(autouse=True)
def wipe_state():
    """Reset the nighttime module state cleanly before each test to prevent bleed."""
    import nighttime
    
    # We acquire the lock and wipe internal atomic states manually without kicking off the mock API calls 
    with nighttime._overlay_lock:
        nighttime._dim_level = 0
        nighttime._red_level = 0
        nighttime._running = True
