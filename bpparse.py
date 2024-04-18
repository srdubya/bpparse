#!/usr/bin/env python3
"""
Parses the XML output of an iPhone's Health app's "Export All Health Data" blood pressure output.
To generate the output:
 1. Start the Health app
 2. Click on your profile picture in the upper-right
 3. Scroll to the bottom and select "Export All Health Data"
 4. Share the resulting data to you Mac using AirDrop

Command line:
  ./bpparse.py <filename> [<minimum date>]

  filename - the location/name of the file with the data as described above
  minimum date - the date after which you'd like blood pressure data for

Output, to stdout:
  CSV formatted data with these columns:
   - Date of the diastolic reading
   - Diastolic pressure reading
   - Date of the systolic pressure reading
   - Systolic pressure reading
"""
import csv
import os.path
import sys
from datetime import datetime, date

import xmltodict


min_date: date = date(1999, 1, 1)
csv_writer = csv.writer(sys.stdout)


def handle_item(_, item):
    if isinstance(item, dict) and 'Record' in item:
        record = item['Record']
        to_print = {
            'systolic': None,
            'diastolic': None,
            'datetime': None
        }
        for entry in record:
            if '@type' in entry:
                if entry['@type'] == 'HKQuantityTypeIdentifierBloodPressureSystolic':
                    to_print['systolic'] = entry['@value']
                    to_print['datetime'] = datetime.strptime(entry['@startDate'], '%Y-%m-%d %H:%M:%S %z')
                elif entry['@type'] == 'HKQuantityTypeIdentifierBloodPressureDiastolic':
                    to_print['diastolic'] = entry['@value']
        if (to_print['systolic'] is not None
                and to_print['diastolic'] is not None
                and (min_date.year == 1999 or to_print['datetime'].date() > min_date)):
            csv_writer.writerow([
                to_print['datetime'],
                to_print['diastolic'],
                to_print['datetime'],
                to_print['systolic']
            ])
    return True


def parse_min_date():
    if len(sys.argv) < 3 or len(sys.argv[2]) < 1:
        return True
    global min_date
    try:
        min_date = date(
            int(sys.argv[2][0:4]),
            int(sys.argv[2][6:7]),
            int(sys.argv[2][9:10])
        )
        return True
    except BaseException as error:
        print(error, file=sys.stderr)
        return False


def main():
    error = None
    if len(sys.argv) < 2:
        error = "Filename required"
    filename = os.path.expanduser(sys.argv[1])
    if not os.path.exists(filename):
        error = f"'{filename}' not found"
    elif not parse_min_date():
        error = f"Error parsing date '{sys.argv[2]}'"
    if error is not None:
        cmdline = ' '.join(x for x in sys.argv)
        print(f"Error:  {error}", file=sys.stderr)
        print(f"  Cmdline: {cmdline}", file=sys.stderr)
        print(f"  Usage:  {os.path.basename(sys.argv[0])} <xml file> [<minimum date>]", file=sys.stderr)
        exit(1)
    with open(filename, mode="rb") as f:
        xmltodict.parse(f, item_depth=2, item_callback=handle_item)


if __name__ == '__main__':
    main()
