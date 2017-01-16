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

'''
Misc. utilities.
'''

import datetime
import hashlib

# XXX: Probably not ideal for this to define the CSV serialization field names,
#      but whatever.
class Inspection(object):
    '''
    Object tracking a single inspection incident.
    '''

    FIELDNAMES = [
            'name',
            'address_street',
            'address_suite',
            'address_zip',
            'inspection_date',
            'inspection_score',
            'inspection_type'
    ]

    def __init__(self, name, address, suite, zipcode, date, score,
                 inspection_type):
        self.name = name
        self.address = address
        self.suite = suite
        self.zipcode = zipcode
        self.date = date
        self.score = score
        self.inspection_type = inspection_type

    def to_dict(self):
        d = {
                'name': self.name,
                'address_street': self.address,
                'address_suite': self.suite,
                'address_zip': self.zipcode,
                'inspection_date': self.date.strftime('%Y-%m-%d'),
                'inspection_score': self.score,
                'inspection_type': self.inspection_type,
        }
        for k, v in d.items():
            d[k] = v

        return d

    @staticmethod
    def from_dict(d):
        return Inspection(
                name=d['name'],
                address=d['address_street'],
                suite=d['address_suite'],
                zipcode=d['address_zip'],
                date=datetime.datetime.strptime(d['inspection_date'], '%Y-%m-%d'),
                score=int(d['inspection_score']),
                inspection_type=d['inspection_type'])


    def __eq__(self, other):
        return self.name == other.name and \
                self.address == other.address and \
                self.suite == other.suite and \
                self.zipcode == other.zipcode and \
                self.date == other.date and \
                self.score == other.score and \
                self.inspection_type == other.inspection_type

    def __lt__(self, other):
        if self.date != other.date:
            return self.date < other.date

        if self.inspection_type != other.inspection_type:
            return self.inspection_type < other.inspection_type

        if self.score != other.score:
            return self.score < other.score

        if self.name != other.name:
            return self.name < other.name

        if self.address != other.address:
            return self.address < other.address

        if self.suite != other.suite:
            return self.suite < other.suite

        return self.zipcode < other.zipcode

    def __hash__(self):
        hd = hashlib.sha1(
                    u'{} {} {} {} {} {} {}'.format(
                        self.name, self.address, self.suite, self.zipcode,
                        self.date, self.score, self.inspection_type).
                            encode('utf-8')
        ).hexdigest()

        hv = 0
        while len(hd) > 0:
            i = int(hd[:16], 16)
            hv ^= i
            hd = hd[16:]

        return hv
