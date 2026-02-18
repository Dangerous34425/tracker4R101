from location_tracker import LocationTracker

tracker = LocationTracker(
    imsi="260011806800000",
    imei="865037047472218",
    mcc_mnc="26001",
    android_id="4363067944118323788",
    meid="86503704747221"
)

# Pobierz ostatnią znaną lokalizację
loc = tracker.get_approximate_location()
print('Approx location:', loc)

# Generuj raport
report = tracker.create_location_report()
print('Report:', report)

# Wygeneruj mapę HTML
html = tracker.generate_map()
print('Map written to', html)

# Eksport historii do CSV
outcsv = tracker.export_to_csv('moja_historia.csv')
print('Exported to', outcsv)
