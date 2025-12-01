bl_info = {
    "name": "STK RUNNER",
    "author": "Ludérïck Le Saouter @LLS",
    "version": (1, 0),
    "blender": (2, 9, 0),
    "category": "Node",
    "description": "nodal editor test SuperTuxKart Project",
    "location": "Node Editor > STK Run Test",
}

import bpy
from io_antarctica_scene.stk_panel import STK_FolderPicker_Operator
from .base import (node_base, menu, node_editor)
from .node.init import (cli, init_stk)
from .node.run import (runner)

classes = (
    node_editor.STKeditor,
    menu.STKinit,
    menu.STKrun,
    menu.STKmode,
    menu.STKdebug,
    node_base.node,
    init_stk.STK_initial,
    init_stk.STK_Pick_Executable_Operator,
    init_stk.STK_Pick_TracksFolder_Operator,
    init_stk.STK_Pick_kartsFolder_Operator,
    cli.STK_cli,
    runner.STK_run,
    runner.STK_OT_RunStk,
)

def add_stk_node_menu(self, context):
    if context.space_data.tree_type == node_editor.STKeditor.bl_idname:
        self.layout.menu(menu.STKinit.bl_idname)
        self.layout.menu(menu.STKrun.bl_idname)
        self.layout.menu(menu.STKmode.bl_idname)
        self.layout.menu(menu.STKdebug.bl_idname)
        

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