import bpy
from ...base.node_base import node

class STK_cli(node):
    bl_idname = 'STK_cli'
    bl_label = 'CLI'
    bl_icon = 'NONE'

    s_input: bpy.props.StringProperty(name="input", default="")
    s_output: bpy.props.StringProperty(name="output", default="")

    cli: bpy.props.StringProperty(name="CLI", default="", update=lambda self, context: self.update())

    def init(self, context):
        self.node_input("NodeSocketString", "input_0", "", "")
        self.node_output("NodeSocketString", "output_0", "", "")

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
                            self.s_input = str(value)
                        except: pass
                    
                    # If that fails, try to get the default_value
                    if hasattr(from_socket, "default_value"):
                        self.s_input = str(from_socket.default_value)
            else:
                self.s_input = ""
        
        # Build the complete instruction with the input and properties
        if len(self.outputs) > 0 and hasattr(self.outputs[0], "default_value"):
            self.s_output = ""
            if self.s_input != "":
                # Add a space if the input doesn't end with one
                if not self.s_input.endswith(" "):
                    self.s_output += self.s_input + " "
                else:
                    self.s_output += self.s_input
            self.s_output += f"{self.cli}"
            self.outputs[0].default_value = self.s_output
        return self.s_output

    def update(self):
        """Called when the node needs to be updated"""
        self.process(bpy.context, None, None)