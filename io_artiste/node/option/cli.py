import bpy
from ...base.node import node

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
        # Check for input socket existence
        if len(self.inputs) > 0:
            input_socket = self.inputs[0]
            
            if input_socket.is_linked:
                links = input_socket.links
                if links:
                    from_socket = links[0].from_socket
                    from_node = links[0].from_node
                    
                    # Try to get the value via the source node's process method first
                    if hasattr(from_node, "process"):
                        try:
                            value = from_node.process(context, id, path)
                            self.entrer = str(value)
                        except:
                            pass
                    
                    # If that fails, try to get the default_value
                    if hasattr(from_socket, "default_value"):
                        self.entrer = str(from_socket.default_value)
            else:
                self.entrer = ""
        
        # Build the complete instruction with the input and properties
        if len(self.outputs) > 0 and hasattr(self.outputs[0], "default_value"):
            instruction = ""
            if self.entrer != "":
                # Add a space if the input doesn't end with one
                if not self.entrer.endswith(" "):
                    instruction += self.entrer + " "
                else:
                    instruction += self.entrer
            instruction += f"{self.cli}"
            self.outputs[0].default_value = instruction
            return instruction
        
        return self.entrer

    def update(self):
        """Called when the node needs to be updated"""
        self.process(bpy.context, None, None)