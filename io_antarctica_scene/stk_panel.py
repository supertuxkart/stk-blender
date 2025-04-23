#!BPY

# Copyright (c) 2020 SuperTuxKart author(s)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import bpy, os
from collections import OrderedDict
from bpy.types import Operator, AddonPreferences
from . import stk_utils

CONTEXT_OBJECT = 0
CONTEXT_SCENE  = 1
CONTEXT_MATERIAL  = 2

datapath = stk_utils.getDataPath(os.path.dirname(__file__))

SCENE_PROPS = []
STK_PER_OBJECT_TRACK_PROPERTIES = []
STK_PER_OBJECT_KART_PROPERTIES = []
STK_MATERIAL_PROPERTIES = []

if os.path.exists(datapath):
    print("(STK) Loading XML files from ", datapath)

    panel_params_path = os.path.join(datapath, "stk_panel_parameters.xml")
    print("(STK) Loading scene properties from ", panel_params_path)

    SCENE_PROPS = stk_utils.getPropertiesFromXML(panel_params_path, contextLevel=CONTEXT_SCENE)

    object_params_path = os.path.join(datapath, "stk_object_parameters.xml")
    print("(STK) Loading object properties from ", object_params_path)

    STK_PER_OBJECT_TRACK_PROPERTIES = stk_utils.getPropertiesFromXML(object_params_path, contextLevel=CONTEXT_OBJECT)

    kart_params_path = os.path.join(datapath, "stk_kart_object_parameters.xml")
    print("(STK) Loading kart properties from ", kart_params_path)

    STK_PER_OBJECT_KART_PROPERTIES = stk_utils.getPropertiesFromXML(kart_params_path, contextLevel=CONTEXT_OBJECT)

    material_params_path = os.path.join(datapath, "stk_material_parameters.xml")
    print("(STK) Loading material properties from ", material_params_path)

    STK_MATERIAL_PROPERTIES = stk_utils.getPropertiesFromXML(material_params_path, contextLevel=CONTEXT_MATERIAL)
else:
    raise RuntimeError("(STK) Make sure the stkdata folder is installed, cannot locate it!!")

class STK_TypeUnset(bpy.types.Operator):
    bl_idname = ("screen.stk_unset_type")
    bl_label = ("STK Object :: unset type")

    def execute(self, context):
        obj = context.object
        obj["type"] = ""
        return {'FINISHED'}

class STK_MissingProps_Object(bpy.types.Operator):
    bl_idname = ("screen.stk_missing_props_" + str(CONTEXT_OBJECT))
    bl_label = ("Create missing properties")

    def execute(self, context):

        is_track = ("is_stk_track" in context.scene and context.scene["is_stk_track"] == "true")
        is_node = ("is_stk_node" in context.scene and context.scene["is_stk_node"] == "true")
        is_kart = ("is_stk_kart" in context.scene and context.scene["is_stk_kart"] == "true")

        obj = context.object

        if is_kart:
            properties = OrderedDict([])
            for curr in STK_PER_OBJECT_KART_PROPERTIES[1]:
                properties[curr.id] = curr
            stk_utils.createProperties(obj, properties)
        elif is_track or is_node:
            properties = OrderedDict([])
            for curr in STK_PER_OBJECT_TRACK_PROPERTIES[1]:
                properties[curr.id] = curr
            print('creating', properties, 'on', obj.name)
            stk_utils.createProperties(obj, properties)

        return {'FINISHED'}

class STK_MissingProps_Scene(bpy.types.Operator):
    bl_idname = ("screen.stk_missing_props_" + str(CONTEXT_SCENE))
    bl_label = ("Create missing properties")

    def execute(self, context):
        scene = context.scene
        properties = OrderedDict([])
        for curr in SCENE_PROPS[1]:
            properties[curr.id] = curr
        stk_utils.createProperties(scene, properties)
        return {'FINISHED'}

class STK_MissingProps_Material(bpy.types.Operator):
    bl_idname = ("screen.stk_missing_props_" + str(CONTEXT_MATERIAL))
    bl_label = ("Create missing properties")

    def execute(self, context):
        material = getObject(context, CONTEXT_MATERIAL)
        properties = OrderedDict([])
        for curr in STK_MATERIAL_PROPERTIES[1]:
            properties[curr.id] = curr
        stk_utils.createProperties(material, properties)
        return {'FINISHED'}

