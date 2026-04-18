"""
Nighttime — f.lux-style screen dimmer for Windows with OLED support.

Core logic:
  - Overlay window (WS_EX_LAYERED) for dimming — pure black, variable alpha.
  - SetDeviceGammaRamp for red-shift  — suppresses blue/green at the driver level,
    exactly like f.lux / Windows Night Light.
  - System tray icon.
  - Low-level keyboard hook for Esc to disable.
"""

import ctypes
import ctypes.wintypes as wt
import threading
import time

import pystray
import win32api
import win32gui
import win32con

# ─── DPI Awareness ───────────────────────────────────────────────────────────
# Must be set before any GetSystemMetrics / CreateWindow calls, otherwise
# Windows returns scaled-down logical pixels and the overlay won't cover
# the full physical screen.
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)   # PROCESS_PER_MONITOR_DPI_AWARE
except Exception:
    ctypes.windll.user32.SetProcessDPIAware()        # Fallback for older Windows


# ─── State ───────────────────────────────────────────────────────────────────

_overlay_hwnd = None
_overlay_lock = threading.Lock()
_dim_level = 0     # 0–100
_red_level = 0     # 0–100
_running = True
_keyboard_hook = None
_hook_proc_ref = None
_original_gamma = None   # saved on first use so we can restore it


# ─── Gamma Ramp (red-shift) ──────────────────────────────────────────────────
#
# f.lux doesn't overlay red — it modifies the display's gamma ramp so the
# monitor itself suppresses blue and green.  Result: the screen looks *warmer*
# without getting brighter, and it composes naturally with the dim overlay.

_GammaArray = (wt.WORD * 256) * 3   # [R][G][B], each 256 entries of WORD


def _save_original_gamma():
    """Grab the current gamma ramp so we can restore it on exit."""
    global _original_gamma
    if _original_gamma is not None:
        return
    hdc = win32gui.GetDC(0)
    ramp = _GammaArray()
    ctypes.windll.gdi32.GetDeviceGammaRamp(hdc, ctypes.byref(ramp))
    win32gui.ReleaseDC(0, hdc)
    _original_gamma = ramp


def _apply_gamma(red_level):
    """
    Adjust the display gamma ramp based on red_level (0–100).

    red_level=0   → normal display (linear ramp)
    red_level=100 → maximum warm shift: blue gone, green at 20%
    """
    _save_original_gamma()

    frac = red_level / 100.0
    # How much to suppress each channel at max red:
    #   Blue:  fully removed   (scale → 0.0)
    #   Green: mostly removed  (scale → 0.20)
    #   Red:   untouched       (scale → 1.0)
    green_scale = 1.0 - frac * 0.80   # 1.0 → 0.20
    blue_scale  = 1.0 - frac * 1.00   # 1.0 → 0.00

    ramp = _GammaArray()
    for i in range(256):
        normal = i * 257   # 0→0, 255→65535 (standard linear ramp)
        ramp[0][i] = int(normal)                        # Red — untouched
        ramp[1][i] = int(normal * green_scale)           # Green — suppressed
        ramp[2][i] = int(normal * blue_scale)            # Blue — suppressed

    hdc = win32gui.GetDC(0)
    ctypes.windll.gdi32.SetDeviceGammaRamp(hdc, ctypes.byref(ramp))
    win32gui.ReleaseDC(0, hdc)


def _restore_gamma():
    """Restore the original gamma ramp (undo red-shift)."""
    if _original_gamma is None:
        return
    hdc = win32gui.GetDC(0)
    ctypes.windll.gdi32.SetDeviceGammaRamp(hdc, ctypes.byref(_original_gamma))
    win32gui.ReleaseDC(0, hdc)


# ─── Overlay Window (dimming only) ───────────────────────────────────────────

_user32 = ctypes.windll.user32

def _overlay_wndproc(hwnd, msg, wparam, lparam):
    if msg == win32con.WM_DESTROY:
        win32gui.PostQuitMessage(0)
        return 0
    if msg == win32con.WM_ERASEBKGND:
        # Paint the window solid black — required for SetLayeredWindowAttributes
        dc = wparam
        rect = win32gui.GetClientRect(hwnd)
        brush = win32gui.CreateSolidBrush(0x00000000)  # Black
        win32gui.FillRect(dc, rect, brush)
        win32gui.DeleteObject(brush)
        return 1
    return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)


def _create_overlay():
    screen_w = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
    screen_h = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)

    # Use a solid black brush so the window is fully black
    black_brush = win32gui.CreateSolidBrush(0x00000000)

    wc = win32gui.WNDCLASS()
    wc.lpfnWndProc = _overlay_wndproc
    wc.lpszClassName = "NighttimeOverlayClass"
    wc.hbrBackground = black_brush
    wc.style = win32con.CS_VREDRAW | win32con.CS_HREDRAW
    win32gui.RegisterClass(wc)

    hwnd = win32gui.CreateWindowEx(
        win32con.WS_EX_LAYERED
        | win32con.WS_EX_TOPMOST
        | win32con.WS_EX_TRANSPARENT
        | win32con.WS_EX_NOACTIVATE
        | win32con.WS_EX_TOOLWINDOW,
        wc.lpszClassName,
        "NighttimeOverlay",
        win32con.WS_POPUP,
        0, 0, screen_w, screen_h,
        None, None, None, None,
    )

    # Initialize with fully transparent so it starts hidden
    win32gui.SetLayeredWindowAttributes(hwnd, 0, 0, win32con.LWA_ALPHA)
    win32gui.ShowWindow(hwnd, win32con.SW_HIDE)
    return hwnd


