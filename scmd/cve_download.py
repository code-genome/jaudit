#!/usr/bin/python
#
# This code is part of the Jaudit utilty.
#
# (C) Copyright IBM 2023.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.
#


import sys
import os
import time
import gzip as GZ

import json
import requests

if sys.version_info.major != 3:
    sys.stderr.write(sys.argv[0] + " requires Python 3\n")
    exit(1)

import lib.jaudit_utils as jutils

myname = sys.argv[0]
mydir = os.path.realpath(os.path.dirname(myname))
basedir = os.path.realpath(mydir+"/..")

jaudit_config = jutils.load_jaudit_config(basedir)

dir=jaudit_config.get("CVE_DATA_DIRECTORY", None)

ndx = 1
while ndx < len(sys.argv):
    arg = sys.argv[ndx]
    ndx += 1
    if arg == '-d':
        dir=sys.argv[ndx]
        ndx += 1
    else:
        sys.stderr.write(f"Unknown option {arg}.\n")
        exit(0)

if dir is None:
    sys.stderr.write("Directory containing CVE data must either be specified in cf/config.cf or using -d command line option.\n")
    exit(1)

position=0
end = None
notified=False
for f in os.listdir(dir):
    if f.startswith('cve_'):
        fn = os.path.join(dir, f)
        if f.endswith(".gz"):
            infile = GZ.open(fn, 'r', encoding='utf8')
        else:
            infile = open(fn, 'r', encoding='utf8')

        if not notified:
            sys.stderr.write("Scanning previously downloaded CVE data...\n")
            notified=True
            
        rec = json.load(infile)
        infile.close()
        
        start = rec['startIndex']
        count = len(rec['vulnerabilities'])
        p = start + count
        if p > position:
            position = p
        if end is None:
            end = rec['totalResults']

nist_url = 'https://services.nvd.nist.gov/rest/json/cves/2.0'

while True:
    sys.stderr.write(f"Requesting records at index {position}...")
    sys.stderr.flush()
    req = requests.get(url=nist_url, params = {
        'startIndex': position
    })

    rec = req.json()
    
    if len(rec['vulnerabilities']) == 0:
        sys.stderr.write(" no new records.\n")
        break
    
    s = json.dumps(rec)
    with open(os.path.join(dir, 'cve_'+str(position)+'.json'), 'w') as f:
        f.write(s)
    end = rec['totalResults']
    position += len(rec['vulnerabilities'])

    sys.stderr.write("\n")

    if position >= end:
        break
    
    sys.stderr.write(f" OK. Next index is {position}. Sleeping 60 seconds.\n")

    time.sleep(60)
    
    
                        


