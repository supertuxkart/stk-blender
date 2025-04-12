import bpy, os
from ..base.node import node

class STK_initial(node):
    bl_idname = 'STK_Initialisation'
    bl_label = 'Init'
    bl_icon = 'NONE'

    # Property to store the output list
    sortie: bpy.props.StringProperty(name="output", default="")

    use_sudo: bpy.props.BoolProperty(
        name="Super User",
        description="Use super-user rights to launch STK",
        default=False,
        update=lambda self, context: self.update())
    
    password: bpy.props.StringProperty(
        name="Password",
        description="Password for sudo command",
        subtype='PASSWORD',
        default="",
        update=lambda self, context: self.update())
    
    executable_game: bpy.props.StringProperty(
            name="Executable (supertuxkart) path",
            subtype='FILE_PATH',
            update=lambda self, context: self.update())
        
    track_path: bpy.props.StringProperty(
            name="Track (data) path",
            subtype='DIR_PATH',
            update=lambda self, context: self.update())
    kart_path: bpy.props.StringProperty(
            name="Kart (data) path",
            subtype='DIR_PATH',
            update=lambda self, context: self.update())
    
    disable_addon_tracks: bpy.props.BoolProperty(
        name="Disable addon tracks",
        description="",
        default=False,
        update=lambda self, context: self.update())
    
    disable_addon_karts: bpy.props.BoolProperty(
        name="Disable addon karts",
        description="",
        default=False,
        update=lambda self, context: self.update())
    
    difficulty: bpy.props.EnumProperty(
        name="Difficulty",
        items=[
            ("0", "Novice", "", "", 0),
            ("1", "Intermediate", "", "", 1),
            ("2", "Expert", "", "", 2),
            ("3", "Super Tux", "", "", 3),
        ],
        default="0",
        update=lambda self, context: self.update()
    )

    # Node initialization
    def init(self, context):
        print("Node STK_initial initialization")
        
        # Create the output
        self.supr_node_sortie("List")
        self.node_sortie('NodeSocketString', 'List', 'liste', "")

    def draw_buttons(self, context, layout):
        # Create buttons
        layout.prop(self, "use_sudo")
        if self.use_sudo:
            layout.prop(self, "password", text="Password")

        ligne = layout.row()
        ligne.label(text=f'Game (file) path: {self.executable_game}')
        ligne.operator('runner.executable_file', icon='FILE', text="").game = self.name

        ligne = layout.row()
        ligne.label(text=f'Track (folder) path: {self.track_path}')
        ligne.operator('runner.track_path', icon='FILEBROWSER', text="").tracks = self.name

        ligne = layout.row()
        ligne.label(text=f'Kart (folder) path: {self.kart_path}')
        ligne.operator('runner.kart_path', icon='FILEBROWSER', text="").karts = self.name

        ligne = layout.row()
        ligne.prop(self, "disable_addon_tracks")
        ligne.prop(self, "disable_addon_karts")

        layout.prop(self, "difficulty")

    def process(self, context, id, path):
        if context is None:
            return

        # Update the output
        if len(self.outputs) > 0 and hasattr(self.outputs[0], "default_value"):
            self.sortie = ""
            if self.use_sudo != False:
                self.sortie += f"echo '{self.password}' | sudo -S "
            if self.executable_game != "":
                self.sortie += f"{self.executable_game}"
            if self.disable_addon_tracks != False:
                self.sortie += f" --disable-addon-tracks"
            if self.disable_addon_karts != False:
                self.sortie += f" --disable-addon-karts"
            if self.track_path != "":
                self.sortie += f" --trackdir='{self.track_path}'"
            if self.kart_path != "":
                self.sortie += f" --kartdir='{self.kart_path}'"
            self.sortie += f" --difficulty={self.difficulty}"
            self.outputs[0].default_value = str(self.sortie)
        return self.sortie

    def update(self):
        self.process(bpy.context, None, None)


class STK_Pick_Executable_Operator(bpy.types.Operator):
    bl_idname = "runner.executable_file"
    bl_label = "Select the SuperTuxKart executable game file"

    game: bpy.props.StringProperty()
    filepath: bpy.props.StringProperty(subtype="FILE_PATH")

    def execute(self, context):
        tree = context.space_data.edit_tree
        if tree:
            for node in tree.nodes:
                if node.name == self.game:
                    node.executable_game = self.filepath
                    node.update()
                    return {'FINISHED'}
        
        self.report({'ERROR'}, "Node not found")
        return {'CANCELLED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


class STK_Pick_TracksFolder_Operator(bpy.types.Operator):
    bl_idname = "runner.track_path"
    bl_label = "Select the SuperTuxKart track (data) folder"

    tracks: bpy.props.StringProperty()
    filepath: bpy.props.StringProperty(subtype="DIR_PATH")

    def execute(self, context):
        tree = context.space_data.edit_tree
        if tree:
            for node in tree.nodes:
                if node.name == self.tracks:
                    node.track_path = self.filepath
                    node.update()
                    return {'FINISHED'}
        self.report({'ERROR'}, "Node not found")
        return {'CANCELLED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


class STK_Pick_kartsFolder_Operator(bpy.types.Operator):
    bl_idname = "runner.kart_path"
    bl_label = "Select the SuperTuxKart kart (data) folder"

    karts: bpy.props.StringProperty()
    filepath: bpy.props.StringProperty(subtype="DIR_PATH")

    def execute(self, context):
        tree = context.space_data.edit_tree
        if tree:
            for node in tree.nodes:
                if node.name == self.karts:
                    node.kart_path = self.filepath
                    node.update()
                    return {'FINISHED'}
        self.report({'ERROR'}, "Node not found")
        return {'CANCELLED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
