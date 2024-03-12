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
#------------------------------------------------------------------------
#
# This utility adds CVE information to the output of Jaudit.  It reads
# JSON records from stdin, one per line, and outputs them with the CVE
# information added.
#

import os
import sys
import json

if sys.version_info.major != 3:
    sys.stderr.write(sys.argv[0] + " requires Python 3\n")
    exit(1)


myname = sys.argv[0]
mydir = os.path.realpath(os.path.dirname(myname))
top = os.path.realpath(os.path.join(mydir, ".."))

def check_cve(rec, cve_info):

    if 'versions' in rec:
        for vi in rec['versions']:
            if vi['version'] in cve_info:
                vv = vi['version']
                cve=[]
                for cid in cve_info[vv]:
                    r = cve_info[vv][cid].copy()
                    r['id'] = cid
                    cve.append(r)
                vi['cve'] = cve
    if 'children' in rec:
        for c in rec['children']:
            check_cve(c, cve_info)


fn = os.path.join(top, "cf/cve_info.json")
with open(fn, 'r', encoding='utf8') as f:
    cve_info = json.load(f)

for line in sys.stdin:
    rec = json.loads(line)

    check_cve(rec, cve_info)
    print(json.dumps(rec))
