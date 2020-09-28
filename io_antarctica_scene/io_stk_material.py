#!BPY

# Copyright (c) 2017 SuperTuxKart author(s)
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

# We then extract each nodes, so far we only support
# * Color
#   * It MUST connected to a texture node so we extract the name of the texture
# * Vector3D
#   * Managed like a texture (for normal maps)
# * Floating point (NO OTHER NODES SHOULD BE CONNECTED)
#   * We simply exctract the value and we add it in the xml
#
# More advanced shader graphs aren't supported
#
# Physical properties (related to gameplay) are stored in custom properties

import bpy

from bpy.props import (StringProperty,
                   BoolProperty,
                   IntProperty,
                   FloatProperty,
                   EnumProperty,
                   PointerProperty
                   )
from bpy.types import (Panel,
                   Operator,
                   PropertyGroup
                   )

bl_info = {
    "name": "SuperTuxKart Material Exporter",
    "description": "Exports material properties to the materials.xml format",
    "author": "Jean-Manuel Clemencon, Joerg Henrichs, Marianne Gagnon",
    "version": (2,0),
    "blender": (2, 80, 0),
    "location": "File > Export",
    "warning": '', # used for warning icon and text in addons panel
    "wiki_url": "https://supertuxkart.net/Community",
    "tracker_url": "https://github.com/supertuxkart/stk-blender/issues",
    "category": "Import-Export"}


# GUI Library
# =============================================================================

class GuiGroup:

    _properties = None
    _class = None

    def __init__(self, clss):
        self._properties = []
        self._class = clss

    def add_property(self, key=None, name=None, prop=None, subprop=None):
        new_prop = {}
        new_prop["key"] = key
        new_prop["name"] = name
        new_prop["prop"] = prop
        new_prop["subprop"] = subprop
        self._properties.append(new_prop)
    
    def register_all(self):
        for prop in self._properties:
            self._class.__annotations__[prop["key"]] = prop["prop"]

    def draw(self, box):
        clss = getattr(bpy.context.scene, self._class.__name__)
        for prop in self._properties:
            if prop["subprop"] == None:
                ui_addproperty(box.column(), clss, prop["key"], prop["name"])
            else:
                subox = box.box()
                ui_addproperty(subox.column(), clss, prop["key"], prop["name"])
                if (getattr(clss, prop["key"]) == True):
                    prop["subprop"].draw(subox)

def ui_addproperty(column, target, prop, text):
    row = column.row(align=True)
    row.label(text=text)
    row.prop(target, prop, text="")

# End of GUI library
# ------------------

# Start GUI declaration
# =============================================================================
class QueryProps(bpy.types.PropertyGroup):
    antractica_serial: bpy.props.StringProperty(default="")


GUI_gameplay = GuiGroup(QueryProps)

GUI_gameplay.add_property(key="below_surface",
                 name="Below shallow water",
                 prop=BoolProperty(default=False, description="Used for the terrain under shallow water where you can drive"))

prop_action = EnumProperty(
        name="Actions",
        description="How to react when kart touches this material",
        items=[("none", "None", ""),
               ("reset", "Rescue kart", ""),
               ("push", "Push back kart", ""),
              ],
        default='none') 


GUI_action = GuiGroup(QueryProps)
GUI_action.add_property(key="collision_reaction", name="Action", prop=prop_action)
GUI_action.add_property(key="collision_particles", name="Particles on hit", prop=StringProperty(default="Test", description="Particle system to be used when the kart hits the material"))
GUI_action.register_all()


GUI_gameplay.add_property(key="collision_detect",
                 name="Enable collision action",
                 prop=BoolProperty(default=False, description="What happens when the kart touches/hits this material in any way"),
                 subprop=GUI_action)


GUI_slowdown = GuiGroup(QueryProps)
GUI_slowdown.add_property(key="slowdown_time", name="Slowdown Time (seconds)", prop=FloatProperty(default=1.0, min=0.0, max=10.0, description="Time it takes for speed to drop to its low point when driving here"))
GUI_slowdown.add_property(key="max_speed", name="Maximum Speed (fraction)", prop=FloatProperty(default=1.0, min=0.0, max=1.0, description="Fraction of the maximum speed can be reached when driving here"))
GUI_slowdown.register_all()
GUI_gameplay.add_property(key="use_slowdown",
                 name="Enable Slowdow",
                 prop=BoolProperty(default=False, description="Whether to slow down the kart when driving on this material"),
                 subprop=GUI_slowdown)

