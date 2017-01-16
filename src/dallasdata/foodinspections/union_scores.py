#!/bin/env python3
#
# The MIT License (MIT)
#
# Copyright (c) 2015 dallasdata
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import argparse
import datetime
import csv
from dallasdata.foodinspections.inspection import Inspection
import logging
import os.path
import sys


def main(argv=sys.argv):
    ap = argparse.ArgumentParser(
        description='''
Given CSV files from download-scores, emit a CSV file that is the union of all
inputs. Writes outout CSV to stdout.
''')
    ap.add_argument(
        'files', nargs='+', metavar='file', default=[],
        help='CSV file to combine')
    ap.add_argument(
        '-v', '--verbose', action='count', dest='verbosity', default=0,
        help='increase global logging verbosity; can be used multiple times')

    args = ap.parse_args()

    logging.basicConfig(
            level=logging.ERROR - args.verbosity * 10,
            style='{',
            format='{}: {{message}}'.format(ap.prog))

    inspections = set()
    for cfp in args.files:
        with open(cfp) as cf:
            cr = csv.DictReader(cf)
            inspections |= set(Inspection.from_dict(r) for r in cr)

    cw = csv.DictWriter(
            sys.stdout,
            fieldnames=Inspection.FIELDNAMES)
    cw.writeheader()
    cw.writerows(r.to_dict() for r in sorted(inspections))


if __name__ == '__main__':
    main(sys.argv)
