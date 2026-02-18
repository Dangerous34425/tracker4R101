#!/usr/bin/env python3
"""
Convert semicolon-delimited `tracking.csv` into `tracking_line.geojson`.
- groups by `mobile_id`
- creates LineString for groups with >= 2 points
- creates Point for single-point tracks

Usage:
  python3 scripts/tracking_to_geojson.py [input_csv] [output_geojson]
"""
import csv
import json
import sys
from collections import defaultdict

infile = sys.argv[1] if len(sys.argv) > 1 else 'tracking.csv'
outfile = sys.argv[2] if len(sys.argv) > 2 else 'tracking_line.geojson'

groups = defaultdict(list)
with open(infile, newline='') as f:
    reader = csv.reader(f, delimiter=';')
    header = next(reader, None)
    for row in reader:
        if not row or len(row) < 4:
            continue
        mobile_id = row[0].strip()
        try:
            point_id = int(row[1])
        except Exception:
            point_id = None
        lat_s = row[2].strip()
        lon_s = row[3].strip()
        if lat_s == '' or lon_s == '':
            continue
        try:
            lat = float(lat_s)
            lon = float(lon_s)
        except Exception:
            continue
        groups[mobile_id].append((point_id, lon, lat))

features = []
for mobile_id, pts in groups.items():
    pts_sorted = sorted(pts, key=lambda x: (x[0] if x[0] is not None else 0))
    coords = [[lon, lat] for (_pid, lon, lat) in pts_sorted]
    if len(coords) >= 2:
        geom = {"type": "LineString", "coordinates": coords}
    else:
        geom = {"type": "Point", "coordinates": coords[0]}
    features.append({
        "type": "Feature",
        "properties": {"mobile_id": mobile_id, "point_count": len(coords)},
        "geometry": geom,
    })

geo = {"type": "FeatureCollection", "features": features}
with open(outfile, 'w', encoding='utf-8') as f:
    json.dump(geo, f, ensure_ascii=False, indent=2)

print('Wrote', outfile)
