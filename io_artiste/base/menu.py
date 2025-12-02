import bpy
from ..node.init import (cli, init_stk)
from ..node.run import (runner)

class STKinit(bpy.types.Menu):
    bl_idname = 'NODE_MT_STK_Init'
    bl_label = 'STK INIT'

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_DEFAULT'
        layout.operator("node.add_node", text=cli.STK_cli.bl_label).type = cli.STK_cli.bl_idname
        layout.operator("node.add_node", text=init_stk.STK_initial.bl_label).type = init_stk.STK_initial.bl_idname

class STKmode(bpy.types.Menu):
    bl_idname = 'NODE_MT_STK_mode'
    bl_label = 'STK MODE'

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_DEFAULT'
            
class STKrun(bpy.types.Menu):
    bl_idname = 'NODE_MT_STK_run'
    bl_label = 'STK RUN'

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_DEFAULT'
        layout.operator("node.add_node", text=runner.STK_run.bl_label).type = runner.STK_run.bl_idname
        
class STKdebug(bpy.types.Menu):
    bl_idname = 'NODE_MT_STK_debug'
    bl_label = 'STK DEBUG'
    
    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_DEFAULT'
        
# TODO
# add nodes 
# menu: Mode, Init, Run, Debug

## INIT
# Initial
# CLI
# Demo Mode
# Graphic
# Windows

## MODE
# Race
# Battle
# Capture Flag
# Cutscene
# Leader
# Soccer
# Time Trial
# Egg Party

## RUN
# Run
# Preview Info

## DEBUG
# Controller
# Graphique
# Kart
# Other
# Track