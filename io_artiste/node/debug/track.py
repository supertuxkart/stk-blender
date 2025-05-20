import bpy
from ...base.node import node

class STK_debug_track(node):
    bl_idname = 'STK_Debug_Track'
    bl_label = 'Debug Track'
    bl_icon = 'NONE'

    entrer: bpy.props.StringProperty(name="input", default="")
    sortie: bpy.props.StringProperty(name="output", default="")

    debug_track: bpy.props.BoolProperty(name="track", default=False, update=lambda self, context: self.update())
    debug_check: bpy.props.BoolProperty(name="checkline", description="activate debug artiste", default=False, update=lambda self, context: self.update())

    def init(self, context):
        self.node_entrer("NodeSocketString", "input_0", "", "")
        self.node_sortie('NodeSocketString', 'output_0', '', "")

    def draw_buttons(self, context, layout):
        ligne = layout.row()
        ligne.prop(self, "debug_check")
        ligne.prop(self, "debug_track")

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
            self.sortie = ""
            if self.entrer != "":
                self.sortie += self.entrer + " "
            if self.debug_check != False:
                self.sortie += f" --check-debug"
            if self.debug_track != False:
                self.sortie += f" --track-debug"
            self.outputs[0].default_value = str(self.sortie)
        return self.sortie

    def update(self):
        self.process(bpy.context, None, None)