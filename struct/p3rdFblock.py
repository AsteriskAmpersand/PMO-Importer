# -*- coding: utf-8 -*-
"""
Created on Sun Oct 20 14:24:50 2024

@author: Asterisk
"""

from collections import OrderedDict

try:
    from ..common.Cstruct import PyCStruct
    from ..struct.fblock import FBlock
except:
    import sys
    sys.path.insert(0, r'..\common')
    from Cstruct import PyCStruct
    from fblock import FBlock
    

class P3Block (FBlock):
    @staticmethod
    def typeLookup(value):
        types = {
            0x40000001:BoneContent,
            0x80000000:P3Block,
            0x00000000:EntityStartBlock,
            }
        return types[value] if value in types else RawContent

class BoneContent(PyCStruct):
    fields = OrderedDict([
            ("nodeID","int32"),
            ("parentID","int32"),
            ("leftChild","int32"),
            ("rightSibling","int32"),
            ("scale","float[4]"),
            ("rot","float[4]"),
            ("pos","float[4]"),
            ("delimiter","uint32"),
            ("null","uint32"),
            ("name","ubyte[8]")
            ])
    def marshall(self,data):
        super().marshall(data)
        self.name = bytes(self.name).split(b'\x00', 1)[0].decode("utf-8")
        return self

class RawContent(PyCStruct):
    fields = OrderedDict([
            ("data","int32"),
            ])
    
EntityStartBlock = RawContent