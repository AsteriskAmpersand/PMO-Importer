# -*- coding: utf-8 -*-
"""
Created on Fri Jan 15 01:07:35 2021

@author: AsteriskAmpersand
"""
import array

try:
    from .. import construct_plugin as C
except:
    import construct as C
    pass

import struct
try:
    from pmo_vertex_buffer import (VPosition,
                                   VNormal,
                                   VWeight,
                                   VRGB,
                                   VUV,
                                   VIndex,)
except:
    from .pmo_vertex_buffer import (VPosition,
                                   VNormal,
                                   VWeight,
                                   VRGB,
                                   VUV,
                                   VIndex,)

from dataclasses import dataclass, fields

@dataclass
class _ParserState:
    """GPU Parser State for primitive properties"""
    backface_culling : bool
    alpha_blending : int
    alpha_test : int
    lighting_enable : bool
    clipping_enable : bool
    texture_enable : bool
    fog_enable : bool
    dither_enable : bool
    alpha_test_enable : bool
    depth_test_enable : bool
    antialiasing_enable : bool
    patch_culling_enable : bool
    color_test_enable : bool
    face_order :  int
    
    def copy(self):
        return self.__class__(*[self.__getattribute__(field.name) for field in fields(self.__class__)])

MetaLayerNames = [field.name for field in fields(_ParserState)]
ParserState = lambda : _ParserState(*[None]*13,0)

def bitarray(op,startStops):
    results = {}
    for key,(start,end) in startStops.items():
        results[key] = (op >> start) & (2**(end-start)-1)
    return results

vertexTypeMap = {
    "uvClass" : (0,2),
    "colorClass" : (2,4),
    "colorUse" : (4,5),
    "normalClass" : (5,7),
    "positionClass" : (7,9),
    "weightClass" : (9,11),
    "indexClass" : (11,13),
    "padding1" : (13,14),
    "weightCount" : (14,18),
    "morphClass" : (18,21),
    "padding2" : (21,23),
    "bypass" : (23,24),
    "operator" : (24,32),
    }

alignment = C.Struct(
        "pos" / C.Tell,
        "padding" / C.Padding((-C.this.pos)%4)
    )

def weightSpan(count,classing):
    wspan = [0,1,2,4][classing]
    stride = wspan*count
    return ((-stride) % 2)

#ix, pos,nor,col,uv,weight (r to l)
def vertexType(command):
    result = bitarray(command,vertexTypeMap)
    #print(result)
    if result["morphClass"]: raise ValueError("Morph Class not implemented")
    VertexBuffer = C.Struct(
                            "weight" / VWeight(result["weightClass"])[result["weightCount"]+1],
                            "padding" / C.Int8ul[weightSpan(result["weightCount"]+1,result["weightClass"])],
                            "uv" / VUV(result["uvClass"],result["bypass"]),
                            "colour" / VRGB(result["colorUse"],result["colorClass"]),
                            "normal" / VNormal(result["normalClass"],result["bypass"]),
                            "position" / VPosition(result["positionClass"],result["bypass"]),
        )
    IndexBuffer = VIndex(result["indexClass"])
    return IndexBuffer, VertexBuffer

primitiveTypeMap = {
    "indexCount" : (0,16),
    "primitiveType" : (16,19),
    "unknown" : (19,24),
    "operator" : (24,32),
    }

class IdentityList(list):
    def __getitem__(self, i):
        return i

def parseFaces(pmo,index_address,index_buffer,index_counts,info):
    faces = []
    ps = []
    pmo.seek(index_address)
    for indexData,parser_state in index_counts:
        count = indexData["indexCount"]
        primitive_type = indexData["primitiveType"]
        strct = C.Struct("index" / index_buffer[count]).parse_stream(pmo)
        if strct and any(strct.index): 
            index = [ix.index for ix in strct.index]
        elif index_buffer == C.Pass:
            index = list(range(count))
            print("Empty Index Structure in Tristrip")
        else:
            raise ValueError("Invalid Index Buffer Structure")
        #if face_order: index = list(reversed(index))
        r = range(count - 2)
        if primitive_type == 3:
            r = range(0, count, 3)
        elif primitive_type != 4:
            ValueError('Unsupported primitive type: 0x{:02X}'.format(primitive_type))
        signum = 0 + parser_state.face_order
        for i in r:
            #print(len(faces))
            face = (index[i+signum],index[i+1-signum], index[i+2])
            signum = (signum + 1)%2
            faces.append(face)
            ps.append(parser_state)
            #print(face)
        #print()
    return faces, ps

