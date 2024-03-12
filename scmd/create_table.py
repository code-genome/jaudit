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
import zipfile

class TableCreator:

    def __init__(self):
        self.reset()

    def set_enabled(self, enabled_apps):

        self.enabled_apps = enabled_apps.copy()
        
        prefixes = sorted(enabled_apps, key=lambda p: len(p), reverse=True)
        
        self.prefixes = prefixes
        self.prefix_to_ndx = {}
        self.ndx_to_prefix = []

    def reset(self):
        self.records = {}
        self.prefixes = None
        self.versions = set()

    def loadz(self, file):
        with zipfile.ZipFile(file) as archive:
            for file in archive.infolist():
                with archive.open(file.filename, 'r') as f:
                    rec = json.load(f)
                    self.records[rec['jar-digest']] = rec
                    self.versions.add(rec['version'])

    def load(self, file):
        for path, _, files in os.walk(file):
            for f in files:
                with open(os.path.join(path,f), "r") as infile:
                    rec = json.load(infile)
                    self.records[rec['jar-digest']] = rec
                    self.versions.add(rec['version'])
                    

    def jar_digest_table(self):
        result = {}
        for d in self.records:
            v = self.compress_version(self.records[d]['version'])
            if v is None:
                continue
            digest = self.records[d]['jar-class-digest']
            if digest is None:
                sys.stderr.write(f"Unexpected None value in {self.records[d]['version']}\n")
                continue
            if digest not in result:
                result[digest] = [v]
            else:
                result[digest].append(v)
                
        jdt, jdt_minsize = self.minimize_keys(result)

        rec = {
            'analytic': 'jar-digest',
            'size': jdt_minsize,
            'identifiers': jdt,
            'prefix-map': tc.get_compression_map()
        }

        return rec
    
    def jar_fingerprint_table(self):
        result = {}
        for d in self.records:
            fp = self.records[d]['jar-fingerprint']
            v = self.compress_version(self.records[d]['version'])
            if v is None:
                continue
            if fp not in result:
                result[fp] = [v]
            else:
                result[fp].append(v)
                
        jfp, jfp_minsize = self.minimize_keys(result)

        rec = {
            'analytic': 'jar-fingerprint',
            'size': jfp_minsize,
            'identifiers': jfp,
            'prefix-map': tc.get_compression_map()
        }

        return rec
    

    def class_fingerprint_table(self):
        result = {}
        packages = []
        pkgmap = {}
        class_map = {}
        classes = []
        version_info = {}
        for d in self.records:
            rec = self.records[d]
            version = rec['version']
            v = self.compress_version(version)
            if v is None:
                continue
            vid,vnum = v
            if version not in version_info:
                version_info[version] = {
                    'classes': set(),
                    'packages': set()
                }
            
            for crec in rec['classes']:
                fingerprint = crec['fingerprint']
                if fingerprint is None:
                    continue
                cname = crec['class']
                version_info[version]['classes'].add(cname)
                x = cname.split('/')
                pkg = "/".join(x[0:-1])
                version_info[version]['packages'].add(pkg)
                cname = x[-1]
                if cname not in class_map:
                    class_map[cname] = len(classes)
                    classes.append(cname)
                cid = class_map[cname]
                if pkg not in pkgmap:
                    pkgmap[pkg] = len(packages)
                    packages.append(pkg)
                pid = pkgmap[pkg]

                v = (pid, cid, vid, vnum)
                if fingerprint not in result:
                    result[fingerprint] = [v]
                else:
                    result[fingerprint].append(v)

        cfp, cfp_minsize = self.minimize_keys(result, safety_margin=4)

        for v in version_info:
            version_info[v]['class_count'] = len(version_info[v]['classes'])
            version_info[v]['packages'] = list(version_info[v]['packages'])
            del version_info[v]['classes']

        rec = {
            'analytic': 'class-fingerprint',
            'size': cfp_minsize,
            'identifiers': cfp,
            'version_info': version_info,
            'package-map': packages,
            'class-map': classes,
            'prefix-map': tc.get_compression_map()
        }

        return rec


    def class_digest_table(self):
        result = {}
        packages = []
        pkgmap = {}
        version_info = {}
        class_map = {}
        classes = []
        
        for d in self.records:
            rec = self.records[d]
            version = rec['version']
            v = self.compress_version(version)
            if v is None:
                continue
            vid,vnum = v
            version_info[version] = {}
            for crec in rec['classes']:
                cname = crec['class']
                x = cname.split('/')
                pkg = "/".join(x[0:-1])
                cname = x[-1]
                if cname not in class_map:
                    class_map[cname] = len(classes)
                    classes.append(cname)
                cid = class_map[cname]
                
                if pkg not in pkgmap:
                    pkgmap[pkg] = len(packages)
                    packages.append(pkg)
                pid = pkgmap[pkg]
                digest = crec['digest']
                v = (pid, cid, vid, vnum)
                if digest not in result:
                    result[digest] = [v]
                else:
                    result[digest].append(v)
            version_info[version]['class_count'] = len(rec['classes'])

        cfp, cfp_minsize = self.minimize_keys(result, safety_margin=4)

        rec = {
            'analytic': 'class-digest',
            'size': cfp_minsize,
            'identifiers': cfp,
            'version_info': version_info,
            'package-map': packages,
            'class-map': classes,
            'prefix-map': tc.get_compression_map()
        }

        return rec
    

    def get_compression_map(self):
        return self.ndx_to_prefix.copy()

    def compress_version(self, version):
        if self.prefixes is None:
            return (-1,version)

        for p in self.prefixes:
            if not version.startswith(p):
                continue

            if p not in self.prefix_to_ndx:
                self.prefix_to_ndx[p] = len(self.ndx_to_prefix)
                self.ndx_to_prefix.append(p)
            
            ndx = self.prefix_to_ndx[p]
            n = len(p)
            return (ndx, version[n:])
        return None

    def minimize_keys(self, input, safety_margin=2):
        minsize=1
        keyset = sorted(list(input.keys()))
        for a in range(0,len(keyset)-1):
            keya = keyset[a]
            keya_s = keya[0:minsize]
            keyb = keyset[a+1]
            while True:
                if keya_s != keyb[0:minsize]:
                    break
                minsize += 1
                keya_s = keya[0:minsize]

        result = {}
        minsize += safety_margin
        for k in input:
            result[k[0:minsize]] = input[k]

        return result, minsize


