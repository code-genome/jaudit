#!/usr/bin/python
##
## This code is part of the Jaudit utilty.
##
## (C) Copyright IBM 2023.
##
## This code is licensed under the Apache License, Version 2.0. You may
## obtain a copy of this license in the LICENSE.txt file in the root directory
## of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
##
## Any modifications or derivative works of this code must retain this
## copyright notice, and modified files need to carry a notice indicating
## that they have been altered from the originals.
##

import os
import json
import re
import sys

class JarNameVersion:

    def __init__(self, config):
        self.load_patterns(config)
        self.reported = set()

    def get_app_record(self, version_string):

        packages = sorted(self.config.keys(), key=lambda x: len(x), reverse=True)

        for pkg in packages:
            if version_string.startswith(pkg):
                n = len(pkg)
                if version_string[n] == '-':
                    if 'id' not in self.config[pkg]:
                        self.config[pkg]['id'] = pkg
                    return self.config[pkg]
        return None
    
    def get_version(self, filename):
        filename = os.path.basename(filename).lower()
        for p,fmt in self.patterns:
            try:
                m = re.match(p, filename)
            except:
                if p not in self.reported:
                    sys.stderr.write("Malformed regular expression " + p + "\n")
                    self.reported.add(p)
                continue
            
            if m is None:
                continue
            if fmt is None:
                fmt="%1"

            pos = 0
            segments = [x for x in m.groups()]
            replacements = []
            for ndx,value in enumerate(segments,1):
                var = '%' + str(ndx)
                value = segments[ndx-1]
                pos = 0
                while True:
                    ndx = fmt.find(var, pos)
                    if ndx == -1:
                        break
                    replacements.append((value,ndx,ndx+len(var)))
                    pos = ndx + len(var)

            v = []
            pos = 0
            for value, start, end in replacements:
                v.append(fmt[pos:start])
                v.append(value)
                pos = end
                
            version = "".join(v)
                
            return version
        return None

    def load_patterns(self, config):
        with open(config, 'r', encoding='utf8') as f:
            monitored = json.load(f)

        self.config = monitored

        standard = [
            "-[0-9][0-9\.]*)\.jar$",
            "-[0-9][0-9\.]*-?rc-?[0-9]*)\.jar$",
            "-[0-9][0-9\.]*-?alpha-?[0-9]*)\.jar$",
            "-[0-9][0-9\.]*-?beta-?[0-9]*)\.jar$"
        ]

        patterns = set()
        for name in monitored.keys():
            rec = monitored[name]
            if not rec['enabled']:
                continue
            for std in standard:
                patterns.add(("(" + name + std,None))

            if 'match' in rec:
                for r in rec['match']:
                    rex = r['regex']
                    if 'format' in r:
                        patterns.add((rex, r['format']))
                    else:
                        patterns.add((rex, None))
        self.patterns = patterns


