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

import bpy, re
from bpy_extras.io_utils import ExportHelper
from collections import OrderedDict

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

from . import stk_utils, stk_panel

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

class ANTARCTICA_PT_properties(Panel, stk_panel.PanelBase):
    bl_idname = "ANTARCTICA_PT_properties"
    bl_label = "Antarctica / SuperTuxKart Properties"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'material'

    def draw(self, context):
        layout = self.layout
        row = layout.row()

        obj = stk_utils.getObject(context, stk_panel.CONTEXT_MATERIAL)
        if obj is not None:
            root_node = get_root_shader(obj.node_tree.nodes)
            if root_node is not None:
                base_color = root_node.inputs["Base Color"]
                if base_color.is_linked:
                    col = base_color.links[0].from_node
                    if type(col) is bpy.types.ShaderNodeTexImage:
                        row.label(text="Backing image: " + col.image.name)
                    elif type(col) is bpy.types.ShaderNodeVertexColor:
                        row.label(text="Backing image: (vertex color)")
                    else:
                        row.label(text="(Incompatible node detected)")
                else:
                    row.label(text="Backing image: (none)")
            else:
                row.label(text="(Material is not node-based)")

            properties = OrderedDict([])
            for curr in stk_panel.STK_MATERIAL_PROPERTIES[1]:
                properties[curr.id] = curr

            self.recursivelyAddProperties(properties, layout, obj, stk_panel.CONTEXT_MATERIAL)

