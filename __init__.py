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
        "description": "Applies modifiers and keeps shapekeys",
        "author": "Johannes Rauch",
        "version": (1, 8, 0),
        "blender": (2, 80, 3),
        "location": "View3D > Object",
        "doc_url": "https://github.com/smokejohn/SKkeeper",
        "tracker_url": "https://github.com/smokejohn/SKkeeper/issues",
        "category": "Object",
        }

import time

from enum import Enum

import bpy
from bpy.types import Operator, PropertyGroup
from bpy.props import BoolProperty, CollectionProperty

class Mode(Enum):
    ALL = 0
    SUBD = 1
    SELECTED = 2

#####################
# UTILITY FUNCTIONS #
#####################

def log(msg):
    """ prints to console in the following format:
        <SKkeeper Time(HH:MM)> message
    """
    t = time.localtime()
    current_time = time.strftime("%H:%M", t)
    print("<SKkeeper {}> {}".format(current_time, (msg)))

def copy_object(obj, times=1, offset=0):
    """ copies the given object and links it to the main collection"""

    objects = []
    for i in range(0,times):
        copy_obj = obj.copy()
        copy_obj.data = obj.data.copy()
        copy_obj.name = obj.name + "_shapekey_" + str(i+1)
        copy_obj.location.x += offset*(i+1)

        bpy.context.collection.objects.link(copy_obj)
        objects.append(copy_obj)

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

def apply_selected_modifiers(obj, resource_list):
    """ applies only the user selected modifiers to the object"""

    for entry in resource_list:
        if entry.selected:
            log("Applying modifier {} on object {}".format(entry.name, obj.name))
            apply_modifier(obj, entry.name)

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


def common_validation(self):
    """Checks for common user errors for all operators and informs user of mistake"""

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

def keep_shapekeys(self, mode=Mode.ALL):
    """
    Function which is used by the blender operators to collapse modifier
    stack and keep shapekeys. The given mode parameter will determine which
    execution style will be used. The available modes match those of the
    available blender operators (SUBD, SELECTED, ALL) which collapse only
    subdivision surface, the selected or all modifiers respectively.
    """

    shapekey_names = [block.name for block in self.obj.data.shape_keys.key_blocks]

    # create receiving object that will contain all collapsed shapekeys
    receiver = copy_object(self.obj, times=1, offset=0)[0]
    receiver.name = "shapekey_receiver"
    apply_shapekey(receiver, 0)
    if mode == Mode.ALL:
        apply_modifiers(receiver)
    elif mode == Mode.SUBD:
        apply_subdmod(receiver)
    elif mode == Mode.SELECTED:
        apply_selected_modifiers(receiver, self.resource_list)

    num_shapekeys = len(self.obj.data.shape_keys.key_blocks)

    shapekeys_to_process = len(shapekey_names) - 1
    log("Processing {} shapekeys on {} in mode {}".format(shapekeys_to_process, self.obj.name, mode))

    # create a copy for each shapekey and transfer it to the receiver one after the other
    # start the loop at 1 so we skip the base shapekey
    for shapekey_index in range(1, num_shapekeys):
        log("Processing shapekey {} with name {}".format(shapekey_index, shapekey_names[shapekey_index]))

        # copy of baseobject / shapekey donor
        shapekey_obj = copy_object(self.obj, times=1, offset=0)[0]
        apply_shapekey(shapekey_obj, shapekey_index)
        if mode == Mode.ALL:
            apply_modifiers(shapekey_obj)
        elif mode == Mode.SUBD:
            apply_subdmod(shapekey_obj)
        elif mode == Mode.SELECTED:
            apply_selected_modifiers(shapekey_obj, self.resource_list)

        # add the copy as a shapekey to the receiver
        add_objs_shapekeys(receiver, [shapekey_obj])


        # check if the shapekey could be added
        # due to problematic modifier stack
        help_url = "https://github.com/smokejohn/SKkeeper/blob/master/readme.md#troubleshooting-problems"
        if receiver.data.shape_keys is None:
            error_msg = ("IMPOSSIBLE TO TRANSFER SHAPEKEY BECAUSE OF VERTEX COUNT MISMATCH\n\n"
                         "The processed shapekey {} with name {} cannot be transferred.\n"
                         "The shapekey doesn't have the same vertex count as the base after applying modifiers.\n"
                         "This is most likely due to a problematic modifier in your modifier stack (Decimate, Weld)\n\n"
                         "For help on how to fix problems visit: {}).\n\n"
                         "Press UNDO to return to your previous working state."
                        )
            self.report({'ERROR'}, error_msg.format(shapekey_index, shapekey_names[shapekey_index], help_url))
            return {'CANCELLED'}

        # due to problematic shape key
        num_transferred_keys = len(receiver.data.shape_keys.key_blocks) - 1
        if num_transferred_keys != shapekey_index:
            error_msg = ("IMPOSSIBLE TO TRANSFER SHAPEKEY BECAUSE OF VERTEX COUNT MISMATCH\n\n"
                         "The processed shapekey {} with name {} cannot be transferred.\n"
                         "The shapekey doesn't have the same vertex count as the base after applying modifiers.\n"
                         "For help on how to fix problems visit: {}).\n\n"
                         "Press UNDO to return to your previous working state."
                        )
            self.report({'ERROR'}, error_msg.format(shapekey_index, shapekey_names[shapekey_index], help_url))
            return {'CANCELLED'}

        # restore the shapekey name
        receiver.data.shape_keys.key_blocks[shapekey_index].name = shapekey_names[shapekey_index]

        # delete the shapekey donor and its mesh datablock (save memory)
        mesh_data = shapekey_obj.data
        bpy.data.objects.remove(shapekey_obj)
        bpy.data.meshes.remove(mesh_data)

    orig_name = self.obj.name
    orig_data = self.obj.data

    # transfer over drivers on shapekeys if they exist
    if orig_data.shape_keys.animation_data is not None:
        receiver.data.shape_keys.animation_data_create()
        for orig_driver in orig_data.shape_keys.animation_data.drivers:
            receiver.data.shape_keys.animation_data.drivers.from_existing(src_driver=orig_driver)

        # if the driver has variable targets that refer to the original object we need to
        # retarget them to the new receiver because we delete the original object later
        for fcurve in receiver.data.shape_keys.animation_data.drivers:
            for variable in fcurve.driver.variables:
                for target in variable.targets:
                    if target.id == self.obj:
                        target.id = receiver


    # delete the original and its mesh data
    bpy.data.objects.remove(self.obj)
    bpy.data.meshes.remove(orig_data)

    # rename the receiver
    receiver.name = orig_name

    return {'FINISHED'}


