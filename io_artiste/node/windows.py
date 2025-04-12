import bpy
from ..base.node import node

class STK_windows(node):
    bl_idname = 'STK_Windows'
    bl_label = 'Windows'
    bl_icon = 'WINDOW'

    entrer: bpy.props.StringProperty(name="input", default="")
    sortie: bpy.props.StringProperty(name="output", default="")

    win_largeur: bpy.props.IntProperty(name="width", update=lambda self, context: self.update())
    win_hauteur: bpy.props.IntProperty(name="height", update=lambda self, context: self.update())

    plein_ecran: bpy.props.BoolProperty(name="fullscreen", default=False, update=lambda self, context: self.update())

    win_size: bpy.props.EnumProperty(
        name="Win Size",
        items=[
            ("800x600", "800x600", "", "SCREEN", 0),
            ("1024x768", "1024x768", "", "SCREEN", 1),
            ("1280x720", "1280x720", "", "SCREEN", 2),
            ("1280x1024", "1280x1024", "", "SCREEN", 3),
            ("1440x900", "1440x900", "", "SCREEN", 4),
            ("1680x1050", "1680x1050", "", "SCREEN", 5),
            ("1920x1080", "1920x1080", "", "SCREEN", 6),
            ("custom", "Custom", "", "SCREEN", 7)
        ],
        default="custom", update=lambda self, context: self.update())

    def init(self, context):
        self.node_entrer("NodeSocketString", "input_0", "", "")
        self.node_sortie('NodeSocketString', 'output_0', '', "")

    def draw_buttons(self, context, layout):
        layout.prop(self, "plein_ecran")
        layout.prop(self, "win_size")
        ligne = layout.row()
        if self.win_size == "custom":
            ligne.prop(self, "win_largeur")
            ligne.prop(self, "win_hauteur")

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
            
            if self.plein_ecran == True: self.sortie += f"--fullscreen"
            else: self.sortie += f"--windowed"
            if self.win_size == "custom":
                self.sortie += f" --screensize={self.win_largeur}x{self.win_hauteur}"
            else:
                self.sortie += f" --screensize={self.win_size}"
                
            self.outputs[0].default_value = str(self.sortie)
        return self.sortie

    def update(self):
        self.process(bpy.context, None, None)