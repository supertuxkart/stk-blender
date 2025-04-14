import bpy
from ...base.node import node

class STK_soccer(node):
    bl_idname = 'STK_Soccer'
    bl_label = 'Soccer'
    bl_icon = 'NONE'

    entrer: bpy.props.StringProperty(name="input", default="")
    sortie: bpy.props.StringProperty(name="output", default="")
    
    num_kart: bpy.props.IntProperty(
        name="N_karts",
        default=3, min=1, max=20, update=lambda self, context: self.update())
    
    choix_kart: bpy.props.EnumProperty(
        name="Kart User",
        description="Select a kart",
        items=[
            ("adiumy", "Adiumy", "", "", 0),
            ("amanda", "Amanda", "", "", 1),
            ("beastie", "Sophia", "", "", 2),
            ("emule", "Emule", "", "", 3),
            ("gavroche", "Gavroche", "", "", 4),
            ("gnu", "GNU", "", "", 5),
            ("hexley", "Hexley", "", "", 6),
            ("kiki", "Kiki", "", "", 7),
            ("konqi", "Konqi", "", "", 8),
            ("nolok", "Nolok", "", "", 9),
            ("pidgin", "Pidgin", "", "", 10),
            ("puffy", "Puffy", "", "", 11),
            ("sara_the_racer", "Pepper", "", "", 12),
            ("sara_the_wizard", "Sara", "", "", 13),
            ("suzanne", "Suzanne", "", "", 14),
            ("tux", "Tux", "", "", 15),
            ("wilber", "Wilber", "", "", 16),
            ("xue", "Xue", "", "", 17),
            ("custom", "Custom", "Custom Kart", "", 18)
        ],
        default="tux",
        update=lambda self, context: self.update()
    )
    choix_track: bpy.props.EnumProperty(
        name="Track Choice",
        description="Select a track",
        items=[
            ("hole_drop", "Hole Drop", "Soccer track", "", 0),
            ("icy_soccer_field", "Icy Soccer Field", "Soccer track", "", 1),
            ("lasdunassoccer", "Las Dunas Soccer", "Soccer track", "", 2),
            ("oasis", "Oasis", "Soccer track", "", 3),
            ("soccer_field", "Soccer Field", "Soccer track", "", 4),
            ("custom", "Custom", "Custom Track", "", 5)
        ],
        default="custom",
        update=lambda self, context: self.update()
    )

    time_limit: bpy.props.IntProperty(name="time limite(s)", description="time define in seconde", default=600, update=lambda self, context: self.update())
    custom_track: bpy.props.StringProperty(name="Other track", default="", update=lambda self, context: self.update())
    custom_kart: bpy.props.StringProperty(name="Other kart", default="", update=lambda self, context: self.update())

    def init(self, context):
        self.node_entrer("NodeSocketString", "input_0", "", "")
        self.node_sortie('NodeSocketString', 'output_0', '', "")

    def draw_buttons(self, context, layout):
        layout.prop(self, "num_kart")

        ligne = layout.row()
        ligne.prop(self, "choix_track")
        if self.choix_track == "custom":
            ligne.prop(self, "custom_track")
        
        ligne = layout.row()
        ligne.prop(self, "choix_kart")
        if self.choix_kart == "custom":
            ligne.prop(self, "custom_kart")
        
        ligne = layout.row()
        ligne.prop(self, "time_limit")

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
            
            self.sortie += f" --numkarts={self.num_kart}"

            if self.choix_track != "custom":
                self.sortie += f" --track={self.choix_track}"
            else:
                self.sortie += f" --track={self.custom_track}"

            if self.choix_kart != "custom":
                self.sortie += f" --kart={self.choix_kart}"
            else:
                self.sortie += f" --kart={self.custom_kart}"        

            self.sortie += f" --mode=3"
            self.outputs[0].default_value = str(self.sortie)
        return self.sortie

    def update(self):
        self.process(bpy.context, None, None)