# -*- coding: utf-8 -*-
"""
Created on Mon Dec 30 01:17:01 2019

@author: AsteriskAmpersand
"""

from ..struct.ahi import FUSkeleton
import bpy
import bmesh
import array
import os
from mathutils import Vector, Matrix
from pathlib import Path


class AHIImporter():
    @staticmethod
    def execute(fmodPath):
        skeleton = FUSkeleton(fmodPath).skeletonStructure()
        currentSkeleton = {}
        o = bpy.data.objects.new("Armature", None)
        bpy.context.scene.collection.objects.link(o)
        # bpy.context.scene.update()
        currentSkeleton = {"Armature": o}
        for bone in skeleton.values():
            AHIImporter.importBone(bone, currentSkeleton, skeleton)
        return o
    
    @staticmethod
    def deserializePoseVector(vec4):
        m = Matrix.Identity(4)
        for i in range(4):
            m[i][3] = vec4[i]
        return m

    @staticmethod
    def importBone(bone, skeleton, skeletonStructure):
        ix = bone.nodeID
        if "Bone.%03d" % ix in skeleton:
            return
        o = bpy.data.objects.new("Bone.%03d" % ix, None)
        skeleton["Bone.%03d" % ix] = o
        bpy.context.scene.collection.objects.link(o)
        parentName = "Armature" if bone.parentID == -1 else "Bone.%03d" % bone.parentID
        if parentName not in skeleton:
            AHIImporter.importBone(
                skeletonStructure[bone.parentID], skeleton, skeletonStructure)
        o["id"] = bone.nodeID
        o.parent = skeleton[parentName]
        o.matrix_local = AHIImporter.deserializePoseVector(bone.posVec)
        o.show_wire = True
        o.show_in_front = True
        o.show_bounds = True
