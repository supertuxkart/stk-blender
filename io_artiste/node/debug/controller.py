import bpy
from ...base.node import node

class STK_debug_controller(node):
    bl_idname = 'STK_Debug_Control'
    bl_label = 'Debug Controller'
    bl_icon = 'NONE'

    entrer: bpy.props.StringProperty(name="input", default="")
    sortie: bpy.props.StringProperty(name="output", default="")

    visual_manette: bpy.props.BoolProperty(name="visual", default=False, update=lambda self, context: self.update())
    BOOL_clavier: bpy.props.BoolProperty(name="Keyboard", default=False, update=lambda self, context: self.update())
    BOOL_wii: bpy.props.BoolProperty(name="WiiMote", default=False, update=lambda self, context: self.update())
    BOOL_manette: bpy.props.BoolProperty(name="Gamepad", default=False, update=lambda self, context: self.update())
    debug_clavier: bpy.props.BoolProperty(name="debug", default=False, update=lambda self, context: self.update())
    debug_manette: bpy.props.BoolProperty(name="debug", default=False, update=lambda self, context: self.update())
    debug_wiimote: bpy.props.BoolProperty(name="debug", default=False, update=lambda self, context: self.update())
    clavier: bpy.props.IntProperty(name="ID", default=0, min=0, update=lambda self, context: self.update())
    manette: bpy.props.IntProperty(name="ID", default=0, min=0, update=lambda self, context: self.update())

    def init(self, context):
        self.node_entrer("NodeSocketString", "input_0", "", "")
        self.node_sortie('NodeSocketString', 'output_0', '', "")

    def draw_buttons(self, context, layout):
        layout.prop(self, "BOOL_clavier")
        if self.BOOL_clavier != False:
            box = layout.box()
            box.prop(self, "clavier")
            box.prop(self, "debug_clavier")
        
        layout.prop(self, "BOOL_manette")
        if self.BOOL_manette != False:
            box = layout.box()
            box.prop(self, "manette")
            box.prop(self, "debug_manette")
            box.prop(self, "visual_manette")
            box = layout.box()
            box.prop(self, "BOOL_wii")
            if self.BOOL_wii != False:
                box.prop(self, "debug_wiimote")

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
            
            if self.BOOL_clavier != False:
                self.sortie += f" --use-keyboard={self.clavier}"
                if self.debug_clavier != False:
                    self.sortie += f" --keyboard-debug"
            if self.BOOL_manette != False:
                self.sortie += f" --use-gamepad={self.manette}"
                if self.debug_manette != False:
                    self.sortie += f" --gamepad-debug"
                if self.visual_manette != False:
                    self.sortie += f" --gamepad-visuals"
                if self.BOOL_wii != False:
                    self.sortie += f" --wii"
                    if self.debug_wiimote != False:
                        self.sortie += f" --wiimote-debug"
            self.outputs[0].default_value = str(self.sortie)
        return self.sortie

    def update(self):
        self.process(bpy.context, None, None)