GUI_gameplay.add_property(key="falling_effect",
                 name="Falling Effect",
                 prop=BoolProperty(default=False, description="Whether this material is the bottom of a pit (then camera will look down at kart falling when over it)"))

GUI_gameplay.add_property(key="high_adhesion",
                 name="High tires adhesion",
                 prop=BoolProperty(default=False, description="If checked, karts will have good grip on this surface and not slip, even at angles"))

GUI_gameplay.add_property(key="has_gravity",
                 name="Affect gravity",
                 prop=BoolProperty(default=False, description="If checked, karts will be fall towards this surface like it was the ground, no matter its angle"))

GUI_gameplay.add_property(key="ignore",
                 name="Ignore (ghost material)",
                 prop=BoolProperty(default=False, description="Drive through this texture like it didn't exist (good for smoke, etc.)"))


GUI_gameplay.register_all()

# End of GUI declaration
# ----------------------

class ANTARCTICA_PT_properties(bpy.types.Panel):
    bl_idname = "ANTARCTICA_PT_properties"
    bl_label = "Antarctica Properties"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'material'

    def draw(self, context):
        pass

class ANTARCTICA_PT_interaction_gameplay(Panel):
    bl_parent_id = "ANTARCTICA_PT_properties"
    bl_idname = "ANTARCTICA_PT_interaction_gameplay"
    bl_label = "Interaction / Gameplay"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'

    def draw_header(self, context):

        props = bpy.context.scene.QueryProps
        layout = self.layout

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        
        props = bpy.context.scene.QueryProps
        
        box2 = layout.box()
        global GUI_gameplay
        GUI_gameplay.draw(box2)

class ANTARCTICA_PT_display(Panel):
    bl_parent_id = "ANTARCTICA_PT_properties"
    bl_idname = "ANTARCTICA_PT_display"
    bl_label = "Shader Properties"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'

    def draw_header(self, context):

        props = bpy.context.scene.QueryProps
        layout = self.layout

    def draw(self, context):
        pass

        if bpy.context.scene.QueryProps.collision_detect == True:
           box3 = box2.box()
           GROUP_ACTION.draw(box3)

