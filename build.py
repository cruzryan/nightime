"""
build.py — Build a single executable using PyInstaller.

Run on Windows cmd:
    python build.py

Output: dist/nighttime.exe
"""

import os
import sys
import subprocess
import shutil

SRC_DIR = os.path.dirname(os.path.abspath(__file__))
DIST_DIR = os.path.join(SRC_DIR, "dist")


def clean():
    for d in ("build", "dist", "__pycache__"):
        p = os.path.join(SRC_DIR, d)
        if os.path.exists(p):
            shutil.rmtree(p)
    spec = os.path.join(SRC_DIR, "nighttime.spec")
    if os.path.exists(spec):
        os.remove(spec)


def build():
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=nighttime",
        "--onefile",
        "--windowed",
        "--add-data=ui;ui",          # Windows separator is semicolon
        "--hidden-import=pystray",
        "--hidden-import=PIL",
        "--hidden-import=win32api",
        "--hidden-import=win32gui",
        "--hidden-import=win32con",
        "--collect-all=pystray",
        "--collect-all=Pillow",
        os.path.join(SRC_DIR, "main.py"),
    ]

    print("Building…")
    result = subprocess.run(cmd, cwd=SRC_DIR)
    if result.returncode != 0:
        print("Build FAILED")
        sys.exit(1)

    exe = os.path.join(DIST_DIR, "nighttime.exe")
    if os.path.exists(exe):
        sz = os.path.getsize(exe) // 1024
        print(f"Build OK — {exe}  ({sz} KB)")
    else:
        print("Build completed but exe not found at", exe)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "clean":
        clean()
    else:
        build()
