"""
TBMG_Country_MainCity2 — Dedicated Live Overwatch & Citizen Telemetry Terminal
Opens in a separate terminal window/tab and streams all Half-Life 2 / Source Engine
events, Combine radio dispatches (540+ lines), Citizen voice lines, weapon reloads,
and Map Editor actions with ANSI colors and emojis instead of cluttering the 3D HUD.
"""
import ctypes
import os
import sys
import time


def enable_windows_ansi_and_utf8():
    """Enables UTF-8 output and Windows 10/11 Virtual Terminal ANSI color sequences."""
    if sys.platform == "win32":
        try:
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleOutputCP(65001)
            kernel32.SetConsoleCP(65001)
            # Enable ENABLE_VIRTUAL_TERMINAL_PROCESSING (0x0004) on STD_OUTPUT_HANDLE (-11)
            h_out = kernel32.GetStdHandle(-11)
            mode = ctypes.c_uint32()
            if kernel32.GetConsoleMode(h_out, ctypes.byref(mode)):
                kernel32.SetConsoleMode(h_out, mode.value | 0x0004)
            kernel32.SetConsoleTitleW("λ TBMG — Half-Life 2 Live Overwatch & Telemetry Log Terminal")
        except Exception:
            pass
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


# ANSI Color Palette
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
HL2_ORANGE = "\033[38;5;208m"
HL2_AMBER = "\033[38;5;214m"
COMBINE_CYAN = "\033[38;5;51m"
CITIZEN_GREEN = "\033[38;5;114m"
WARN_YELLOW = "\033[38;5;226m"
ERROR_RED = "\033[38;5;196m"
ADMIN_PURPLE = "\033[38;5;207m"
WATER_BLUE = "\033[38;5;39m"
EDITOR_LIME = "\033[38;5;154m"
GRAY = "\033[38;5;245m"


def format_colored_log_line(level, msg, timestamp=0.0):
    """Formats a game log entry with rich ANSI colors and Half-Life 2 / Source emojis."""
    u_msg = str(msg).upper()
    if level == "dispatch" or "OVERWATCH PA" in u_msg or "OVERWATCH DISPATCH" in u_msg:
        icon = "📢"
        tag = f"{COMBINE_CYAN}{BOLD}[OVERWATCH PA] {RESET}"
        text_col = COMBINE_CYAN
    elif "CP UNIT" in u_msg or "OVERWATCH" in u_msg or "CIVIL PROTECTION" in u_msg or "METROCOP" in u_msg:
        icon = "🚓"
        tag = f"{COMBINE_CYAN}{BOLD}[COMBINE RADIO]{RESET}"
        text_col = COMBINE_CYAN
    elif "CITIZEN" in u_msg:
        icon = "🗣️"
        tag = f"{CITIZEN_GREEN}{BOLD}[CITIZEN VOICE]{RESET}"
        text_col = CITIZEN_GREEN
    elif "MAP EDITOR" in u_msg or "PLACED" in u_msg or "CUSTOM_MAPS" in u_msg:
        icon = "🛠️"
        tag = f"{EDITOR_LIME}{BOLD}[MAP EDITOR]   {RESET}"
        text_col = EDITOR_LIME
    elif "VPHYSICS" in u_msg or "WATER" in u_msg or "SOURCE ENGINE" in u_msg:
        icon = "🌊"
        tag = f"{WATER_BLUE}{BOLD}[SOURCE ENGINE]{RESET}"
        text_col = WATER_BLUE
    elif "RELOAD" in u_msg or "WEAPON" in u_msg or "ARMED" in u_msg or "PICKED UP" in u_msg:
        icon = "🔫"
        tag = f"{HL2_ORANGE}{BOLD}[HL2 ARSENAL]  {RESET}"
        text_col = HL2_AMBER
    elif "SETTINGS" in u_msg or "GRAPHICS" in u_msg or "FOG" in u_msg:
        icon = "⚙️"
        tag = f"{WARN_YELLOW}{BOLD}[SETTINGS]     {RESET}"
        text_col = WARN_YELLOW
    elif level == "admin" or "PRESIDENT" in u_msg or "DARK LEADER" in u_msg:
        icon = "👑"
        tag = f"{ADMIN_PURPLE}{BOLD}[EXECUTIVE]    {RESET}"
        text_col = ADMIN_PURPLE
    elif level == "error" or "DEATH" in u_msg or "CRASH" in u_msg:
        icon = "💀"
        tag = f"{ERROR_RED}{BOLD}[CRITICAL]     {RESET}"
        text_col = ERROR_RED
    elif level == "warn" or "WANTED" in u_msg:
        icon = "⚠️"
        tag = f"{WARN_YELLOW}{BOLD}[TACTICAL WARN]{RESET}"
        text_col = WARN_YELLOW
    elif level == "sys":
        icon = "📡"
        tag = f"{COMBINE_CYAN}{BOLD}[SYSTEM]       {RESET}"
        text_col = "\033[38;5;159m"
    else:
        icon = "λ "
        tag = f"{HL2_ORANGE}{BOLD}[HL2 EVENT]    {RESET}"
        text_col = "\033[38;5;252m"

    time_str = f"{GRAY}[{timestamp:06.1f}s]{RESET}"
    return f"  {time_str} {icon} {tag} {text_col}{msg}{RESET}"


