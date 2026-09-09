"""
Build TBMG_Country_MainCity2 DOOM Edition as a standalone Windows EXE.
Run: python build_exe.py
"""
import subprocess
import sys

def main():
    print("="*60)
    print("  TBMG_Country_MainCity2 — DOOM Edition EXE Builder")
    print("  7 Weapons · Doom AI · Doors · Pickups · Automap")
    print("  Build 6660 | Instability: HELLISH")
    print("="*60)

    # Install pyinstaller if needed
    print("\n[1/2] Ensuring PyInstaller is installed...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller", "--quiet"])

    # Build
    print("[2/2] Building EXE...")
    subprocess.check_call([
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--windowed",
        "--name", "TBMG_Country_DOOM",
        "--icon", "NONE",
        "game.py"
    ])

    print("\n" + "="*60)
    print("  BUILD COMPLETE!")
    print("  EXE Location: dist/TBMG_Country_DOOM.exe")
    print("="*60)

if __name__ == "__main__":
    main()
