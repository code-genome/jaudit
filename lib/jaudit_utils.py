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

def load_config(filename, config):

    def expand(cf, value):
        ndx = value.find('$')
        if ndx == -1:
            return value
        for vname in cf:
            if vname == name:
                continue
            value = value.replace('$' + vname, cf[vname])
        return value
    
    with open(filename, 'rt', encoding='utf8') as infile:
        for line in infile:
            if line[0] == '#':
                continue
            line = line.rstrip()
            name, value = line.split('=', 1)
            config[name] = expand(config, value)


def load_jaudit_config(top):
    config={
        "JAUDIT": top
    }
    filename=os.path.join(top, "cf/config.cf")
    load_config(filename, config)

    return config
