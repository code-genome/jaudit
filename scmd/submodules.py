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

if sys.version_info.major != 3:
    sys.stderr.write(sys.argv[0] + " requires Python 3\n")
    exit(1)

myname = sys.argv[0]
bindir=os.path.dirname(myname)
mydir = os.path.realpath(bindir)
top = os.path.realpath(os.path.join(mydir, ".."))
runcmd=os.path.join(bindir, "run")

cffile = os.path.join(top, "cf/submodules.cf")

with open(cffile, 'r', encoding='utf8') as cfin:
     config = json.load(cfin)

args=sys.argv[1:]
    
if len(args) < 1:
    sys.stderr.write(f"Usage: {runcmd} submodules [list|add] names\n")
    exit(0)

def format_text(text, width=72, indent=None):
    lines=[]
    line=''
    line_len=0
    if indent is None:
        space=''
        space_len=0
    else:
        space=' ' * indent
        space_len = indent
    for word in text.split():
        wordlen = len(word)
        if line_len+wordlen >= width:
            lines.append(line)
            line=''
            line_len=0
            if indent is None:
                space=''
                space_len=0
            else:
                space=' ' * indent
                space_len = indent
        line += space + word
        line_len += wordlen + space_len
        space=' '
        space_len = 1
    if line_len != 0:
        lines.append(line)
        
    return "\n".join(lines)

def add_dependencies(config, names):

    all_added=set()

    while True:
        toadd = set()

        for name in names:
            entry = config[name]
            if 'requires' not in entry:
                continue
            for r in entry['requires']:
                if r not in names:
                    toadd.add(r)
        if len(toadd) == 0:
            break
        for name in toadd:
            all_added.add(name)
            names.add(name)

    if len(all_added) != 0:
        s = ', '.join(sorted(list(all_added)))
        sys.stderr.write(f"Including required dependencies: {s}.\n")
    return

cmd = args[0]

if cmd == 'list':
    for name in sorted(config.keys()):
        cf_entry = config[name]
        url=cf_entry['url']
        dirname = cf_entry['name']

        fulldirname = os.path.join(top, dirname)
        installed=''
        if os.path.exists(fulldirname):
            name=name+'[Y]'
        else:
            name=name+'[N]'
        
        desc=format_text(cf_entry['description'], width=78, indent=15)
        print(f"{name:14s} {url}\n{desc}\n")
    exit(0)

if cmd == 'add':
    added_submodules=set()
    exit_code = 0

    names=set()
    ndx=1
    use_links=False
    if os.getenv('SUBMODULE_LINKS') is not None:
        use_links=True
    base_directory=os.path.realpath(os.path.join(top, ".."))
    error=False
    while ndx < len(args):
        arg = args[ndx]
        ndx += 1
        if arg == '--use-links' or arg == '-l':
            use_links=True
        elif arg == '--base-directory' or arg == '-b':
            base_directory=args[ndx]
            ndx += 1
        elif arg[0] == '-':
            sys.stderr.write(f"submodules add: Unknown option '{arg}'.\n")
            error=True
            exit_code=1
        else:
            if arg not in config:
                sys.stderr.write(f"submodules: Unknown submodule '{arg}'.\n")
                exit_code = 1
                continue
            names.add(arg)

    if error:
        exit(exit_code)
    
    add_dependencies(config, names)

    for name in names:

        if name in added_submodules:
            continue

        cf_entry = config[name]
        url = cf_entry['url']
        dirname = cf_entry['name']

        fulldirname = os.path.join(top, dirname)

        if os.path.exists(fulldirname):
            sys.stderr.write(f"submodules: Submodule {name} already added.\n")
            continue

        if use_links:
            repo_name = os.path.basename(url)
            src=os.path.join(base_directory, repo_name)
            src=os.path.splitext(src)[0]
            os.system(f"ln -s {src} {fulldirname}")
            added_submodules.add(name)
        else:
            os.system(f"git clone {url} {fulldirname}")
            added_submodules.add(name)

    if len(added_submodules) != 0:
        added_names = ", ".join(sorted(list(added_submodules)))
        s='s'
        if len(added_submodules) == 1:
            s=''
        print(f"Added submodule{s} {added_names}.")
    
    exit(exit_code)

if cmd == 'check_installed':
    names=[]
    ndx=1
    base_directory=os.path.realpath(os.path.join(top, ".."))
    error=False
    quiet=False
    while ndx < len(args):
        arg = args[ndx]
        ndx += 1
        if arg == '--base-directory' or arg == '-b':
            base_directory=args[ndx]
            ndx += 1
        elif arg == '--quiet':
            quiet=True
        elif arg[0] == '-':
            sys.stderr.write(f"submodules check_installed: Unknown option '{arg}'.\n")
            error=True
            exit_code=1
        else:
            names.extend(arg.split(','))

    if error:
        exit(exit_code)

    missing=set()
    for name in names:
        if name not in config:
            sys.stderr.write(f"submodules: Unknown submodule '{name}'.\n")
            exit_code = 1
            continue

        cf_entry = config[name]
        url = cf_entry['url']
        dirname = cf_entry['name']

        fulldirname = os.path.join(top, dirname)

        if not os.path.exists(fulldirname):
            missing.add(name)

    if len(missing) == 0:
        exit(0)

    if not quiet:
        s=" ".join(sorted(list(missing)))
        print(f"\nsubmodules: Missing modules: {s}")
        print(f"\nTo install, use:\n\n\t{runcmd} submodules add {s}\n")
    exit(1)

if cmd == 'status':
    for line in sys.stdin:
        line=line.rstrip()
        deps = line.split()[0]
        ok=True
        for name in deps.split(','):
            if name == '-':
                continue
            if name not in config:
                ok=False
                break

            cf_entry = config[name]
            url = cf_entry['url']
            dirname = cf_entry['name']

            fulldirname = os.path.join(top, dirname)

            if not os.path.exists(fulldirname):
                ok=False
                break

        if not ok:
            status="N"
        else:
            status="Y"
        print(f"{status} {line}")
    exit(0)

sys.stderr.write(f"{sys.argv[0]}: Unknown subcommand '{cmd}'.\n")
exit(1)