def parseVertices(pmo, vertex_address,vertexBuffer,index,weights,info):
    vertices = []
    pmo.seek(vertex_address)
    for i in range(index):
        vertex = vertexBuffer.parse_stream(pmo)
        vertex["weightData"] = list(zip(weights,vertex.weight))
        vertices.append(vertex)
    return vertices

def run_ge(pmo,weights,parser_state,debug = None):
    base = pmo.tell()
    def info(op):
        print("        %s: %d - %X"%(op,pmo.tell()-4-base,pmo.tell()-4))
        return
    ps = parser_state
    bool_commands = {
        0x17 : ("lighting_enable","LTE"),
        0x1c : ("clipping_enable", "CLE"),
        0x1d : ("backface_culling", "BCE"),
        0x1e : ("texture_enable", "TME"),
        0x1f : ("fog_enable", "FGE"),
        0x20 : ("dither_enable", "DTE"),
        0x22 : ("alpha_test_enable", "ATE"),
        0x23 : ("depth_test_enable", "ZTE"),
        0x25 : ("antialiasing_enable", "AAE"),
        0x26 : ("patch_culling_enable", "PCE"),
        0x27 : ("color_test_enable", "CTE"),        
        }
        
    index_counts = []
    index_address = 0
    parser_state.face_order = 0
    while True:
        command = array.array('I', pmo.read(4))[0]
        command_type = command >> 24
        # NOP - No Operation
        if command_type == 0x00: info("NOP")
        # ??? - Origin Address (BASE)
        elif command_type == 0x14: info ("ORI_BASE")
        # BASE - Base Address Register
        elif command_type == 0x10: info("BASE")
        # IADDR - Index Address (BASE)
        elif command_type == 0x02:
            info("IADDR")
            index_address = base + (command & 0xffffff)
        # VADDR - Vertex Address (BASE)
        elif command_type == 0x01:
            info("VADDR")
            vertex_address = base + (command & 0xffffff)
        # VTYPE - Vertex Type
        elif command_type == 0x12:
            info("VTYPE")
            index_buffer, vertex_buffer = vertexType(command)
        # FFACE - Front Face Culling Order
        elif command_type == 0x9b:
            info ("FACE_CULL")
            parser_state.face_order = command & 1
            if command & 0xfffffE:
                print (bin(command & 0xfffffE))
        # PRIM - Primitive Kick
        elif command_type == 0x04:
            info("PRIM")
            index_counts.append((bitarray(command,primitiveTypeMap),ps.copy()))
            
        # Bool Commands Table
        elif command_type in bool_commands:
            field,code = bool_commands[command_type]
            info(code)
            setattr(ps,field,command & 0xFFFFFF)
            
        # ABE - Alpha Blending
        elif command_type == 0x21:
            info("ABE")
            parser_state.alpha_blending = command & 0xFFFFFF#mask blending mode missing
        # ATEST - Alpha Test
        elif command_type == 0xdb:
            info("ATEST")
            parser_state.alpha_test = command & 0xFFFFFF#mask blending mode missing
        # RET - Return from Call
        elif command_type == 0x0b:
            info("RET")
            break
        # ??? - Offset Address (BASE)
        elif command_type == 0x13: info("OFF_BASE")
        else: raise ValueError('Unknown GE command: 0x{:02X}'.format(command_type))
    #print(index_counts)
    faces,pss = parseFaces(pmo,index_address,index_buffer,index_counts,info)
    #print(vertex_address)
    vertices = parseVertices(pmo,vertex_address,vertex_buffer,max(map(max,faces))+1,weights,info)
    faces = list(zip(faces,pss))
    if debug != None:
        debug.append(index_address)
        debug.append(vertex_address)
    return vertices, faces