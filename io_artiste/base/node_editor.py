import bpy

# création de l'éditeur de node
class STKeditor(bpy.types.NodeTree):
    bl_idname = "STK_editor"
    bl_label = "STK Run Test"
    bl_icon = "AUTO"

    def mise_a_jour_valeur_node(self):
        for node in self.nodes:
            node.update()

        for area in bpy.context.screen.areas:
            if area.type == 'NODE_EDITOR':
                for space in area.spaces:
                    if space.type == 'NODE_EDITOR' and space.tree_type == self.bl_idname:
                        area.tag_redraw()

    def update(self):
        self.mise_a_jour_valeur_node()

    def update_scene_handler(self, scene):
        for area in bpy.context.screen.areas:
            if area.type == 'NODE_EDITOR':
                for space in area.spaces:
                    if space.type == 'NODE_EDITOR':
                        tree = getattr(space, "node_tree", None) or getattr(space, "edit_tree", None)
                        if tree and getattr(tree, "bl_idname", "") == STKeditor.bl_idname:
                            try: tree.update()
                            except Exception: pass