# ==== PANEL BASE ====
class PanelBase:

    def recursivelyAddProperties(self, properties, layout, obj, contextLevel):

        for id in properties.keys():
            curr = properties[id]

            row = layout.row()

            if isinstance(curr, stk_utils.StkPropertyGroup):

                state = "true"
                icon = 'TRIA_DOWN'
                if id in bpy.data.scenes[0]:
                    state = bpy.data.scenes[0][id]
                    if state == "true":
                        icon = 'TRIA_DOWN'
                    else:
                        icon = 'TRIA_RIGHT'

                row.operator(stk_utils.generateOpName("screen.stk_tglbool_", curr.fullid, curr.id), text=curr.name, icon=icon, emboss=False)
                row.label(text=" ") # force the operator to not maximize
                if state == "true":
                    if len(curr.subproperties) > 0:
                        box = layout.box()
                        self.recursivelyAddProperties(curr.subproperties, box, obj, contextLevel)

            elif isinstance(curr, stk_utils.StkBoolProperty):

                state = "false"
                icon = 'CHECKBOX_DEHLT'
                split = row.split(factor=0.8)
                split.label(text=curr.name)
                if id in obj:
                    state = obj[id]
                    if state == "true":
                       icon = 'CHECKBOX_HLT'
                split.operator(stk_utils.generateOpName("screen.stk_tglbool_", curr.fullid, curr.id), text="                ", icon=icon, emboss=False)

                if state == "true":
                    if len(curr.subproperties) > 0:
                        if curr.box:
                            box = layout.box()
                            self.recursivelyAddProperties(curr.subproperties, box, obj, contextLevel)
                        else:
                            self.recursivelyAddProperties(curr.subproperties, layout, obj, contextLevel)

            elif isinstance(curr, stk_utils.StkColorProperty):
                row.label(text=curr.name)
                if curr.id in obj:
                    row.prop(obj, '["' + curr.id + '"]', text="")
                    row.operator(stk_utils.generateOpName("screen.stk_apply_color_", curr.fullid, curr.id), text="", icon='COLOR')
                else:
                    row.operator('screen.stk_missing_props_' + str(contextLevel))

            elif isinstance(curr, stk_utils.StkCombinableEnumProperty):

                row.label(text=curr.name)

                if curr.id in obj:
                    curr_val = obj[curr.id]

                    for value_id in curr.values:
                        icon = 'CHECKBOX_DEHLT'
                        if value_id in curr_val:
                            icon = 'CHECKBOX_HLT'
                        row.operator(stk_utils.generateOpName("screen.stk_set_", curr.fullid, curr.id + "_" + value_id), text=curr.values[value_id].name, icon=icon)
                else:
                    row.operator('screen.stk_missing_props_' + str(contextLevel))

            elif isinstance(curr, stk_utils.StkLabelPseudoProperty):
                row.label(text=curr.name)

            elif isinstance(curr, stk_utils.StkEnumProperty):

                row.label(text=curr.name)

                if id in obj:
                    curr_value = obj[id]
                else:
                    curr_value = ""

                label = curr_value
                if curr_value in curr.values:
                    label = curr.values[curr_value].name

                row.menu(curr.menu_operator_name, text=label)
                #row.operator_menu_enum(curr.getOperatorName(), property="value", text=label)

                if curr_value in curr.values and len(curr.values[curr_value].subproperties) > 0:
                    box = layout.box()
                    self.recursivelyAddProperties(curr.values[curr_value].subproperties, box, obj, contextLevel)

            elif isinstance(curr, stk_utils.StkObjectReferenceProperty):

                row.label(text=curr.name)

                if curr.id in obj:
                    row.prop(obj, '["' + curr.id + '"]', text="")
                    row.menu(stk_utils.generateOpName("STK_MT_object_menu_", curr.fullid, curr.id), text="", icon='TRIA_DOWN')
                else:
                    row.operator('screen.stk_missing_props_' + str(contextLevel))

            else:
                row.label(text=curr.name)

                # String or int or float property (Blender chooses the correct widget from the type of the ID-property)
                if curr.id in obj:
                    if "min" in dir(curr) and "max" in dir(curr) and curr.min is not None and curr.max is not None:
                        row.prop(obj, '["' + curr.id + '"]', text="", slider=True)
                    else:
                        row.prop(obj, '["' + curr.id + '"]', text="")
                else:
                    row.operator('screen.stk_missing_props_' + str(contextLevel))

