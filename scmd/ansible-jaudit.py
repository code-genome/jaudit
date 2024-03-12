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


from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import sys
import json
import shutil
import importlib

if sys.version_info.major != 3:
    sys.stderr.write(sys.argv[0] + " requires Python 3\n")
    exit(1)

import ansible.constants as C
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.module_utils.common.collections import ImmutableDict
from ansible.inventory.manager import InventoryManager
from ansible.parsing.dataloader import DataLoader
from ansible.playbook.play import Play
from ansible.plugins.callback import CallbackBase
from ansible.vars.manager import VariableManager
from ansible import context

#------------------------------------------------------------------------

# Create a callback plugin so we can capture the output
class JauditCallback(CallbackBase):
    def __init__(self, storage_modules, *args, **kwargs):
        super(JauditCallback, self).__init__(*args, **kwargs)
        self.__storage_modules = storage_modules
        self.__exception_counts={}
        for _,name in storage_modules:
            self.__exception_counts[name] = 0

    def record(self, result, output):
        for sm,sm_name in self.__storage_modules:
            try:
                sm.log(result)
            except Exception as e:
                self.__exception_counts[sm_name] += 1
                if self.__exception_counts[sm_name] == 10:
                    sys.stderr.write(f"{sm_name}: Exception {e} (no longer reporting).\n")
                elif self.__exception_counts[sm_name] < 10:
                    sys.stderr.write(f"{sm_name}: Exception {e}.\n")
        if len(self.__storage_modules) == 0:
            output.write(json.dumps(result)+"\n")

    def v2_runner_on_ok(self, result, *args, **kwargs):
        host = str(result._host)
        res = json.loads(result._result['stdout'])
        res['inventory_name'] = host
        res['status'] = 'ok'
        self.record(res, sys.stdout)

    def v2_runner_on_failed(self, result, *args, **kwargs):
        host = str(result._host)
        res = {
            'type': 'host',
            'inventory_name': host,
            'status': 'failed',
            'error': result._result['stderr']
        }
        self.record(res, sys.stderr)

    def v2_runner_on_unreachable(self, result):
        host = str(result._host)

        res = {
            'type': 'host',
            'inventory_name': host,
            'status': 'down',
            'error': result._result['msg']
        }
        self.record(res, sys.stderr)

#------------------------------------------------------------------------

def main(jaudit, cmdargs, host_file, host_group, storage_modules=[]):

    
    context.CLIARGS = ImmutableDict(connection='smart',
                                    module_path=[],
                                    forks=10,
                                    become=None,
                                    become_method=None,
                                    become_user=None,
                                    check=False,
                                    diff=False,
                                    verbosity=0)

    if host_file is not None:
        sources = [host_file]
    else:
        sources = []


    # initialize needed objects
    loader = DataLoader()  # Takes care of finding and reading yaml, json and ini files
    #passwords = dict(vault_pass='secret')

    results_callback = JauditCallback(storage_modules)

    inventory = InventoryManager(loader=loader, sources=sources)

    variable_manager = VariableManager(loader=loader, inventory=inventory)
    
    tqm = TaskQueueManager(
        inventory=inventory,
        variable_manager=variable_manager,
        loader=loader,
        passwords=None,
        stdout_callback=results_callback,
    )

    if host_group is not None:
        host_list = [str(x) for x in inventory.get_hosts(pattern=host_group)]
        if len(host_list) == 0:
            sys.stderr.write("No matching hosts found in host file for "+host_group+".\n")
            exit(1)
    else:
        host_list = [str(x) for x in inventory.get_hosts()]
        if len(host_list) == 0:
            sys.stderr.write("No hosts found in host file.\n")
            exit(1)
            
 
    # create data structure that represents our play, including tasks, this is basically what our YAML loader does internally.
    cmdargs.append('--ansible-managed')
    play_source = {
        'name': "Jaudit",
        'hosts': host_list,
        'gather_facts': 'no',
        'tasks': [
            {
                'action': {
                    'module': 'script',
                    'cmd': jaudit + ' ' + ' '.join(cmdargs)
                },
                'register': 'shell_out'
            }
        ]
    }

    play = Play().load(play_source,
                       variable_manager=variable_manager,
                       loader=loader)

    try:
        result = tqm.run(play)
    finally:
        tqm.cleanup()
        if loader:
            loader.cleanup_all_tmp_files()

    shutil.rmtree(C.DEFAULT_LOCAL_TMP, True)

