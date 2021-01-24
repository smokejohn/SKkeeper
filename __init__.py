##
##  GPL License
##
##  Blender Addon | SKkeeper
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
        "name": "SKkeeper",
        "author": "Johannes Rauch",
        "version": (1, 6),
        "blender": (2, 80, 3),
        "location": "Search > Apply modifiers (Keep Shapekeys)",
        "description": "Applies modifiers and keeps shapekeys",
        "category": "Utility",
        "wiki_url": "https://github.com/smokejohn/SKkeeper",
        }

import time

import bpy
from bpy.types import Operator, PropertyGroup
from bpy.props import BoolProperty, CollectionProperty

def log(msg):
    """ prints to console in the following format:
        <SKkeeper Time(HH:MM)> message
    """
    t = time.localtime()
    current_time = time.strftime("%H:%M", t)
    print("<SKkeeper {}> {}".format(current_time, (msg)))

def copy_object(obj, times=1, offset=0):
    # TODO: maybe get the collection of the source and link the object to
    # that collection instead of the scene main collection

    objects = []
    for i in range(0,times):
        copy_obj = obj.copy()
        copy_obj.data = obj.data.copy()
        copy_obj.name = obj.name + "_shapekey_" + str(i+1)
        copy_obj.location.x += offset*(i+1)

        bpy.context.collection.objects.link(copy_obj)
        objects.append(copy_obj)

    return objects

def duplicate_object(obj, times=1, offset=0):
    """ duplicates the given object and its data """

    # DEPRECATED >> USE copy_object instead

    for o in bpy.context.scene.objects:
        o.select_set(False)

    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

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
    # now uses object.convert to circumvent errors with disabled modifiers

    modifiers = obj.modifiers
    for modifier in modifiers:
        if modifier.type == 'SUBSURF':
            modifier.show_only_control_edges = False

    for o in bpy.context.scene.objects:
        o.select_set(False)

    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    bpy.ops.object.convert(target='MESH')

    # for mod in modifiers:
    #     bpy.ops.object.modifier_apply(apply_as='DATA', modifier=mod.name)

def remove_modifiers(obj):
    """ removes all modifiers from the object """

    for i in reversed(range(0, len(obj.modifiers))):
        modifier = obj.modifiers[i]
        obj.modifiers.remove(modifier)

def apply_subdmod(obj):
    """ applies subdivision surface modifier """

    # get subsurface modifier/s
    modifiers = [mod for mod in obj.modifiers if mod.type == 'SUBSURF']

    for o in bpy.context.scene.objects:
        o.select_set(False)
    bpy.context.view_layer.objects.active = obj

    modifiers[0].show_only_control_edges = False
    bpy.ops.object.modifier_apply(modifier=modifiers[0].name)

def apply_modifier(obj, modifier_name):
    """ applies a specific modifier """

    log("Applying chosen modifier")
    log(obj)

    modifier = [mod for mod in obj.modifiers if mod.name == modifier_name][0]
    
    # deselect all
    for o in bpy.context.scene.objects:
        o.select_set(False)

    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=modifier.name)

def add_objs_shapekeys(destination, sources):
    """ takes an array of objects and adds them as shapekeys to the destination object """
    for o in bpy.context.scene.objects:
        o.select_set(False)

    for src in sources:
        src.select_set(True)

    bpy.context.view_layer.objects.active = destination
    bpy.ops.object.join_shapes()

class SK_TYPE_Resource(PropertyGroup):
    selected: BoolProperty(name="Selected", default=False)

