import bpy
from ..base.node import node

class STK_capture_flag(node):
    bl_idname = 'STK_flag_capture'
    bl_label = 'Capture Flag'
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
            ("abyss", "Abyss", "Race track", "", 0),
            ("alien_signal", "Alien Signal", "Battle track", "", 1),
            ("ancient_colosseum_labyrinth", "Ancient Colosseum Labyrinth", "Battle track", "", 2),
            ("arena_candela_city", "Arena Candela City", "Battle track", "", 3),
            ("battleisland", "Battle Island", "Battle track", "", 4),
            ("black_forest", "Black Forest", "Race track", "", 5),
            ("candela_city", "Candela City", "Race track", "", 6),
            ("cave", "Cave", "Battle track", "", 7),
            ("cocoa_temple", "Cocoa Temple", "Race track", "", 8),
            ("cornfiel_crossing", "Cornfield Crossing", "Race track", "", 9),
            ("fortmagma", "Fort Magma", "Race track", "", 10),
            ("gran_paradiso_island", "Gran Paradiso Island", "Race track", "", 11),
            ("hacienda", "Hacienda", "Race track", "", 12),
            ("hole_drop", "Hole Drop", "Soccer track", "", 13),
            ("icy_soccer_field", "Icy Soccer Field", "Soccer track", "", 14),
            ("lasdunasarena", "Las Dunas Arena", "Battle track", "", 15),
            ("lasdunassoccer", "Las Dunas Soccer", "Soccer track", "", 16),
            ("lighthouse", "Light House", "Race track", "", 17),
            ("mines", "Mines", "Race track", "", 18),
            ("minigolf", "Mini Golf", "Race track", "", 19),
            ("oasis", "Oasis", "Soccer track", "", 20),
            ("olivermath", "Oliver Math", "Race track", "", 21),
            ("pumpkin_park", "Pumpkin Park", "Battle track", "", 22),
            ("ravenbridge_mansion", "Ravenbridge Mansion", "Race track", "", 23),
            ("sandtrack", "Sand Track", "Race track", "", 24),
            ("scotland", "Scotland", "Race track", "", 25),
            ("snowmountain", "Snow Mountain", "Race track", "", 26),
            ("snowtuxpeak", "Snow Tux Peak", "Race track", "", 27),
            ("soccer_field", "Soccer Field", "Soccer track", "", 28),
            ("stadium", "Stadium", "Battle track", "", 29),
            ("stk_entreprise", "STK Entreprise", "Race track", "", 30),
            ("temple", "Temple", "Battle track", "", 31),
            ("volcano_island", "Volcano Island", "Race track", "", 32),
            ("xr591", "XR591", "Race track", "", 33),
            ("zengarden", "Zen Garden", "Race track", "", 34),
            ("custom", "Custom", "Custom Track", "", 35)
        ],
        default="custom",
        update=lambda self, context: self.update()
    )

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

            self.sortie += f" --mode=5"
            self.outputs[0].default_value = str(self.sortie)
        return self.sortie

    def update(self):
        self.process(bpy.context, None, None)