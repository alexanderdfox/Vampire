#!/usr/bin/env python3
"""
Vampire Monitor – cross-platform (Linux, macOS, Windows, BSD)
Detects logged-in users in a target group and flags long-running / idle sessions.
"""

import platform
import os
import sys
import subprocess
import getpass
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple

# ---------- Configuration ----------
TARGET_GROUP = "developers"
IDLE_THRESHOLD_MIN = 30          # minutes
SHOW_TOP_PROCESSES = 5

# ---------- Optional dependency ----------
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    print("Note: Install 'psutil' for best results →  pip install psutil\n")

SYSTEM = platform.system()  # 'Linux', 'Darwin', 'Windows', 'FreeBSD', ...


def get_current_user() -> str:
    return getpass.getuser()


def get_group_members(group: str) -> List[str]:
    """Return list of usernames in the given group (best-effort)."""
    members = []

    if SYSTEM in ("Linux", "Darwin", "FreeBSD", "OpenBSD", "NetBSD"):
        try:
            import grp
            g = grp.getgrnam(group)
            members = list(g.gr_mem)
            # Also include the primary group owner if relevant
        except KeyError:
            print(f"Group '{group}' not found.")
        except Exception as e:
            print(f"Could not read group (Unix): {e}")

    elif SYSTEM == "Windows":
        try:
            # net localgroup is available on all modern Windows
            result = subprocess.run(
                ["net", "localgroup", group],
                capture_output=True, text=True, timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0
            )
            if result.returncode == 0:
                lines = result.stdout.splitlines()
                in_members = False
                for line in lines:
                    line = line.strip()
                    if line.lower().startswith("members"):
                        in_members = True
                        continue
                    if in_members:
                        if not line or line.startswith("---") or "The command completed" in line:
                            break
                        # Windows can show DOMAIN\user
                        user = line.split("\\")[-1].strip()
                        if user:
                            members.append(user)
            else:
                print(f"Group '{group}' not found or access denied.")
        except Exception as e:
            print(f"Could not read group (Windows): {e}")

    else:
        print(f"Group lookup not implemented for {SYSTEM}")

    return sorted(set(members))


def get_logged_in_users() -> List[Dict]:
    """
    Returns list of dicts:
    {name, terminal, host, started (datetime or None), pid}
    """
    users = []

    if HAS_PSUTIL:
        for u in psutil.users():
            started = None
            if u.started:
                started = datetime.fromtimestamp(u.started)
            users.append({
                "name": u.name,
                "terminal": u.terminal,
                "host": u.host,
                "started": started,
                "pid": u.pid,
            })
        return users

    # Fallback without psutil
    if SYSTEM in ("Linux", "Darwin", "FreeBSD"):
        try:
            result = subprocess.run(["who"], capture_output=True, text=True, timeout=5)
            for line in result.stdout.splitlines():
                parts = line.split()
                if len(parts) >= 2:
                    users.append({
                        "name": parts[0],
                        "terminal": parts[1] if len(parts) > 1 else None,
                        "host": parts[4] if len(parts) > 4 else None,
                        "started": None,
                        "pid": None,
                    })
        except Exception:
            pass

    elif SYSTEM == "Windows":
        try:
            # query user / quser
            result = subprocess.run(
                ["query", "user"], capture_output=True, text=True, timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0
            )
            # parsing quser output is messy; leave empty if it fails
        except Exception:
            pass

    return users


def session_age_minutes(started: Optional[datetime]) -> Optional[float]:
    if not started:
        return None
    delta = datetime.now() - started
    return delta.total_seconds() / 60.0


def get_unix_idle_from_w(username: str) -> Optional[str]:
    """Best-effort idle string from classic 'w' command (Unix only)."""
    try:
        result = subprocess.run(["w", "-h", username], capture_output=True, text=True, timeout=3)
        if result.returncode == 0 and result.stdout.strip():
            # Typical: USER TTY FROM LOGIN@ IDLE ...
            parts = result.stdout.split()
            if len(parts) >= 5:
                return parts[4]  # idle column
    except Exception:
        pass
    return None


def get_top_processes(username: str, n: int = 5) -> List[Tuple]:
    """Return list of (pid, cpu%, mem%, name) for the user."""
    if not HAS_PSUTIL:
        return []

    procs = []
    for p in psutil.process_iter(["pid", "username", "cpu_percent", "memory_percent", "name"]):
        try:
            if p.info["username"] == username:
                # cpu_percent needs a previous call or interval; we do a quick sample
                cpu = p.cpu_percent(interval=0.05)
                procs.append((
                    p.info["pid"],
                    cpu,
                    p.info["memory_percent"] or 0.0,
                    p.info["name"] or "?"
                ))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    # Sort by CPU descending
    procs.sort(key=lambda x: x[1], reverse=True)
    return procs[:n]


def main():
    current = get_current_user()
    print("=" * 60)
    print("Vampire Monitor – Cross Platform")
    print(f"OS          : {SYSTEM} ({platform.platform()})")
    print(f"Current user: {current}")
    print(f"Target group: {TARGET_GROUP}")
    print(f"Threshold   : {IDLE_THRESHOLD_MIN} minutes")
    print("=" * 60)
    print()

    # 1. Current user
    print(f"--- Current User: {current} ---")
    logged_in = get_logged_in_users()
    my_sessions = [u for u in logged_in if u["name"] == current]

    if my_sessions:
        print("Active session(s):")
        for s in my_sessions:
            age = session_age_minutes(s["started"])
            age_str = f"{age:.1f} min" if age is not None else "unknown"
            print(f"  terminal={s['terminal']}  host={s['host']}  age={age_str}")
    else:
        print("No active sessions detected for current user.")

    if HAS_PSUTIL:
        print("\nTop processes (by CPU):")
        tops = get_top_processes(current, SHOW_TOP_PROCESSES)
        if tops:
            print(f"{'PID':>8}  {'CPU%':>6}  {'MEM%':>6}  NAME")
            for pid, cpu, mem, name in tops:
                print(f"{pid:8d}  {cpu:6.1f}  {mem:6.1f}  {name}")
        else:
            print("  (none or access denied)")
    print()

    # 2. Group members
    print(f"--- Group: {TARGET_GROUP} ---")
    members = get_group_members(TARGET_GROUP)
    if not members:
        print("No members found or group does not exist.")
        return

    print(f"Members: {', '.join(members)}\n")

    for user in members:
        if user == current:
            continue  # already shown

        user_sessions = [u for u in logged_in if u["name"] == user]
        if not user_sessions:
            continue

        print(f"Active group member: {user}")
        for s in user_sessions:
            age = session_age_minutes(s["started"])
            age_str = f"{age:.1f} min" if age is not None else "unknown"
            idle_extra = ""
            if SYSTEM != "Windows":
                w_idle = get_unix_idle_from_w(user)
                if w_idle:
                    idle_extra = f"  (w idle: {w_idle})"

            print(f"  terminal={s['terminal']}  age={age_str}{idle_extra}")

            if age is not None and age >= IDLE_THRESHOLD_MIN:
                print(f"  >>> VAMPIRE DETECTED: session age ≥ {IDLE_THRESHOLD_MIN} min")

        if HAS_PSUTIL:
            tops = get_top_processes(user, 3)
            if tops:
                print("  Top processes:")
                for pid, cpu, mem, name in tops:
                    print(f"    {pid:>6}  {cpu:5.1f}%  {name}")
        print()

    print("Scan complete.")


if __name__ == "__main__":
    main()
