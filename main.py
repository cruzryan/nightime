"""
Nighttime — entry point.

Starts the core engine in a background thread, then launches the
pywebview control panel (Chromium Edge web UI).
"""

import os
import sys
import threading

import webview

if hasattr(sys, '_MEIPASS'):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    
UI_DIR = os.path.join(BASE_DIR, "ui")


class Api:
    def __init__(self, window_ref):
        self._window_ref = window_ref

    def nt_set_dim(self, v):
        import nighttime
        nighttime.set_dim(v)

    def nt_set_red(self, v):
        import nighttime
        nighttime.set_red(v)

    def nt_disable(self):
        import nighttime
        nighttime.disable_all()

    def nt_get_state(self):
        import nighttime
        # Return simple primitives only
        state = nighttime.get_state()
        return {"dim": int(state["dim"]), "red": int(state["red"])}

    def nt_quit(self):
        import nighttime
        nighttime.shutdown()
        win = self._window_ref()
        if win:
            win.destroy()

    def nt_hide(self):
        win = self._window_ref()
        if win:
            win.hide()


def main():
    import nighttime
    import weakref

    # Use a container so we can pass the window to the API before it's actually created if needed
    # but create_window returns it. We use weakref to avoid any circular nonsense.
    window_container = []
    
    def get_window():
        return window_container[0] if window_container else None

    api = Api(lambda: window_container[0] if window_container else None)

    html_path = os.path.join(UI_DIR, "index.html")
    width, height = 380, 430
    window = webview.create_window(
        "Nighttime",
        html_path,
        width=width,
        height=height,
        resizable=False,
        on_top=True,
        frameless=True,
        hidden=True,
        easy_drag=False,
        js_api=api
    )
    window_container.append(window)

    def show_ui():
        try:
            import win32gui, win32con
            rect = win32gui.SystemParametersInfo(win32con.SPI_GETWORKAREA)
            x = rect[2] - width - 12
            y = rect[3] - height - 12
            window.move(x, y)
        except Exception:
            pass
        window.show()

    def on_ready():
        nighttime.set_show_callback(show_ui)

    engine_thread = threading.Thread(
        target=nighttime.main,
        args=(on_ready,),
        daemon=True,
    )
    engine_thread.start()

    webview.start(http_server=False)


if __name__ == "__main__":
    main()
