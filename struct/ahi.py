# -*- coding: utf-8 -*-
"""
Created on Sun Dec 29 21:50:00 2019

@author: AsteriskAmpersand
"""
try:
    from ..struct.fblock import FBlock
    from ..struct.p3rdFblock import P3Block
    from ..common.FileLike import FileLike
except:
    import sys
    sys.path.insert(0, r'..\common')
    sys.path.insert(0, r'..\fmod')
    from fblock import FBlock
    from p3rdFblock import P3Block
    from FileLike import FileLike   

class FBone():
    def __init__(self,fbone):
        for field in fbone.Data[0].fields:
            setattr(self,field,getattr(fbone.Data[0],field))

class Skeleton():
    def __init__(self, FilePath):
        with open(FilePath, "rb") as modelFile:
            frontierFile = self.blocktype()
            frontierFile.marshall(FileLike(modelFile.read()))
        Bones = frontierFile.Data[1:]
        self.Skeleton = {}
        for fileBone in Bones:
            fbone = FBone(fileBone)
            self.Skeleton[fbone.nodeID]=fbone
    
    def skeletonStructure(self):
        return self.Skeleton
    
class FUSkeleton(Skeleton):
    blocktype = FBlock
    
class P3Skeleton(Skeleton):
    blocktype = P3Block
    
if "__main__" in __name__:
    fu = FUSkeleton(r'C:/Users/Asterisk/Downloads/rathfu - Copy.ahi')
    p3 = P3Skeleton(r'C:/Users/Asterisk/Downloads/p3rd_rath_skel - Copy.ahi')