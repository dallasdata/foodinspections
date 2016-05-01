#!/bin/env python2.7
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
# Download City of Dallas Food Safety inspection reports and display as CSV.
#
# XXX: Need to handle the case of 0 records for a given zip (e.g. 75222). For
#      now, I've just removed the offending zip.
#
# XXX: Is there a hard limit of 2 years history? After scraping all zips, the
#      earliest dates are *exactly* 2 years earlier than the scrape run.

import argparse
import contextlib
import datetime
import csv
from foodscores.inspection import Inspection
import io
import logging
import lxml.etree
import os.path
import urllib
import urllib2
import re
import sys


def node_text(n):
    '''
    Get the text from a table node.

    This is not at all generic; it's a horrible hack to handle the fact that
    the address field embeds its text in a (broken) anchor tag.
    '''

    children = n.getchildren()
    if children and children[0].tag == 'a':
        return children[0].text

    return n.text


def clean_text(t):
    '''
    Clean up text.
    '''

    if not t:
        return t

    # Some restaurant names have 'App#<NNN>'
    t = re.sub(r'app#\s*\d+', '', t, 0, re.I)

    # Clean multiple consecutive whitespaces
    t = re.sub(r'\s+', ' ', t.strip())

    return t


def inspections_by_zipcode(zipcode):
    '''
    Iterator to yield all inspections for the given zipcode.
    '''

    base_url = 'http://www2.dallascityhall.com/FoodInspection/SearchScoresAction.cfm'

    od = urllib2.OpenerDirector()
    od.add_handler(urllib2.ProxyHandler())
    od.add_handler(urllib2.HTTPCookieProcessor())
    od.add_handler(urllib2.HTTPHandler())

    page_num = 1
    while True:
        logging.debug('fetching page {} for zip {}'.format(page_num, zipcode))

        if page_num > 1:
            url = base_url + '?' + urllib.urlencode({'PageNum_q_search': page_num})
            data = None
        else:
            url = base_url
            data = urllib.urlencode({
                    'NAME': '',
                    'STNO': '',
                    'STNAME': '',
                    'ZIP': zipcode,
                    'Submit': 'Search+Scores'})

        with contextlib.closing(od.open(url, data)) as r:
            et = lxml.etree.parse(io.BytesIO(r.read()), lxml.etree.HTMLParser())
            t = et.xpath('//body/table')[0]

            fields = None
            for tr in t.xpath('tr'):

                if fields is None:
                    fields = []
                    for td in tr.xpath('td'):
                        fields += [td.text.strip()]
                    continue

                d = dict(
                        zip(
                            fields,
                            [clean_text(node_text(td)) for td in tr.xpath('td')]))
                for k, v in d.iteritems():
                    if type(v) == str:
                        v = unicode(v, 'utf-8', 'replace')
                    d[k] = v

                yield Inspection(
                    name=d['Name'],
                    address=d['Address'],
                    suite=d['Suite#'],
                    zipcode=d['Zip'],
                    date=datetime.datetime.strptime(d['Inspected'], '%m/%d/%Y'),
                    score=int(d['Score']),
                    inspection_type=d['Inspection Type'].lower())

            if not et.xpath('//a[text()="Next"]'):
                break

            page_num += 1


def main(argv):
    ap = argparse.ArgumentParser(
        description='''
    Download food inspection scores from the City of Dallas website.
    ''')
    ap.add_argument(
        '-v', '--verbose', action='count', dest='verbosity', default=0,
        help='increase global logging verbosity; can be used multiple times')

    args = ap.parse_args()

    logging.basicConfig(
            level=logging.ERROR - args.verbosity * 10,
            format='{}: %(message)s'.format(ap.prog))

    od = urllib2.OpenerDirector()
    od.add_handler(urllib2.ProxyHandler())
    od.add_handler(urllib2.HTTPCookieProcessor())
    od.add_handler(urllib2.HTTPHandler())

    inspections = set()
    for z in [
            75201, 75202, 75203, 75204, 75205,
            75206, 75207, 75208, 75209, 75210,
            75211, 75212, 75214, 75215, 75216,
            75217, 75218, 75219, 75220, 75221,
            75223, 75224, 75225, 75226, 75227,
            75228, 75229, 75230, 75231, 75232,
            75233, 75234, 75235, 75236, 75237,
            75238, 75240, 75241, 75243, 75244,
            75246, 75247, 75248, 75249, 75250,
            75251, 75252, 75253, 75254, 75287]:
        inspections |= set(r for r in inspections_by_zipcode(z))

    cw = csv.DictWriter(
            sys.stdout,
            fieldnames=Inspection.FIELDNAMES)
    cw.writeheader()
    cw.writerows(i.to_dict() for i in sorted(inspections))


if __name__ == '__main__':
    main(sys.argv)
