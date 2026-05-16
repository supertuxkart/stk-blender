import bpy
from ..node.init import (cli, init_stk)
from ..node.run import (runner, preview_cmd)

class STKoperator(bpy.types.Menu):
    bl_idname = 'NODE_MT_STK_Operator'
    bl_label = 'STK OPERATOR'

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_DEFAULT'
        layout.operator("node.add_node", text=init_stk.STK_initial.bl_label).type = init_stk.STK_initial.bl_idname
        layout.operator("node.add_node", text=runner.STK_run.bl_label).type = runner.STK_run.bl_idname
        layout.operator("node.add_node", text=cli.STK_cli.bl_label).type = cli.STK_cli.bl_idname

class STKmode(bpy.types.Menu):
    bl_idname = 'NODE_MT_STK_mode'
    bl_label = 'STK MODE'

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_DEFAULT'
            

class STKdebug(bpy.types.Menu):
    bl_idname = 'NODE_MT_STK_debug'
    bl_label = 'STK DEBUG'
    
    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_DEFAULT'
        layout.operator("node.add_node", text=preview_cmd.STK_preview_cmd.bl_label).type = preview_cmd.STK_preview_cmd.bl_idname