def _update_overlay():
    """Update the dim overlay using SetLayeredWindowAttributes.
    
    Pure black window with alpha = dim_level mapped to 0–255.
    This is much simpler and more reliable than per-pixel UpdateLayeredWindow.
    """
    global _overlay_hwnd
    if _overlay_hwnd is None:
        return

    with _overlay_lock:
        dim = _dim_level

    if dim == 0:
        _user32.ShowWindow(_overlay_hwnd, win32con.SW_HIDE)
        return

    # Map 0–100 to 0–255 alpha. At 100% dim, alpha must be exactly 255 (fully opaque black).
    alpha = int(round(dim * 255.0 / 100.0))
    alpha = max(0, min(255, alpha))

    win32gui.SetLayeredWindowAttributes(_overlay_hwnd, 0, alpha, win32con.LWA_ALPHA)
    _user32.ShowWindow(_overlay_hwnd, win32con.SW_SHOWNOACTIVATE)


# ─── Keyboard Hook ────────────────────────────────────────────────────────────

_HOOKPROC = ctypes.WINFUNCTYPE(wt.LPARAM, ctypes.c_int, wt.WPARAM, wt.LPARAM)

_user32.SetWindowsHookExW.argtypes   = [ctypes.c_int, _HOOKPROC, wt.HINSTANCE, wt.DWORD]
_user32.SetWindowsHookExW.restype    = wt.HHOOK
_user32.CallNextHookEx.argtypes      = [wt.HHOOK, ctypes.c_int, wt.WPARAM, wt.LPARAM]
_user32.CallNextHookEx.restype       = wt.LPARAM
_user32.UnhookWindowsHookEx.argtypes = [wt.HHOOK]
_user32.UnhookWindowsHookEx.restype  = wt.BOOL


def _low_level_keyboard_proc(nCode, wParam, lParam):
    try:
        if nCode >= 0 and (wParam == 0x100 or wParam == 0x104):
            vk = ctypes.cast(lParam, ctypes.POINTER(ctypes.c_ulong))[0]
            if vk == 0x1B:  # VK_ESCAPE
                threading.Thread(target=disable_all, daemon=True).start()
    except Exception:
        pass
    return _user32.CallNextHookEx(_keyboard_hook, nCode, wParam, lParam)


def _install_hook():
    global _keyboard_hook, _hook_proc_ref
    proc = _HOOKPROC(_low_level_keyboard_proc)
    _hook_proc_ref = proc
    _keyboard_hook = _user32.SetWindowsHookExW(13, proc, None, 0)


def _remove_hook():
    global _keyboard_hook
    if _keyboard_hook:
        _user32.UnhookWindowsHookEx(_keyboard_hook)
        _keyboard_hook = None


# ─── System Tray ─────────────────────────────────────────────────────────────

_tray_icon = None
_show_callback = None


def set_show_callback(cb):
    global _show_callback
    _show_callback = cb


def _make_tray_icon():
    from PIL import Image, ImageDraw
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse((8, 8, 56, 56), fill=(160, 140, 255, 255))
    draw.ellipse((20, 4, 60, 44), fill=(0, 0, 0, 0))
    return img


def _show_ui(icon, item):
    if _show_callback:
        _show_callback()


def _setup_tray():
    global _tray_icon
    _tray_icon = pystray.Icon(
        "Nighttime",
        _make_tray_icon(),
        "Nighttime",
        menu=pystray.Menu(
            pystray.MenuItem("Show", _show_ui, default=True),
            pystray.MenuItem("Disable", lambda _: disable_all()),
            pystray.MenuItem("Exit", lambda _: shutdown()),
        ),
    )


def _run_tray():
    if _tray_icon:
        _tray_icon.run()


# ─── Public API ──────────────────────────────────────────────────────────────

def set_dim(level: int):
    global _dim_level
    with _overlay_lock:
        _dim_level = max(0, min(100, int(level)))
    _update_overlay()


def set_red(level: int):
    global _red_level
    with _overlay_lock:
        _red_level = max(0, min(100, int(level)))
    _apply_gamma(_red_level)


def disable_all():
    global _dim_level, _red_level
    with _overlay_lock:
        _dim_level = 0
        _red_level = 0
    _update_overlay()
    _restore_gamma()


def get_state():
    with _overlay_lock:
        return {"dim": _dim_level, "red": _red_level}


def shutdown():
    global _running
    _running = False
    _remove_hook()
    _restore_gamma()
    win32gui.PostQuitMessage(0)


# ─── Main ────────────────────────────────────────────────────────────────────

def main(on_ready):
    global _overlay_hwnd

    _overlay_hwnd = _create_overlay()
    _save_original_gamma()
    _install_hook()
    _setup_tray()

    threading.Thread(target=_run_tray, daemon=True).start()
    on_ready()

    while _running:
        win32gui.PumpWaitingMessages()
        time.sleep(0.016)

    _remove_hook()
    _restore_gamma()
    if _tray_icon:
        _tray_icon.stop()
    if _overlay_hwnd:
        try:
            win32gui.DestroyWindow(_overlay_hwnd)
        except Exception:
            pass
