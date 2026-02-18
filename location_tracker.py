"""location_tracker — prosty helper do pracy z `tracking.csv` i generowania raportów / map.
API (krótko):

from location_tracker import LocationTracker
tracker = LocationTracker(imei="865037047472218")
loc = tracker.get_approximate_location()
report = tracker.create_location_report()
tracker.generate_map()           # zapisuje HTML w ./maps/
tracker.export_to_csv("out.csv")

To rozwiązanie używa lokalnego `tracking.csv` jako źródła historii.
"""
from __future__ import annotations
import csv
import os
from datetime import datetime, timezone
from typing import List, Optional, Tuple, Dict

CSV_HEADER = ['mobile_id', 'point_id', 'lat', 'lon', 'status']


class LocationTracker:
    def __init__(self,
                 imsi: Optional[str] = None,
                 imei: Optional[str] = None,
                 mcc_mnc: Optional[str] = None,
                 android_id: Optional[str] = None,
                 meid: Optional[str] = None,
                 tracking_csv: str = 'tracking.csv'):
        self.imsi = imsi
        self.imei = imei
        self.mcc_mnc = mcc_mnc
        self.android_id = android_id
        self.meid = meid
        self.tracking_csv = tracking_csv
        self.location_history = self._load_history()

    def _load_history(self) -> List[Dict]:
        rows = []
        if not os.path.exists(self.tracking_csv):
            return rows
        with open(self.tracking_csv, newline='') as f:
            reader = csv.reader(f, delimiter=';')
            for r in reader:
                if not r:
                    continue
                # normalize rows shorter than 5
                if len(r) < 5:
                    r = r + [''] * (5 - len(r))
                rows.append({
                    'mobile_id': r[0],
                    'point_id': r[1],
                    'lat': r[2],
                    'lon': r[3],
                    'status': r[4]
                })
        return rows

    def refresh(self) -> None:
        """Reload history from disk."""
        self.location_history = self._load_history()

    def _rows_for_device(self, mobile_id: Optional[str]) -> List[Dict]:
        mid = mobile_id or self.imei or self.imsi
        if not mid:
            return []
        return [r for r in self.location_history if r.get('mobile_id') == mid]

    def get_approximate_location(self, mobile_id: Optional[str] = None) -> Optional[Tuple[float, float, str]]:
        """Return last known location for `mobile_id` (lat, lon, point_id) or None.
        Prefers rows with status=='LAST'."""
        self.refresh()
        rows = self._rows_for_device(mobile_id)
        if not rows:
            return None
        # prefer the last row marked LAST
        for r in reversed(rows):
            if r.get('status') == 'LAST':
                try:
                    return float(r['lat']), float(r['lon']), r['point_id']
                except Exception:
                    return None
        # fallback: last available
        r = rows[-1]
        try:
            return float(r['lat']), float(r['lon']), r['point_id']
        except Exception:
            return None

    def create_location_report(self, location: Optional[Tuple[float, float, str]] = None) -> Optional[Dict]:
        """Create a small location report dict from provided or last location."""
        if location is None:
            location = self.get_approximate_location()
        if location is None:
            return None
        lat, lon, pid = location
        ts = None
        try:
            ts_i = int(pid)
            if ts_i > 1000000000:
                ts = datetime.fromtimestamp(ts_i, tz=timezone.utc).isoformat()
        except Exception:
            ts = None
        return {
            'imei': self.imei,
            'imsi': self.imsi,
            'mcc_mnc': self.mcc_mnc,
            'android_id': self.android_id,
            'meid': self.meid,
            'lat': lat,
            'lon': lon,
            'point_id': pid,
            'timestamp': ts
        }

    def generate_map(self, out_html: Optional[str] = None, mobile_id: Optional[str] = None) -> str:
        """Generate a simple Leaflet HTML map for device history and return path to HTML."""
        self.refresh()
        rows = self._rows_for_device(mobile_id)
        coords = []
        for r in rows:
            try:
                coords.append((float(r['lat']), float(r['lon'])))
            except Exception:
                pass
        if not coords:
            raise ValueError('No coordinates available to generate map')
        if out_html is None:
            out_dir = 'maps'
            os.makedirs(out_dir, exist_ok=True)
            mid = mobile_id or self.imei or self.imsi or 'device'
            out_html = os.path.join(out_dir, f'location_{mid}.html')
        # write simple HTML with embedded coords
        markers_js = ',\n'.join([f'[{lat},{lon}]' for lat, lon in coords])
        html = f"""<!doctype html>
<html>
<head>
  <meta charset=\"utf-8\">
  <title>Location map</title>
  <link rel=\"stylesheet\" href=\"https://unpkg.com/leaflet@1.9.4/dist/leaflet.css\"/>
  <style>html,body,#map{{height:100%;margin:0}}</style>
</head>
<body>
<div id=\"map\"></div>
<script src=\"https://unpkg.com/leaflet@1.9.4/dist/leaflet.js\"></script>
<script>
var map = L.map('map').setView([{coords[0][0]},{coords[0][1]}], 14);
L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png',{{maxZoom:19}}).addTo(map);
var latlngs = [ {markers_js} ];
var poly = L.polyline(latlngs, {{color:'#0077cc'}}).addTo(map);
map.fitBounds(poly.getBounds());
L.marker(latlngs[latlngs.length-1]).addTo(map).bindPopup('LAST');
</script>
</body>
</html>"""
        with open(out_html, 'w', encoding='utf-8') as f:
            f.write(html)
        return out_html

    def export_to_csv(self, filename: str, mobile_id: Optional[str] = None) -> str:
        """Export device history to CSV (semicolon-delimited). Returns path."""
        self.refresh()
        rows = self._rows_for_device(mobile_id)
        if not rows:
            raise ValueError('No rows to export')
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerow(CSV_HEADER)
            for r in rows:
                writer.writerow([r['mobile_id'], r['point_id'], r['lat'], r['lon'], r.get('status','')])
        return filename

    def __repr__(self):
        return f"<LocationTracker imei={self.imei} imsi={self.imsi} rows={len(self.location_history)}>"