class SK_OT_apply_mods_SK(Operator):
    """ Applies modifiers and keeps shapekeys """
    bl_idname = "sk.apply_mods_sk"
    bl_label = "Apply All Modifiers (Keep Shapekeys)"
    bl_options = {'REGISTER', 'UNDO'}

    def validate_input(self, obj):
        # GUARD CLAUSES | USER ERROR

        # check for valid selection
        if not self.obj:
            self.report({'ERROR'}, "No Active object. Please select an object")
            return {'CANCELLED'}

        # check for valid obj-type
        if self.obj.type != 'MESH':
            self.report({'ERROR'}, "Wrong object type. Please select a MESH object")
            return {'CANCELLED'}

        # check for shapekeys
        if not self.obj.data.shape_keys:
            self.report({'ERROR'}, "The selected object doesn't have any shapekeys")
            return {'CANCELLED'}

        # check for multiple shapekeys
        if len(self.obj.data.shape_keys.key_blocks) == 1:
            self.report({'ERROR'}, "The selected object only has a base shapekey")
            return {'CANCELLED'}

        # check for modifiers
        if len(self.obj.modifiers) == 0:
            self.report({'ERROR'}, "The selected object doesn't have any modifiers")
            return {'CANCELLED'}

    def execute(self, context):
        self.obj = context.active_object

        # check for valid object
        if self.validate_input(self.obj) == {'CANCELLED'}:
            return {'CANCELLED'}

        # VALID OBJECT

        # get the shapekey names
        sk_names = []
        for block in self.obj.data.shape_keys.key_blocks:
            sk_names.append(block.name)

        # create receiving object that will contain all collapsed shapekeys
        receiver = copy_object(self.obj, times=1, offset=0)[0]
        receiver.name = "sk_receiver"
        apply_shapekey(receiver, 0)
        apply_modifiers(receiver)

        num_shapes = len(self.obj.data.shape_keys.key_blocks)

        # create a copy for each blendshape and transfer it to the receiver one after the other
        # start the loop at 1 so we skip the base shapekey
        for i in range(1, num_shapes):
            # copy of baseobject / blendshape donor
            blendshape = copy_object(self.obj, times=1, offset=0)[0]
            apply_shapekey(blendshape, i)
            apply_modifiers(blendshape)

            # add the copy as a blendshape to the receiver
            add_objs_shapekeys(receiver, [blendshape])

            # restore the shapekey name
            receiver.data.shape_keys.key_blocks[i].name = sk_names[i]

            # delete the blendshape donor and its mesh datablock (save memory)
            mesh_data = blendshape.data
            bpy.data.objects.remove(blendshape)
            bpy.data.meshes.remove(mesh_data)


        # delete the original and its mesh data
        orig_name = self.obj.name
        orig_data = self.obj.data
        bpy.data.objects.remove(self.obj)
        bpy.data.meshes.remove(orig_data)

        # rename the receiver
        receiver.name = orig_name

        return {'FINISHED'}

class SK_OT_apply_subd_SK(Operator):
    """ Applies modifiers and keeps shapekeys """
    bl_idname = "sk.apply_subd_sk"
    bl_label = "Apply All Subdivision (Keep Shapekeys)"
    bl_options = {'REGISTER', 'UNDO'}

    def validate_input(self, obj):
        # GUARD CLAUSES | USER ERROR

        # check for valid selection
        if not self.obj:
            self.report({'ERROR'}, "No Active object. Please select an object")
            return {'CANCELLED'}

        # check for valid obj-type
        if self.obj.type != 'MESH':
            self.report({'ERROR'}, "Wrong object type. Please select a MESH object")
            return {'CANCELLED'}

        # check for shapekeys
        if not self.obj.data.shape_keys:
            self.report({'ERROR'}, "The selected object doesn't have any shapekeys")
            return {'CANCELLED'}

        # check for multiple shapekeys
        if len(self.obj.data.shape_keys.key_blocks) == 1:
            self.report({'ERROR'}, "The selected object only has a base shapekey")
            return {'CANCELLED'}

        # check for subd modifiers
        subd = [mod for mod in self.obj.modifiers if mod.type == 'SUBSURF']
        if len(subd) == 0:
            self.report({'ERROR'}, "The selected object doesn't have any subdivision surface modifiers")
            return {'CANCELLED'}

    def execute(self, context):
        self.obj = context.active_object

        # check for valid object
        if self.validate_input(self.obj) == {'CANCELLED'}:
            return {'CANCELLED'}

        # VALID OBJECT

        # get the shapekey names
        sk_names = []
        for block in self.obj.data.shape_keys.key_blocks:
            sk_names.append(block.name)

        # create receiving object that will contain all collapsed shapekeys
        receiver = copy_object(self.obj, times=1, offset=0)[0]
        receiver.name = "sk_receiver"
        apply_shapekey(receiver, 0)
        apply_subdmod(receiver)

        num_shapes = len(self.obj.data.shape_keys.key_blocks)

        # create a copy for each blendshape and transfer it to the receiver one after the other
        # start the loop at 1 so we skip the base shapekey
        for i in range(1, num_shapes):
            # copy of baseobject / blendshape donor
            blendshape = copy_object(self.obj, times=1, offset=0)[0]
            apply_shapekey(blendshape, i)
            apply_subdmod(blendshape)

            # add the copy as a blendshape to the receiver
            add_objs_shapekeys(receiver, [blendshape])

            # restore the shapekey name
            receiver.data.shape_keys.key_blocks[i].name = sk_names[i]

            # delete the blendshape donor and its mesh datablock (save memory)
            mesh_data = blendshape.data
            bpy.data.objects.remove(blendshape)
            bpy.data.meshes.remove(mesh_data)


        # delete the original and its mesh data
        orig_name = self.obj.name
        orig_data = self.obj.data
        bpy.data.objects.remove(self.obj)
        bpy.data.meshes.remove(orig_data)

        # rename the receiver
        receiver.name = orig_name

        return {'FINISHED'}

