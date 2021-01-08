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
        "version": (1, 4),
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
    t = time.localtime()
    current_time = time.strftime("%H:%M", t)
    print("<SKkeeper {}> {}".format(current_time, (msg)))

def duplicate_object(obj, times=1, offset=0):
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
    # now uses object.convert to circumvent errors with disabled modifiers

    # modifiers = obj.modifiers

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

    bpy.ops.object.modifier_apply(modifier=modifiers[0].name)

def apply_modifier(obj, modifier_name):
    """ applies a specific modifier """

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

    def execute(self, context):

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

        # VALID OBJECT

        # get the shapekey names
        sk_names = []
        for block in self.obj.data.shape_keys.key_blocks:
            sk_names.append(block.name)

        # duplicate object for each shapekey
        num_shapes = len(self.obj.data.shape_keys.key_blocks) - 1
        blendshapes = duplicate_object(self.obj, times=num_shapes)
        blendshapes.insert(0, self.obj)

        # clear/apply shapekeys
        for i in range(0, len(blendshapes)):
            apply_shapekey(blendshapes[i], i)

        # apply modifiers
        for shape in blendshapes:
            apply_modifiers(shape)

        # add meshes as shapekeys for the base - function
        add_objs_shapekeys(self.obj, blendshapes)

        # restore the names
        for i, name in enumerate(sk_names):
            self.obj.data.shape_keys.key_blocks[i].name = name

        # delete the duplicates
        for i in range(1, len(blendshapes)):
            bpy.data.objects.remove(blendshapes[i])

        return {'FINISHED'}

class SK_OT_apply_subd_SK(Operator):
    """ Applies subdivision surface and keeps shapekeys """
    bl_idname = "sk.apply_subd_sk"
    bl_label = "Apply Subdivision (Keep Shapekeys)"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

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

        # check for subd modifiers
        subd = [mod for mod in self.obj.modifiers if mod.type == 'SUBSURF']
        if len(subd) == 0:
            self.report({'ERROR'}, "The selected object doesn't have any subdivision surface modifiers")
            return {'CANCELLED'}

        # VALID OBJECT

        # get the shapekey names
        sk_names = []
        for block in self.obj.data.shape_keys.key_blocks:
            sk_names.append(block.name)

        # duplicate object for each shapekey
        num_shapes = len(self.obj.data.shape_keys.key_blocks) - 1
        blendshapes = duplicate_object(self.obj, times=num_shapes)
        blendshapes.insert(0, self.obj)

        # clear/apply shapekeys
        for i in range(0, len(blendshapes)):
            apply_shapekey(blendshapes[i], i)

        # apply subdivision surface modifier
        # and remove all other modifiers
        for i, shape in enumerate(blendshapes):
            apply_subdmod(shape)
            # skip the base object; only remove mods from shapes
            if i != 0:
                remove_modifiers(shape)

        # add meshes as shapekeys for the base - function
        add_objs_shapekeys(self.obj, blendshapes)

        # restore the names
        for i, name in enumerate(sk_names):
            self.obj.data.shape_keys.key_blocks[i].name = name

        # delete the duplicates
        for i in range(1, len(blendshapes)):
            bpy.data.objects.remove(blendshapes[i])

        return {'FINISHED'}

class SK_OT_apply_mods_choice_SK(Operator):
    """ Applies subdivision surface and keeps shapekeys """
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
        context = bpy.context

        # get the shapekey names
        sk_names = []
        for block in self.obj.data.shape_keys.key_blocks:
            sk_names.append(block.name)

        # duplicate object for each shapekey
        num_shapes = len(self.obj.data.shape_keys.key_blocks) - 1
        blendshapes = duplicate_object(self.obj, times=num_shapes)
        blendshapes.insert(0, self.obj)

        # clear/apply shapekeys
        for i in range(0, len(blendshapes)):
            apply_shapekey(blendshapes[i], i)

        # apply the selected modifiers
        # and remove all other modifiers
        for i, shape in enumerate(blendshapes):
            for entry in self.resource_list:
                if entry.selected:
                    apply_modifier(shape, entry.name)

            # skip the base object; only remove mods from shapes
            if i != 0:
                remove_modifiers(shape)

        # add meshes as shapekeys for the base - function
        add_objs_shapekeys(self.obj, blendshapes)

        # restore the names
        for i, name in enumerate(sk_names):
            self.obj.data.shape_keys.key_blocks[i].name = name

        # delete the duplicates
        for i in range(1, len(blendshapes)):
            bpy.data.objects.remove(blendshapes[i])

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
    # if context.active_object.data.shape_keys:
    layout.separator()
    layout.operator("sk.apply_mods_sk")
    layout.operator("sk.apply_mods_choice_sk")
    layout.operator("sk.apply_subd_sk")

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
