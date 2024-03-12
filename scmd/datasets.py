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
import gzip
import sqlite3

if sys.version_info.major != 3:
    sys.stderr.write(sys.argv[0] + " requires Python 3\n")
    exit(1)


myname = sys.argv[0]
dir = os.path.realpath(os.path.join(myname, ".."))
top = os.path.realpath(os.path.join(dir, ".."))
bindir=os.path.join(top, "bin")
runcmd=os.path.join(bindir, "run")

status = os.system(f"{runcmd} submodules check_installed data")
if status != 0:
    exit(1)

fpdir = os.path.join(top, "jaudit.data/jardata")
hashdir = top

fn = os.path.join(top, "cf/datasets.json")
with open(fn, 'r', encoding='utf8') as f:
    archive_info = json.load(f)

if len(sys.argv) < 2:
    sys.stderr.write(f"Usage: {sys.argv[0]} [list|verify]\n")
    exit(1)

cmd = sys.argv[1]

if cmd == 'list':
    print("")
    for name in sorted(archive_info.keys()):
        desc = archive_info[name]['description']
        vcnt = archive_info[name]['counts']['versions']
        jfpcnt = archive_info[name]['counts']['jar-fingerprints']
        cfpcnt = archive_info[name]['counts']['class-fingerprints']
        print(f"{name:17s} {desc}\n\t[{vcnt:,d} versions, {jfpcnt:,d} distinct, {cfpcnt:,d} distinct classes]")
    exit(0)

if cmd == 'verify':
    for name in sorted(archive_info.keys()):
        rec = archive_info[name]
        fn = rec['dataset']
        p = fn
        if p[0] != '/':
            p = os.path.join(fpdir, fn)
        if not os.path.exists(p):
            print(f"{name}: Missing fingerprint file {fn}.")
    exit(0)
