#!/usr/bin/env python3
"""
Vampire Monitor – Cross-platform (Linux, macOS, Windows, BSD)
Monitors logged-in users by group or all users.
"""

import argparse
import platform
import os
import sys
import subprocess
import getpass
from datetime import datetime
from typing import List, Dict, Optional, Set, Tuple

# ---------- Optional dependency ----------
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

SYSTEM = platform.system()

# Common system groups to skip when using --all-groups
SYSTEM_GROUPS = {
    "root", "wheel", "daemon", "bin", "sys", "adm", "tty", "disk", "lp", "mail",
    "news", "uucp", "man", "proxy", "kmem", "dialout", "fax", "voice", "cdrom",
    "floppy", "tape", "sudo", "audio", "dip", "www-data", "backup", "operator",
    "list", "irc", "src", "gnats", "shadow", "utmp", "video", "sasl", "plugdev",
    "staff", "games", "users", "nogroup", "systemd-journal", "systemd-network",
    "systemd-resolve", "systemd-timesync", "messagebus", "input", "kvm", "render",
    "netdev", "lpadmin", "ssl-cert", "bluetooth", "avahi", "scanner", "colord",
    "saned", "sambashare", "docker", "libvirt", "lxd",
    # macOS / BSD extras
    "admin", "staff", "everyone", "localaccounts", "netaccounts", "_*",
    # Windows common
    "Administrators", "Users", "Guests", "Power Users", "Backup Operators",
    "Replicator", "Remote Desktop Users", "Network Configuration Operators",
}


def get_current_user() -> str:
    return getpass.getuser()


def get_group_members(group: str) -> List[str]:
    """Return list of usernames belonging to the group."""
    members: List[str] = []

    if SYSTEM in ("Linux", "Darwin", "FreeBSD", "OpenBSD", "NetBSD"):
        try:
            import grp
            g = grp.getgrnam(group)
            members = list(g.gr_mem)
        except KeyError:
            pass
        except Exception:
            pass

    elif SYSTEM == "Windows":
        try:
            flags = subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0
            result = subprocess.run(
                ["net", "localgroup", group],
                capture_output=True, text=True, timeout=8, creationflags=flags
            )
            if result.returncode == 0:
                in_members = False
                for line in result.stdout.splitlines():
                    line = line.strip()
                    if line.lower().startswith("members"):
                        in_members = True
                        continue
                    if in_members:
                        if not line or line.startswith("---") or "The command completed" in line:
                            break
                        user = line.split("\\")[-1].strip()
                        if user:
                            members.append(user)
        except Exception:
            pass

    return sorted(set(members))


def get_all_groups() -> List[str]:
    """Best-effort list of local groups."""
    groups: List[str] = []

    if SYSTEM in ("Linux", "Darwin", "FreeBSD", "OpenBSD", "NetBSD"):
        try:
            import grp
            for g in grp.getgrall():
                name = g.gr_name
                if name.startswith("_") or name in SYSTEM_GROUPS:
                    continue
                if g.gr_mem:  # only groups that actually have members
                    groups.append(name)
        except Exception:
            pass

    elif SYSTEM == "Windows":
        try:
            flags = subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0
            result = subprocess.run(
                ["net", "localgroup"],
                capture_output=True, text=True, timeout=8, creationflags=flags
            )
            if result.returncode == 0:
                for line in result.stdout.splitlines():
                    line = line.strip()
                    if line.startswith("*"):
                        name = line[1:].strip()
                        if name and name not in SYSTEM_GROUPS:
                            groups.append(name)
        except Exception:
            pass

    return sorted(set(groups))


def get_logged_in_users() -> List[Dict]:
    users = []
    if HAS_PSUTIL:
        for u in psutil.users():
            started = datetime.fromtimestamp(u.started) if u.started else None
            users.append({
                "name": u.name,
                "terminal": u.terminal,
                "host": u.host,
                "started": started,
                "pid": u.pid,
            })
    else:
        # Minimal fallback
        if SYSTEM != "Windows":
            try:
                result = subprocess.run(["who"], capture_output=True, text=True, timeout=5)
                for line in result.stdout.splitlines():
                    parts = line.split()
                    if parts:
                        users.append({
                            "name": parts[0],
                            "terminal": parts[1] if len(parts) > 1 else None,
                            "host": None,
                            "started": None,
                            "pid": None,
                        })
            except Exception:
                pass
    return users


