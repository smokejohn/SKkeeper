# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

bl_info = {
        "name": "Apply subdivision and keep shapekeys",
        "author": "Johannes Rauch",
        "version": (1, 0),
        "blender": (2, 80, 3),
        "location": "Search > Apply Subd and keep Shapekeys",
        "description": "Applies Subdivision Surface modifier and keeps shapekeys",
        "category": "Utility",
        }

import bpy
from bpy.types import Operator

class SDASK_OT_apply_SD_SK(Operator):
    """ Applies subdivision surface modifier and keeps shapekeys """
    bl_idname = "utils.apply_subd_sk"
    bl_label = "Apply Subd (Keep Shapekeys)"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        print("testing {}".format(self.bl_label))
        # get obj
        # test for mesh
        # test for shapekeys
        # test for subdmod

        # duplicate for each shapekey

        # remove all shapekeys - do a function for this

        # add meshes as shapekeys for the base

        return {'FINISHED'}

def register():
    bpy.utils.register_class(SDASK_OT_apply_SD_SK)

def unregister():
    bpy.utils.unregister_class(SDASK_OT_apply_SD_SK)