#####################
# BLENDER OPERATORS #
#####################

class SK_TYPE_Resource(PropertyGroup):
    selected: BoolProperty(name="Selected", default=False)

class SK_OT_apply_mods_SK(Operator):
    """ Applies modifiers and keeps shapekeys """

    bl_idname = "sk.apply_mods_sk"
    bl_label = "Apply All Modifiers (Keep Shapekeys)"
    bl_options = {'REGISTER', 'UNDO'}

    def validate_input(self, obj):
        if common_validation(self) == {'CANCELLED'}:
            return {'CANCELLED'}

        # check for modifiers
        if len(self.obj.modifiers) == 0:
            self.report({'ERROR'}, "The selected object doesn't have any modifiers")
            return {'CANCELLED'}

    def execute(self, context):
        self.obj = context.active_object

        # Exit out if the selected object is not valid
        if self.validate_input(self.obj) == {'CANCELLED'}:
            return {'CANCELLED'}

        return keep_shapekeys(self, mode=Mode.ALL)


class SK_OT_apply_subd_SK(Operator):
    """ Applies modifiers and keeps shapekeys """

    bl_idname = "sk.apply_subd_sk"
    bl_label = "Apply All Subdivision (Keep Shapekeys)"
    bl_options = {'REGISTER', 'UNDO'}

    def validate_input(self, obj):
        if common_validation(self) == {'CANCELLED'}:
            return {'CANCELLED'}

        # check for subd modifiers
        subd = [mod for mod in self.obj.modifiers if mod.type == 'SUBSURF']
        if len(subd) == 0:
            self.report({'ERROR'}, "The selected object doesn't have any subdivision surface modifiers")
            return {'CANCELLED'}

    def execute(self, context):
        self.obj = context.active_object

        # Exit out if the selected object is not valid
        if self.validate_input(self.obj) == {'CANCELLED'}:
            return {'CANCELLED'}

        return keep_shapekeys(self, mode=Mode.SUBD)

class SK_OT_apply_mods_choice_SK(Operator):
    """ Applies modifiers and keeps shapekeys """

    bl_idname = "sk.apply_mods_choice_sk"
    bl_label = "Apply Chosen Modifiers (Keep Shapekeys)"
    bl_options = {'REGISTER', 'UNDO'}

    resource_list : CollectionProperty(name="Modifier List", type=SK_TYPE_Resource)

    def invoke(self, context, event):
        self.obj = context.active_object

        if common_validation(self) == {'CANCELLED'}:
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
        return keep_shapekeys(self, mode=Mode.SELECTED)

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

    log("Registered SKKeeper addon")
    bpy.types.VIEW3D_MT_object.append(modifier_panel)

def unregister():
    from bpy.utils import unregister_class
    for cls in classes:
        unregister_class(cls)

    log("Unregistered SKKeeper addon")
    bpy.types.VIEW3D_MT_object.remove(modifier_panel)
