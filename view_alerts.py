"""
Alert Log Viewer
================
View all recorded intruder alerts.
Usage: python view_alerts.py
"""

import json
import os

LOG_FILE = "alert_log.json"

def view_alerts():
    if not os.path.exists(LOG_FILE):
        print("No alerts recorded yet.")
        return

    with open(LOG_FILE, "r") as f:
        try:
            alerts = json.load(f)
        except json.JSONDecodeError:
            print("Log file is empty or corrupted.")
            return

    if not alerts:
        print("No alerts in log.")
        return

    print(f"\n{'═'*55}")
    print(f"  INTRUDER ALERT LOG  –  {len(alerts)} event(s)")
    print(f"{'═'*55}")

    for i, alert in enumerate(reversed(alerts), 1):
        print(f"\n[{i}]  Time     : {alert.get('timestamp', 'N/A')}")
        print(f"     Person   : {alert.get('person', 'N/A')}")
        snap = alert.get('snapshot', '')
        exists = "✓ exists" if os.path.exists(snap) else "✗ not found"
        print(f"     Snapshot : {snap or 'None'}  {exists if snap else ''}")

    print(f"\n{'═'*55}\n")

if __name__ == "__main__":
    view_alerts()