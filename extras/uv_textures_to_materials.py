# To be run for STK Blender source files before being opened in 2.80+
# Searches for UV textures, creates materials out of them, and assigns
# those materials to all meshes using them
#
# Limitations (most of which can be fixed after migration):
# * Vertex colors are not supported, but they are left intact
# * Decal shaders (two UV maps) are not supported

import bpy

def createImageMaterial(material, image):
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
    tex1_node.image = image
    links.new(tex1_node.outputs["Color"], principled_node.inputs["Base Color"])

    uvmap_node = nodes.new(type="ShaderNodeUVMap")
    uvmap_node.uv_map = "UVMap" # first UV map for first texture
    links.new(uvmap_node.outputs[0], tex1_node.inputs["Vector"])

# Step 1: Search through all images and create materials out of them
# Create a node-based material per image, reusing materials if already created
for image in bpy.data.images:
    im_name = image.name.split('.')[0]
    if im_name in bpy.data.materials:
        material = bpy.data.materials[im_name]
        # Overwrite the old material if it is not using nodes
        if not material.use_nodes and material.library is None:
            createImageMaterial(material, image)
    else:
        material = bpy.data.materials.new(im_name)
        createImageMaterial(material, image)

    # Copy the custom properties from image to material if they exist
    if len(image.keys()) > 0:
        for prop in image.keys():
            material[prop] = image[prop]

# Step 2: Run though all non-library meshes with faces and assign the created materials
# Only meshes with UV maps will be dealt with
# Each material is to be assigned by image, in case a mesh uses at least two images
for mesh in bpy.data.meshes:
    if mesh.library is None and len(mesh.polygons) > 0 and len(mesh.uv_textures) > 0:
        # Clear all existing materials for a fresh start
        mesh.materials.clear()

        # Search for all images used per mesh
        images = set()
        for uv_tex in mesh.uv_textures[0].data:
            try:
                if uv_tex.image.name not in images:
                    images.add(uv_tex.image)
            except:
                # Face does not have an image assigned
                continue

        for im in images:
            im_name = im.name.split('.')[0]
            material = bpy.data.materials[im_name]

            # Add the material to the current mesh if not already there
            if im_name not in mesh.materials:
                mesh.materials.append(material)

            # Assign current material using the current image
            for polygon in mesh.polygons:
                if mesh.uv_textures.active.data[polygon.index].image == im:
                    polygon.material_index = mesh.materials.find(im_name)