def is_spam_or_ambient_line(raw_line):
    """Filters out annoying repetitive ambient mutterings, micro ticks, and clutter in clean mode."""
    u = raw_line.upper()
    if "SOMETIMES, I DREAM ABOUT CHEESE" in u:
        return True
    if "BUMPED OFFICER" in u:
        return True
    if "SECURITY DOOR OPENING" in u:
        return True
    if "CAMERA SWITCHED" in u:
        return True
    if "PUNTED " in u:
        return True
    if "RELOADING " in u:
        return True
    if "RELOADED!" in u:
        return True
    return False


def print_terminal_header():
    print(f"{HL2_ORANGE}{BOLD}╔══════════════════════════════════════════════════════════════════════════════════════╗{RESET}")
    print(f"{HL2_ORANGE}{BOLD}║  λ  TBMG_Country_MainCity2 — HALF-LIFE 2 LIVE OVERWATCH & TELEMETRY TERMINAL    🔊   ║{RESET}")
    print(f"{HL2_ORANGE}{BOLD}║  🚓 Tactical Combine Dispatch      |  💀 Combat Milestones |  🔫 Weapon Upgrades      ║{RESET}")
    print(f"{HL2_ORANGE}{BOLD}║  🛠️ Hammer Map Editor Operations   |  ⚠️ Threat Alerts     |  🌊 Source Engine Events ║{RESET}")
    print(f"{HL2_ORANGE}{BOLD}╚══════════════════════════════════════════════════════════════════════════════════════╝{RESET}")
    print(f"  {CITIZEN_GREEN}{BOLD}🛡️  ANTI-SPAM FILTER ACTIVE [Clean / Tactical Mode]{RESET}")
    print(f"  {GRAY}   Ambient repetitive chatter and micro-ticks are suppressed so the terminal stays clean.{RESET}")
    print(f"  {COMBINE_CYAN}✨ In-game HUD log overlay removed — 3D viewport remains 100% immersive.{RESET}\n")


def main():
    enable_windows_ansi_and_utf8()
    os.system("cls" if os.name == "nt" else "clear")
    print_terminal_header()

    log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "live_game_log.log")
    if not os.path.exists(log_path):
        with open(log_path, "w", encoding="utf-8") as f:
            pass

    with open(log_path, "r", encoding="utf-8", errors="replace") as f:
        # Read existing lines from current session
        while True:
            line = f.readline()
            if not line:
                time.sleep(0.08)
                continue
            if is_spam_or_ambient_line(line):
                continue
            sys.stdout.write(line)
            sys.stdout.flush()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{HL2_ORANGE}  [λ] Live Telemetry Terminal closed.{RESET}")
