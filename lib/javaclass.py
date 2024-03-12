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
import struct
from io import BytesIO

def isClassFile(file):
    '''
    Returns True if the file handle is referencing a file that is a
    Java class file.  Returns False otherwise.
    '''
    magic = file.read(4)
    if len(magic) != 4:
        return False

    if magic[0] != 0xCA or magic[1] != 0xFE or magic[2] != 0xBA or magic[3] != 0xBE:
       return False
    return True

TAG_UTF8String = 1
TAG_Int32 = 3
TAG_Float = 4
TAG_Int64 = 5
TAG_Double = 6
TAG_ClassRef = 7
TAG_StringRef = 8
TAG_FieldRef = 9
TAG_MethodRef = 10
TAG_InterfaceMethodRef = 11
TAG_NameAndType = 12
TAG_MethodHandle = 15
TAG_MethodType = 16
TAG_Dynamic = 17
TAG_InvokeDynamic = 18
TAG_Module = 19
TAG_Package = 20

def decodeType(type, objName):
    ndx = 0
    res = []
    args = None
    retType = None
    isArray = False

    while ndx < len(type):
        c = type[ndx]
        name = None
        if c == 'I':
            name = 'int'
        elif c == 'Z':
            name = 'boolean'
        elif c == 'B':
            name = 'byte'
        elif c == 'C':
            name = 'char'
        elif c == 'S':
            name = 'short'
        elif c == 'J':
            name = 'long'
        elif c == 'F':
            name = 'float'
        elif c == 'D':
            name = 'double'
        elif c == 'V':
            name = ""
        elif c == 'L':
            ndx = ndx+1
            start=ndx
            while ndx < len(type) and type[ndx] != ';':
                ndx = ndx+1
            name = type[start:ndx]
        elif c == '[':
            isArray=True
            ndx = ndx + 1
            continue
        
        elif c == '(':
            ndx = ndx + 1
            start = ndx
            while ndx < len(type) and type[ndx] != ')':
                ndx = ndx+1
            args = '(' +  decodeType(type[start:ndx], None) + ')'
        else:
            print(type)
            raise TypeError("Invalid character '"+c+"'in type signature")

        if isArray:
            name = name + '[]'
        isArray = False

        if name is not None and args is None:
            res.append(name)
        else:
            retType = name
        ndx = ndx + 1


    if args:
        if retType == "":
            return objName + args
        else:
            return retType + " " + objName + args
    else:
        s = ",".join(res)
        if objName is None:
            return s
        elif s == "":
            return objName
        else:
            return s + " " + objName
            

