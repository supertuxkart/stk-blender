import bpy
from ..base.node import node

class STK_race(node):
    bl_idname = 'STK_Race'
    bl_label = 'Racing'
    bl_icon = 'NONE'

    entrer: bpy.props.StringProperty(name="input", default="")
    sortie: bpy.props.StringProperty(name="Race data", default="")

    num_kart: bpy.props.IntProperty(
        name="Number of karts",
        default=3,
        min=0,
        max=20,
        update=lambda self, context: self.update())
    
    laps: bpy.props.IntProperty(
        name="Number of lap",
        description="Number of lap for the race",
        default=1,
        min=1,
        max=20,
        update=lambda self, context: self.update())
    
    choix_kart: bpy.props.EnumProperty(
        name="Kart User",
        description="Select a kart",
        items=[
            ("adiumy", "Adiumy", "", "", 0),
            ("amanda", "Amanda", "", "", 1),
            ("beastie", "Beastie", "", "", 2),
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
            ("black_forest", "Black Forest", "Race track", "", 1),
            ("candela_city", "Candela City", "Race track", "", 2),
            ("cocoa_temple", "Cocoa Temple", "Race track", "", 3),
            ("cornfiel_crossing", "Cornfield Crossing", "Race track", "", 4),
            ("fortmagma", "Fort Magma", "Race track", "", 5),
            ("gran_paradiso_island", "Gran Paradiso Island", "Race track", "", 6),
            ("hacienda", "Hacienda", "Race track", "", 7),
            ("lighthouse", "Light House", "Race track", "", 8),
            ("mines", "Mines", "Race track", "", 9),
            ("minigolf", "Mini Golf", "Race track", "", 10),
            ("olivermath", "Oliver Math", "Race track", "", 11),
            ("ravenbridge_mansion", "Ravenbridge Mansion", "Race track", "", 12),
            ("sandtrack", "Sand Track", "Race track", "", 13),
            ("scotland", "Scotland", "Race track", "", 14),
            ("snowmountain", "Snow Mountain", "Race track", "", 15),
            ("snowtuxpeak", "Snow Tux Peak", "Race track", "", 16),
            ("stk_entreprise", "STK Entreprise", "Race track", "", 17),
            ("volcano_island", "Volcano Island", "Race track", "", 18),
            ("xr591", "XR591", "Race track", "", 19),
            ("zengarden", "Zen Garden", "Race track", "", 20),
            ("custom", "Custom", "Custom Track", "", 21)
        ],
        default="custom",
        update=lambda self, context: self.update()
    )

    custom_track: bpy.props.StringProperty(name="Other track", default="", update=lambda self, context: self.update())
    custom_kart: bpy.props.StringProperty(name="Other kart", default="", update=lambda self, context: self.update())
    reverse: bpy.props.BoolProperty(name="Reverse Track", default=False, update=lambda self, context: self.update())

    def init(self, context):
        self.node_entrer("NodeSocketString", "input_0", "", "")
        self.node_sortie('NodeSocketString', 'Race', 'race', "")

    def draw_buttons(self, context, layout):
        ligne = layout.row()
        ligne.prop(self, "reverse")
        ligne.prop(self, "num_kart")
        ligne.prop(self, "laps")

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
            self.sortie += f"--numkarts={self.num_kart} --laps={self.laps}"
            if self.choix_track != "custom":
                self.sortie += f" --track={self.choix_track}"
            else:
                self.sortie += f" --track={self.custom_track}"
            if self.choix_kart != "custom":
                self.sortie += f" --kart={self.choix_kart}"
            else:
                self.sortie += f" --kart={self.custom_kart}"
            if self.reverse != False:
                self.sortie += f" --reverse"
            self.sortie += f" --mode=0"
            self.outputs[0].default_value = str(self.sortie)
        return self.sortie

    def update(self):
        self.process(bpy.context, None, None)