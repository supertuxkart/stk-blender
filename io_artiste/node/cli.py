import bpy
from ..base.node import node

class STK_cli(node):
    bl_idname = 'STK_cli'
    bl_label = 'CLI'
    bl_icon = 'NONE'

    entrer: bpy.props.StringProperty(name="input", default="")
    sortie: bpy.props.StringProperty(name="output", default="")

    cli: bpy.props.StringProperty(name="CLI", default="", update=lambda self, context: self.update())

    def init(self, context):
        self.node_entrer("NodeSocketString", "input_0", "", "")
        self.node_sortie("NodeSocketString", "output_0", "", "")

    def draw_buttons(self, context, layout):
        layout.prop(self, "cli")

    def process(self, context, id, path):
        # Vérifier l'existence du socket d'entrée
        if len(self.inputs) > 0:
            input_socket = self.inputs[0]
            
            if input_socket.is_linked:
                links = input_socket.links
                if links:
                    from_socket = links[0].from_socket
                    from_node = links[0].from_node
                    
                    # Essaie d'abord d'obtenir la valeur via process du nœud source
                    if hasattr(from_node, "process"):
                        try:
                            value = from_node.process(context, id, path)
                            self.entrer = str(value)
                        except:
                            pass
                    
                    # Si ça ne marche pas, essaie d'obtenir la default_value
                    if hasattr(from_socket, "default_value"):
                        self.entrer = str(from_socket.default_value)
            else:
                self.entrer = ""
        
        # Construire l'instruction complète avec l'entrée et les propriétés
        if len(self.outputs) > 0 and hasattr(self.outputs[0], "default_value"):
            instruction = ""
            if self.entrer != "":
                instruction += self.entrer + " "
            instruction += f"{self.cli}"
            self.outputs[0].default_value = instruction
            return instruction
        
        return self.entrer

    def update(self):
        """Appelé quand le nœud doit être mis à jour"""
        self.process(bpy.context, None, None)