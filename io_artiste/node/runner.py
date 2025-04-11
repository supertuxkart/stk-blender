import bpy, subprocess
from ..base.node import node

class STK_run(node):
    bl_idname = 'STK_Go'
    bl_label = 'Go Run Test'
    bl_icon = 'NONE'

    # Propriété pour stocker la valeur à afficher
    doc: bpy.props.StringProperty(
        name="Valeur",
        default=""
    )

    def init(self, context):
        # Création du socket d'entrée
        self.node_entrer("NodeSocketString", "info_input", "Info", "")

    def draw_buttons(self, context, layout):
        # Affichage de la valeur dans l'interface
        ligne = layout.row()
        ligne.operator('runner.run_stk', text="Run STK", icon='PLAY').node_id = self.name

    def process(self, context, id, path):
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
                        self.doc = str(value)
                        return self.doc
                    except:
                        pass
                
                # Si ça ne marche pas, essaie d'obtenir la default_value
                if hasattr(from_socket, "default_value"):
                    self.doc = str(from_socket.default_value)
                    return self.doc
        
        # Si pas de connexion, utilise la valeur par défaut
        self.doc = str(input_socket.default_value)
        return self.doc

    def update(self):
        """Appelé quand le nœud doit être mis à jour"""
        self.process(bpy.context, None, None)


class STK_OT_RunStk(bpy.types.Operator):
    bl_idname = "runner.run_stk"
    bl_label = "Run STK"

    node_id: bpy.props.StringProperty()

    def execute(self, context):
        command = []
        tree = context.space_data.edit_tree # Récupérer le nœud actif
        if tree: # Trouver le nœud correspondant à l'ID
            for node in tree.nodes:
                if node.name == self.node_id and hasattr(node, "doc"):
                    #print(f"Nœud trouvé: {node.name} ({node.bl_idname})")
                    command.append(node.doc)
                    print(f"Commande exécutée: {command[0].split()}")
                    tester = command[0].split()
                    try:
                        subprocess.Popen(tester)
                        return {'FINISHED'}
                    except:
                        return {'ERROR'}
        
        self.report({'ERROR'}, "Nœud avec la fonction non trouvé")
        return {'CANCELLED'}