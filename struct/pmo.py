# -*- coding: utf-8 -*-
"""
Created on Thu Jan 14 22:39:43 2021

@author: AsteriskAmpersand
"""
#import construct as C
try:
    from .pmo_parse import run_ge
    from .. import construct_plugin as C
except:
    from pmo_parse import run_ge
    import construct as C
    #from pmo_parse_orig import run_ge
    pass

alignment = C.Struct(
        "pos" / C.Tell,
        "padding" / C.Padding((-C.this.pos)%16)
    )

Header = C.Struct(
    "pmo" / C.Int8ul[4],
    "ver" / C.Int8ul[4],
    "filesize" / C.Int32ul,
    "clippingDistance" / C.Float32l,
    "scale" / C.Float32l[3],
    "meshCount" / C.Int16ul,
    "materialCount" / C.Int16ul,
    "meshHeaderOffset" / C.Int32ul,
    "vertexGroupHeaderOffset" / C.Int32ul,
    "materialRemapOffset" / C.Int32ul,
    "unknI10" / C.Int32ul,
    "materialDataOffset" / C.Int32ul,
    "meshDataOffset" / C.Int32ul,
    "padding" / alignment,
    )

VertexGroupHeader = C.Struct(
    "materialOffset" / C.Int8ul,
    "boneCount" / C.Int8ul,    
    "cumulativeBoneCount" / C.Int16ul,    
    "meshOffset" / C.Int32ul,
    "vertexOffset" / C.Int32ul,
    "indexOffset" / C.Int32ul,
    )

MeshHeader = C.Struct(
    "uvScale" / C.Float32l[2],
    "unkn1" / C.Int8ul[8],
    "materialCount" / C.Int16ul,
    "cumulativeMaterialCount" / C.Int16ul,
    "subMeshCount" / C.Int16ul,
    "cumulativeSubmeshCount" / C.Int16ul,
    "submeshHeaders" / C.Pointer(C.this._.header.vertexGroupHeaderOffset + C.this.cumulativeSubmeshCount*VertexGroupHeader.sizeof(),
                                 VertexGroupHeader[C.this.subMeshCount])
    )

Skeleton = C.Struct(
    "index" / C.Int8ul,
    "bone" / C.Int8ul,
    )

MaterialContent = C.Struct(
    "index" / C.Computed(C.this._index),
    "rgba" / C.Int8ul[4],
    "rgba2" / C.Int8ul[4],
    "textureID" / C.Int32sl,
    "unkn" / C.Int8ul[4],
    )

PMO = C.Struct(
    "header" / Header,
    "padding0" / alignment,
    "meshHeaders" / MeshHeader[C.this.header.meshCount],
    "padding1" / alignment,
    C.Seek(C.this.header.materialRemapOffset),
    "materialRemapCount" / C.Computed(lambda this: this.meshHeaders[this.header.meshCount-1].cumulativeMaterialCount + this.meshHeaders[this.header.meshCount-1].materialCount),
    "materialRemap" / C.Int8ul[C.this.materialRemapCount],
    "padding3" / alignment,
    "skeletonRemapCount" / C.Computed(lambda this: this.meshHeaders[this.header.meshCount-1].submeshHeaders[this.meshHeaders[this.header.meshCount-1].subMeshCount-1].boneCount+
                                                  this.meshHeaders[this.header.meshCount-1].submeshHeaders[this.meshHeaders[this.header.meshCount-1].subMeshCount-1].cumulativeBoneCount),
    "skeleton" / Skeleton[C.this.skeletonRemapCount],
    "padding4" / alignment,
    "materialData" / MaterialContent[C.this.header.materialCount],
    C.Seek(C.this.header.meshDataOffset),
    )

class weightParser():
    def __init__(self,weightList):
        
        bufferSize = max([w.index for w in weightList])+1 if weightList else 0
        self.boneIds = [-1]*bufferSize
        self.weightIter = iter(weightList)
    def consume(self,count):
        for _ in range(count):
            w = next(self.weightIter)            
            self.boneIds[w.index] = w.bone
    def __iter__(self):
        return iter(self.boneIds)

def load_pmo(pmopath):
    meshes = []
    with open(pmopath,"rb") as inf:
        pmo = PMO.parse_stream(inf)
        weightData = weightParser(pmo.skeleton)
        for mesh in pmo.meshHeaders:
            verts = []
            faces = []
            materials = []
            for tristripHeader in mesh.submeshHeaders:
                weightData.consume(tristripHeader.boneCount)
                try:
                    matRIx = mesh.cumulativeMaterialCount + tristripHeader.materialOffset
                    matIx = pmo.materialRemap[matRIx]
                    mat = pmo.materialData[matIx]
                except:
                    mat = pmo.materialData[0]
                inf.seek(pmo.header.meshDataOffset + tristripHeader.meshOffset)
                #DEBUG = []
                v,f = run_ge(inf,weightData)
                faces += [tuple(map(lambda x: x + len(verts),face)) for face in f]
                verts += v
                materials += [mat.index for face in f]
            meshes.append((verts,faces,materials,pmo.header.scale,mesh.uvScale))
    return meshes,pmo

def load_cmo(cmopath):
    meshes = []
    verts = []
    faces = []
    with open(cmopath,"rb") as inf:
        cmoflag = inf.read(1)
        v,f = run_ge(inf,[0 for i in range(8)])
        faces += [tuple(map(lambda x: x + len(verts),face)) for face in f]
        verts += v
        meshes.append((verts,faces,[],[1,1,1],[1,1]))
    return meshes,cmoflag

if __name__ in "__main__":
    from pathlib import Path
    for file in Path(r"D:\Downloads\em37\models\models").rglob("*.pmo"):
        #print(file)
        meshes,pmo = load_pmo(file)
        an = False
        for ix,mat in enumerate(pmo.materialData):
            if tuple(mat.unkn) != (0,0,0,0):
                if not an: print(file.replace(r"D:\Downloads\em37\models"+"\\",""))
                print("%d:%s"%(ix,tuple(mat.unkn)))
                an = True