class JavaClass:

    
    major_version = 0
    minor_version = 0
    
    __class = None
    __super = None
    __constants = []
    __methodInfo = []
    __fields = []
    __interfaces = []

    __NullSlot = False

    __file = None

    
    def __init__(self):
        self.__class = None
        self.__loaded = False
            
    def load(self, file):
        '''Loads a class file from a file handle'''
        if type(file) == type(b''):
            self.__file = BytesIO(file)
        else:
            self.__file = file
        data = self.__readbytes(4)
        if len(data) != 4:
            return None
        magic = self.__readlong(data)
        if magic != 0xCAFEBABE:
            return None

        self.minor_version = self.__readshort()
        self.major_version = self.__readshort()

        const_count = self.__readshort()

        #
        # To do this as a list comprehension, we need a bit of a hack
        # because of the TAG_Int64 TAG_Double stupidity.  These two tags
        # count as "two slots" in the constant pool, but are actually just
        # one slot.  So, we have to do two things.  One, not read anything
        # for the "second" slot, but because everything indexes into the
        # constant pool, we have to insert a dummy entry into the pool for
        # them.  self.__NullSlot is checked in readconstant() and doesn't
        # read anything, it just returns a dummy slot.  When we see a
        # TAG_Int64 or TAG_Double, we set self.__NullSlot to True
        #
        self.__NullSlot = False
        self.__constants = [self.__readconstant() for i in range(0,const_count-1)]

        self.__flags = self.__readshort()
        self.__class = self.__readshort()
        self.__super = self.__readshort()


        ifcount = self.__readshort()

        self.__interfaces = [self.__readshort() for i in range(0,ifcount)]

        fcount = self.__readshort()
        self.__fields = [self.__readfm() for i in range(0,fcount)]

        mcount = self.__readshort()
        self.__methodInfo = [self.__readfm() for i in range(0,mcount)]

        acount = self.__readshort()

        attr = [self.__readattr() for i in range(0,acount)]

        self.__file = None

        self.__loaded = True

        return self
        
    def loadFile(self,filename):
        '''Loads a class file specified by filename'''
        with open(filename, mode='rb') as file:
            self.load(file)
        return self

    #------------------------------------------------------------------------

    def is_loaded(self):
        return self.__loaded

    def get_class_name(self, raw=False):
        '''Returns the name of the class of the loaded class file'''
        if self.__class != 0:
            return self.__getClassName(self.__class, raw)
        return None

    def get_class_flags(self):
        return self.__flags
    
    def get_super_class_name(self, raw=False):
        '''Returns the name of the super class of the loaded class file'''
        if self.__super != 0:
            return self.__getClassName(self.__super, raw)
        return None

    def methods(self, raw=False):
        '''
        Returns a list of the defined method names in the class.

        Each element of the list contains a tuple consisting of the
        method name and the type signature of the method and the
        integer representation of the flags field.
        '''
        for x in self.__methodInfo:
            name = self.__getStrConst(x[1], raw)
            desc = self.__getStrConst(x[2], raw)
            yield (name, desc, x[0])


    def fields(self, raw=False):
        '''
        Returns a list of the defined fields in the class.

        Each element of the list contains a tuple consisting of the
        method name and the type signature of the method and the
        integer representation of the flags.
        '''
        for x in self.__fields:
            name = self.__getStrConst(x[1], raw)
            desc = self.__getStrConst(x[2], raw)
            yield (name, desc, x[0])
            

    def method_references(self, raw=False):
        '''
        Returns a list of methods referenced by the class.

        Each element of the list contains a 3 element tuple. The first
        element is the class where the called class is located.  The second
        element is the method name, and the third is the type signature of
        the method.
        '''

        for x in self.__constants:
            if x[0] == TAG_MethodRef:
                cname = self.__getClassName(x[1], raw)
                method,type = self.__getNameType(x[2],raw)
                yield (cname,method,type)

    def field_references(self, raw=False):
        for x in self.__constants:
            if x[0] == TAG_FieldRef:
                cname = self.__getClassName(x[1], raw)
                method,type = self.__getNameType(x[2],raw)
                yield (cname,method,type)
        

    def strings(self, raw=False):
        '''Returns a list of all the string constants in the class file'''

        for x in self.__constants:
            if x[0] != TAG_StringRef:
                continue
            s = self.__getStrConst(x[1], raw=True)
            if len(s) > 1:
                b = struct.unpack('B', s[0:1])[0]
                if b == 1:
                    continue
            yield self.__getStrConst(x[1], raw)

    def getPackageName(self, raw=False):
        '''Returns the package name'''
        cname = self.className(raw)
        if raw:
            n = cname.rfind(b'/')
        else:
            n = cname.rfind('/')
        if n == -1:
            return None
        return cname[0:n]

    def get_int_constants(self, raw=False):
        '''Returns a list of all the int32 constants in the class file'''

        if raw:
            for x in self.__constants:
                if x[0] == TAG_Int32 or x[0] == TAG_Int64:
                    yield x[2]
        else:
            for x in self.__constants:
                if x[0] == TAG_Int32 or x[0] == TAG_Int64:
                    yield x[1]

    def get_float_constants(self, raw=False):
        '''Returns a list of all the int32 constants in the class file'''

        if raw:
            for x in self.__constants:
                if x[0] == TAG_Float or x[0] == TAG_Double:
                    yield x[2]
        else:
            for x in self.__constants:
                if x[0] == TAG_Float or x[0] == TAG_Double:
                    yield x[1]

    def interfaces(self, raw=False):
        '''Returns a list of all implemented interfaces'''

        return map(lambda x: self.__getClassName(x,raw), self.__interfaces)

    
        
    #------------------------------------------------------------------------

    def __getClassName(self, index, raw=False):
        c = self.__constants[index-1]
        type = c[0]
        if type == TAG_ClassRef:
            return self.__getStrConst(c[1], raw)
        raise TypeError("Wrong type tag<"+str(type)+"> for class name record")

    def __getNameType(self, index, raw=False):
        c = self.__constants[index-1]
        type = c[0]
        if type == TAG_NameAndType:
            name = self.__getStrConst(c[1], raw)
            type = self.__getStrConst(c[2], raw)
            return (name,type)
        raise TypeError("Wrong type tag<"+str(type)+"> for name record")
        

    def __getMethodName(self, index, raw=False):
        c = self.__constants[index-1]
        type = c[0]
        if type == TAG_MethodRef:
            cname = self.__getClassName(c[1], raw)
            (name,type) = self.__getNameType(c[2], raw)
            return (cname, name, type)
        raise TypeError("Wrong type tag<"+str(type)+"> for method name record")

    def __getStrConst(self, index, raw=False):
        c = self.__constants[index-1]
        type = c[0]

        if type == TAG_UTF8String:
            if raw:
                return c[1]
            return c[1].decode("utf-8", errors='replace')
        raise TypeError("Wrong type tag<"+str(type)+"> for UTF-8 string constant")

    #------------------------------------------------------------------------

    def __readbytes(self, nbytes):
        res = None
        while nbytes > 0:
            d = self.__file.read(nbytes)
            n = len(d)
            if n <= 0:
                break
            if res is None:
                res = d
            else:
                res = res + d
            nbytes = nbytes - n
        if res is None:
            res = b''
        return res
    
    def __readshortd(self,data):
        return struct.unpack('>H', data[0:2])[0]

    def __readlong(self,data,offset=0):
        return struct.unpack('>I', data[offset:offset+4])[0]

    def __readshort(self):
        data = self.__readbytes(2)
        return self.__readshortd(data)

    def __read2short(self):
        data = self.__readbytes(4)
        a = self.__readshortd(data[0])
        b = self.__readshortd(data[2:])
        return (a,b)
    

    def __readfm(self):
        
        data = self.__readbytes(8)
        flags = self.__readshortd(data)
        index = self.__readshortd(data[2:])
        desc = self.__readshortd(data[4:])
        acount = self.__readshortd(data[6:])
        attr = [self.__readattr() for i in range(0,acount)]
        return (flags, index, desc, attr)

    def __readattr(self):

        data = self.__readbytes(6)
        index = self.__readshortd(data)
        alen = self.__readlong(data[2:])
        data = self.__readbytes(alen)
        return (index, data)

    def __readconstant(self):

        if self.__NullSlot is True:
            self.__NullSlot = False
            return (-1,None)

        data = self.__readbytes(3)
        tag = struct.unpack('B',data[0:1])[0]
        data = data[1:]
        if tag == TAG_UTF8String:
            dlen = self.__readshortd(data)
            data = self.__readbytes(dlen)
            return (tag, data)
                
        elif tag == TAG_NameAndType or tag == TAG_MethodRef or \
             tag == TAG_FieldRef or tag == TAG_InterfaceMethodRef:
            index1 = self.__readshortd(data)
            index2 = self.__readshort()
            return (tag,index1,index2)
                
        elif tag == TAG_ClassRef or tag == TAG_StringRef:
            index = self.__readshortd(data)
            return (tag,index)
                
        elif tag == TAG_Int32:
            data2 = self.__readbytes(2)
            a = self.__readshortd(data)
            b = self.__readshortd(data2)
            n = a << 16 | b
            return (tag, n, data+data2)
                
        elif tag == TAG_Float:
            data = data + self.__readbytes(2)
            v = struct.unpack('>f', data)[0]
            return (tag, v,data)
                
        elif tag == TAG_Int64:
            data = data + self.__readbytes(6)
            a = self.__readlong(data)
            b = self.__readlong(data, 4)
            v = a << 32 | b
            self.__NullSlot = True
            return(tag, v, data)

        elif tag == TAG_Double:
            data = data + self.__readbytes(6)
            v = struct.unpack('>d', data)[0]
            self.__NullSlot = True
            return(tag, v, data)
        
                
        elif tag == TAG_MethodHandle:
            data = data + self.__readbytes(1)
            return (tag, data)

        elif tag == TAG_MethodType:
            return (tag, data)
                
        elif tag == TAG_Dynamic:
            data = data + self.__readbytes(2)
            return (tag, data)
                
        elif tag == TAG_InvokeDynamic:
            data = data + self.__readbytes(2)
            return (tag, data)
                
        elif tag == tag == TAG_Package or tag == TAG_Module:
            index = self.__readshortd(data)
            return (tag, index)
                
        else:
            raise TypeError("Unrecognized tag<"+str(type)+"> while loading constant pool")

