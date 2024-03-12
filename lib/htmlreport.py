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
import os

class HTMLReport:

    @classmethod
    def name(cls):
        return "html"

    
    def __init__(self, args):
        
        use_color=args['use_color']
    
        if use_color:
            self.red="severity_critical"
            self.orange="severity_high"
            self.yellow="severity_medium"
        else:
            self.red="severity_normal"
            self.orange="severity_normal"
            self.yellow="severity_normal"
        
        self.output=[]
        self.terminated = False

        self.write("<!DOCTYPE html>\n")
        self.write("<html>\n")
        self.write("<head>\n")
        if 'css' in args:
            self.add_css_file(args['css'])
        else:
            self.add_default_css()
        self.write("<title>log4j version report</title>\n")
        self.write("</head>\n")
        self.write("<body>\n")

    def write(self, text):
        self.output.append(text)

    def get(self):
        if not self.terminated:
            self.write("</body>\n")
            self.write("</html>\n")

            self.terminated = True
            
        return "".join(self.output)

    def add_default_css(self):

        myname = sys.argv[0]
        mydir = os.path.dirname(myname)
        top = os.path.realpath(os.path.join(mydir, ".."))
        cfdir = os.path.join(top, "cf")

        filename = os.path.join(cfdir, "default.css")
        
        self.add_css_file(filename)

    def add_css_file(self, name):
        self.write("<style>\n")
        
        with open(name, "r") as f:
            css = f.read(-1)
            self.write(css)
        
        self.write("</style>\n")

    def get_color(self, score):
        if score >= 8.5:
            return self.red

        if score >= 7.5:
            return self.orange

        if score >= 5:
            return self.yellow

        return "severity_normal"
        
        
    def get_version_color(self, record):
        tv = 0
        fv = 0
        if 'versions' in record:
            tv = tv + 1
            for v in record['versions']:
                if 'cve' in v:
                    fv = fv + 1
                    break
        if 'children' in record:
            for c in record['children']:
                a,b = getCounts(c)
                tv = tv + a
                fv = fv + b
        return tv, fv

        print(record)

    def get_child_version_counts(self, record):
        tv = 0
        fv = 0
        if 'versions' in record:
            tv = tv + 1
            for v in record['versions']:
                if 'cve' in v:
                    fv = fv + 1
                    break
        if 'children' in record:
            for c in record['children']:
                a,b = self.get_child_version_counts(c)
                tv = tv + a
                fv = fv + b
        return tv, fv
        


    def convert(self, record, indent=0, row=0):
        type = record['type']
        name = record['name']

        total=100

        collapsible = False
        if 'children' in record:
            if len(record['children']) > 0:
                collapsible = True

        self.write("<div style=\"margin-left:"+str(indent)+"%;\">")

        tv, fv = self.get_child_version_counts(record)

        if tv != 0:
            collapsible = True

        if fv != 0:
            color=self.get_color(10)
        else:
            color=None
        if collapsible:
            self.write("<details class=\"type-"+type+"\">")
            self.write("<summary>")
            self.write("[")
            self.write(str(fv))
            if fv != tv:
                self.write("/"+str(tv))
            self.write("] ")
            self.write(name)
            self.write("</summary>\n")
        else:
            self.write("<span>")
            self.write(name)
            self.write("</span>")

        if 'versions' in record:
            for v in record['versions']:
                color = None
                if 'cve' in v:
                    for c in sorted(v['cve'],key=lambda x: x['score'], reverse=True):
                        color = self.get_color(c['score'])
                        if color is not None:
                            break
                        
                self.write("<div style=\"margin-left:"+str(indent)+"%\">\n")
                self.write("<details>\n")
                self.write("<summary>\n")
                self.write("Version: ")
                vnames = v['version'].split(":")
                vname = " or ".join(vnames)
                self.write('<span class="'+color+'">') 
                self.write(vname)
                self.write('</span>')
                self.write("</summary>")

                self.write("<div style=\"margin-left:"+str(indent+1)+"%\">")

                self.write("</div>")

                if 'cve' in v:
                    for c in sorted(v['cve'],key=lambda x: x['score'], reverse=True):

                        id = c['id']
                        level = c['severity']
                        score = c['score']

                        color = self.get_color(score)

                        self.write("<div style=\"margin-left:"+str(indent+2)+"%\">")
                        self.write(id+" [")
                        self.write('<span class="' + color + '">')
                        self.write(level+"/"+str(score))
                        self.write("</span>]")
                        self.write("</div>\n")

                    self.write("")

                self.write("</details>\n")
                self.write("</div>\n")

        if 'children' in record:
            for c in record['children']:
                tn,fn = self.get_child_version_counts(c)
                c['_tv_'] = fn
            ordered = sorted(record['children'], key=lambda x: x['_tv_'],reverse=True)
            for c in ordered:
                self.convert(c, indent=indent+1)

        if collapsible:
            self.write("</details>\n")

        self.write("</div>\n")
