import bpy
from ..base.node import node

class STK_info(node):
    bl_idname = 'STK_Info'
    bl_label = 'Info'
    bl_icon = 'INFO'

    # Property to store the value to display
    doc: bpy.props.StringProperty(
        name="Value",
        description="Value to display",
        default=""
    )

    def init(self, context):
        # Create input socket
        self.node_entrer("NodeSocketString", "info_input", "Info", "")

    def draw_buttons(self, context, layout):
        # Display the value in the interface
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
                
                # Try to get the value via the source node's process method first
                if hasattr(from_node, "process"):
                    try:
                        value = from_node.process(context, id, path)
                        self.doc = str(value)
                        return self.doc
                    except:
                        pass
                
                # If that fails, try to get the default_value
                if hasattr(from_socket, "default_value"):
                    self.doc = str(from_socket.default_value)
                    return self.doc
        
        # If no connection or retrieval fails, use the default value
        self.doc = str(input_socket.default_value)
        return self.doc

    def format_text(self, text):
        """Format the text by adding line breaks every 70 characters or 8 words."""
        words = text.split()
        formatted_lines = []
        current_line = []
        current_length = 0

        for word in words:
            word_length = len(word)
            
            # Check if adding the word exceeds the character or word limit
            if current_length + word_length + len(current_line) > 70 or len(current_line) >= 8:
                formatted_lines.append(' '.join(current_line))
                current_line = [word]
                current_length = word_length
            else:
                current_line.append(word)
                current_length += word_length

        # Add the last line if it's not empty
        if current_line:
            formatted_lines.append(' '.join(current_line))

        return '\n'.join(formatted_lines)
    
    def update(self):
        """Called when the node needs to be updated"""
        self.process(bpy.context, None, None)
