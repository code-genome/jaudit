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
import requests

from pkg_resources import parse_version as Version

if sys.version_info.major != 3:
    sys.stderr.write(sys.argv[0] + " requires Python 3\n")
    exit(1)

import lib.jaudit_utils as jutils
import lib.configuration as jconfig

myname = sys.argv[0]
mydir = os.path.realpath(os.path.dirname(myname))
basedir = os.path.realpath(mydir+"/..")

jaudit_config=jutils.load_jaudit_config(basedir)

config=os.path.join(basedir, "cf/monitored.json")
outfn=os.path.join(basedir, "cf/cve_info.json")

dump_all=False
dir=None

ndx = 1
while ndx < len(sys.argv):
    arg = sys.argv[ndx]
    ndx += 1
    if arg == '-d':
        dir=sys.argv[ndx]
        ndx += 1
    elif arg == '-o':
        outfn = sys.argv[ndx]
        ndx += 1
    elif arg == '--all':
        dump_all=True
    else:
        sys.stderr.write("Unknown command line argument '"+arg+"'.\n")
        exit(1)

if dir is None:
    dir=os.path.join(basedir, "cve")

def get_cvss2(rec):
    sev = None
    score = None
    for r in rec:
        cvss = r['cvssData']
        s = cvss['baseScore']
        if score is None or s > score:
            score = s
            sev = r['baseSeverity']
            
    return sev, score

def get_cvss3(rec):
    sev = None
    score = None
    for r in rec:
        cvss = r['cvssData']
        s = cvss['baseScore']
        if score is None or s > score:
            score = s
            sev = cvss['baseSeverity']

    return sev, score

cvss_metrics_handlers = {
    'cvssMetricV31': get_cvss3,
    'cvssMetricV30': get_cvss3,
    'cvssMetricV2': get_cvss2
}

#
# In order of preference
#
cvss_metrics = [
    'cvssMetricV31',
    'cvssMetricV2'
]

def get_threat(metric):
    for mname in cvss_metrics:
        if mname in metric:
            sev, score = cvss_metrics_handlers[mname](metric[mname])
            if sev is not None:
                return sev, score

    return None, None

#------------------------------------------------------------------------

#
# Retrieve the CISA-KEV list of exploited vulnerabilities
#
URL='https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json'

req = requests.get(url=URL, params=None)

cisa_kev = req.json()

req=None

cisa_cve_map = {}
for r in cisa_kev['vulnerabilities']:
    cve = r['cveID']
    if cve in cisa_cve_map:
        sys.stderr.write(f"Multiple CISA KEV entries for {cve}\n")
    cisa_cve_map[cve] = {
        'date': r['dateAdded'],
        'due': r['dueDate']
    }


minscore=5

monitored={}
with open(os.path.join(basedir, 'cf/monitored.json'), 'r') as f:
    monitored = json.load(f)

supported_versions=jconfig.ConfigurationData.analytic_data['supported_versions']

result = {}
cves_used=set()
for fn in os.listdir(dir):
    if not fn.startswith('cve_'):
        continue

    ifn = os.path.join(dir, fn)
    if fn.endswith(".gz"):
        infile = GZ.open(ifn, 'r', encoding='utf8')
    else:
        infile = open(ifn, 'r', encoding='utf8')

    try:
        dataset = json.load(infile)
        infile.close()
    except json.decoder.JSONDecodeError as e:
        infile.close()
        sys.stderr.write(f"{ifn}: {e}\n")
        continue

    for vuln in dataset['vulnerabilities']:
        cve_rec = vuln['cve']

        if cve_rec.get('vulnStatus', "") == 'Rejected':
            continue

        id = cve_rec['id']
        severity, score = get_threat(cve_rec['metrics'])

        if severity is None:
            continue

        if score < minscore:
            continue

        if 'configurations' not in cve_rec:
            continue

        for cf in cve_rec['configurations']:
            for node in cf['nodes']:
                for match in node['cpeMatch']:
                    criteria = match['criteria']
                    is_vuln = match['vulnerable']
                    if not is_vuln:
                        continue
                    vendor, product  = criteria.split(':')[3:5]
                    vendor = vendor.replace("\\", "", -1)
                    product = product.replace("\\", "", -1)

                    if 'versionStartIncluding' in match:
                        vstart = match['versionStartIncluding']
                    else:
                        vstart = ''

                    if 'versionEndExcluding' in match:
                        vend = match['versionEndExcluding']
                        op='<'
                    elif 'versionEndIncluding' in match:
                        vend = match['versionEndIncluding']
                        op='<='
                    else:
                        continue

                    if vstart == '':
                        versionStart = None
                    else:
                        versionStart = Version(vstart)

                    vEnd = Version(vend)

                    if dump_all:
                        print(f"{id},{severity},{score},{vendor},{product},{vstart},{op}{vend}")
                        continue

                    monitored_record = None
                    for name in monitored:
                        rec = monitored[name]
                        if not rec['enabled']:
                            continue
                        if 'vendor' not in rec:
                            sys.stderr.write("Entry '"+name+"' is mising 'vendor' field.\n")
                            continue
                        
                        if rec['vendor'] != vendor:
                            continue
                        cvename=name
                        if 'cve-name' in rec:
                            cvename = rec['cve-name']
                        if cvename != product:
                            continue

                        if 'version' in rec:
                            vinfo = rec['version']
                            if 'start' in vinfo:
                                vs = vinfo['start']
                                if op == '<':
                                    if Version(vs) >= vEnd:
                                        continue
                                elif op == '<=':
                                    if Version(vs) > vEnd:
                                        continue
                                
                            if 'end' in vinfo and versionStart is not None:
                                ve = vinfo['end']
                                if Version(ve) < versionStart:
                                    continue
                        
                        monitored_record = rec
                        monitored_name = name
                        break

                    if monitored_record is None:
                        continue

                    plen = len(monitored_name)

                    versionEnd = Version(vend)
                    for vname in supported_versions:
                        if not vname.startswith(monitored_name):
                            continue
                        vid = vname[plen+1:]
                        if not vid[0].isdigit():
                            continue
                        v = Version(vid)
                        if versionStart is not None and v < versionStart:
                            continue
                        if op == '<':
                            if v >= versionEnd:
                                continue
                        elif v > versionEnd:
                            continue
                        if vname not in result:
                            result[vname] = {
                            }
                        nr = {
                            'severity': severity,
                            'score': score,
                        }
                        vr = {}
                        if vstart != '':
                            vr['start'] = vstart
                        vr['end'] = vend
                        vr['end_op'] = op
                        nr['versions'] = vr
                        if id in cisa_cve_map:
                            nr['known_exploited'] = True
                            nr['cisa_kev'] = cisa_cve_map[id]
                        result[vname][id] = nr
                        cves_used.add(id)

cvelist=sorted(cves_used)
EPSS_URL='https://api.first.org/data/v1/epss'
epss_info={}
ndx=0

while ndx < len(cvelist):
    cvesubset = cvelist[ndx:ndx+30]
    ndx += 30
    req = requests.get(url=EPSS_URL, params={
        'cve': ",".join(cvesubset)
    })
    epss = req.json()
    for r in epss['data']:
        id = r['cve']
        epss_score = r['epss']
        epss_percentile = r['percentile']
        epss_info[id] = {
            'score': float(epss_score),
            'percentile': float(epss_percentile)
        }

for name in result:
    for id in result[name]:
        if id not in epss_info:
            continue
        result[name][id]['epss'] = epss_info[id]

with open(outfn, 'w', encoding='utf8') as f:                        
    f.write(json.dumps(result, indent=4, sort_keys=True))
    f.write("\n")
