#!/usr/bin/env python3
"""Build script: compiles LIFE_GPT into a standalone .exe using PyInstaller."""
import os
import subprocess
import sys

def main():
    project_dir = os.path.dirname(os.path.abspath(__file__))
    spec_file = os.path.join(project_dir, "build_exe.spec")

    # Check if PyInstaller is installed
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        print("PyInstaller not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    # Build
    print("Building LIFE_GPT.exe with PyInstaller...")
    subprocess.check_call([
        sys.executable, "-m", "PyInstaller",
        spec_file,
        "--noconfirm",
        "--clean",
    ])

    exe_path = os.path.join(project_dir, "dist", "life_gpt.exe")
    if os.path.exists(exe_path):
        print(f"\nBuild successful! Executable: {exe_path}")
    else:
        print("\nBuild completed but exe not found at expected path.")
        print("Check dist/life_gpt/life_gpt.exe")

if __name__ == "__main__":
    main()