# Writes the materials files, which includes all texture definitions
# Items are accessed by nodes, instead of being accessed directly
def writeMaterialsFile(sPath):
    sp_mat_props = {
               'shader_name'            : {'default': "", 'parent': None, 'type': 'string'},
               'uv_two_tex'             : {'default': "", 'parent': None, 'type': 'string'},
               'tex_layer_2'            : {'default': "", 'parent': None, 'type': 'string'},
               'tex_layer_3'             : {'default': "", 'parent': None, 'type': 'string'},
               'tex_layer_4'            : {'default': "", 'parent': None, 'type': 'string'},
               'tex_layer_5'             : {'default': "", 'parent': None, 'type': 'string'}
        }

    other_mat_props = {
               'below_surface'         : {'default': "N", 'parent': None, 'type': 'bool'},
               'collision_detect'      : {'default': "N", 'parent': None, 'type': 'bool'},
               'collision_particles'   : {'default': "", 'parent': 'collision_detect', 'type': 'string'},
               'collision_reaction'    : {'default': "none", 'parent': 'collision_detect', 'type': 'string'},
               'falling_effect'        : {'default': "N", 'parent': None, 'type': 'bool'},
               'ignore'                : {'default': "N", 'parent': None, 'type': 'bool'},
               'mask'                  : {'default': "", 'parent': None, 'type': 'string'},
               'mirror_axis'           : {'default': "none", 'parent': None, 'type': 'string'},
               'reset'                 : {'default': "N", 'parent': None, 'type': 'bool'},
               'surface'               : {'default': "N", 'parent': None, 'type': 'bool'},
               'high_adhesion'         : {'default': "N", 'parent': None, 'type': 'bool'},
               'has_gravity'           : {'default': "N", 'parent': None, 'type': 'bool'},
               'slowdown_time'         : {'default': 1.0, 'parent': 'use_slowdown', 'type': 'number'},
               'max_speed'             : {'default': 1.0, 'parent': 'use_slowdown', 'type': 'number'},
               'water_splash'          : {'default': "N", 'parent': None, 'type': 'bool'},
               'colorizable'           : {'default': "N", 'parent': None, 'type': 'bool'},
               'colorization_factor'   : {'default': 0.0, 'parent': 'colorizable', 'type': 'number'},
               'colorization_mask'     : {'default': "", 'parent': 'colorizable', 'type': 'string'},
               'hue_settings'          : {'default': "", 'parent': 'colorizable', 'type': 'string'}
        }

    class LogReport:

        def log(name):
            print("Error detected in the following material:", name)

        def info(info):
            print(info)

        def abort(error, reason):
            raise Exception("Material" + error, reason)

    # Detect if we are dealing with a SuperTuxKart shader
    # The custom STK PBR shader is not yet implemented
    # Use a principled BSDF shader for now
    def is_stk_shader(node):
        if node.bl_static_type == "BSDF_PRINCIPLED":
        #if node.bl_static_type == "GROUP":
            # if node.node_tree.name == "stk_pbr_shader":
            return True
        else:
            return False

    # Get the SuperTuxKart shader name
    def get_stk_shader_name(node):
        return node.name

    # We make sure we get the root of the node tree (we start from the output and build up)
    def get_root_shader(node_network):
        for node in node_network:
            # We check if it's a material output
            if node.bl_static_type == "OUTPUT_MATERIAL":
                # The surface should be linked
                if node.inputs["Surface"].is_linked:
                    # and the surface should be linked to a stk shader
                    child = node.inputs["Surface"].links[0].from_node
                    if is_stk_shader(child):
                        return child

        return None

    print("\nAntractica Material Exporter")
    print("===")
    for mat in bpy.data.materials:
        # Do not export non-node based materials
        if mat.node_tree is not None:
            root = get_root_shader(mat.node_tree.nodes)
            print("Exporting material \'" + mat.name + "\'")

            # If we can't find a root node we raise an error
            if root == None:
                LogReport.log(mat.name)
                LogReport.info(" Make sure you only have one 'Material Output' in your shader graph")
                LogReport.info(" Make sure you connected a valid SuperTuxKart shader to 'Material Output'")
                LogReport.abort("ShaderEditor", "We can't find a root node.")

            xml_output = '<material> name="{}" shader_name="{}" '.format(mat.name, get_stk_shader_name(root))

            count = 0 # Counter for the texture layers
            for inp in root.inputs:
                # Only certain inputs will be used from the shader, not all of them
                # Managing colors / 3D
                if type(inp) is bpy.types.NodeSocketColor or type(inp) is bpy.types.NodeSocketVector:
                    print("Export Color or Vector: " + inp.name)
                    if inp.is_linked:
                        # Get the connected node
                        child = inp.links[0].from_node
                        if type(child) is bpy.types.ShaderNodeTexImage:
                            xml_output += 'tex-layer-{}="{}" '.format(count, child.image.name)
                            count += 1
                        else:
                            LogReport.log(mat.name)
                            LogReport.info("Texture node not found, skipping this input node")
                    else:
                        LogReport.log(mat.name)
                        LogReport.info("Color or Vector input not connected, skipping")

                # Managing floating point numbers
                elif type(inp) is bpy.types.NodeSocketFloatFactor:
                    print("Export Float: " + inp.name)
                    xml_output += '{}="{}" '.format(inp.name, inp.default_value)

                else:
                    LogReport.log(mat.name)
                    LogReport.info("Unsupported node input/output type found; skipping this node")

                for k in mat.keys():
                    if k not in "_RNA_UI":
                        xml_output += '{}="{}" '.format(k, mat[k])

            xml_output += "</material>"
            print(xml_output)
        else:
            LogReport.log(mat.name)
            LogReport.info("No node tree was found; skipping this material")



class STK_Material_Export_Operator(bpy.types.Operator):
    bl_idname = ("screen.stk_material_exporter")
    bl_label = ("Export Materials")
    filepath: bpy.props.StringProperty()

    def execute(self, context):
        writeMaterialsFile(self.filepath)
        return {'FINISHED'}

# Add to a menu
def menu_func_export(self, context):
    global the_scene
    the_scene = context.scene
    self.layout.operator(STK_Material_Export_Operator.bl_idname, text="STK Materials")

classes = (
    QueryProps,
    ANTARCTICA_PT_properties,
    ANTARCTICA_PT_display,
    ANTARCTICA_PT_interaction_gameplay,
    STK_Material_Export_Operator
)

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
    # Register QueryProps
    bpy.types.Scene.QueryProps = bpy.props.PointerProperty(type=QueryProps)

    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)

def unregister():
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)

    from bpy.utils import unregister_class
    for cls in classes:
        unregister_class(cls)
    # $ delete QueryProps on unregister
    del(bpy.types.Scene.QueryProps)


if __name__ == "__main__":
    register()
