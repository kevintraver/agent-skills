#!/usr/bin/env python3
"""
Archive a client's billed timesheets: move every CSV in the client root into submitted/.

Usage:
    ./archive.py /path/to/Timesheets/Acme

A period that spans two invoices leaves the same week-of-*.csv name in both places.
Those are merged by date instead of overwritten, so the already-billed rows survive.
"""

import csv
import os
import sys
from datetime import datetime
from glob import glob


# Keep these formats in sync with invoice.py.
def parse_date(date_str):
    """Try multiple date formats and return a datetime object."""
    date_str = date_str.strip().strip('"')
    for fmt in ('%Y-%m-%d', '%b %d %Y', '%b %d, %Y', '%m/%d/%Y', '%m/%d/%y'):
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None


def date_key(line):
    # Legacy TOTAL rows and other non-dates sort last.
    return parse_date(next(csv.reader([line]))[0]) or datetime.max


def merge(src, dest):
    """Fold src's rows into dest, ordered by date; same-day rows keep their order."""
    with open(dest) as fh:
        header, *billed = fh.read().splitlines()
    with open(src) as fh:
        unbilled = fh.read().splitlines()[1:]
    rows = sorted((line for line in billed + unbilled if line.strip()), key=date_key)
    tmp = dest + '.tmp'
    with open(tmp, 'w') as fh:
        fh.write('\n'.join([header, *rows]) + '\n')
    os.replace(tmp, dest)
    os.remove(src)


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    client_dir = sys.argv[1]

    sheets = sorted(glob(os.path.join(client_dir, '*.csv')))
    if not sheets:
        print("Nothing to archive: no CSVs in the client root.")
        return

    submitted = os.path.join(client_dir, 'submitted')
    os.makedirs(submitted, exist_ok=True)
    for src in sheets:
        name = os.path.basename(src)
        dest = os.path.join(submitted, name)
        if os.path.exists(dest):
            merge(src, dest)
            print(f"Merged {name} into submitted/{name} (part of this period was billed earlier)")
        else:
            os.rename(src, dest)
            print(f"Moved {name} to submitted/")


if __name__ == '__main__':
    main()
