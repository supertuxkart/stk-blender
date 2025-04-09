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
    "author": "Jean-Manuel Clemencon, Joerg Henrichs, Marianne Gagnon, Richard Qian, LLS",
    "version": (4,1),
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
    stk_panel.STK_GO_FolderPicker_Operator,
    stk_panel.STK_tracks_FolderPicker_Operator,
    stk_panel.STK_karts_FolderPicker_Operator,
    stk_panel.STK_PT_Quick_Export_Panel,
    stk_material.ANTARCTICA_PT_properties,
    stk_material.STK_Material_Export_Operator,
    stk_kart.STK_Kart_Export_Operator,
    stk_track.STK_Track_Export_Operator,
    stk_panel.STK_OT_RunStk,
    stk_panel.STK_PT_Quick_Runner_Panel,
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

    # Add debug properties for Quick Runner Panel
    bpy.types.Scene.debug_track = bpy.props.BoolProperty(
        name="Debug Track",
        description="Enable track debugging",
        default=False
    )
    bpy.types.Scene.debug_checkline = bpy.props.BoolProperty(
        name="Debug Checkline", 
        description="Enable checkline debugging",
        default=False
    )
    
    # Add kart selection properties
    bpy.types.Scene.ia_used = bpy.props.StringProperty(
        name="IA Used",
        description="IA configuration",
        default=''
    )
    bpy.types.Scene.number_kart = bpy.props.IntProperty(
        name="Number of Karts",
        description="Number of karts in the race",
        default=6,
        min=0,
        max=20
    )
    bpy.types.Scene.choix_kart = bpy.props.StringProperty(
        name="Kart Choice",
        description="Custom kart selection",
        default=''
    )
    bpy.types.Scene.kart_user = bpy.props.EnumProperty(
        name="Kart User",
        description="Select a kart",
        items=[
            ("adiumy", "Adiumy", "", "", 0),
            ("amanda", "Amanda", "", "", 1),
            ("beastie", "Beastie", "", "", 2),
            ("emule", "Emule", "", "", 3),
            ("gavroche", "Gavroche", "", "", 4),
            ("gnu", "GNU", "", "", 5),
            ("hexley", "Hexley", "", "", 6),
            ("kiki", "Kiki", "", "", 7),
            ("konqi", "Konqi", "", "", 8),
            ("nolok", "Nolok", "", "", 9),
            ("pidgin", "Pidgin", "", "", 10),
            ("puffy", "Puffy", "", "", 11),
            ("sara_the_racer", "Pepper", "", "", 12),
            ("sara_the_wizard", "Sara", "", "", 13),
            ("suzanne", "Suzanne", "", "", 14),
            ("tux", "Tux", "", "", 15),
            ("wilber", "Wilber", "", "", 16),
            ("xue", "Xue", "", "", 17),
        ],
        default="tux"
    )
    bpy.types.Scene.choix_track = bpy.props.StringProperty(
        name="Track Choice",
        description="Custom track selection",
        default=''
    )
    bpy.types.Scene.track_run = bpy.props.EnumProperty(
        name="Track Choice",
        description="Select a track",
        items=[
            ("abyss", "Abyss", "Race track", "", 0),
            ("alien_signal", "Alien Signal", "Battle track", "", 1),
            ("ancient_colosseum_labyrinth", "Ancient Colosseum Labyrinth", "Battle track", "", 2),
            ("arena_candela_city", "Arena Candela City", "Battle track", "", 3),
            ("battleisland", "Battle Island", "Battle track", "", 4),
            ("black_forest", "Black Forest", "Race track", "", 5),
            ("candela_city", "Candela City", "Race track", "", 6),
            ("cave", "Cave", "Battle track", "", 7),
            ("cocoa_temple", "Cocoa Temple", "Race track", "", 8),
            ("cornfiel_crossing", "Cornfield Crossing", "Race track", "", 9),
            ("fortmagma", "Fort Magma", "Race track", "", 10),
            ("gran_paradiso_island", "Gran Paradiso Island", "Race track", "", 11),
            ("hacienda", "Hacienda", "Race track", "", 12),
            ("hole_drop", "Hole Drop", "Soccer track", "", 13),
            ("icy_soccer_field", "Icy Soccer Field", "Soccer track", "", 14),
            ("lasdunasarena", "Las Dunas Arena", "Battle track", "", 15),
            ("lasdunassoccer", "Las Dunas Soccer", "Soccer track", "", 16),
            ("lighthouse", "Light House", "Race track", "", 17),
            ("mines", "Mines", "Race track", "", 18),
            ("minigolf", "Mini Golf", "Race track", "", 19),
            ("oasis", "Oasis", "Soccer track", "", 20),
            ("olivermath", "Oliver Math", "Race track", "", 21),
            ("pumpkin_park", "Pumpkin Park", "Battle track", "", 22),
            ("ravenbridge_mansion", "Ravenbridge Mansion", "Race track", "", 23),
            ("sandtrack", "Sand Track", "Race track", "", 24),
            ("scotland", "Scotland", "Race track", "", 25),
            ("snowmountain", "Snow Mountain", "Race track", "", 26),
            ("snowtuxpeak", "Snow Tux Peak", "Race track", "", 27),
            ("soccer_field", "Soccer Field", "Soccer track", "", 28),
            ("stadium", "Stadium", "Battle track", "", 29),
            ("stk_entreprise", "STK Entreprise", "Race track", "", 30),
            ("temple", "Temple", "Battle track", "", 31),
            ("volcano_island", "Volcano Island", "Race track", "", 32),
            ("xr591", "XR591", "Race track", "", 33),
            ("zengarden", "Zen Garden", "Race track", "", 34)
        ],
        default="hacienda",
    )
    bpy.types.Scene.game_mode = bpy.props.EnumProperty(
        name="Game Mode",
        description="Choice the game mode",
        items=[
            ("0", "Normal", "Racing", "", 0),
            ("1", "Time trial", "", "", 1),
            ("2", "Battle", "", "", 2),
            ("3", "Soccer", "", "", 3),
            ("4", "Follow The Leader", "", "", 4),
            ("5", "Capture The Flag", "", "", 5),
        ],
        default="0",
    )
    bpy.types.Scene.difficulty = bpy.props.EnumProperty(
        name="Difficulty",
        description="Difficulty level",
        items=[
            ("0", "Beginner", "", "", 0),
            ("1", "Intermediate", "", "", 1),
            ("2", "Expert", "", "", 2),
            ("3", "SuperTux", "", "", 3),
        ],
        default="3",
    )
    bpy.types.Scene.laps = bpy.props.IntProperty(
        name="Number of lap",
        description="Number of lap for the race",
        default=1,
        min=1,
        max=20
    )
    bpy.types.Scene.use_sudo = bpy.props.BoolProperty(
        name="Super User",
        description="Use super-user rights to launch STK",
        default=False
    )
    bpy.types.Scene.custom_command = bpy.props.StringProperty(
        name="CLI Command",
        description="use a personnal command",
        default='',
    )

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
    del bpy.types.Scene.debug_track
    del bpy.types.Scene.debug_checkline
    del bpy.types.Scene.ia_used
    del bpy.types.Scene.number_kart
    del bpy.types.Scene.choix_kart
    del bpy.types.Scene.kart_user
    del bpy.types.Scene.choix_track
    del bpy.types.Scene.track_run
    del bpy.types.Scene.game_mode
    del bpy.types.Scene.difficulty
    del bpy.types.Scene.laps
    del bpy.types.Scene.use_sudo
    del bpy.types.Scene.custom_command

    from bpy.utils import unregister_class
    for cls in classes:
        unregister_class(cls)

if __name__ == "__main__":
    register()
