bl_info = {
    "name": "STK RUNNER",
    "author": "Ludérïck Le Saouter @LLS",
    "version": (1, 0),
    "blender": (3, 6, 0),
    "category": "Node",
    "description": "éditeur orienté test d'actif pour SuperTuxKart",
    "location": "Node Editor > STK RUNNER",
}

import bpy, os
from .base import (node, menu, editor, NPanel_editor)
from .node.mode import (
    battle_info, capture_flag_info,
    cutscene_info, leader_info, race_info,
    soccer_info, time_trial)
from .node.option import (
    cli, demo_info, global_info,
    graphic, initial_info, windows)
from .node.run import (preview_info, runner)
from .node.experimental import (egg_info)
from .node.debug import (controller, kart, other, track)

classes = (
    editor.STKeditor,
    menu.STKmenu,
    menu.STKoption,
    menu.STKrun,
    menu.STKexperimental,
    menu.STKdebug,
    NPanel_editor.STKpanel,
    NPanel_editor.STK_modif_config,
    NPanel_editor.STK_config_file1,
    NPanel_editor.STK_config_file2,
    node.node,
    battle_info.STK_battle,
    capture_flag_info.STK_capture_flag,
    cli.STK_cli,
    cutscene_info.STK_cut_scene,
    demo_info.STK_demo_mode,
    egg_info.STK_egg_paty,
    global_info.STK_global,
    graphic.STK_graphic,
    initial_info.STK_initial,
    initial_info.STK_Pick_Executable_Operator,
    initial_info.STK_Pick_TracksFolder_Operator,
    initial_info.STK_Pick_kartsFolder_Operator,
    leader_info.STK_leader,
    preview_info.STK_info,
    race_info.STK_race,
    runner.STK_run,
    runner.STK_OT_RunStk,
    soccer_info.STK_soccer,
    time_trial.STK_time_trial,
    windows.STK_windows,
    controller.STK_debug_controller,
    kart.STK_debug_kart,
    other.STK_debug_other,
    track.STK_debug_track,
)

def add_stk_node_menu(self, context):
    if context.space_data.tree_type == editor.STKeditor.bl_idname:
        self.layout.menu(menu.STKdebug.bl_idname)
        self.layout.menu(menu.STKmenu.bl_idname)
        self.layout.menu(menu.STKoption.bl_idname)
        self.layout.menu(menu.STKrun.bl_idname)
        self.layout.menu(menu.STKexperimental.bl_idname)
        

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.NODE_MT_add.append(add_stk_node_menu)

def unregister():
    bpy.types.NODE_MT_add.remove(add_stk_node_menu)
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()