# 🌙 Nighttime

A minimalist, high-performance screen dimmer for Windows, optimized for OLED displays.

## ✨ Key Features

*   **OLED-Safe Dimming**: Uses a pure black hardware-accelerated overlay. Perfect for keeping contrast high on OLED panels.
*   **f.lux-style Red Shift**: Uses driver-level Gamma Ramps to suppress blue/green light, making the screen warmer without reducing brightness.
*   **Ultra Minimalist**: No window clutter. It lives entirely in your system tray.
*   **Panic Button**: Press `Esc` at any time to instantly restore your screen to 100% brightness and normal color.
*   **Zero-Lag Performance**: Uses efficient `SetLayeredWindowAttributes` for real-time responsiveness with zero CPU/GPU overhead.
*   **HiDPI Aware**: Automatically handles Windows scaling, ensuring the overlay covers the full screen on 4K and Retina displays.

## 🚀 How to Use

1.  **Launch**: Run `dist/nighttime.exe`.
2.  **Access**: Look for the **Moon Icon** 🌙 in your Windows System Tray (bottom right).
3.  **Control**:
    *   **Left-Click** the tray icon to open the Control Panel.
    *   **Dim Slider**: Controls the darkness of the black overlay.
    *   **Redness Slider**: Controls the warmth (blue-light suppression).
    *   **Disable**: Instantly clear all effects.
4.  **Quick Exit**: Press the `Esc` key on your keyboard to instantly return to normal settings.

## 🛠️ Development & Building

If you want to modify the code:

### Requirements
*   Python 3.12+
*   Dependencies: `pip install -r requirements.txt`

### Build your own EXE
Run the build script to package everything into a single file:
```powershell
python build.py
```
The result will be in the `dist/` folder.
