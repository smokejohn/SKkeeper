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

def duplicate_object(obj, times=1, offset=3):
    """ duplicates the given object and its data """
    # TODO: implement this without using bpy.ops
    # would be faster and wouldn't clutter up the scene
    objects = []
    for i in range(0, times):
        bpy.ops.object.duplicate()
        copy = bpy.context.active_object
        copy.name = obj.name + "_shapekey_" + str(i+1)
        copy.location.x += offset
        objects.append(copy)

    return objects

def apply_shapekey(obj, sk_keep):
    """ deletes all shapekeys except the one with the given index """
    shapekeys = obj.data.shape_keys.key_blocks

    # check for valid index
    if sk_keep < 0 or sk_keep > len(shapekeys):
        return

    # remove all other shapekeys
    for i in reversed(range(0, len(shapekeys))):
        if i != sk_keep:
            obj.shape_key_remove(shapekeys[i])

    # remove the chosen one and bake it into the object
    obj.shape_key_remove(shapekeys[0])

def apply_modifiers(obj):
    """ applies all modifiers in order """
    # now uses object.convert to circumevent errors with disabled modifiers

    # modifiers = obj.modifiers

    for o in bpy.context.scene.objects:
        o.select_set(False)

    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    bpy.ops.object.convert(target='MESH')

    # for mod in modifiers:
    #     bpy.ops.object.modifier_apply(apply_as='DATA', modifier=mod.name)

def apply_subdmod(obj):
    """ applies subdivision surface modifier """

    # get subsurface modifier/s
    modifiers = [mod for mod in obj.modifiers if mod.type == 'SUBSURF']

    for o in bpy.context.scene.objects:
        o.select_set(False)
    bpy.context.view_layer.objects.active = obj

    bpy.ops.object.modifier_apply(apply_as='DATA', modifier=modifiers[0].name)

def add_objs_shapekeys(destination, sources):
    """ takes an array of objects and adds them as shapekeys to the destination object """
    for o in bpy.context.scene.objects:
        o.select_set(False)

    for src in sources:
        src.select_set(True)

    bpy.context.view_layer.objects.active = destination
    bpy.ops.object.join_shapes()

class EF_OT_apply_mods_SK(Operator):
    """ Applies modifiers and keeps shapekeys """
    bl_idname = "utils.apply_mods_sk"
    bl_label = "Apply Modifiers (Keep Shapekeys)"
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

        # get the shapekey names
        sk_names = []
        for block in obj.data.shape_keys.key_blocks:
            sk_names.append(block.name)

        # duplicate object for each shapekey
        num_shapes = len(obj.data.shape_keys.key_blocks) - 1
        blendshapes = duplicate_object(obj, times=num_shapes)
        blendshapes.insert(0, obj)

        # clear/apply shapekeys
        for i in range(0, len(blendshapes)):
            apply_shapekey(blendshapes[i], i)

        # apply modifiers
        for shape in blendshapes:
            apply_modifiers(shape)

        # add meshes as shapekeys for the base - function
        add_objs_shapekeys(obj, blendshapes)

        # restore the names
        for i, name in enumerate(sk_names):
            obj.data.shape_keys.key_blocks[i].name = name

        # delete the duplicates
        for i in range(1, len(blendshapes)):
            bpy.data.objects.remove(blendshapes[i])

        return {'FINISHED'}

class EF_OT_apply_subd_SK(Operator):
    """ Applies subdivision surface and keeps shapekeys """
    bl_idname = "utils.apply_subd_sk"
    bl_label = "Apply Subdivision (Keep Shapekeys)"
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

        # check for subd modifiers
        subd = [mod for mod in obj.modifiers if mod.type == 'SUBSURF']
        if len(subd) == 0:
            self.report({'ERROR'}, "The selected object doesn't have any subdivision surface modifiers")
            return {'CANCELLED'}

        # VALID OBJECT

        # get the shapekey names
        sk_names = []
        for block in obj.data.shape_keys.key_blocks:
            sk_names.append(block.name)

        # duplicate object for each shapekey
        num_shapes = len(obj.data.shape_keys.key_blocks) - 1
        blendshapes = duplicate_object(obj, times=num_shapes)
        blendshapes.insert(0, obj)

        # clear/apply shapekeys
        for i in range(0, len(blendshapes)):
            apply_shapekey(blendshapes[i], i)

        # apply modifiers
        for shape in blendshapes:
            apply_subdmod(shape)
            # apply_modifiers(shape)

        # add meshes as shapekeys for the base - function
        add_objs_shapekeys(obj, blendshapes)

        # restore the names
        for i, name in enumerate(sk_names):
            obj.data.shape_keys.key_blocks[i].name = name

        # delete the duplicates
        for i in range(1, len(blendshapes)):
            bpy.data.objects.remove(blendshapes[i])

        return {'FINISHED'}

def register():
    bpy.utils.register_class(EF_OT_apply_mods_SK)
    bpy.utils.register_class(EF_OT_apply_subd_SK)

def unregister():
    bpy.utils.unregister_class(EF_OT_apply_mods_SK)
    bpy.utils.unregister_class(EF_OT_apply_subd_SK)
