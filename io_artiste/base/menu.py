import bpy
from ..node.mode import (
    battle_info, capture_flag_info,
    cutscene_info, leader_info, race_info,
    soccer_info, time_trial)
from ..node.option import (
    cli, demo_info, global_info,
    graphic, initial_info, windows)
from ..node.run import (preview_info, runner)
from ..node.experimental import (egg_info)

class STKmenu(bpy.types.Menu):
    bl_idname = 'NODE_MT_STK_mode'
    bl_label = 'STK MODE'

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_DEFAULT'
        #layout.operator("node.add_node", text=info.Info.bl_label).type = info.Info.bl_idname
        layout.operator("node.add_node", text=battle_info.STK_battle.bl_label).type = battle_info.STK_battle.bl_idname
        layout.operator("node.add_node", text=capture_flag_info.STK_capture_flag.bl_label).type = capture_flag_info.STK_capture_flag.bl_idname
        layout.operator("node.add_node", text=cutscene_info.STK_cut_scene.bl_label).type = cutscene_info.STK_cut_scene.bl_idname
        layout.operator("node.add_node", text=leader_info.STK_leader.bl_label).type = leader_info.STK_leader.bl_idname
        layout.operator("node.add_node", text=race_info.STK_race.bl_label).type = race_info.STK_race.bl_idname
        layout.operator("node.add_node", text=soccer_info.STK_soccer.bl_label).type = soccer_info.STK_soccer.bl_idname
        layout.operator("node.add_node", text=time_trial.STK_time_trial.bl_label).type = time_trial.STK_time_trial.bl_idname
        
class STKoption(bpy.types.Menu):
    bl_idname = 'NODE_MT_STK_option'
    bl_label = 'STK OPTION'

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_DEFAULT'
        layout.operator("node.add_node", text=cli.STK_cli.bl_label).type = cli.STK_cli.bl_idname
        layout.operator("node.add_node", text=demo_info.STK_demo_mode.bl_label).type = demo_info.STK_demo_mode.bl_idname
        layout.operator("node.add_node", text=global_info.STK_global.bl_label).type = global_info.STK_global.bl_idname
        layout.operator("node.add_node", text=graphic.STK_graphic.bl_label).type = graphic.STK_graphic.bl_idname
        layout.operator("node.add_node", text=initial_info.STK_initial.bl_label).type = initial_info.STK_initial.bl_idname
        layout.operator("node.add_node", text=windows.STK_windows.bl_label).type = windows.STK_windows.bl_idname

class STKrun(bpy.types.Menu):
    bl_idname = 'NODE_MT_STK_run'
    bl_label = 'STK RUN'

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_DEFAULT'
        layout.operator("node.add_node", text=runner.STK_run.bl_label).type = runner.STK_run.bl_idname
        layout.operator("node.add_node", text=preview_info.STK_info.bl_label).type = preview_info.STK_info.bl_idname

class STKexperimental(bpy.types.Menu):
    bl_idname = 'NODE_MT_STK_experiental'
    bl_label = 'STK EXPERIMENTAL'
    
    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_DEFAULT'
        layout.operator("node.add_node", text=egg_info.STK_egg_paty.bl_label).type = egg_info.STK_egg_paty.bl_idname
