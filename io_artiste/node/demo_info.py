import bpy
from ..base.node import node

class STK_demo_mode(node):
    bl_idname = 'STK_mode_demo'
    bl_label = 'Demo Mode'
    bl_icon = 'NONE'

    entrer: bpy.props.StringProperty(name="input", default="")
    sortie: bpy.props.StringProperty(name="output", default="")

    times: bpy.props.IntProperty(name="start", default=60, min=1, update=lambda self, context: self.update())
    tracks: bpy.props.StringProperty(name="track", default="hacienda", update=lambda self, context: self.update())
    laps: bpy.props.IntProperty(name="laps", default=3, min=1, update=lambda self, context: self.update())
    karts: bpy.props.IntProperty(name="Karts", default=4, min=0, max=20, update=lambda self, context: self.update())

    def init(self, context):
        self.node_entrer("NodeSocketString", "input_0", "", "")
        self.node_sortie("NodeSocketString", "output_0", "", "")

    def draw_buttons(self, context, layout):
        layout.prop(self, "times")
        layout.prop(self, "tracks")
        layout.prop(self, "laps")
        layout.prop(self, "karts")

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
                instruction += self.entrer + " "
            instruction += f"--demo-mode={self.times} --demo-tracks={self.tracks} --demo-laps={self.laps} --demo-karts={self.karts}"
            self.outputs[0].default_value = instruction
            return instruction
        
        return self.entrer

    def update(self):
        """Called when the node needs to be updated"""
        self.process(bpy.context, None, None)