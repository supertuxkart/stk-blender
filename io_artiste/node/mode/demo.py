import bpy

from ...base.node_base import node


class STK_demo(node):
    bl_idname = 'STK_demo'
    bl_label = 'Demo'
    bl_icon = 'NONE'

    times: bpy.props.IntProperty(name="start", default=60, min=1, update=lambda self, context: self.update())
    tracks: bpy.props.StringProperty(name="track", default="hacienda", update=lambda self, context: self.update())
    laps: bpy.props.IntProperty(name="laps", default=3, min=1, update=lambda self, context: self.update())
    karts: bpy.props.IntProperty(name="Karts", default=4, min=0, max=20, update=lambda self, context: self.update())

    def init(self, context):
        self.node_input("NodeSocketString", "input_0", "", "")
        self.node_output("NodeSocketString", "output_0", "", "")

    def draw_buttons(self, context, layout):
        layout.prop(self, "times")
        layout.prop(self, "tracks")
        layout.prop(self, "laps")
        layout.prop(self, "karts")

    def process(self, context, id, path):
        # Check for input socket linked status and retrieve the value
        self.s_input = node.process(self, context, id, path)

        # Build the complete instruction with the input and properties
        if len(self.outputs) > 0 and hasattr(self.outputs[0], "default_value"): 
            self.s_output = ""
            if self.s_input != "":
                self.s_output += self.s_input + " "
            self.s_output += f"--demo-mode={self.times} --demo-tracks={self.tracks} --demo-laps={self.laps} --demo-karts={self.karts}"
            self.outputs[0].default_value = self.s_output
        return self.s_output


    def update(self):
        self.process(bpy.context, None, None)