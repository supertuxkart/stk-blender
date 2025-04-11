import bpy
from .editor import STKeditor

class node(bpy.types.Node):
    bl_idname = 'CustomNodeType'
    bl_label = 'Custom Node'
    bl_icon = 'INFO'

    @classmethod
    def poll(cls, node_tree):
        return node_tree.bl_idname == STKeditor.bl_idname

    # initialisation du Node
    def node_entrer(self, type_node, nom, label, valeur=None):
        socket = self.inputs.new(type_node, label)
        if valeur is not None and hasattr(socket, "default_value"):
            socket.default_value = valeur
        return socket
    
    def supr_node_entrer(self, nom):
        if self.inputs.get(nom): self.inputs.remove(self.inputs[nom])
    
    def node_sortie(self, type_node, nom, label, valeur=None):
        socket = self.outputs.new(type_node, label)
        if valeur is not None and hasattr(socket, "default_value"):
            socket.default_value = valeur
        return socket
    
    def supr_node_sortie(self, nom):
        if self.outputs.get(nom): self.outputs.remove(self.outputs[nom])
    # =========================

    def draw_buttons(self, context, layout):
        pass

    def copy(self, node):
        if self.bl_idname:
            self.label = self.name
        print(f"Copie de {self.name} vers {node.name}")

    def free(self):  # Suppression du node
        print(f"Suppression du node {self.name}")
    
    def process(self, context, id, path):
        pass
    
    def process_group(self, context, id, path):
        pass

    def update_value_node(self, context):
        """Gestion des mises à jour"""
        for output in self.outputs:
            for link in output.links:
                if hasattr(link.to_node, "update"):
                    link.to_node.update()
        if context and context.space_data:
            context.space_data.node_tree.update()

    def update(self):
        self.update_value_node(bpy.context)