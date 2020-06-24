##
##  GPL License
##
##  Blender Addon | Apply modifiers and keep shapekeys
##  Copyright (C) 2020  Johannes Rauch
##
##  This program is free software: you can redistribute it and/or modify
##  it under the terms of the GNU General Public License as published by
##  the Free Software Foundation, either version 3 of the License, or
##  (at your option) any later version.
##
##  This program is distributed in the hope that it will be useful,
##  but WITHOUT ANY WARRANTY; without even the implied warranty of
##  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##  GNU General Public License for more details.
##
##  You should have received a copy of the GNU General Public License
##  along with this program.  If not, see <https://www.gnu.org/licenses/>.


bl_info = {
        "name": "Apply modifiers and keep shapekeys",
        "author": "Johannes Rauch",
        "version": (1, 0),
        "blender": (2, 80, 3),
        "location": "Search > Apply modifiers (Keep Shapekeys)",
        "description": "Applies modifiers and keeps shapekeys",
        "category": "Utility",
        }

import bpy
from bpy.types import Operator

def duplicate_object(obj):
    """ duplicates the given object and its data """
    pass

def strip_shapekeys(sk_keep):
    """ deletes all shapekeys except the one with the given index """
    pass

def apply_modifiers(obj):
    """ applies all modifiers in order """
    pass

def add_objs_shapekeys(destination, sources):
    """ takes an array of objects and adds them as shapekeys to the destination object """
    pass

class EF_OT_apply_mods_SK(Operator):
    """ Applies modifiers and keeps shapekeys """
    bl_idname = "utils.apply_mods_sk"
    bl_label = "Apply modifiers (Keep Shapekeys)"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        print("testing {}".format(self.bl_label))

        obj = context.active_object

        # GUARD CLAUSES | USER ERROR

        # check for valid selection
        if not obj:
            self.report({'ERROR'}, "No Active object. Please select an object")
            return {'CANCELLED'}

        # check for valid obj-type
        if obj.type != 'MESH':
            self.report({'ERROR'}, "Wrong object type. Please select a MESH object")
            return {'CANCELLED'}

        # check for shapekeys
        if not obj.data.shape_keys:
            self.report({'ERROR'}, "The selected object doesn't have any shapekeys")
            return {'CANCELLED'}

        # check for modifiers
        if len(obj.modifiers) == 0:
            self.report({'ERROR'}, "The selected object doesn't have any modifiers")
            return {'CANCELLED'}

        # VALID OBJECT

        # duplicate object for each shapekey
        for key in obj.data.shape_keys.key_blocks:
            print(key.name)

        # remove all shapekeys - function

        # apply modifiers - function

        # add meshes as shapekeys for the base - function

        return {'FINISHED'}

def register():
    bpy.utils.register_class(EF_OT_apply_mods_SK)

def unregister():
    bpy.utils.unregister_class(EF_OT_apply_mods_SK)
