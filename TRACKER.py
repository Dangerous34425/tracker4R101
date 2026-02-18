# TRACKER.py
# This file is part of trackerR101
# https://github.com/jtornero/tracker4R101
# Programmed by Jorge Tornero http://imasdemase.com @imasdemase
# This is free and unencumbered software released into the public domain.

# Anyone is free to copy, modify, publish, use, compile, sell, or
# distribute this software, either in source code form or as a compiled
# binary, for any purpose, commercial or non-commercial, and by any
# means.

# In jurisdictions that recognize copyright laws, the author or authors
# of this software dedicate any and all copyright interest in the
# software to the public domain. We make this dedication for the benefit
# of the public at large and to the detriment of our heirs and
# successors. We intend this dedication to be an overt act of
# relinquishment in perpetuity of all present and future rights to this
# software under copyright law.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.

# For more information, please refer to <http://unlicense.org/>

#/usr/bin/env python

import csv
import json
import time
import os
import subprocess
import paho.mqtt.client as mqtt

def on_message(client, userdata, message):
    # Accepts two payload formats:
    #  - JSON: {"tid":"<mobile_id>","tst":<timestamp>,"lat":<lat>,"lon":<lon>}
    #  - semicolon: mobile_id;point_id;lat;lon
    try:
        payload = message.payload
n    except Exception:
        payload = message.payload

    try:
        payload_str = payload.decode('utf-8') if isinstance(payload, bytes) else str(payload)
    except Exception:
        payload_str = str(payload)

    print "RECEIVED ->", payload_str

    ide = None
    pid = None
    lat = None
    lon = None

    # try JSON payload first
    if payload_str.strip().startswith('{'):
        try:
            data = json.loads(payload_str)
            ide = data.get('tid') or data.get('mobile_id') or data.get('id') or data.get('imei')
            pid = str(data.get('tst') or data.get('point_id') or int(time.time()))
            lat = str(data.get('lat') or data.get('latitude') or 0)
            lon = str(data.get('lon') or data.get('longitude') or 0)
        except Exception as e:
            print "JSON parse error:", e
            return
    else:
        # fallback to semicolon format
        try:
            ide, pid, lat, lon = payload_str.split(';')
        except Exception as e:
            print "Payload parse error:", e
            return

    if not ide:
        print "Missing mobile identifier — ignoring message"
        return

    # Optional per-device filter (None = accept all)
    mobile_filter = os.environ.get('MOBILE_FILTER', None)
    if mobile_filter and ide != mobile_filter:
        print "Filtered out mobile_id", ide
        return

    # ignore empty/zero coordinates
    if lat == '0' and lon == '0':
        print "NOT LOGGED"
        return

    # read existing tracking file (robust to missing/short rows)
    try:
        tracking_file = open('tracking.csv', 'r')
        reader = csv.reader(tracking_file, delimiter=';')
        rows = [row for row in reader if len(row) > 0]
        tracking_file.close()
    except Exception:
        rows = []

    # ensure header exists and normalize rows to 5 columns
    header = ['mobile_id', 'point_id', 'lat', 'lon', 'status']
    normalized = []
    if not rows:
        normalized.append(header)
    else:
        # if first row is not header, add header
        if rows[0][0] != 'mobile_id':
            normalized.append(header)
        for r in rows:
            if len(r) < 5:
                r = r + [''] * (5 - len(r))
            normalized.append(r)

    # remove any previous LAST for this mobile_id
    for r in normalized[1:]:
        try:
            if r[0] == ide:
                r[4] = ''
        except Exception:
            pass

    # append new row and persist
    new_data = [ide, pid, lat, lon, 'LAST']
    normalized.append(new_data)

    try:
        tracking_file = open('tracking.csv', 'w')
        writer = csv.writer(tracking_file, delimiter=';', quoting=csv.QUOTE_NONE)
        writer.writerows(normalized)
        tracking_file.close()
        print 'LOGGED'
    except Exception as e:
        print 'Error writing tracking.csv:', e
        return

    # regenerate GeoJSON so QGIS shows updated line/point (best-effort)
    try:
        subprocess.call(['python3', 'scripts/tracking_to_geojson.py'])
        print 'GeoJSON regenerated'
    except Exception as e:
        print 'GeoJSON regeneration failed:', e
        
        

mqtt_client = mqtt.Client()

#create file to store tracking points
tracking_file=open('./tracking.csv', 'w')
tracking_file.write('mobile_id;point_id;lat;lon;status\n')
tracking_file.close()


#Here goes your broker IP/Address and port, username, and password if appliable
# Default: public test broker for quick real-time testing
broker='test.mosquitto.org'
broker_port=1883
user=''
passwd=''
# Optional: set MOBILE_FILTER to an IMEI to accept only that device (None accepts all)
# You can also set the env var MOBILE_FILTER to the IMEI you want to monitor.
# Example: export MOBILE_FILTER=865037047472218

# MQTT topic to subscribe (must match the topic used by DEVICE.py)
mqtt_topic = 'TRACK'

#Connection
mqtt_client.username_pw_set(user,passwd)
mqtt_client.connect(broker,broker_port)

# subscribe
mqtt_client.subscribe(mqtt_topic,qos=2)

mqtt_client.on_message=on_message
mqtt_client.loop_forever()
