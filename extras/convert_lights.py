import bpy
# .distance property in blender 2.8+ is no longer configurable in GUI, we use the "Radius" now
# which is .shadow_soft_size in API
instancing = []
for object in bpy.context.scene.objects:
    if object.type=="LIGHT" and object["type"].upper() == "LIGHT" and not object.data.name in instancing:
        if object.data["ponctuel"] == True:
            object.data.energy = 0.1 # (object.data.energy / 100.0)
            object.data.shadow_soft_size = object.data.distance
            instancing.append(object.data.name)