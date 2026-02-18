#!/usr/bin/env python3
"""Monitoruje `tracking.csv` i wypisuje natychmiastowe aktualizacje `LAST` dla podanego mobile_id.
Usage: python3 scripts/watch_last.py --id 865037047472218 --interval 1
"""
import argparse
import csv
import time
from datetime import datetime, timezone

parser = argparse.ArgumentParser()
parser.add_argument('--id', dest='mobile_id', default='865037047472218')
parser.add_argument('--interval', dest='interval', type=float, default=1.0)
args = parser.parse_args()

mobile_id = args.mobile_id
interval = args.interval

last_coord = None
last_point = None

print(f"Monitoring tracking.csv for mobile_id={mobile_id} (poll {interval}s)")
try:
    while True:
        try:
            with open('tracking.csv', newline='') as f:
                reader = csv.reader(f, delimiter=';')
                rows = [r for r in reader if r]
        except FileNotFoundError:
            rows = []

        # find last row for mobile_id with status LAST, else last row for mobile_id
        candidate = None
        for r in reversed(rows):
            if len(r) < 4:
                continue
            if r[0] == mobile_id:
                candidate = r
                if len(r) >= 5 and r[4] == 'LAST':
                    break

        if candidate:
            try:
                pid = candidate[1]
                lat = float(candidate[2])
                lon = float(candidate[3])
            except Exception:
                pid = candidate[1]
                lat = None
                lon = None

            coord = (lat, lon)
            if coord != last_coord:
                last_coord = coord
                last_point = pid
                # format time if pid looks like timestamp
                time_str = pid
                try:
                    ts = int(pid)
                    if ts > 1000000000:
                        time_str = datetime.fromtimestamp(ts, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
                except Exception:
                    pass
                print(f"NEW -> {mobile_id} | point_id={pid} | {lat},{lon} | {time_str}")
                print(f"MAP -> https://www.google.com/maps/search/?api=1&query={lat},{lon}\n")
        time.sleep(interval)
except KeyboardInterrupt:
    print('\nStopped.')
