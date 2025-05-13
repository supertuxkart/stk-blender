import bpy
from ...base.node import node

class STK_battle(node):
    bl_idname = 'STK_Battle'
    bl_label = 'Battle'
    bl_icon = 'NONE'

    entrer: bpy.props.StringProperty(name="input", default="")
    sortie: bpy.props.StringProperty(name="output", default="")

    num_kart_custom: bpy.props.IntProperty(
        name="N_karts",
        default=3, min=1, max=30, update=lambda self, context: self.update())
    num_kart_10: bpy.props.IntProperty(
        name="N_karts",
        default=3, min=1, max=10, update=lambda self, context: self.update())
    num_kart_6: bpy.props.IntProperty(
        name="N_karts",
        default=3, min=1, max=6, update=lambda self, context: self.update())
    num_kart_4: bpy.props.IntProperty(
        name="N_karts",
        default=3, min=1, max=4, update=lambda self, context: self.update())
    
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
            ("alien_signal", "Alien Signal", "Battle track", "", 0),
            ("ancient_colosseum_labyrinth", "Ancient Colosseum Labyrinth", "Battle track", "", 1),
            ("arena_candela_city", "Arena Candela City", "Battle track", "", 2),
            ("battleisland", "Battle Island", "Battle track", "", 3),
            ("cave", "Cave", "Battle track", "", 4),
            ("lasdunasarena", "Las Dunas Arena", "Battle track", "", 5),
            ("pumpkin_park", "Pumpkin Park", "", "Battle track", 6),
            ("stadium", "Stadium", "Battle track", "", 7),
            ("temple", "Temple", "Battle track", "", 8),
            ("custom", "Custom", "Custom Track", "", 9)
        ],
        default="custom",
        update=lambda self, context: self.update()
    )

    custom_track: bpy.props.StringProperty(name="Other track", default="", update=lambda self, context: self.update())
    custom_kart: bpy.props.StringProperty(name="Other kart", default="", update=lambda self, context: self.update())

    def init(self, context):
        self.node_entrer("NodeSocketString", "input_0", "", "")
        self.node_sortie('NodeSocketString', 'Battle', 'battle', "")

    def draw_buttons(self, context, layout):
        ligne = layout.row()
        if self.choix_track in {"alien_signal", "ancient_colosseum_labyrinth", "arena_candela_city", "lasdunasarena", "pumpkin_park", "stadium", "temple"}:
            ligne.prop(self, "num_kart_10")
        elif self.choix_track in {"battleisland"}: ligne.prop(self, "num_kart_6")
        elif self.choix_track in {"cave"}: ligne.prop(self, "num_kart_4")
        else: ligne.prop(self, "num_kart_custom")
        
    
        ligne = layout.row()
        ligne.prop(self, "choix_track")
        if self.choix_track == "custom":
            ligne.prop(self, "custom_track")
        
        ligne = layout.row()
        ligne.prop(self, "choix_kart")
        if self.choix_kart == "custom":
            ligne.prop(self, "custom_kart") 
        

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

            if self.choix_track in {"alien_signal", "ancient_colosseum_labyrinth", "arena_candela_city", "lasdunasarena", "pumpkin_park", "stadium", "temple"}:
                self.sortie += f"--numkarts={self.num_kart_10}"
            elif self.choix_track in {"battleisland"}: self.sortie += f"--numkarts={self.num_kart_6}"
            elif self.choix_track in {"cave"}: self.sortie += f"--numkarts={self.num_kart_4}"
            else: self.sortie += f"--numkarts={self.num_kart_custom}"

            if self.choix_track != "custom":
                self.sortie += f" --track={self.choix_track}"
            else:
                self.sortie += f" --track={self.custom_track}"
            if self.choix_kart != "custom":
                self.sortie += f" --kart={self.choix_kart}"
            else:
                self.sortie += f" --kart={self.custom_kart}"
            self.sortie += f" --mode=2"
            self.outputs[0].default_value = str(self.sortie)
        return self.sortie

    def update(self):
        self.process(bpy.context, None, None)