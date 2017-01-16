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
#
# Render RSS and Atom feeds from a CSV of food inspection scores.

import argparse
import collections
import csv
from feedgen.feed import FeedGenerator
from dallasdata.foodinspections.inspection import Inspection
import hashlib
import logging
import os.path
import pytz
import sys


TZ = pytz.timezone('US/Central')

def get_inspections_to_feed(stream, num_entries, flavor):
    '''
    Yield a list of Inspection objects that should be rendered into the feed.
    '''

    cr = csv.DictReader(stream)
    all_inspections = sorted(
            [Inspection.from_dict(r) for r in cr], reverse=True)

    if flavor == 'all':
        inspections_to_feed = all_inspections
    if flavor == 'failures':
        def location_key(i):
            return ('{name} {address_street} {address_suite} '
                    '{address_zip}').format(**i.to_dict())

        history_map = collections.defaultdict(list)
        inspections_to_feed = set()
        for i in all_inspections:
            k = location_key(i)

            # Scores of less than 70 require re-inspection. Scores of less than
            # 60 require immediate closure and a passing inspection before
            # re-opening. Report all scores of less than 70 as well as
            # subsequent inspections. We use a set here because consecutive
            # failed inspections would result in duplicate entries.
            if i.score < 70:
                if k not in history_map:
                    inspections_to_feed |= set([i])
                else:
                    inspections_to_feed |= set([history_map[k][-1], i])

            history_map[k] += [i]

        inspections_to_feed = sorted(inspections_to_feed, reverse=True)

    return inspections_to_feed[:num_entries]


def main(argv):
    ap = argparse.ArgumentParser(
        description='''
Render RSS and Atom feeds from a CSV of food inspection data.
''')
    ap.add_argument(
        '-v', '--verbose', action='count', dest='verbosity', default=0,
        help='increase global logging verbosity; can be used multiple times')
    ap.add_argument(
       '-f', '--format', choices=['rss', 'atom'], default='atom',
       help='''
specify the format to use when rendering the feed (default: %(default)s)')
''')
    ap.add_argument(
        '-n', '--num_incidents', metavar='<num>', type=int, default=10,
        help='render <num> recent incidents in the feed (default: %(default)s)')
    ap.add_argument(
        'flavor', nargs='?', default='all', choices=['all', 'failures'],
        help='select the flavor of feed to render (default: %(default)s)')

    args = ap.parse_args()

    logging.basicConfig(
            level=logging.ERROR - args.verbosity * 10,
            style='{',
            format='{}: {{message}}'.format(ap.prog))

    fg = FeedGenerator()
    fg.id('http://pgriess.github.io/dallas-foodscores/')
    fg.link(href=fg.id(), rel='self')
    fg.title('Dallas Food Inspection Scores')
    fg.subtitle('''
Food inspection scores from the official City of Dallas dataset; updated daily
''')
    fg.description(fg.subtitle())
    fg.language('en')
    fg.author(
        name='Peter Griess',
        email='pg@std.in',
        uri='https://twitter.com/pgriess')

    for i in get_inspections_to_feed(sys.stdin, args.num_incidents,
            args.flavor):
        fe = fg.add_entry()
        fe.title('{name} at {address} scored {score}'.format(
            name=i.name, address=i.address, score=i.score))
        fe.id(fg.id() + '#!/' + str(abs(hash(i))))
        fe.link(href=fe.id(), rel='alternate')
        fe.content(fe.title())
        fe.published(TZ.localize(i.date))

    if args.format == 'atom':
        print(str(fg.atom_str(pretty=True), encoding='utf-8'))
    else:
        print(str(fg.rss_str(pretty=True), encoding='utf-8'))


if __name__ == '__main__':
    main(sys.argv)
