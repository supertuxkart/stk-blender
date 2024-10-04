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

# Addon information
bl_info = {
    "name": "SuperTuxKart Exporter Tools",
    "description": "Export various items to SuperTuxKart objects (karts, tracks, and materials)",
    "author": "Jean-Manuel Clemencon, Joerg Henrichs, Marianne Gagnon, Richard Qian",
    "version": (4,0),
    "blender": (2, 80, 0),
    "location": "File > Import-Export",
    "warning": '', # used for warning icon and text in addons panel
    "wiki_url": "https://supertuxkart.net/Community",
    "tracker_url": "https://github.com/supertuxkart/stk-blender/issues",
    "category": "Import-Export"}

if "bpy" in locals():
    import importlib
    if "stk_utils" in locals():
        importlib.reload(stk_utils)
    if "stk_panel" in locals():
        importlib.reload(stk_panel)
    if "stk_material" in locals():
        importlib.reload(stk_material)
    if "stk_kart" in locals():
        importlib.reload(stk_kart)
    if "stk_track" in locals():
        importlib.reload(stk_track)
else:
    from . import stk_utils, stk_panel, stk_material, stk_kart, stk_track

import bpy, bpy_extras, os

# Define export buttons for 3D View header menu
def header_func_export_stk_kart(self, context):
    self.layout.operator(stk_kart.STK_Kart_Export_Operator.bl_idname, text="Export STK Kart")

def header_func_export_stk_track(self, context):
    self.layout.operator(stk_track.STK_Track_Export_Operator.bl_idname, text="Export STK Track")
    
  
# Define export buttons for File -> Export menu
def menu_func_export_stk_material(self, context):
    self.layout.operator(stk_material.STK_Material_Export_Operator.bl_idname, text="STK Materials")

def menu_func_export_stk_kart(self, context):
    self.layout.operator(stk_kart.STK_Kart_Export_Operator.bl_idname, text="STK Kart")

def menu_func_export_stk_track(self, context):
    self.layout.operator(stk_track.STK_Track_Export_Operator.bl_idname, text="STK Track")


# Define custom STK object submenu for 3D View -> Add menu
def menu_func_add_stk_object(self, context):
    self.layout.operator_menu_enum("scene.stk_add_object", property="value", text="STK", icon='AUTO')

classes = (
    stk_panel.STK_TypeUnset,
    stk_panel.STK_MissingProps_Object,
    stk_panel.STK_MissingProps_Scene,
    stk_panel.STK_MissingProps_Material,
    stk_panel.StkPanelAddonPreferences,
    stk_panel.STK_PT_Object_Panel,
    stk_panel.STK_PT_Scene_Panel,
    stk_panel.STK_OT_Add_Object,
    stk_panel.STK_FolderPicker_Operator,
    stk_panel.STK_PT_Quick_Export_Panel,
    stk_material.ANTARCTICA_PT_properties,
    stk_material.STK_Material_Export_Operator,
    stk_kart.STK_Kart_Export_Operator,
    stk_track.STK_Track_Export_Operator,
    stk_panel.STK_OT_RunStk,
    stk_panel.STK_GO_FolderPicker_Operator,
)

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
	
	# Add export buttons to File -> Export menu
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export_stk_material)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export_stk_kart)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export_stk_track)
    
    # Add custom STK object buttons to 3D View -> Add menu
    bpy.types.VIEW3D_MT_add.append(menu_func_add_stk_object)
    
    # Add export buttons the 3D View header menu
    bpy.types.VIEW3D_HT_tool_header.append(header_func_export_stk_kart)
    bpy.types.VIEW3D_HT_tool_header.append(header_func_export_stk_track)
    bpy.types.Scene.stk_runner = bpy.props.StringProperty(name="filepath")

def unregister():
	# Unregister export buttons from 3D View header menu
    bpy.types.VIEW3D_HT_tool_header.remove(menu_func_export_stk_kart)
    bpy.types.VIEW3D_HT_tool_header.remove(menu_func_export_stk_track)
    
    # Unregister custom STK object buttons from 3D View -> Add menu
    bpy.types.VIEW3D_MT_add.remove(menu_func_add_stk_object)
    
    # Unregister export buttons from File -> Export Menu
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export_stk_material)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export_stk_kart)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export_stk_track)
    del bpy.types.Scene.stk_runner

    from bpy.utils import unregister_class
    for cls in classes:
        unregister_class(cls)

if __name__ == "__main__":
    register()