class SK_OT_apply_mods_choice_SK(Operator):
    """ Applies modifiers and keeps shapekeys """
    bl_idname = "sk.apply_mods_choice_sk"
    bl_label = "Apply Chosen Modifiers (Keep Shapekeys)"
    bl_options = {'REGISTER', 'UNDO'}

    resource_list : CollectionProperty(name="Modifier List", type=SK_TYPE_Resource)

    def invoke(self, context, event):
        self.obj = context.active_object

        # GUARD CLAUSES | USER ERROR

        # check for valid selection
        if not self.obj:
            self.report({'ERROR'}, "No Active object. Please select an object")
            return {'CANCELLED'}

        # check for valid obj-type
        if self.obj.type != 'MESH':
            self.report({'ERROR'}, "Wrong object type. Please select a MESH object")
            return {'CANCELLED'}

        # check for shapekeys
        if not self.obj.data.shape_keys:
            self.report({'ERROR'}, "The selected object doesn't have any shapekeys")
            return {'CANCELLED'}

        # check for multiple shapekeys
        if len(self.obj.data.shape_keys.key_blocks) == 1:
            self.report({'ERROR'}, "The selected object only has a base shapekey")
            return {'CANCELLED'}

        # check for modifiers
        if len(self.obj.modifiers) == 0:
            self.report({'ERROR'}, "The selected object doesn't have any modifiers")
            return {'CANCELLED'}

        # populate the resource_list
        self.resource_list.clear()
        for mod in self.obj.modifiers:
            entry = self.resource_list.add()
            entry.name = mod.name

        # display floating gui
        return context.window_manager.invoke_props_dialog(self, width=350)

    def execute(self, context):

        # VALID OBJECT

        # get the shapekey names
        sk_names = []
        for block in self.obj.data.shape_keys.key_blocks:
            sk_names.append(block.name)

        # create receiving object that will contain all collapsed shapekeys
        receiver = copy_object(self.obj, times=1, offset=0)[0]
        receiver.name = "sk_receiver"
        # bake in the shapekey
        apply_shapekey(receiver, 0)
        # apply the selected modifiers
        for entry in self.resource_list:
            if entry.selected:
                apply_modifier(receiver, entry.name)
        # change its name

        # get the number of shapekeys on the original mesh
        num_shapes = len(self.obj.data.shape_keys.key_blocks)

        # create a copy for each blendshape and transfer it to the receiver one after the other
        # start the loop at 1 so we skip the base shapekey
        for i in range(1, num_shapes):
            # copy of baseobject / blendshape donor
            blendshape = copy_object(self.obj, times=1, offset=0)[0]
            # bake shapekey
            apply_shapekey(blendshape, i)
            # # apply the selected modifiers
            for entry in self.resource_list:
                if entry.selected:
                    log(entry.name)
                    apply_modifier(blendshape, entry.name)

            # remove all the other modifiers
            # they are not needed the receiver object has them
            remove_modifiers(blendshape)

            # add the copy as a blendshape to the receiver
            add_objs_shapekeys(receiver, [blendshape])

            # restore the shapekey name
            receiver.data.shape_keys.key_blocks[i].name = sk_names[i]

            # delete the blendshape donor and its mesh datablock (save memory)
            mesh_data = blendshape.data
            bpy.data.objects.remove(blendshape)
            bpy.data.meshes.remove(mesh_data)

        # delete the original and its mesh data
        orig_name = self.obj.name
        orig_data = self.obj.data
        bpy.data.objects.remove(self.obj)
        bpy.data.meshes.remove(orig_data)

        # rename the receiver
        receiver.name = orig_name

        return {'FINISHED'}

    def draw(self, context):
        """ Draws the resource selection GUI """
        layout = self.layout
        col = layout.column(align=True)
        for entry in self.resource_list:
            row = col.row()
            row.prop(entry, 'selected', text=entry.name)

classes = (
        SK_TYPE_Resource,
        SK_OT_apply_mods_SK,
        SK_OT_apply_subd_SK,
        SK_OT_apply_mods_choice_SK
        )

def modifier_panel(self, context):
    layout = self.layout
    layout.separator()
    layout.operator("sk.apply_mods_sk")
    layout.operator("sk.apply_subd_sk")
    layout.operator("sk.apply_mods_choice_sk")

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

    bpy.types.VIEW3D_MT_object.append(modifier_panel)

def unregister():
    from bpy.utils import unregister_class
    for cls in classes:
        unregister_class(cls)

    bpy.types.VIEW3D_MT_object.remove(modifier_panel)
