# Generates airports.js from OurAirports data (https://ourairports.com/data/, public domain).
# Keeps airports that are currently operating with scheduled airline service and have an open paved runway, with the
# longest length and widest width of those runways, so the page can filter by runway requirements. Run this script any time to refresh the data;
# it downloads the latest CSVs.
import csv
import io
import json
import math
import re
import urllib.request
from collections import defaultdict

DATA_URL = 'https://davidmegginson.github.io/ourairports-data'
FEET_TO_M = 0.3048
PAVED = re.compile(r'^(ASP|CON|PEM|BIT|TAR|PAV|MAC)')  # Asphalt, concrete, etc. (the surface field is free text)


def download_csv(name):
    print(f'Downloading {name}...')
    with urllib.request.urlopen(f'{DATA_URL}/{name}') as response:
        return list(csv.DictReader(io.StringIO(response.read().decode('utf-8'))))


# Longest length and widest width (in meters) of each airport's open paved runways. The width is None if unknown.
lengths, widths = defaultdict(float), {}
for r in download_csv('runways.csv'):
    if r['closed'] == '1' or not PAVED.match(r['surface'].strip().upper()):
        continue
    airport = r['airport_ref']
    lengths[airport] = max(lengths[airport], float(r['length_ft'] or 0) * FEET_TO_M)
    if r['width_ft']:
        widths[airport] = max(widths.get(airport, 0), float(r['width_ft']) * FEET_TO_M)

airports = []
for a in download_csv('airports.csv'):
    if a['type'] == 'closed' or a['scheduled_service'] != 'yes' or a['id'] not in lengths:
        continue
    code = a['iata_code'] or a['icao_code'] or a['ident']
    width = widths.get(a['id'])
    airports.append((code, round(float(a['latitude_deg']), 4), round(float(a['longitude_deg']), 4), a['name'],
                     # Rounded down, so comparing with whole-meter minimums gives the same result as the exact value
                     # (e.g. 98 ft = 29.87 m must not pass a 30 m minimum)
                     math.floor(lengths[a['id']]), math.floor(width) if width is not None else None))
airports.sort()

with open('airports.js', 'w', encoding='utf-8') as f:
    f.write('// Generated from OurAirports data by gen_airports.py -- do not edit manually.\n')
    f.write('// Operating airports with scheduled service and a paved runway:\n')
    f.write('// [code, latitude, longitude, name, longest runway (m), widest runway (m)]. The width is null if unknown.\n')
    f.write('const AIRPORTS = [\n')
    for code, lat, lon, name, length, width in airports:
        f.write(f'    [{json.dumps(code)}, {lat}, {lon}, {json.dumps(name, ensure_ascii=False)}, {length}, {json.dumps(width)}],\n')
    f.write('];\n')

print(f'Wrote {len(airports)} airports to airports.js')