def session_age_minutes(started: Optional[datetime]) -> Optional[float]:
    if not started:
        return None
    return (datetime.now() - started).total_seconds() / 60.0


def get_top_processes(username: str, n: int = 4) -> List[Tuple]:
    if not HAS_PSUTIL:
        return []
    procs = []
    for p in psutil.process_iter(["pid", "username", "name"]):
        try:
            if p.info["username"] == username:
                cpu = p.cpu_percent(interval=0.05)
                procs.append((p.info["pid"], cpu, p.info["name"] or "?"))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    procs.sort(key=lambda x: x[1], reverse=True)
    return procs[:n]


def print_user_info(user: str, sessions: List[Dict], threshold: int, show_procs: bool = True):
    if not sessions:
        return

    print(f"  User: {user}")
    for s in sessions:
        age = session_age_minutes(s["started"])
        age_str = f"{age:.1f} min" if age is not None else "unknown"
        print(f"    terminal={s['terminal'] or '-'}  host={s['host'] or '-'}  age={age_str}")

        if age is not None and age >= threshold:
            print(f"    >>> VAMPIRE: session age ≥ {threshold} minutes")

    if show_procs and HAS_PSUTIL:
        tops = get_top_processes(user)
        if tops:
            print("    Top processes:")
            for pid, cpu, name in tops:
                print(f"      {pid:>7}  {cpu:5.1f}%  {name}")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Vampire Monitor – detect long-running / idle sessions by group or for all users"
    )
    parser.add_argument(
        "-g", "--group", action="append", default=[],
        help="Group to monitor (can be used multiple times)"
    )
    parser.add_argument(
        "--all-groups", action="store_true",
        help="Monitor every non-system group that has members"
    )
    parser.add_argument(
        "-t", "--threshold", type=int, default=30,
        help="Idle / session age threshold in minutes (default: 30)"
    )
    parser.add_argument(
        "--no-procs", action="store_true",
        help="Do not show top processes"
    )
    args = parser.parse_args()

    current = get_current_user()
    threshold = args.threshold

    print("=" * 64)
    print("Vampire Monitor")
    print(f"OS           : {SYSTEM}")
    print(f"Current user : {current}")
    print(f"Threshold    : {threshold} minutes")
    print("=" * 64)
    print()

    logged_in = get_logged_in_users()
    logged_names = {u["name"] for u in logged_in}

    # ---------- Decide what to monitor ----------
    target_groups: List[str] = []

    if args.all_groups:
        target_groups = get_all_groups()
        print(f"Mode: all non-system groups ({len(target_groups)} groups)\n")
    elif args.group:
        target_groups = args.group
        print(f"Mode: specific groups → {', '.join(target_groups)}\n")
    else:
        # No group specified → just show all currently logged-in users
        print("Mode: all currently logged-in users (no group filter)\n")
        print("--- Logged-in Users ---")
        for name in sorted(logged_names):
            sessions = [u for u in logged_in if u["name"] == name]
            print_user_info(name, sessions, threshold, show_procs=not args.no_procs)
        print("Scan complete.")
        return

    # ---------- Group mode ----------
    for group in target_groups:
        members = get_group_members(group)
        active_members = [m for m in members if m in logged_names]

        print(f"--- Group: {group} ---")
        if not members:
            print("  (group not found or empty)\n")
            continue

        print(f"  Members     : {', '.join(members) if members else '(none)'}")
        print(f"  Currently on: {', '.join(active_members) if active_members else '(none)'}")
        print()

        for user in active_members:
            sessions = [u for u in logged_in if u["name"] == user]
            print_user_info(user, sessions, threshold, show_procs=not args.no_procs)

    print("Scan complete.")


if __name__ == "__main__":
    main()
