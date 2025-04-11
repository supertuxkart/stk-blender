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
        # Vérifier l'existence du socket d'entrée
        if len(self.inputs) > 0:
            input_socket = self.inputs[0]
            
            if input_socket.is_linked:
                links = input_socket.links
                if links:
                    from_socket = links[0].from_socket
                    from_node = links[0].from_node
                    
                    # Essaie d'abord d'obtenir la valeur via process du nœud source
                    if hasattr(from_node, "process"):
                        try:
                            value = from_node.process(context, id, path)
                            self.entrer = str(value)
                        except:
                            pass
                    
                    # Si ça ne marche pas, essaie d'obtenir la default_value
                    if hasattr(from_socket, "default_value"):
                        self.entrer = str(from_socket.default_value)
            else:
                self.entrer = ""
        
        # Construire l'instruction complète avec l'entrée et les propriétés
        if len(self.outputs) > 0 and hasattr(self.outputs[0], "default_value"):
            instruction = ""
            if self.entrer != "":
                instruction += self.entrer + " "
            instruction += f"--demo-mode={self.times} --demo-tracks={self.tracks} --demo-laps={self.laps} --demo-karts={self.karts}"
            self.outputs[0].default_value = instruction
            return instruction
        
        return self.entrer

    def update(self):
        """Appelé quand le nœud doit être mis à jour"""
        self.process(bpy.context, None, None)