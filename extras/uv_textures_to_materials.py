# To be run for STK Blender source files before being opened in 2.80+
# Searches for UV textures, creates materials out of them, and assigns
# those materials to all meshes using them
import bpy

def createNodeBasedMaterial(material, im):
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links

    principled_node = nodes.new(type="ShaderNodeBsdfPrincipled")
    # Make it less shiny
    principled_node.inputs["Specular"].default_value = 0
    principled_node.inputs["Roughness"].default_value = 1

    if 'Diffuse BSDF' in nodes:
        nodes.remove(nodes['Diffuse BSDF'])

    if 'Material' in nodes:
        nodes.remove(nodes['Material'])

    if 'Output' in nodes:
        nodes.remove(nodes['Output'])

    if 'Material Output' in nodes:
        node_output = nodes['Material Output']
    else:
        node_output = nodes.new(type="ShaderNodeOutputMaterial")

    links.new(principled_node.outputs[0], node_output.inputs[0])

    tex1_node = nodes.new(type="ShaderNodeTexImage")
    tex1_node.image = im
    links.new(tex1_node.outputs["Color"], principled_node.inputs["Base Color"])

    uvmap_node = nodes.new(type="ShaderNodeUVMap")
    uvmap_node.uv_map = "UVMap" # first UV map for first texture
    links.new(uvmap_node.outputs[0], tex1_node.inputs["Vector"])

# Remove blank materials
for mat in bpy.data.materials:
    if "Material" in mat.name:
        bpy.data.materials.remove(mat)

for obj in bpy.data.objects:
    if (obj.type == 'MESH'):
        # Search for all images used per mesh
        images = set()
        for uv_tex in obj.data.uv_textures.active.data:
            if uv_tex.image.name not in images:
                images.add(uv_tex.image)

        print(obj.data.name)
        print(images)

        # Create a node-based material per image, reusing materials if already created
        for im in images:
            im_name = im.name.split('.')[0]
            if im_name in bpy.data.materials:
                material = bpy.data.materials[im_name]
                # Overwrite the old material if it is not using nodes
                if not material.use_nodes:
                    createNodeBasedMaterial(material, im)
            else:
                material = bpy.data.materials.new(im_name)
                createNodeBasedMaterial(material, im)

            if im_name not in obj.data.materials and len(obj.data.materials) < 1:
                obj.data.materials.append(material)
            elif len(obj.data.materials) > 0:
                obj.material_slots[0].material = material
