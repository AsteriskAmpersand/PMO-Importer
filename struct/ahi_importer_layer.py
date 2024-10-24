# -*- coding: utf-8 -*-
"""
Created on Mon Dec 30 01:17:01 2019

@author: AsteriskAmpersand
"""

from ..struct.ahi import FUSkeleton,P3Skeleton
import bpy
import bmesh
import array
import os
from mathutils import Vector, Matrix, Euler
from pathlib import Path

_formats = {
    "FU" :  FUSkeleton,
    "P3" : P3Skeleton,
    }

formats = [
    ("FU","Freedom Unite","Monster Hunter Freedom Unite",0),
    ("P3","Portable 3rd","Monster Hunter Portable 3rd",1),
    ]

class AHIImporter():
    @staticmethod
    def execute(context,fmodPath,fformat,rename):
        skeleton = _formats[fformat](fmodPath).skeletonStructure()
        currentSkeleton = {}
        o = bpy.data.objects.new("Armature", None)
        bpy.context.collection.objects.link(o)
        # bpy.context.view_layer.update()
        currentSkeleton = {-1: o}
        for bone in skeleton.values():
            AHIImporter.importBone(bone, currentSkeleton, skeleton)
        if rename: AHIImporter.renameWeights(context,currentSkeleton)
        return o
    
    @staticmethod
    def renameWeights(ctx,skeletonmap):
        remap = {"Bone.%03d" % bid:bone.name for bid, bone in skeletonmap.items()}
        for obj in ctx.scene.objects:
            if obj.type == "MESH":
                for group in obj.vertex_groups:
                    if group.name in remap:
                        group.name = remap[group.name]
                
    @staticmethod
    def deserializePoseVector(pos,scale,rot):
        m = Matrix.Identity(4)
        #m.LocRotScale(pos[:3],Euler(rot[:3]),scale[:3])   
        m.translation = pos[:3]
        return m

    @staticmethod
    def importBone(bone, skeleton, skeletonStructure):
        ix = bone.nodeID
        if hasattr(bone,"name"):
            name = bone.name
        else:
            name = "Bone.%03d" % ix
        if name in skeleton:
            return
        o = bpy.data.objects.new(name, None)
        skeleton[ix] = o
        bpy.context.collection.objects.link(o)
        if bone.parentID not in skeleton:
            AHIImporter.importBone(
                skeletonStructure[bone.parentID], skeleton, skeletonStructure)
        o["id"] = bone.nodeID
        if hasattr(bone,"chainID"): o["chain id"] = bone.chainID
        o.parent = skeleton[bone.parentID]
        o.matrix_local = AHIImporter.deserializePoseVector(bone.pos, bone.scale, bone.rot)
        o.show_wire = True
        o.show_in_front = True
        o.show_bounds = True
