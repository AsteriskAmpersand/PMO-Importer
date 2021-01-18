# -*- coding: utf-8 -*-
"""
Created on Wed Mar  6 13:38:47 2019

@author: AsteriskAmpersand
"""
#from .dbg import dbg_init
#dbg_init()

content=bytes("","UTF-8")
bl_info = {
    "name": "MH PMO Model Importer",
    "category": "Import-Export",
    "author": "AsteriskAmpersand (Code) & Seth VanHeulen (Vertex and Face Buffer Structure)",
    "location": "File > Import-Export > PMO/MH",
    "version": (1,0,0)
}
 
import bpy

from .operators.importer import menu_func_import as pmo_model_menu_func_import
from .operators.importer import ImportPMO

def register():
    bpy.utils.register_class(ImportPMO)
    bpy.types.INFO_MT_file_import.append(pmo_model_menu_func_import)

def unregister():
    bpy.utils.unregister_class(ImportPMO)
    bpy.types.INFO_MT_file_import.remove(pmo_model_menu_func_import)
    
    del bpy.types.Object.MHW_Symmetric_Pair

if __name__ == "__main__":
    try:
        unregister()
    except:
        pass
    register()
