import bpy
from .editor import STKeditor

bpy.types.Scene.stk_config1 = bpy.props.StringProperty(
            name="STK Configuration File",
            subtype='FILE_PATH',
            default="")

bpy.types.Scene.stk_config2 = bpy.props.StringProperty(
            name="STK Configuration File",
            subtype='FILE_PATH',
            default="")

bpy.types.Scene.version_stk = bpy.props.EnumProperty(
        name="Version STK",
        items=[
            ("1.x", "Series 1.x", "", "", 0),
            ("2.x", "Series 2.x", "", "", 1)
        ],
        default='1.x')

bpy.types.Scene.debug_artiste = bpy.props.BoolProperty(
    name="Debug Artiste", 
    default=False)

class STKpanel(bpy.types.Panel):
    bl_idname = "STK_PT_panel"
    bl_label = "STK Node Panel"
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"
    bl_context = "scene"
    bl_category = "STK"

    @classmethod
    def poll(cls, context):
        # Check if we are in the correct editor type
        if context.area.type != 'NODE_EDITOR':
            return False
            
        # Check if we have a node tree
        if not hasattr(context.space_data, 'edit_tree') or context.space_data.edit_tree is None:
            return False
            
        # Check if it's our custom node tree type
        if context.space_data.edit_tree.bl_idname != STKeditor.bl_idname:
            return False
            
        return True

    def draw(self, context):
        layout = self.layout

        layout.label(text="Config.xml")
        boite = layout.box()
        ligne = boite.row()
        ligne.label(text=f'Config STK 1.x: {context.scene.stk_config1}')
        ligne.operator('runner.config_stk_1', icon='FILE', text="")
        ligne = boite.row()
        ligne.label(text=f'Config STK 2.x: {context.scene.stk_config2}')
        ligne.operator('runner.config_stk_2', icon='FILE', text="")
        ligne = boite.row()
        ligne.prop(context.scene, "debug_artiste")
        ligne.prop(context.scene, "version_stk")
        boite.operator('runner.modif_config', icon="PLAY", text="Modify config")

        layout.separator()
        layout.label(text="STK online")
        boite = layout.box()



class STK_config_file1(bpy.types.Operator):
    bl_idname = "runner.config_stk_1"
    bl_label = "Config STK"

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        import bpy.path
        context.scene.stk_config1 = bpy.path.abspath(self.filepath)
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

class STK_config_file2(bpy.types.Operator):
    bl_idname = "runner.config_stk_2"
    bl_label = "Config STK"

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        import bpy.path
        context.scene.stk_config2 = bpy.path.abspath(self.filepath)
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

class STK_modif_config(bpy.types.Operator):
    bl_idname = "runner.modif_config"
    bl_label = "Modif Config"

    def execute(self, context):
        import pathlib
        if context.scene.debug_artiste == True:
            if pathlib.Path(context.scene.stk_config1).name == "config.xml":
                if context.scene.version_stk == "1.x":
                    print("Enabling artist debug mode for STK 1.x")
                    remplacer_ligne(pathlib.Path(context.scene.stk_config1), "    <artist_debug_mode value=\"true\" />")
                else:
                    print("Enabling artist debug mode for STK 2.x")
                    remplacer_ligne(pathlib.Path(context.scene.stk_config2), "    <artist_debug_mode value=\"true\" />")
        else:
            if pathlib.Path(context.scene.stk_config2).name == "config.xml":
                if context.scene.version_stk == "1.x":
                    print("Disabling artist debug mode for STK 1.x")
                    remplacer_ligne(pathlib.Path(context.scene.stk_config1), "    <artist_debug_mode value=\"false\" />")
                else:
                    print("Disabling artist debug mode for STK 2.x")
                    remplacer_ligne(pathlib.Path(context.scene.stk_config2), "    <artist_debug_mode value=\"false\" />")
        return {'FINISHED'}

def remplacer_ligne(fichier, texte: str):
    if fichier.exists():
        with open(fichier, "r") as f:
            lignes = f.readlines()
        
        # Check if the line exists
        ligne_trouvee = False
        for i, l in enumerate(lignes):
            if "artist_debug_mode" in l:
                ligne_trouvee = True
                ligne = i
                break

        if ligne_trouvee:
            try:
                lignes[ligne] = texte + "\n"  # Replace the line at the specified position
                
                with open(fichier, "w") as f:
                    f.writelines(lignes)
                print(f"Line at position {ligne} replaced with: {texte}")
                return ligne
            except Exception as e:
                print(f"Error: {str(e)}")
                return -1
        else:
            print("Error: Line not found.")
            return -1
    else:
        print("Error: File does not exist.")
        return -1
