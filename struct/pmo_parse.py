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
  

def parseFaces(pmo,index_address,index_buffer,index_counts,face_order,info):
    faces = []
    pmo.seek(index_address)
    for indexData in index_counts:
        count = indexData["indexCount"]
        primitive_type = indexData["primitiveType"]
        index = [ix.index for ix in C.Struct("index" / index_buffer[count]).parse_stream(pmo).index]
        #if face_order: index = list(reversed(index))          
        r = range(count - 2)
        if primitive_type == 3:
            r = range(0, count, 3)
        elif primitive_type != 4:
            ValueError('Unsupported primative type: 0x{:02X}'.format(primitive_type))            
        signum = 0 + face_order
        for i in r:
            face = (index[i+signum],index[i+1-signum], index[i+2])
            signum = (signum + 1)%2     
            faces.append(face)
    return faces

def parseVertices(pmo, vertex_address,vertexBuffer,index,weights,info):
    vertices = []
    pmo.seek(vertex_address)
    for i in range(index):        
        vertex = vertexBuffer.parse_stream(pmo)
        vertex["weightData"] = list(zip(weights,vertex.weight))
        vertices.append(vertex)
    return vertices

def run_ge(pmo,weights,debug = None):
    base = pmo.tell()
    def info(op):
        return
        print("        %s: %d - %X"%(op,pmo.tell()-4-base,pmo.tell()-4))
    index_counts = []
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
            face_order = command & 1
            if command & 0xfffffE:
                print (bin(command & 0xfffffE))
        # PRIM - Primitive Kick
        elif command_type == 0x04:
            info("PRIM")
            index_counts.append(bitarray(command,primitiveTypeMap))
        # RET - Return from Call
        elif command_type == 0x0b:
            info("RET")
            break
        # ??? - Offset Address (BASE)
        elif command_type == 0x13: info("OFF_BASE")
        else:raise ValueError('Unknown GE command: 0x{:02X}'.format(command_type))
    #print(index_counts)
    faces = parseFaces(pmo,index_address,index_buffer,index_counts,face_order,info)
    #print(vertex_address)
    vertices = parseVertices(pmo,vertex_address,vertex_buffer,max(map(max,faces))+1,weights,info)
    if debug != None:
        debug.append(index_address)
        debug.append(vertex_address)
    return vertices, faces