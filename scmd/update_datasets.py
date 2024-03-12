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
import json
import zipfile

if sys.version_info.major != 3:
    sys.stderr.write(sys.argv[0] + " requires Python 3\n")
    exit(1)


myname = sys.argv[0]
bindir=os.path.dirname(myname)
mydir = os.path.realpath(bindir)
top = os.path.realpath(os.path.join(mydir, ".."))
runcmd=os.path.join(bindir, "run")
datadir=os.path.join(top, "jaudit.data/jardata")

status = os.system(f"{runcmd} submodules check_installed data")
if status != 0:
    exit(1)

fpdir = top
hashdir = top

dataset_config = os.path.join(top, "cf/datasets.json")
with open(dataset_config, 'r', encoding='utf8') as f:
    datasets = json.load(f)

for name in datasets:
    num_jars = 0
    num_records = 0
    num_classes = 0
    versions = set()
    jds = set()
    jfp = set()
    cds = set()
    cfp = set()
    for file in datasets[name]['datasets']:
        if file[0] != '/':
            file = os.path.join(datadir, file)
        with zipfile.ZipFile(file) as zip:
            for zfi in zip.infolist():
                zfn = zfi.filename
                with zip.open(zfn, 'r') as zf:
                    rec = json.load(zf)
                    versions.add(rec['version'])
                    jds.add(rec['jar-class-digest'])
                    jfp.add(rec['jar-fingerprint'])

                    for c in rec['classes']:
                        cds.add(c['digest'])
                        cfp.add(c['fingerprint'])

    num_versions = len(versions)
    num_jar_digests = len(jds)
    num_jar_fingerprints = len(jfp)
    num_class_digests = len(cds)
    num_class_fingerprints = len(cfp)
    datasets[name]['counts'] = {
        'versions': num_versions,
        'jar-digests': num_jar_digests,
        'jar-fingerprints': num_jar_fingerprints,
        'class-digests': num_class_digests,
        'class-fingerprints': num_class_fingerprints
    }

with open(dataset_config, 'w', encoding='utf8') as f:
    f.write(json.dumps(datasets, indent=4)+"\n")

