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

import sys

class TextReport:

    @classmethod
    def name(cls):
        return "text"

    def __init__(self, args):

        use_color=args['use_color']
        
        if not use_color:
            self.red="<Alert>"
            self.orange="<Attention>"
            self.yellow="<Notice>"
            self.reset=""
        else:
            self.red="[91m"
            self.orange="[33m"
            self.yellow="[93m"
            self.reset="[39;49m"

        if sys.version_info.major == 3:
            self.vbar =  chr(0x2502)
            self.hbar =  chr(0x2500)
            self.angle = chr(0x2514)
            self.joint = chr(0x251c)
            self.cross = chr(0x253c)
        else:
            self.vbar = '|'
            self.hbar = '-'
            self.angle = '+'
            self.joint = '+'
            self.cross = '+'
        
        self.output=[]

    def get_color(self, score):
        if score >= 7.5:
            return self.red

        if score >= 5:
            return self.orange

        if score >= 2.5:
            return self.yellow

        return None

    def indent(self, indents, blank=False):
        if len(indents) == 0:
            return
        
        for indent in indents[0:-1]:
            if indent:
                self.output.append("  " + self.vbar + "  ")
            else:
                self.output.append("     ")

        bar = self.hbar
        if blank:
            self.output.append("  " + self.vbar + "\n")
            return
            
        if indents[-1]:
            self.output.append("  " + self.joint + self.hbar + self.hbar)
        else:
            self.output.append("  " + self.angle + self.hbar + self.hbar) 
                

    def convert(self, record, indents=[]):

        type = record['type']
        name = record['name']

        self.indent(indents)

        self.output.append(type+":"+name+"\n")
        if 'versions' in record:
            nversions = len(record['versions'])
            for ndx in range(0,nversions):
                v = record['versions'][ndx]
                vindent = indents + [ndx < (nversions-1)]
                self.indent(vindent)
                color=None

                if 'cve' in v:
                    for c in sorted(v['cve'],key=lambda x: x['score'], reverse=True):
                        color = self.get_color(c['score'])
                        if color is not None:
                            break

                if color is None:
                    color=""

                vnames = " or ".join(v['version'].split(":"))
                self.output.append("version: "+color+vnames+self.reset+"\n")
                if 'cve' in v:
                    cve_list = sorted(v['cve'],key=lambda x: x['score'], reverse=True)
                    ncve = len(cve_list)
                    for cndx in range(0,ncve):
                        c = cve_list[cndx]
                        cve_indent = vindent + [cndx < (ncve-1)]
                        id = c['id']
                        level = c['severity']
                        score = c['score']
                        color = self.get_color(score)
                        self.indent(cve_indent)
                        self.output.append(color+id+self.reset+" ["+level+"/"+str(score)+"]"+"\n")
                    if ndx < (nversions-1):
                        self.indent(vindent, blank=True)

        if 'children' in record:
            nchild = len(record['children'])-1
            for ndx in range(0,nchild+1):
                c = record['children'][ndx]
                self.convert(c, indents=indents + [ndx < nchild])


    def get(self):
        return "".join(self.output)
