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

import json
import sys
import os
import traceback
import zipfile
import time
from hashlib import sha256

if sys.version_info.major != 3:
    sys.stderr.write(sys.argv[0] + " requires Python 3\n")
    exit(1)

from lib.jardata import JarDataExtract
from lib.jarversion import JarNameVersion

if __name__ == '__main__':

    myname = sys.argv[0]
    mydir = os.path.realpath(os.path.dirname(myname))
    basedir = os.path.realpath(mydir+"/..")

    config=os.path.join(basedir, "cf/monitored.json")
    datasets=os.path.join(basedir, "cf/datasets.json")

    with open(datasets, "r") as f:
        dataset_config = json.load(f)
    
    inputfiles=[]
    archive = None
    ndx = 1
    while ndx < len(sys.argv):
        arg = sys.argv[ndx]
        ndx += 1
        if arg == '-a':
            archive=sys.argv[ndx]
            ndx += 1
        elif arg == '-c':
            config=sys.argv[ndx]
            ndx += 1
        else:
            inputfiles.append(arg)

    jv = JarNameVersion(config)

    if len(inputfiles) == 0:
        for line in sys.stdin:
            inputfiles.append(line.rstrip())

    for fn in inputfiles:
        output = None
        hashes = set()

        version = jv.get_version(fn)
        
        if version is None:
            sys.stderr.write(f"Unable to determine version for {fn}, not processing.\n")
            continue

        if archive is None:
            jdata = os.path.join(basedir, "jaudit.data/json")
            appinfo = jv.get_app_record(version)
            appid = appinfo['id']
            dataset_name = dataset_config[appid]['dataset']
            archive = os.path.join(jdata, dataset_name)

        try:
            h = sha256()
            with open(fn, 'rb') as infile:
                h.update(infile.read(-1))
                digest = h.digest().hex()

                
            if archive is not None:
                sd1 = os.path.join(archive, digest[0])
                if not os.path.exists(sd1):
                    os.mkdir(sd1)

                sd2 = os.path.join(sd1, digest[1])
                if not os.path.exists(sd2):
                    os.mkdir(sd2)

                outname = digest + ".json"
                out_fn = os.path.join(sd2, outname)

                if os.path.exists(out_fn):
                    continue

            with zipfile.ZipFile(fn) as zf:
                jde = JarDataExtract()
                record = jde.get_jar_fingerprints(zf)
                record['jar-digest'] = digest
                record['version'] = version
                output = json.dumps(record,sort_keys=True,separators=(',',':'))

                if archive is None:
                    print(output)
                    continue

                with open(out_fn, 'w') as out:
                    out.write(output+"\n")

        except Exception as e:
            sys.stderr.write(f"{fn}:\n")
            traceback.print_exc()

