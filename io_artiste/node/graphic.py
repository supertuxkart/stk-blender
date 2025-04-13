import bpy
from ..base.node import node

class STK_graphic(node):
    bl_idname = 'STK_Graphic'
    bl_label = 'Graphic'
    bl_icon = 'NONE'

    entrer: bpy.props.StringProperty(name="input", default="")
    sortie: bpy.props.StringProperty(name="output", default="")

    glow: bpy.props.BoolProperty(name="GLOW", description="Enable/Disable glow effect.", default=False, update=lambda self, context: self.update())
    bloom: bpy.props.BoolProperty(name="BLOOM", description="Enable/Disable bloom effect.", default=False, update=lambda self, context: self.update())
    light_shaft: bpy.props.BoolProperty(name="LIGHT SHAFT", description="Enable/Disable light shafts (God rays).", default=False, update=lambda self, context: self.update())
    dof: bpy.props.BoolProperty(name="DOF", description="Enable/Disable depth of field.", default=False, update=lambda self, context: self.update())
    particule: bpy.props.BoolProperty(name="PARTICULE", description="Enable/Disable particles.", default=False, update=lambda self, context: self.update())
    animation_kart: bpy.props.BoolProperty(name="ANIM KART", description="Enable/Disable animated characters.", default=False, update=lambda self, context: self.update())
    motion_blur: bpy.props.BoolProperty(name="BLUR", description="Enable/Disable motion blur.", default=False, update=lambda self, context: self.update())
    mlaa: bpy.props.BoolProperty(name="MLAA", description="Enable/Disable MLAA.", default=False, update=lambda self, context: self.update())
    tex_compression: bpy.props.BoolProperty(name="COMPRESSION TEXTURE", description="Enable/Disable texture compression.", default=False, update=lambda self, context: self.update())
    ssao: bpy.props.BoolProperty(name="SSAO", description="Enable/Disable SSAO.", default=False, update=lambda self, context: self.update())
    ibl: bpy.props.BoolProperty(name="IBL", description="Enable/Disable IBL.", default=False, update=lambda self, context: self.update())
    tex_hd: bpy.props.BoolProperty(name="HD TEXTURE", description="Enable/Disable HD textures.", default=False, update=lambda self, context: self.update())
    light_dynamic: bpy.props.BoolProperty(name="DYNAMIC LIGHT", description="Enable/Disable dynamic lights.", default=False, update=lambda self, context: self.update())

    #anisotropic: bpy.props.IntProperty(name="ANISOTROPIC", description="Anisotropic filtering quality (0 to disable).", default=0, update=lambda self, context: self.update())
    #shadows: bpy.props.IntProperty(name="SHADOWS", description="Shadow resolution (0 to disable).", default=0, update=lambda self, context: self.update())
    render_driver: bpy.props.EnumProperty(name="RENDER DRIVER", 
    description="Render driver to use (gl or directx9).", 
    items=[
        ('gl', 'OpenGL', 'OpenGL', '', 0),
        ('directx9', 'DirectX9', 'DirectX9', '', 1),
        ('vulkan', 'Vulkan', 'Vulkan', '', 2),
        ],
        default='gl', update=lambda self, context: self.update())

    def init(self, context):
        self.node_entrer("NodeSocketString", "input_0", "", "")
        self.node_sortie('NodeSocketString', 'output_0', '', "")

    def draw_buttons(self, context, layout):
        box = layout.box()
        ligne = box.row()
        ligne.prop(self, "particule")
        ligne.prop(self, "animation_kart")
        ligne.prop(self, "tex_compression")

        ligne = box.row()
        ligne.label(text="rendu avancer si activation de")
        ligne.prop(self, "light_dynamic")

        ligne = box.row()
        ligne.prop(self, "glow")
        ligne.prop(self, "bloom")
        ligne.prop(self, "dof")

        ligne = box.row()
        ligne.prop(self, "mlaa")
        ligne.prop(self, "motion_blur")
        ligne.prop(self, "light_shaft")
        
        ligne = box.row()
        ligne.prop(self, "ibl")
        ligne.prop(self, "tex_hd")
        ligne.prop(self, "ssao")

        #box.prop(self, "anisotropic")
        #box.prop(self, "shadows")
        box.prop(self, "render_driver")
        
        
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
                            self.entrer = str(value)
                        except:
                            pass
                    
                    # If that fails, try to get the default_value
                    if hasattr(from_socket, "default_value"):
                        self.entrer = str(from_socket.default_value)
            else:
                self.entrer = ""
        
        # Build the complete instruction with the input and properties
        if len(self.outputs) > 0 and hasattr(self.outputs[0], "default_value"):
            self.sortie = ""
            if self.entrer != "":
                self.sortie += self.entrer + " "
            
            if self.glow == True: self.sortie += f"--enable-glow"
            else: self.sortie += f"--disable-glow"
            
            if self.bloom == True: self.sortie += f" --enable-bloom"
            else: self.sortie += f" --disable-bloom"

            if self.light_shaft == True: self.sortie += f" --enable-light-shaft"
            else: self.sortie += f" --disable-light-shaft"
            
            if self.dof == True: self.sortie += f" --enable-dof"
            else: self.sortie += f" --disable-dof"

            if self.particule == True: self.sortie += f" --enable-particles"
            else: self.sortie += f" --disable-particles"

            if self.animation_kart == True: self.sortie += f" --enable-animated-characters"
            else: self.sortie += f" --disable-animated-characters"

            if self.motion_blur == True: self.sortie += f" --enable-motion-blur"
            else: self.sortie += f" --disable-motion-blur"

            if self.mlaa == True: self.sortie += f" --enable-mlaa"
            else: self.sortie += f" --disable-mlaa"

            if self.tex_compression == True: self.sortie += f" --enable-texture-compression"
            else: self.sortie += f" --disable-texture-compression"

            if self.ssao == True: self.sortie += f" --enable-ssao"
            else: self.sortie += f" --disable-ssao"

            if self.ibl == True: self.sortie += f" --enable-ibl"
            else: self.sortie += f" --disable-ibl"

            if self.tex_hd == True: self.sortie += f" --enable-hd-textures"
            else: self.sortie += f" --disable-hd-textures"

            if self.light_dynamic == True: self.sortie += f" --enable-dynamic-lights"
            else: self.sortie += f" --disable-dynamic-lights"

            #self.sortie += f" --anisotropic={self.anisotropic}"
            #self.sortie += f" --shadows={self.shadows}"
            self.sortie += f" --render-driver={self.render_driver}"

            self.outputs[0].default_value = str(self.sortie)
        return self.sortie

    def update(self):
        self.process(bpy.context, None, None)
"""
--anisotropic=n | Qualité du filtrage anisotropique (0 pour désactiver). Prend le pas sur le filtrage trilinéaire ou bilinéaire 
--shadows=n | Définir la résolution des ombres (0 pour désactiver) 
--render-driver=n | Pilote de rendu à utiliser (gl ou directx9) 
"""