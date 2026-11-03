import bpy

from ...base.node_base import node


class STK_direct_run(node):
    bl_idname = 'STK_Direct_Run'
    bl_label = 'Direct Run'
    bl_icon = 'NONE'

    race_now: bpy.props.BoolProperty(name="Race Now", default=False, update=lambda self, context: self.update())
    start_screen: bpy.props.BoolProperty(name="No Start Screen", default=False,
                                         update=lambda self, context: self.update())

    def init(self, context):
        self.node_input("NodeSocketString", "input_0", "", "")
        self.node_output('NodeSocketString', 'output_0', '', "")

    def draw_buttons(self, context, layout):
        ligne = layout.box()
        ligne.prop(self, "race_now")
        ligne.prop(self, "start_screen")

    def process(self, context, id, path):
        # Check for input socket linked status and retrieve the value
        self.s_input = node.process(self, context, id, path)

        # Build the complete instruction with the input and properties
        if len(self.outputs) > 0 and hasattr(self.outputs[0], "default_value"): 
            self.s_output = ""
            if self.s_input != "":
                self.s_output += self.s_input + " "
            
            if self.start_screen: self.s_output += f" --no-start-screen"
            if self.race_now: self.s_output += f" --race-now"

            self.outputs[0].default_value = str(self.s_output)
        return self.s_output

    def update(self):
        self.process(bpy.context, None, None)