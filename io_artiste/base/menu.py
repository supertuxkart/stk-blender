import bpy
from ..node.debug import (direct_run)
from ..node.init import (cli, init_stk)
from ..node.run import (runner, preview_cmd)
from ..node.mode import (demo, game_mode)


class STKmenu(bpy.types.Menu):
    bl_idname = 'NODE_MT_STK_Menu'
    bl_label = 'STK Node'

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_DEFAULT'
        layout.label(text="Operator")
        layout.operator("node.add_node", text=init_stk.STK_initial.bl_label).type = init_stk.STK_initial.bl_idname
        layout.operator("node.add_node", text=runner.STK_run.bl_label).type = runner.STK_run.bl_idname
        layout.operator("node.add_node", text=cli.STK_cli.bl_label).type = cli.STK_cli.bl_idname
        layout.operator("node.add_node", text=direct_run.STK_direct_run.bl_label).type = direct_run.STK_direct_run.bl_idname
        layout.separator()
        layout.label(text="Mode")
        layout.operator("node.add_node", text=demo.STK_demo.bl_label).type = demo.STK_demo.bl_idname
        layout.operator("node.add_node", text=game_mode.STK_game_mode.bl_label).type = game_mode.STK_game_mode.bl_idname
        layout.separator()
        layout.label(text="Debug")
        layout.operator("node.add_node", text=preview_cmd.STK_preview_cmd.bl_label).type = preview_cmd.STK_preview_cmd.bl_idname
