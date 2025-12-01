import bpy

# création de l'éditeur de node
class STKeditor(bpy.types.NodeTree):
    bl_idname = "STK_editor"
    bl_label = "STK Run Test"
    bl_icon = "AUTO"

    def __init__(self):
        bpy.app.handlers.depsgraph_update_post.append(self.update_scene_handler)
        print("Gestionnaire d'événements enregistré")

    def mise_a_jour_valeur_node(self):
        """Met à jour tous les nœuds et rafraîchit l'interface"""
        # Mettre à jour tous les nœuds
        for node in self.nodes:
            node.update()

        # Forcer le rafraîchissement de l'interface
        for area in bpy.context.screen.areas:
            if area.type == 'NODE_EDITOR':
                for space in area.spaces:
                    if space.type == 'NODE_EDITOR' and space.tree_type == self.bl_idname:
                        area.tag_redraw()

    def update(self):
        self.mise_a_jour_valeur_node()

    def update_scene_handler(self, scene):
        print("Mise à jour de la scène appelée")
        for area in bpy.context.screen.areas:
            if area.type == 'NODE_EDITOR':
                for space in area.spaces:
                    if space.type == 'NODE_EDITOR' and space.tree_type == self.bl_idname:
                        print("Mise à jour des nœuds")
                        self.mise_a_jour_valeur_node()