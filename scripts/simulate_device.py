#!/usr/bin/env python3
"""Simulate device sending locations by appending rows to tracking.csv and regenerating GeoJSON.
Usage: python3 scripts/simulate_device.py [IMEI] [steps] [interval_seconds]
"""
import csv
import sys
import time
import subprocess

imei = sys.argv[1] if len(sys.argv) > 1 else '865037047472218'
steps = int(sys.argv[2]) if len(sys.argv) > 2 else 10
interval = float(sys.argv[3]) if len(sys.argv) > 3 else 3.0

# small movement deltas (latitude, longitude)
deltas = [(0.00005, 0.00005), (0.00007, -0.00004), (-0.00006, 0.00003), (0.00004, 0.00002)]

for i in range(steps):
    # read existing CSV
    rows = []
    try:
        with open('tracking.csv', newline='') as f:
            reader = csv.reader(f, delimiter=';')
            rows = [r for r in reader if r]
    except FileNotFoundError:
        # create header if missing
        rows = [['mobile_id','point_id','lat','lon','status']]

    # find last known coordinate for IMEI or fallback to current POINT in geojson
    last_lat = None
    last_lon = None
    last_pid = 0
    for r in rows[1:]:
        if r[0] == imei:
            try:
                last_pid = max(last_pid, int(r[1]))
                last_lat = float(r[2])
                last_lon = float(r[3])
            except Exception:
                pass

    if last_lat is None or last_lon is None:
        # fallback coordinates (Warsaw example)
        last_lat = 52.2259608
        last_lon = 16.5315942
        last_pid = 0

    # compute new coordinate
    dx, dy = deltas[i % len(deltas)]
    new_lat = last_lat + dx
    new_lon = last_lon + dy
    new_pid = last_pid + 1

    # remove LAST flags for this IMEI
    for r in rows[1:]:
        if r[0] == imei and len(r) >= 5:
            r[4] = ''

    # append new row
    rows.append([imei, str(new_pid), str(new_lat), str(new_lon), 'LAST'])

    # write back
    with open('tracking.csv', 'w', newline='') as f:
        writer = csv.writer(f, delimiter=';', quoting=csv.QUOTE_NONE)
        writer.writerows(rows)

    # regenerate geojson
    try:
        subprocess.call(['python3', 'scripts/tracking_to_geojson.py'])
    except Exception as e:
        print('GeoJSON regen failed:', e)

    print('Simulated', imei, '->', new_lat, new_lon, '(point', new_pid, ')')
    time.sleep(interval)

print('Simulation finished')
