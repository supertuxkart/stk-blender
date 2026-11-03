import bpy
from ...base.node_base import node

class STK_cli(node):
    bl_idname = 'STK_cli'
    bl_label = 'CLI'
    bl_icon = 'NONE'

    cli: bpy.props.StringProperty(name="CLI", default="", update=lambda self, context: self.update())

    def init(self, context):
        self.node_input("NodeSocketString", "input_0", "", "")
        self.node_output("NodeSocketString", "output_0", "", "")

    def draw_buttons(self, context, layout):
        layout.prop(self, "cli")

    def process(self, context, id, path):
        # Check for input socket linked status and retrieve the value
        self.s_input = node.process(self, context, id, path)
        
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
        self.process(bpy.context, None, None)