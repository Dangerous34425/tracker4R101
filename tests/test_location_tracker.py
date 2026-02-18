import os
from location_tracker import LocationTracker


def test_get_approximate_location_returns_last():
    tracker = LocationTracker(imei='865037047472218')
    loc = tracker.get_approximate_location()
    assert loc is not None
    lat, lon, pid = loc
    # expected values come from tracking.csv in workspace
    assert abs(lat - 52.2263008) < 1e-6
    assert abs(lon - 16.5317342) < 1e-6


def test_export_creates_file(tmp_path):
    tracker = LocationTracker(imei='865037047472218')
    out = tmp_path / 'out.csv'
    tracker.export_to_csv(str(out))
    assert out.exists()
    content = out.read_text()
    assert '865037047472218' in content