# ==== OBJECT PANEL ====
class STK_PT_Object_Panel(bpy.types.Panel, PanelBase):
    bl_label = STK_PER_OBJECT_TRACK_PROPERTIES[0]
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"

    def draw(self, context):

        layout = self.layout

        is_track = ("is_stk_track" in context.scene and context.scene["is_stk_track"] == "true")
        is_node = ("is_stk_node" in context.scene and context.scene["is_stk_node"] == "true")
        is_kart = ("is_stk_kart" in context.scene and context.scene["is_stk_kart"] == "true")

        if not is_track and not is_kart and not is_node:
            layout.label(text="(Not a SuperTuxKart scene)")
            return

        obj = context.object

        if obj.library is not None or obj.override_library is not None:
            layout.label(text="Library nodes cannot be configured here")
            return

        if obj is not None:
            if is_track or is_node:
                properties = OrderedDict([])
                for curr in STK_PER_OBJECT_TRACK_PROPERTIES[1]:
                    properties[curr.id] = curr
                self.recursivelyAddProperties(properties, layout, obj, CONTEXT_OBJECT)

            if is_kart:
                properties = OrderedDict([])
                for curr in STK_PER_OBJECT_KART_PROPERTIES[1]:
                    properties[curr.id] = curr
                self.recursivelyAddProperties(properties, layout, obj, CONTEXT_OBJECT)


# ==== SCENE PANEL ====
class STK_PT_Scene_Panel(bpy.types.Panel, PanelBase):
    bl_label = SCENE_PROPS[0]
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"

    def draw(self, context):
        layout = self.layout
        obj = context.scene

        if obj is not None:

            properties = OrderedDict([])
            for curr in SCENE_PROPS[1]:
                properties[curr.id] = curr

            self.recursivelyAddProperties(properties, layout, obj, CONTEXT_SCENE)

# Extension to the 'add' menu
class STK_OT_Add_Object(bpy.types.Operator):
    """Create a new SuperTuxKart Object"""
    bl_idname = ("scene.stk_add_object")
    bl_label = ("STK Object :: Add Object")
    bl_options = {'REGISTER', 'UNDO'}

    name: bpy.props.StringProperty()

    value: bpy.props.EnumProperty(attr="values", name="values", default='banana',
                                           items=[('banana', 'Banana', 'Banana'),
                                                  ('item', 'Item (Gift Box)', 'Item (Gift Box)'),
                                                  ('light', 'Light', 'Light'),
                                                  ('nitro_big', 'Nitro (Big)', 'Nitro (big)'),
                                                  ('nitro_small', 'Nitro (Small)', 'Nitro (Small)'),
                                                  ('red_flag', 'Red flag', 'Red flag'),
                                                  ('blue_flag', 'Blue flag', 'Blue flag'),
                                                  ('particle_emitter', 'Particle Emitter', 'Particle Emitter'),
                                                  ('sfx_emitter', 'Sound Emitter', 'Sound Emitter'),
                                                  ('start', 'Start position (for battle mode)', 'Start position (for battle mode)')
                                                  ])

    def execute(self, context):
        if self.value == 'light':
            bpy.ops.object.add(type='LIGHT', location=context.scene.cursor.location)

            for curr in bpy.data.objects:
                if curr.type == 'LIGHT' and curr.select_get():
                    # FIXME: create associated subproperties if any
                    curr['type'] = self.value
                    break
        else:
            bpy.ops.object.add(type='EMPTY', location=context.scene.cursor.location)

            for curr in bpy.data.objects:
                if curr.type == 'EMPTY' and curr.select_get():
                    # FIXME: create associated subproperties if any
                    curr['type'] = self.value

                    if self.value == 'item':
                        curr.empty_display_type = 'CUBE'
                    elif self.value == 'nitro_big' or self.value == 'nitro_small' :
                        curr.empty_display_type = 'CONE'
                    elif self.value == 'sfx_emitter':
                        curr.empty_display_type = 'SPHERE'

                    for prop in STK_PER_OBJECT_TRACK_PROPERTIES[1]:
                        if prop.name == "Type":
                            stk_utils.createProperties(curr, prop.values[self.value].subproperties)
                            break

                    break

        return {'FINISHED'}


