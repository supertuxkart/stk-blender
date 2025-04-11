import bpy
from ..base.node import node

class STK_global(node):
    bl_idname = 'STK_global'
    bl_label = 'Global Info'
    bl_icon = 'NONE'

    def init(self, context):
        pass

    def draw_buttons(self, context, layout):
        pass

    def process(self, context, id, path):
        pass

    def update(self):
        pass