# Writes the materials files, which includes all texture definitions
# Items are accessed by nodes, instead of being accessed directly
def writeMaterialsFile(self, sPath):
    used_inputs = ["Base Color", "Metallic", "Specular", "Roughness", "Emission", "Alpha", "Normal"]

    sp_mat_props = {
               'shader_name'            : {'default': "", 'parent': None, 'type': 'string'},
               'uv_two_tex'             : {'default': "", 'parent': None, 'type': 'string'},
               'tex_layer_2'            : {'default': "", 'parent': None, 'type': 'string'},
               'tex_layer_3'             : {'default': "", 'parent': None, 'type': 'string'},
               'tex_layer_4'            : {'default': "", 'parent': None, 'type': 'string'},
               'tex_layer_5'             : {'default': "", 'parent': None, 'type': 'string'}
    }

    old_mat_props = {
           'shader'                : {'default': 'solid', 'parent': None, 'type': 'string'},
           'splatting_texture_1'   : {'default': "", 'parent': ('shader','splatting'), 'type': 'string'},
           'splatting_texture_2'   : {'default': "", 'parent': ('shader','splatting'), 'type': 'string'},
           'splatting_texture_3'   : {'default': "", 'parent': ('shader','splatting'), 'type': 'string'},
           'splatting_texture_4'   : {'default': "", 'parent': ('shader','splatting'), 'type': 'string'},
           'normal_map'            : {'default': "", 'parent': None, 'type': 'string'},
           'gloss_map'             : {'default': "", 'parent': None, 'type': 'string'},
           'clampu'                : {'default': "N", 'parent': None, 'type': 'bool'},
           'clampv'                : {'default': "N", 'parent': None, 'type': 'bool'},
           'grass_speed'           : {'default': 0.4, 'parent': ('shader','grass'), 'type': 'number'},
           'grass_amplitude'       : {'default': 0.25, 'parent': ('shader','grass'), 'type': 'number'}
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

        def error(name):
            self.report({'ERROR'}, "Error detected in the following material: " + name)

        def warn(name):
            self.report({'WARNING'}, "Warning reported in the following material: " + name)

        def info(info):
            self.report({'INFO'}, info)

        def abort(error, reason):
            raise RuntimeError("Material" + error, reason)

    print("\nAntractica Material Exporter")
    print("===")

    with open(sPath, "w", encoding="utf8", newline="\n") as f:
        f.write("<?xml version=\"1.0\" encoding=\"utf-8\"?>\n")
        f.write("<materials>\n")

        for mat in bpy.data.materials:
            # Check if a material is using SP shader materials first
            sp_mat = stk_utils.getIdProperty(mat, "shader", default="", set_value_if_undefined=0) == "sp_shader"
            if sp_mat == True:
                mat_dic = stk_utils.merge_materials(other_mat_props, sp_mat_props)
            else:
                mat_dic = stk_utils.merge_materials(other_mat_props, old_mat_props)

            # Iterate through material definitions and collect data
            matLine = ""
            paramLine = ""
            sImage = ""
            sSFX = ""
            sParticle = ""
            sZipper = ""
            hasNormal = False
            hasTwoUVs = False
            hasSoundeffect = (stk_utils.convertTextToYN(stk_utils.getIdProperty(mat, "use_sfx", "no")) == "Y")
            hasParticle = (stk_utils.convertTextToYN(stk_utils.getIdProperty(mat, "particle", "no")) == "Y")
            hasZipper = (stk_utils.convertTextToYN(stk_utils.getIdProperty(mat, "zipper", "no")) == "Y")

            # Create a copy of the list of defaults so that it can be modified. Then add
            # all properties of the current image
            props_copy = []
            for sAttrib in mat.keys():
                if sAttrib not in props_copy:
                    props_copy.append( (sAttrib, mat[sAttrib]) )

            for AProperty,ADefault in props_copy:
                # Don't add the (default) values to the property list
                currentValue = stk_utils.getIdProperty(mat, AProperty, ADefault, set_value_if_undefined=0)
                # Correct for all the ways booleans can be represented (true/false;yes/no;zero/not_zero)
                if AProperty in mat_dic and mat_dic[AProperty]['type'] == 'bool':
                    currentValue = stk_utils.convertTextToYN(currentValue)

                # These items pertain to the soundeffects (starting with sfx_)
                if AProperty.strip().startswith("sfx_"):
                    strippedName = AProperty.strip()[len("sfx_"):]

                    if strippedName in ['filename', 'rolloff', 'min_speed', 'max_speed', 'min_pitch', 'max_pitch', 'positional', 'volume']:
                        if isinstance(currentValue, float):
                            sSFX = "%s %s=\"%.2f\""%(sSFX,strippedName,currentValue)
                        else:
                            sSFX = "%s %s=\"%s\""%(sSFX,strippedName,currentValue)
                elif AProperty.strip().upper().startswith("PARTICLE_"):
                    #These items pertain to the particles (starting with particle_)
                    strippedName = AProperty.strip()[len("PARTICLE_"):]
                    sParticle = "%s %s=\"%s\""%(sParticle,strippedName,currentValue)
                elif AProperty.strip().upper().startswith("ZIPPER_"):
                    #These items pertain to the zippers (starting with zipper_)
                    strippedName = AProperty.strip()[len("ZIPPER_"):]

                    sZipper = "%s %s=\"%s\""%(sZipper,strippedName.replace('_', '-'),currentValue)
                else:
                    # These items are standard items
                    prop = AProperty.strip()#.lower()

                    if prop in mat_dic.keys():

                        # If this property is conditional on another
                        cond = mat_dic[prop]['parent']

                        conditionPassed = False
                        if cond is None:
                            conditionPassed = True
                        elif type(cond) is tuple:
                            if cond[0] in mat and mat[cond[0]] == cond[1]:
                                conditionPassed = True
                        elif cond in mat and mat[cond] == "true":
                            conditionPassed = True

                        if currentValue != mat_dic[prop]['default'] and conditionPassed:
                            fixed_property = AProperty
                            if AProperty == 'shader_name':
                                fixed_property = 'shader'
                            if isinstance(currentValue, float):
                                # In Blender, properties use '_', but STK still expects '-'
                                paramLine = "%s %s=\"%.2f\""%(paramLine,fixed_property.replace("_","-"),currentValue)
                            else:
                                # In Blender, properties use '_', but STK still expects '-'
                                paramLine = "%s %s=\"%s\""%(paramLine,fixed_property.replace("_","-"),(currentValue+'').strip())

            # Do not export non-node based materials
            if mat.node_tree is not None:
                root = get_root_shader(mat.node_tree.nodes)
                # If we can't find a root node we raise an error
                if root == None:
                    LogReport.error(mat.name)
                    LogReport.info("Make sure you only have one 'Material Output' in your shader graph")
                    LogReport.info("Make sure you connected a valid SuperTuxKart shader to 'Material Output'")
                    LogReport.abort("ShaderEditor", "We can't find a root node.")

                for inp in root.inputs:
                    # Only certain inputs will be used from the shader, not all of them
                    # Managing colors / 3D
                    if type(inp) is bpy.types.NodeSocketColor or type(inp) is bpy.types.NodeSocketVector and \
                    inp.name in used_inputs:
                        if inp.is_linked:
                            # Get the connected node
                            child = inp.links[0].from_node
                            if type(child) is bpy.types.ShaderNodeTexImage:
                                sImage = child.image
                            elif type(child) is bpy.types.ShaderNodeMixRGB:
                                uvOne = child.inputs['Color1'].links[0].from_node
                                uvTwo = child.inputs['Color2'].links[0].from_node
                                if type(uvOne) is bpy.types.ShaderNodeTexImage:
                                    sImage = uvOne.image
                                # Use image specified in node tree only if not already specified
                                # Switch shader to 'decal' only if not already specified
                                if type(uvTwo) is bpy.types.ShaderNodeTexImage:
                                    hasTwoUVs = True
                                    if "uv-two-tex" in paramLine:
                                        re.sub("uv-two-tex=\".*\"", "uv-two-tex=\"" + uvTwo.image.name + "\"", paramLine)
                                    else:
                                        paramLine += " uv-two-tex=\"" + uvTwo.image.name + "\""

                                    if "shader" in paramLine:
                                        re.sub("shader=\".*\"", "shader=\"decal\"")
                                    else:
                                        paramLine += " shader=\"decal\""
                            elif type(child) is bpy.types.ShaderNodeNormalMap:
                                nmColor = child.inputs['Color'].links[0].from_node
                                if type(nmColor) is bpy.types.ShaderNodeTexImage:
                                    hasNormal = True
                                    if "normal-map" in paramLine:
                                        re.sub("normal-map=\".*\"", "normal-map=\"" + nmColor.image.name + "\"", paramLine)
                                    else:
                                        paramLine += " normal-map=\"" + nmColor.image.name + "\""
                            else:
                                LogReport.warn(mat.name)
                                LogReport.info("Texture node not found, skipping this input node")

                    # Managing floating point numbers
                    #elif type(inp) is bpy.types.NodeSocketFloatFactor and inp.name in used_inputs:
                        #paramLine += '{}="{}" '.format(inp.name, inp.default_value)

                # Now write the main content of the materials.xml file
                # Each line is written only if there are parameters configured
                if sImage and (paramLine or hasNormal or hasTwoUVs or hasSoundeffect or hasParticle or hasZipper):
                    print("Exporting material \'" + mat.name + "\'")
                    matLine = "  <material name=\"%s\"" % (sImage.name)
                    if paramLine:
                        matLine += paramLine
                    if hasSoundeffect:
                        matLine += ">\n    <sfx%s/>" % (sSFX)
                    if hasParticle:
                        matLine += ">\n    <particles%s/>" % (sParticle)
                    if hasZipper:
                        matLine += ">\n    <zipper%s/>" % (sZipper)
                    if not hasSoundeffect and not hasParticle and not hasZipper:
                        matLine += "/>\n"
                    else:
                        matLine += "\n  </material>\n"

                    f.write(matLine)
                else:
                    print("No parameters configured for material \'" + mat.name + "\', skipping")

        f.write("</materials>\n")


class STK_Material_Export_Operator(bpy.types.Operator, ExportHelper):
    """Export XML flies describing STK materials"""

    bl_idname = ("screen.stk_material_export")
    bl_label = ("Export STK Materials")

    filename_ext = ".xml"
    filepath: bpy.props.StringProperty()

    def execute(self, context):
        writeMaterialsFile(self, self.filepath)
        return {'FINISHED'}
