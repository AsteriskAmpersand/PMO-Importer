# -*- coding: utf-8 -*-
"""
Created on Mon Dec 30 01:10:11 2019

@author: AsteriskAmpersand
"""
import bpy
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty
from bpy.types import Operator
from ..struct import ahi_importer_layer
from ..operators import ahi_converter

class ImportFUAHI(Operator, ImportHelper):
    bl_idname = "custom_import.import_mhfu_ahi"
    bl_label = "Load MHF AHI file (.ahi)"
    bl_options = {'REGISTER', 'PRESET', 'UNDO'}
 
    # ImportHelper mixin class uses this
    filename_ext = ".fskl"
    filter_glob : StringProperty(default="*.ahi", options={'HIDDEN'}, maxlen=255)
    import_armature : BoolProperty(name = "Import as Armature", default = False)
    
    def execute(self,context):
        try:
            bpy.ops.object.mode_set(mode='OBJECT')
        except:
            pass
        bpy.ops.object.select_all(action='DESELECT')
        importer = ahi_importer_layer.AHIImporter()
        root = importer.execute(self.properties.filepath)
        if self.import_armature:
            ahi_converter.createArmature(root)
        return {'FINISHED'}
    
    
def menu_func_import(self, context):
    self.layout.operator(ImportFUAHI.bl_idname, text="MHFU AHI (.ahi)")