import bpy
from ...base.node_base import node


class STK_battle(node):
    bl_idname = 'STK_Battle'
    bl_label = 'Battle'
    bl_icon = 'NONE'

    s_input: bpy.props.StringProperty(name="input", default="")
    s_output: bpy.props.StringProperty(name="output", default="")

    num_kart: bpy.props.IntProperty(
        name="N_karts",
        default=3, 
        min=1, 
        max=20, 
        update=lambda self, context: self.update())

    choise_kart: bpy.props.StringProperty(
        name="Kart User",
        description="Select a kart",
        default="tux",
        update=lambda self, context: self.update())
    
    choise_track: bpy.props.StringProperty(
        name="Track Choice",
        description="Select a track",
        default="stadium",
        update=lambda self, context: self.update())
    
    battle_type: bpy.props.BoolProperty(name="time/live", default=False, update=lambda self, context: self.update())

    def init(self, context):
        self.node_input("NodeSocketString", 'Battle', 'battle', "")
        self.node_output('NodeSocketString', 'Battle', 'battle', "")

    def draw_buttons(self, context, layout):
        ligne = layout.row()
        ligne.prop(self, "num_kart")
        #ligne.prop(self, "battle_type")

        ligne = layout.row()
        ligne.prop(self, "choise_track")

        ligne = layout.row()
        ligne.prop(self, "choise_kart")

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
                            self.s_input = str(value)
                        except:
                            pass

                    # If that fails, try to get the default_value
                    if hasattr(from_socket, "default_value"):
                        self.s_input = str(from_socket.default_value)
            else:
                self.s_input = ""

        # Build the complete instruction with the input and properties
        if len(self.outputs) > 0 and hasattr(self.outputs[0], "default_value"):
            self.s_output = ""
            if self.s_input != "":
                self.s_output += self.s_input + " "

            self.s_output += f"--numkarts={self.num_kart}"
            self.s_output += f" --track={self.choise_track}"
            self.s_output += f" --kart={self.choise_kart}"
            self.s_output += f" --mode=2"

            self.outputs[0].default_value = str(self.s_output)
        return self.s_output

    def update(self):
        self.process(bpy.context, None, None)