if __name__ == '__main__':

    import sys
    import os

    if sys.version_info.major != 3:
        sys.stderr.write(sys.argv[0] + " requires Python 3\n")
        exit(1)

    myname = sys.argv[0]
    mydir = os.path.realpath(os.path.dirname(myname))
    basedir = os.path.realpath(mydir+"/..")

    config=os.path.join(basedir, "cf/monitored.json")
    dataset_config=os.path.join(basedir, "cf/datasets.json")
    #datadir=os.path.join(basedir, "jaudit.data/datasets")
    datadir=os.path.join(basedir, "jaudit.data/json")

    ndx = 1

    enabled = None
    disabled = set(['instructions'])
    enabled_analytics = None
    error=False
    output_filename = None
    prettyprint = False
    while ndx < len(sys.argv):
        arg = sys.argv[ndx]
        ndx += 1
        if arg == '-c':
            config = sys.argv[ndx]
            ndx += 1
        elif arg == '-a':
            if enabled_analytics is None:
                enabled_analytics = set()
            v = sys.argv[ndx]
            ndx += 1
            for a in v.split(','):
                enabled_analytics.add(a)
        elif arg == '-d':
            v = sys.argv[ndx]
            ndx += 1
            for p in v.split(','):
                disabled.add(p)
        elif arg == '-e':
            if enabled is None:
                enabled = set()
            v = sys.argv[ndx]
            ndx += 1
            for p in v.split(','):
                enabled.add(p)
        elif arg == '-o':
            output_filename = sys.argv[ndx]
            prettyprint=True
            ndx += 1
        elif arg == '--pretty':
            prettyprint=True
        else:
            sys.stderr.write(f"Unknown option to create_table: {arg}\n")
            error=True

    with open(dataset_config, 'r', encoding='utf8') as f:
        datasets=json.load(f)

        
    infiles = []
    for name in datasets:
        ds = datasets[name]['dataset']
        if type(ds) == type(""):
            ds = [ds]
            
        for fn in ds:
            if fn[0] != '/':
                fn = os.path.join(datadir, fn)
            infiles.append(fn)

    error=False
    if enabled_analytics is None:
        enabled_analytics=set([
            'jar-digest', 'jar-fingerprint'
        ])
    else:
        for a in enabled_analytics:
            if a not in ["jar-name", "jar-digest", "jar-fingerprint",
                         "class-fingerprint", "class-digest"]:
                sys.stderr.write(f"Unknown analytic {a}.\n")
                error=True


    names = []
    with open(config, 'r', encoding='utf8') as f:
        monitored = json.load(f)

        ids = set([monitored[c].get('id', c) for c in monitored.keys()])

        if enabled is not None:
            for e in enabled:
                if e not in ids:
                    sys.stderr.write(f"Unknown monitored app {e} in enabled list.\n")
                    error=True

        for d in disabled:
            if d == 'information':
                continue
            if d not in ids:
                sys.stderr.write(f"Unknown monitored app {d} in disabled list.\n")
                error=True
                    
        
        if enabled is None:
            names = list(filter(lambda c: monitored[c].get('enabled',False), monitored.keys()))
        else:
            names = list(filter(lambda c : monitored[c].get('id', c) in enabled, monitored.keys()))
        names = list(filter(lambda c : monitored[c].get('id', c) not in disabled, names))

            
    if error:
        exit(1)
        

    tc = TableCreator()

    tc.set_enabled(names)


    for archive in infiles:
        if os.path.isdir(archive):
            tc.load(archive)
        else:
            tc.loadz(archive)

    analytic_data = {}
    
    if 'jar-digest' in enabled_analytics:
        rec = tc.jar_digest_table()
        analytic_data[rec['analytic']] = rec

    if 'jar-fingerprint' in enabled_analytics:
        rec = tc.jar_fingerprint_table()
        analytic_data[rec['analytic']] = rec

    if 'class-fingerprint' in enabled_analytics:
        rec = tc.class_fingerprint_table()
        analytic_data[rec['analytic']] = rec

    if 'class-digest' in enabled_analytics:
        rec = tc.class_digest_table()
        analytic_data[rec['analytic']] = rec

    if 'jar-name' in enabled_analytics:
        regexes=[]
        standard = [
            "-[0-9][0-9\.]*)\.jar$",
            "-[0-9][0-9\.]*-?rc-?[0-9]*)\.jar$",
            "-[0-9][0-9\.]*-?alpha-?[0-9]*)\.jar$",
            "-[0-9][0-9\.]*-?beta-?[0-9]*)\.jar$"
        ]
        
        for ident in monitored:
            if not monitored[ident].get('enabled',False):
                continue
            for re in monitored[ident].get('match',[]):
                regexes.append(re)
            for std in standard:
                re = {
                    'regex': '^(' + ident + std
                }
                regexes.append(re)

        rec = {
            'analytic': 'jar-name',
            'identifiers': regexes
        }
        analytic_data[rec['analytic']] = rec

    analytic_data['enabled_apps'] = list(names)
    analytic_data['supported_versions'] = list(tc.versions)

    if prettyprint:
        s = json.dumps(analytic_data, indent=4)
    else:
        s = json.dumps(analytic_data, separators=(',',':'))

    if output_filename is None:
        print(s)
    else:
        with open(output_filename, 'w') as out:
            out.write(s+"\n")
