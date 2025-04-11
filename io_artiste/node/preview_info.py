import bpy
from ..base.node import node

class STK_info(node):
    bl_idname = 'STK_Info'
    bl_label = 'Info'
    bl_icon = 'INFO'

    # Propriété pour stocker la valeur à afficher
    doc: bpy.props.StringProperty(
        name="Valeur",
        description="Valeur à afficher",
        default=""
    )

    def init(self, context):
        # Création du socket d'entrée
        self.node_entrer("NodeSocketString", "info_input", "Info", "")

    def draw_buttons(self, context, layout):
        # Affichage de la valeur dans l'interface
        box = layout.box()
        formatted_text = self.format_text(self.doc)
        for ligne in formatted_text.split('\n'):
            box.label(text=ligne)

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
        
        # Si pas de connexion ou échec de récupération, utilise la valeur par défaut
        self.doc = str(input_socket.default_value)
        return self.doc

    def format_text(self, text):
        """Formate le texte en ajoutant des retours à la ligne tous les 70 caractères ou 8 mots."""
        words = text.split()
        formatted_lines = []
        current_line = []
        current_length = 0

        for word in words:
            word_length = len(word)
            
            # Vérifie si l'ajout du mot dépasse la limite de caractères ou de mots
            if current_length + word_length + len(current_line) > 70 or len(current_line) >= 8:
                formatted_lines.append(' '.join(current_line))
                current_line = [word]
                current_length = word_length
            else:
                current_line.append(word)
                current_length += word_length

        # Ajoute la dernière ligne si elle n'est pas vide
        if current_line:
            formatted_lines.append(' '.join(current_line))

        return '\n'.join(formatted_lines)
    
    def update(self):
        """Appelé quand le nœud doit être mis à jour"""
        self.process(bpy.context, None, None)
