import bpy

from ...base.node_base import node


class STK_game_mode(node):
    bl_idname = 'STK_Game_Mode'
    bl_label = 'Game Mode'
    bl_icon = 'NONE'

    mode_actif: bpy.props.StringProperty(name="mode_actif", default="")
    race_actif: bpy.props.StringProperty(name="race_actif", default="hacienda")
    battle_actif: bpy.props.StringProperty(name="battle_actif", default="stadium")
    soccer_actif: bpy.props.StringProperty(name="soccer_actif", default="icy_soccer_field")

    chosen_mode: bpy.props.EnumProperty(
        name="Game Mode",
        description="Select a game mode",
        items=[
            ("racing", "Racing", "", "", 0),
            ("battle", "Battle", "", "", 1),
            ("soccer", "Soccer", "", "", 2)
        ],
        default="racing",
        update=lambda self, context: self.update()
    )

    # parameter commun
    num_kart: bpy.props.IntProperty(
        name="n_karts", default=3,
        min=1, max=20,
        update=lambda self, context: self.update())

    chosen_kart: bpy.props.StringProperty(
        name="Kart User",
        description="Select a kart",
        default="tux",
        update=lambda self, context: self.update())

    chosen_track: bpy.props.StringProperty(
        name="Play Track",
        description="Select a track",
        default="",
        update=lambda self, context: self.update())

    # other parameter
    ## Racing
    reverse: bpy.props.BoolProperty(name="Reverse Track", default=False, update=lambda self, context: self.update())    
    laps: bpy.props.IntProperty(
            name="N_laps", description="Number of lap for the race",
            default=1, min=0, max=20,
            update=lambda self, context: self.update())
    ## Soccer
    time_limit: bpy.props.IntProperty(
        name="time limite(s)", description="time define in seconde", 
        default=600, update=lambda self, context: self.update())


    def init(self, context):
        self.node_input("NodeSocketString", "input_0", "", "")
        self.node_output('NodeSocketString', 'output_0', '', "")

    def draw_buttons(self, context, layout):
        layout.prop(self, "chosen_mode")
        
        layout.prop(self, "num_kart")
        layout.prop(self, "chosen_kart")
        layout.prop(self, "chosen_track")

        if self.chosen_mode == "racing":
            layout.prop(self, "laps")
        elif self.chosen_mode == "soccer":
            layout.prop(self, "time_limit")
        
    def process(self, context, id, path):
        # Check for input socket linked status and retrieve the value
        self.s_input = node.process(self, context, id, path)

        if self.mode_actif != self.chosen_mode:
            self.mode_actif = self.chosen_mode
            if self.chosen_mode == "racing":
                if self.chosen_track != self.race_actif:
                    self.chosen_track = self.race_actif
            elif self.chosen_mode == "battle":
                if self.chosen_track != self.battle_actif:
                    self.chosen_track = self.battle_actif
            elif self.chosen_mode == "soccer":
                if self.chosen_track != self.soccer_actif:
                    self.chosen_track = self.soccer_actif
        else:
            if self.chosen_mode == "racing" and self.chosen_track != self.race_actif:
                self.race_actif = self.chosen_track
            elif self.chosen_mode == "battle" and self.chosen_track != self.battle_actif:
                self.battle_actif = self.chosen_track
            elif self.chosen_mode == "soccer" and self.chosen_track != self.soccer_actif:
                self.soccer_actif = self.chosen_track

    
        # Build the complete instruction with the input and properties
        if len(self.outputs) > 0 and hasattr(self.outputs[0], "default_value"): 
            self.s_output = ""
            if self.s_input != "":
                self.s_output += self.s_input + " "

            self.s_output += f" --numkarts={self.num_kart} --track={self.chosen_track} --kart={self.chosen_kart}"

            if self.chosen_mode == "racing":
                if self.reverse != False:
                    self.s_output += f" --reverse"
                self.s_output += f" --laps={self.laps} --mode=0"
            elif self.chosen_mode == "battle":
                self.s_output += f" --mode=2"
            elif self.chosen_mode == "soccer":
                self.s_output += f" --time-limit={self.time_limit} --mode=3"
            self.outputs[0].default_value = str(self.s_output)

        return self.s_output

    def update(self):
        self.process(bpy.context, None, None)