# ======== PREFERENCES ========
class StkPanelAddonPreferences(bpy.types.AddonPreferences):
    bl_idname = os.path.basename(os.path.dirname(__file__))

    stk_assets_path: bpy.props.StringProperty(
            name="Assets (data) path",
            #subtype='DIR_PATH',
            )

    stk_delete_old_files_on_export: bpy.props.BoolProperty(
            name="Delete all old files when exporting a track in a folder (*.spm)",
            default = False
            )

    stk_export_images: bpy.props.BoolProperty(
            name="Copy texture files when exporting a kart, track, or library node",
            default = False
            )

    def draw(self, context):
        layout = self.layout
        layout.label(text="The data folder contains folders named 'karts', 'tracks', 'textures', etc.")
        layout.prop(self, "stk_assets_path")
        layout.operator('screen.stk_pick_assets_path', icon='FILEBROWSER', text="Select...")
        layout.prop(self, "stk_delete_old_files_on_export")
        layout.prop(self, "stk_export_images")

class STK_FolderPicker_Operator(bpy.types.Operator):
    bl_idname = "screen.stk_pick_assets_path"
    bl_label = "Select the SuperTuxKart assets (data) folder"

    filepath: bpy.props.StringProperty(subtype="DIR_PATH")

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        import bpy.path
        import os.path
        preferences = context.preferences
        addon_prefs = preferences.addons[os.path.basename(os.path.dirname(__file__))].preferences
        addon_prefs.stk_assets_path = os.path.dirname(bpy.path.abspath(self.filepath))
        bpy.ops.wm.save_userpref()
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

# ==== QUICK EXPORT PANEL ====
class STK_PT_Quick_Export_Panel(bpy.types.Panel):
    bl_label = "Quick Exporter"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"

    def draw(self, context):
        isNotANode = ('is_stk_node' not in context.scene) or (context.scene['is_stk_node'] != 'true')
        layout = self.layout

        # ==== Types group ====
        row = layout.row()

        assets_path = context.preferences.addons[os.path.basename(os.path.dirname(__file__))].preferences.stk_assets_path

        if assets_path is not None and len(assets_path) > 0:
            row.label(text='Assets (data) path: ' + assets_path)
        else:
            row.label(text='Assets (data) path: [please select path]')
        row.operator('screen.stk_pick_assets_path', icon='FILEBROWSER', text="")

        if assets_path is None or len(assets_path) == 0:
            return

        # row = layout.row()
        # row.prop(the_scene, 'stk_track_export_images', text="Copy texture files")

        row = layout.row()
        row.operator("screen.stk_kart_export", text="Export Kart", icon='AUTO')

        if isNotANode:
            row.operator("screen.stk_track_export", text="Export Track", icon='TRACKING')
        else:
            row.operator("screen.stk_track_export", text="Export Library Node", icon='GROUP')

        if (assets_path is None or len(assets_path) == 0) \
            and bpy.context.mode != 'OBJECT':
            row.enabled = False
<<<<<<< HEAD
=======


# === STK LAUNCHER ===
class STK_OT_RunStk(bpy.types.Operator):
    bl_idname = "screen.run_stk"
    bl_label = "Run STK"

    def execute(self, context):
        # Ici, vous pouvez ajouter le code pour exécuter votre exécutable
        # Par exemple, utiliser subprocess pour lancer l'exécutable
        import subprocess

        # Récupérer le chemin de l'exécutable depuis les propriétés de la scène
        executable_path = context.scene.stk_runner

        try:
            subprocess.Popen(executable_path)
            self.report({'INFO'}, f"Launching STK: {executable_path}")
        except Exception as e:
            self.report({'ERROR'}, f"Failed to launch STK: {str(e)}")

        return {'FINISHED'}


# ==== launcher STK PANEL ====
class STK_PT_Launcher_Stk_Panel(bpy.types.Panel):
    bl_label = "STK GO !!!"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"
        
    def draw(self, context):
        layout = self.layout

        # Champ de texte pour entrer le chemin de l'exécutable
        row = layout.row()
        row.label(text="executable: ")
        row.prop(context.scene, "stk_runner", text="")

        # Bouton pour lancer l'opérateur
        buttom_exec = self.layout.operator("screen.run_stk", text="Launch STK", icon='PLAY')
>>>>>>> 3.x
