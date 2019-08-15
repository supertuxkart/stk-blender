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
    "wiki_url": "http://supertuxkart.sourceforge.net/Get_involved",
    "tracker_url": "https://sourceforge.net/apps/trac/supertuxkart/",
    "category": "Import-Export"}





import bpy

class QueryProps(bpy.types.PropertyGroup):
    antractica_serial: bpy.props.StringProperty(default="")


class SelectByQuery(bpy.types.Operator):

    bl_idname = "object.select_by_query"
    bl_label = "Selection of object by query"

    def execute(self, context):
        try:
            bpy.data.objects[self.query].select_set(True)
            return {'FINISHED'}
        except:
            print('Could not select object')
            return {'CANCELLED'}


class PanelThree(bpy.types.Panel):
    bl_idname = "PanelThree"
    bl_label = "Antarctica Properties"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'

    def draw(self, context):
        pass

class ANTARCTICA_PT_interaction_gameplay(Panel):
    bl_parent_id = "PanelThree"
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
        global GUI
        #GUI.draw(box2)

class ANTARCTICA_PT_display(Panel):
    bl_parent_id = "PanelThree"
    bl_idname = "ANTARCTICA_PT_display"
    bl_label = "Shader Properties"
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
        global GUI
        GUI.draw(box2)

        #if bpy.context.scene.QueryProps.collision_detect == True:
        #    box3 = box2.box()
        #    GROUP_ACTION.draw(box3)
        #else:
        #    print("stop")

class GuiGroup:

    _properties = None

    def __init__(self):
        self._properties = []

    def add_property(self, key=None, name=None, prop=None, subprop=None):
        new_prop = {}
        new_prop["key"] = key
        new_prop["name"] = name
        new_prop["prop"] = prop
        new_prop["subprop"] = subprop
        self._properties.append(new_prop)
    
    def register_all(self, clss):
        for prop in self._properties:
            clss.__annotations__[prop["key"]] = prop["prop"]

    def draw(self, box):
        for prop in self._properties:
            if prop["subprop"] == None:
                ui_addproperty(box.column(), bpy.context.scene.QueryProps, prop["key"], prop["name"])
            else:
                subox = box.box()
                ui_addproperty(subox.column(), bpy.context.scene.QueryProps, prop["key"], prop["name"])
                if (getattr(bpy.context.scene.QueryProps, prop["key"]) == True):
                    prop["subprop"].draw(subox)
    
    def print(self):
        for prop in self._properties:
            print("---", prop)

def ui_addproperty(column, target, prop, text):
    row = column.row(align=True)
    row.label(text=text)
    row.prop(target, prop, text="")


classes = (
    QueryProps,
    SelectByQuery,
    PanelThree,
    ANTARCTICA_PT_display,
    ANTARCTICA_PT_interaction_gameplay
)

print("\n\n")
print("="*20)
GUI = GuiGroup()



GUI.add_property(key="below_surface",
                 name="Below shallow water",
                 prop=BoolProperty(default=False, description="Used for the terrain under shallow water where you can drive"))


#

pp = EnumProperty(
        name="Actions",
        description="How to react when kart touches this material",
        items=[("none", "None", ""),
               ("reset", "Rescue kart", ""),
               ("push", "Push back kart", ""),
              ],
        default='none') 


GROUP_ACTION = GuiGroup()
GROUP_ACTION.add_property(key="collision_reaction", name="Action", prop=pp)
GROUP_ACTION.add_property(key="collision_particles", name="Particles on hit", prop=StringProperty(default="Test", description="Particle system to be used when the kart hits the material"))
GROUP_ACTION.register_all(QueryProps)


GUI.add_property(key="collision_detect",
                 name="Enable collision action",
                 prop=BoolProperty(default=False, description="What happens when the kart touches/hits this material in any way"),
                 subprop=GROUP_ACTION)


GUI.register_all(QueryProps)


def register():

    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
    # Register QueryProps
    bpy.types.Scene.QueryProps = bpy.props.PointerProperty(type=QueryProps)


def unregister():

    from bpy.utils import unregister_class
    for cls in classes:
        unregister_class(cls)
    # $ delete QueryProps on unregister
    del(bpy.types.Scene.QueryProps)


if __name__ == "__main__":
    register()


"""

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

mats = bpy.data.materials

class LogReport:

    def log(name):
        print("Error detected in the following material:", name)
    
    def info(info):
        print(info)
    
    def abort(error, reason):
        raise Exception("Material" + error, reason)

# Detect if we are dealing with a SuperTuxKart shader
def is_stk_shader(node):
    if node.bl_static_type == "GROUP":
        if node.node_tree.name == "stk_pbr_shader":
            return True
    else:
        return False

# Get the SuperTuxKart shader name
def get_stk_shader_name(node):
    return node.node_tree.name

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
for mat in mats:
    root = get_root_shader(mat.node_tree.nodes)
    
    # If we can't find a root node we raise an error
    if root == None:
        LogReport.log(mat.name)
        LogReport.info(" Make sure you only have one 'Material Output' in your shader graph")
        LogReport.info(" Make sure you connected a valid SuperTuxKart shader to 'Material Output'")
        LogReport.abort("ShaderEditor", "We can't find a root node.")

    xml_output = '<material> name="{}" shader_name="{}" '.format(mat.name, get_stk_shader_name(root))

    count = 0 # Counter for the texture layers
    for inp in root.inputs:

        # Managing colors / 3D
        if type(inp) is bpy.types.NodeSocketColor or type(inp) is bpy.types.NodeSocketVector:
            print("Export Color or Vector")
            if not inp.is_linked:
                LogReport.log(mat.name)
                LogReport.abort("ShaderEditor", "Color and Vector input MUST be connected '" + inp.name + "'")
            
            # Get the connected node
            child = inp.links[0].from_node
            if type(child) is not bpy.types.ShaderNodeTexImage:
                LogReport.log(mat.name)
                LogReport.abort("ShaderEditor", "You should only connect a texture node to a color or vector socket")
            
            xml_output += 'tex-layer-{}="{}" '.format(count, child.image.name)
            count += 1

        # Managing floating point numbers
        elif type(inp) is bpy.types.NodeSocketFloatFactor:
            print("Export Float")
            xml_output += '{}="{}" '.format(inp.name, inp.default_value)

        else:
            LogReport.log(mat.name)
            LogReport.abort("ShaderEditor", "Unsupported node input/output type" + type(inp))
        
        for k in mat.keys():
            if k not in "_RNA_UI":
                xml_output += '{}="{}" '.format(k, mat[k])
    
    xml_output += "</material>"
    print(xml_output)

"""