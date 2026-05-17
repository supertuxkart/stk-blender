import bpy
from .node_editor import STKeditor

class node(bpy.types.Node):
    bl_idname = 'STK_node'
    bl_label = 'STK Node'
    bl_icon = 'INFO'

    # check good space editor
    @classmethod
    def poll(cls, node_tree):
        return node_tree.bl_idname == STKeditor.bl_idname

    # initialisation node
    def node_input(self, type_node, name, label, value=None):
        socket = self.inputs.new(type_node, label)
        if value is not None and hasattr(socket, "default_value"):
            socket.default_value = value
        return socket
    
    def del_node_input(self, name):
        if self.inputs.get(name): self.inputs.remove(self.inputs[name])
    
    def node_output(self, type_node, name, label, value=None):
        socket = self.outputs.new(type_node, label)
        if value is not None and hasattr(socket, "default_value"):
            socket.default_value = value
        return socket
    
    def del_node_output(self, name):
        if self.outputs.get(name): self.outputs.remove(self.outputs[name])
    # =========================
    def draw_buttons(self, context, layout):
        pass

    def copy(self, node):
        if self.bl_idname:
            self.label = self.name
        print(f"Copy {self.name} too {node.name}")

    def free(self):  # Delete node
        print(f"remove node {self.name}")
    
    def process(self, context, id, path):
        pass
    
    def process_group(self, context, id, path):
        pass

    def update_value_node(self, context):
        for output in self.outputs:
            for link in output.links:
                if hasattr(link.to_node, "update"):
                    link.to_node.update()
        if context and context.space_data:
            context.space_data.node_tree.update()

    def update(self):
        self.update_value_node(bpy.context)