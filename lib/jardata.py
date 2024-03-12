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

from io import BytesIO
from hashlib import sha256
import struct
import string

from .javaclass import JavaClass

class JarDataExtract:
    def __init__(self):
        self.synthetics = set()
        self.object_overrides = set()
        self.class_elements = {}
        self.class_digests = {}
        self.class_counter = 0

    @classmethod
    def hexnyb(cls, n):
        return "0123456789abcdef"[n]

    @classmethod
    def hexbyte(cls, b):
        a = (b >> 4) & 15
        b = b & 15
        return cls.hexnyb(a) + cls.hexnyb(b)

    @classmethod
    def hex(cls, data):
        res=[]
        for b in struct.unpack(str(len(data))+"B", data):
            res.append(cls.hexbyte(b))
        return "".join(res)
        
    

    def get_class_fingerprints(self, jc):

        elements = set()

        flags = jc.get_class_flags()
        #
        # Ignore synthetic classes
        #

        if (flags & 0x1000) != 0:
            return None
        
        cname = jc.get_class_name()

        if cname == 'module-info':
            return None
        
        if cname is not None:
            elements.add('cn:' + cname)

        sclass = jc.get_super_class_name()
        if sclass is not None:
            elements.add("pc:" + sclass)
        s = str(flags)
        elements.add("cf:" + s)

        for interface in jc.interfaces():
            elements.add("if:" + interface)

        for name,descr,flags in jc.fields():            
            if flags & 0x1000 != 0:
                key = "F:" + cname + "." + name
                self.synthetics.add(key)
                continue
            flags = str(flags)
            elements.add("fd:" + name + ";" + descr + ";" + flags)
            prefix="fd:" + name + ":"

        for name,descr,flags in jc.methods():
            
            key = "M:" + cname + ";" + name + ";" +descr

            if name in ['clone', 'equals', 'finalize', 'getClass', 'hashCode', 'notify', 'notifyAll', 'toString']:
                self.object_overrides.add(key)
                
            if flags & 0x1040 != 0:
                self.synthetics.add(key)
                continue
            
            flags = str(flags)
            elements.add("md:" + name + ";" + descr + ";" + flags)
            prefix="md:" + name + ";" + descr + ":"

        for s in jc.strings():
            elements.add("sc:" + s)

        for n in jc.get_int_constants():
            elements.add("iv:" + str(n))

        for n in jc.get_float_constants():
            s = "{0:0.4f}".format(n)
            elements.add("fv:" + s)

        for cname,mname,descr in jc.method_references():

            key = "M:" + cname + "." + name + ";" +descr

            if mname == '$values':
                continue


            #
            # Ignore return type
            #
            ndx = descr.find(")")
            if ndx != -1:
                descr = descr[0:ndx+1]
            elements.add("mr:" + cname + "." + name + ";" + descr)

        for cname,fname,descr in jc.field_references():
            if fname.find('$SwitchMap$') != -1:
                continue

            elements.add("fr:" + cname + "." + name + ";" + descr)

        classname = jc.get_class_name()
        self.class_elements[classname] = sorted(list(elements))
        self.class_counter += 1

    def get_class_count(self):
        return self.class_counter

    def get(self):

        class_fingerprints = []
        digest_set = []
        fingerprint_set = []

        #
        # Need to handle method references to local instances that
        # override java.lang.Object methods.
        #
        #if mname in ['clone', 'equals', 'finalize', 'getClass', 'hashCode', 'notify', 'notifyAll', 'toString']:
        #   if key not in self.object_overrides:
        #        continue

        allnames = set()
        for cname in self.class_digests:
            allnames.add(cname)
        for cname in self.class_elements:
            allnames.add(cname)

        for cname in sorted(allnames):
            if cname in self.class_elements:
                h = sha256()
                for e in sorted(filter(lambda x : x not in self.synthetics,
                                self.class_elements[cname])):
                    #
                    # Temporary work around for Python2 / Python3
                    # differences in handling non-ASCII
                    #
                    if False and not all(c in string.printable for c in e):
                        continue
                    
                    if e[0:3] != 'mr:':
                        h.update(e.encode(encoding='utf8'))
                        continue
                    mr = e.split(';')[0]
                    mname = mr.split('.')[-1]

                    if mname in ['clone', 'equals', 'finalize', 'getClass', 'hashCode', 'notify', 'notifyAll', 'toString']:                    
                        if e not in self.object_overrides:
                            continue
                        
                    h.update(e.encode(encoding='utf8'))
                    
                fingerprint = self.hex(h.digest())
                fingerprint_set.append(fingerprint)
            else:
                fingerprint = None

            rec = {
                'class': cname,
                'fingerprint': fingerprint
            }

            if cname in self.class_digests:
                digest = self.class_digests[cname]
                digest_set.append(digest)
                rec['digest'] = digest
            

            class_fingerprints.append(rec)

        if len(digest_set) != 0:
            h = sha256()
            for d in sorted(digest_set):
                h.update(d.encode('utf8'))
            jar_digest = self.hex(h.digest())
        else:
            jar_digest = None

        
        h = sha256()
        for d in sorted(fingerprint_set):
            h.update(d.encode('utf8'))
        fingerprint = self.hex(h.digest())

        #
        # jar-class-digest: Digest of the sorted digests of the
        #                   raw bytes of all class files.
        # jar-fingerprint:  Digest of the sorted fingerprints of
        #                   all of the class files.
        # classes:          Individual class information:
        #
        #    fingerprint:   Fingerprint of the class file
        #    digest:        Digest of the raw bytes of the class file.
        #    class:         Name of the class
        #
        
        rec = {
            'jar-fingerprint': fingerprint,
            'jar-class-digest': jar_digest,
            'classes': class_fingerprints,
        }

        return rec


    def add_class_file(self, filehandle):
        h = sha256()
        classbytes = BytesIO()
        while True:
            d = filehandle.read(-1)
            if d is None:
                continue
            if len(d) == 0:
                break
            h.update(d)
            classbytes.write(d)
        digest = self.hex(h.digest())
        classbytes.seek(0,0)
        jc = JavaClass()
        jc.load(classbytes)
        classname = jc.get_class_name()
        self.class_digests[classname] = digest
        self.get_class_fingerprints(jc)

    def get_jar_fingerprints(self, zipHandle):

        for f in zipHandle.infolist():
            zfn = f.filename
            if not zfn.endswith('.class'):
                continue
            if zfn.startswith("META-INF/"):
                continue
            with zipHandle.open(zfn) as zf:
                self.add_class_file(zf)
        return self.get()
    

