#!/usr/bin/python3

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

from lib.textreport import TextReport
from lib.htmlreport import HTMLReport

colorize=True

args = sys.argv[1:]

generator_class=TextReport

generators = [
    TextReport,
    HTMLReport
]

generator_names = {}
for g in generators:
    generator_names[g.name()] = g

ndx = 1
infiles=[]
generator_args={
    'use_color': True
}
while ndx < len(sys.argv):
    arg = sys.argv[ndx]
    ndx += 1
    if arg == "--no-color":
        generator_args['use_color'] =  False
        
    elif arg == '--mode':
        modename = sys.argv[ndx]
        ndx += 1
        if modename not in generator_names:
            sys.stderr.write("Unknown report generator " + modename + ".\n")
            exit(1)
        generator_class=generator_names[modename]

    elif arg == '--set':
        kv = sys.argv[ndx]
        ndx += 1
        k,v = kv.split('=', 1)
        generator_args[k] = v
        
    elif arg[0] == '-':
        sys.stderr.write(f"{sys.argv[0]}: Unknown option {arg}\n")
        exit(1)
    else:
        infiles.append(arg)

generator = generator_class(generator_args)

if len(infiles) > 0:
    for f in infiles:
        with open(f, "r") as file:
            try:
                record = json.load(file)
                if type(record) == list:
                    for rec in record:
                        generator.convert(rec)
                else:
                    generator.convert(record)
            except json.decoder.JSONDecodeError as e:
                sys.stderr.write(e.msg+"\n")
else:
    try:
        record = json.load(sys.stdin)
        if type(record) == list:
            for rec in record:
                generator.convert(rec)
        else:
            generator.convert(record)
    except json.decoder.JSONDecodeError as e:
        sys.stderr.write(e.msg+"\n")

print(generator.get())