#------------------------------------------------------------------------

def usage(cmd):
    print("Usage: " + cmd + " --host-file <file-name> [options] [jaudit-options]")
    print("")
    print("Options:")
    print("      --host-group <group>     Select specific group from host file")
    print("      --jaudit-script <path>   Path to the jaudit.py script")
    print("      --help")
    print("")
    print("The --host-file option is required.  The hosts file must be a YAML")
    print("formatted file structured as an ansible host inventory file.")
    print("")
    print("Options for the jaudit.py script can also be provided.  Run")
    print("  jaudit.py --help")
    print("for a list of options.")
    print("")
    print("The location of jaudit.py will be determined automatically.  If it")
    print("is unable to be located, the --jaudit-script option can be used to")
    print("the location of it.\n")

if __name__ == '__main__':

    args = []
    ndx = 1
    storage_modules=[]

    jaudit=None
    host_file = None
    host_group = None

    while ndx < len(sys.argv):
        arg = sys.argv[ndx]
        ndx += 1
        
        if arg[0] != '-':
            args.append(arg)
            continue

        if arg == '--jaudit-script':
            jaudit = sys.argv[ndx]
            ndx += 1
            continue
        
        if arg == '--host-file':
            host_file = sys.argv[ndx]
            ndx += 1
            continue

        if arg == '--host-group':
            host_group = sys.argv[ndx]
            ndx += 1
            continue

        if arg == '--storage-module':
            mod_name = sys.argv[ndx]
            mod_name, init_args = mod_name.split('?')
            x = mod_name.split('.')
            class_name = x[-1]
            pkg_name = '.'.join(x[0:-1])
            ndx += 1
            try:
                p = importlib.import_module(pkg_name)
            except Exception as e:
                sys.stderr.write(f"Storage module package {mod_name} failed to load:\n\t{e}\n")
                exit(1)

            try:
                c = p.__getattribute__(class_name)
            except Exception as e:
                sys.stderr.write(f"Storage module package {mod_name} does not have class {class_name}.\n")
                exit(1)


            arg_dict = {}
            for a in init_args.split('&'):
                k,v = a.split('=', maxsplit=1)
                arg_dict[k] = v

            try:
                ci = c(**arg_dict)
            except Exception as e:
                sys.stderr.write(f"Storage module class {mod_name}.{class_name} failed to initialize:\n\t{e}\n")
                exit(1)

            try:
                l = ci.__getattribute__('log')
            except Exception as e:
                sys.stderr.write(f"Storage class {mod_name}.{class_name} does not have 'log()' method.\n")
                exit(1)
                
            
            storage_modules.append((ci, mod_name))
            continue
                
        
        if arg == '--help':
            usage(sys.argv[0])
            exit(0)


        args.append(arg)

    if host_file is None:
        sys.stderr.write("Must specify --host-file option.\n")
        exit(1)

    if len(args) == 0:
        args=['--running']

    if jaudit is None:
        #
        # Try to find jaudit.py
        #
        myname = sys.argv[0]
        mydir = os.path.realpath(os.path.dirname(myname))
        jaudit = os.path.realpath(mydir+"/../jaudit/jaudit.py")

        if not os.path.exists(jaudit):
            sys.stderr.write("Unable to find jaudit.py script.\n")
            exit(1)

    rc = os.system("python "+ jaudit + " --check-tables-ready")
    if rc != 0:
        sys.stderr.write("Jaudit script is not compatible with ansible-jaudit. It does not contain analytic tables.\n")
        exit(1)
        
    main(jaudit, args, host_file, host_group, storage_modules)
