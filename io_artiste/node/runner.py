import bpy, subprocess
from ..base.node import node

class STK_run(node):
    bl_idname = 'STK_Go'
    bl_label = 'Go Run Test'
    bl_icon = 'NONE'

    # Property to store the value to display
    doc: bpy.props.StringProperty(
        name="Value",
        default=""
    )
    run_or_popen: bpy.props.EnumProperty(
        name="Run or Popen",
        description="Run command for testing from Blender or Popen for independent execution from Blender",
        items=[
            ("run", "Run", "Run the command", 0),
            ("popen", "Popen", "Popen the command", 1)
        ],
        default="run",
        update=lambda self, context: self.update()
    )

    def init(self, context):
        # Create input socket
        self.node_entrer("NodeSocketString", "info_input", "Info", "")

    def draw_buttons(self, context, layout):
        # Display the value in the interface
        layout.prop(self, "run_or_popen")
        layout.operator('runner.run_stk', text="Run STK", icon='PLAY').node_id = self.name

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
        
        # If no connection, use the default value
        self.doc = str(input_socket.default_value)
        return self.doc

    def update(self):
        """Called when the node needs to be updated"""
        self.process(bpy.context, None, None)


class STK_OT_RunStk(bpy.types.Operator):
    bl_idname = "runner.run_stk"
    bl_label = "Run STK"

    node_id: bpy.props.StringProperty()

    def execute(self, context):
        command = []
        tree = context.space_data.edit_tree  # Get the active node
        if tree:  # Find the node corresponding to the ID
            for node in tree.nodes:
                if node.name == self.node_id and hasattr(node, "doc"):
                    # Node found: print its name and ID
                    command.append(node.doc)
                    print(command[0])
                    """
                    if node.run_or_popen == "popen":
                        try:
                            # Create a new process group
                            process = subprocess.Popen(
                                command[0],
                                shell=True,
                                stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                start_new_session=True,
                                text=True
                            )
                            
                            # Store the process ID for potential future use
                            context.scene['stk_process_id'] = process.pid
                            
                            return {'FINISHED'}
                        except Exception as e:
                            self.report({'ERROR'}, f"Failed to start STK: {str(e)}")
                            return {'CANCELLED'}
                    if node.run_or_popen == "run":
                        try:
                            result = subprocess.run(
                                command[0],
                                shell=True,
                                capture_output=True,
                                text=True,
                                check=True
                            )
                            if result.returncode != 0:
                                self.report({'ERROR'}, f"STK returned error: {result.stderr}")
                                return {'CANCELLED'}
                            return {'FINISHED'}
                        except subprocess.CalledProcessError as e:
                            self.report({'ERROR'}, f"STK execution failed: {e.stderr}")
                            return {'CANCELLED'}
                        except Exception as e:
                            self.report({'ERROR'}, f"Failed to run STK: {str(e)}")
                            return {'CANCELLED'}"""
        self.report({'ERROR'}, "Node with the function not found")
        return {'CANCELLED'}