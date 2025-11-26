#!BPY

# Copyright (c) 2020 SPM author(s)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import bpy, sys, os, struct, math, string, mathutils, bmesh, time

spm_version = 1

def get_fcurves(anim_data):
    if not anim_data:
        return None
    if bpy.app.version < (5, 0, 0):
        if hasattr(anim_data, "action") and anim_data.action:
            if hasattr(anim_data.action, "fcurves"):
                return anim_data.action.fcurves
    else:
        if hasattr(anim_data, "action") and anim_data.action:
            if (hasattr(anim_data.action, "layers") and anim_data.action.layers and
                hasattr(anim_data.action.layers[0], "strips") and anim_data.action.layers[0].strips and
                hasattr(anim_data.action.layers[0].strips[0], "channelbags") and
                anim_data.action.layers[0].strips[0].channelbags):

                channelbag = anim_data.action.layers[0].strips[0].channelbags[0]
                if hasattr(channelbag, "fcurves"):
                    return channelbag.fcurves
    return None

# Helper Functions
def writeFloat(value1):
    return struct.pack("<f", value1)

def writeInt(value1):
    return struct.pack("<i", value1)

def writeUint(value1):
    return struct.pack("<I", value1)

def writeInt16(value1):
    assert value1 > -32769
    assert value1 < 32768
    return struct.pack("<h", value1)

def writeUint16(value1):
    assert value1 < 65536
    return struct.pack("<H", value1)

def writeUint8(value1):
    assert value1 < 256
    return struct.pack("<B", value1)

def writeHalfFloat(float32):
    return struct.pack("<e", float32)

def write2101010Rev(vector3):
    part = 0
    ret = 0
    v = min(1.0, max(-1.0, vector3[0]))
    if v > 0.0:
        part = (int)((v * 511.0) + 0.5)
    else:
        part = (int)((v * 512.0) - 0.5)
    ret |= part & 1023

    v = min(1.0, max(-1.0, vector3[1]))
    if v > 0.0:
        part = (int)((v * 511.0) + 0.5)
    else:
        part = (int)((v * 512.0) - 0.5)
    ret |= (part & 1023) << 10

    v = min(1.0, max(-1.0, vector3[2]))
    if v > 0.0:
        part = (int)((v * 511.0) + 0.5)
    else:
        part = (int)((v * 512.0) - 0.5)
    ret |= (part & 1023) << 20

    if len(vector3) == 4:
        v = min(1.0, max(-1.0, vector3[3]));
        if v > 0.0:
            part = (int)((v * 1.0) + 0.5);
        else:
            part = (int)((v * 2.0) - 0.5);
    else:
        part = 0
    ret |= (part & 3) << 30
    return writeUint(ret)

def writeLenString(value):
    encoded = str.encode(value)
    if len(encoded) > 255:
        value = encoded[0:255]
    bin = "<%ds" % len(encoded)
    tmp_buf = bytearray()
    tmp_buf += writeUint8(len(encoded))
    tmp_buf += struct.pack(bin, encoded)
    return tmp_buf

def writeMatrixAsLocRotScale(mat):
    loc, rot, scale = mat.decompose()
    rot.normalize()
    return struct.pack('<ffffffffff', *loc.xzy, -rot.x, -rot.z, -rot.y, rot.w, *scale.xzy)

def getUniqueFrame(armature, keyframe_only):
    unique_frame = []
    if armature.animation_data and armature.animation_data.action:
        ipo = get_fcurves(armature.animation_data)
        for curve in ipo:
            if "pose" in curve.data_path:
                for keyframe in curve.keyframe_points:
                    if keyframe.co[0] < 0:
                        continue
                    global_key = int(keyframe.co[0])
                    global_key = 1 if global_key == 0 else global_key
                    if not global_key in unique_frame:
                        unique_frame.append(global_key)

    if armature.animation_data and armature.animation_data.nla_tracks:
        for nla_track in armature.animation_data.nla_tracks:
            for nla_strip in nla_track.strips:
                max_frame = int(nla_track.strips[-1].frame_end)
                if nla_strip.action:
                    for action_group in nla_strip.action.groups:
                        for curve in action_group.channels:
                            for keyframe in curve.keyframe_points:
                                if keyframe.co[0] < 0:
                                    continue
                                global_key = int(nla_strip.frame_start + keyframe.co[0])
                                if global_key > max_frame:
                                    global_key = int(nla_strip.frame_start)
                                global_key = 1 if global_key == 0 else global_key
                                #print('f: {} {} {}'.format(nla_strip.name, nla_strip.frame_start, keyframe.co[0]))
                                if not global_key in unique_frame:
                                    unique_frame.append(global_key)

    if armature.pose and armature.pose.bones:
        for pose_bone in armature.pose.bones:
            for constraint in pose_bone.constraints:
                try:
                    if constraint.target.animation_data.action:
                        ipo = constraint.target.animation_data.action.fcurves
                        for curve in ipo:
                            for modifier in curve.modifiers:
                                if modifier.frame_start > 0 and modifier.frame_end > 0:
                                    for f in range(int(modifier.frame_start), int(modifier.frame_end + 1)):
                                        #print('{} {}'.format(f, modifier.type))
                                        if not f in unique_frame:
                                            unique_frame.append(f)
                            #print('{}'.format(constraint.name))
                            for keyframe in curve.keyframe_points:
                                if keyframe.co[0] < 0:
                                    continue
                                global_key = int(keyframe.co[0])
                                global_key = 1 if global_key == 0 else global_key
                                #print('f: {} {}'.format(global_key, constraint.target.name))
                                if not global_key in unique_frame:
                                    #bpy.context.scene.frame_set(global_key)
                                    #bpy.context.scene.frame_current = global_key
                                    #armature.update_tag(refresh={'OBJECT', 'DATA'})
                                    #bpy.context.scene.update()
                                    #if constraint.influence == 0.0:
                                        #print('unused')
                                        #continue
                                    unique_frame.append(global_key)
                except (AttributeError) as e:
                    pass

    if len(unique_frame) == 0:
        print('No keyframes found for armature: {},'
        ' please remove the armature if it contains no keyframe.'.format(armature.name))
        return None
    unique_frame.sort()
    #for frame in unique_frame:
    #    print('unique_frame:{} {}'.format(frame, armature.name))
    if keyframe_only == False:
        first = bpy.context.scene.frame_start
        last = unique_frame[-1]
        unique_frame = []
        for frame in range(first, last + 1):
            unique_frame.append(frame)
        #for frame in unique_frame:
        #    print('unique_frame:{} {}'.format(frame, armature.name))
    return unique_frame

def equals(float1, float2):
    return (float1 + 0.0001 >= float2) and (float1 - 0.0001 <= float2)

def vectorEquals(vec1, vec2):
    if vec1 is None and vec2 is None:
        return True
    if len(vec1) != len(vec2):
        raise Exception("Vector length is different")
    return all(equals(v1, v2) for v1, v2 in zip(vec1, vec2))

class ExportArm:
    m_accumulated_bone = 0
    NEW_BONE = 99999999

    def __init__(self, arm, obj, local_space, keyframe_only):
        self.m_original_pose_position = arm.data.pose_position
        arm.data.pose_position = 'REST'
        if local_space:
            self.m_real_matrix = obj.matrix_world.inverted_safe() @ arm.matrix_world
        else:
            self.m_real_matrix = arm.matrix_world
        self.m_real_inv_matrix = self.m_real_matrix.inverted_safe()
        self.m_arm = arm
        self.m_bone_in_use = 0
        self.m_bone_local_id = []
        self.m_bone_names = {}
        self.m_keyframe_only = keyframe_only
        for pose_bone in arm.pose.bones:
            self.m_bone_names[pose_bone.name] = ExportArm.NEW_BONE

    def buildIndex(self, all_triangles):
        self.m_arm.data.pose_position = 'POSE'
        for triangle in all_triangles:
            if triangle.m_armature_name != self.m_arm.data.name:
                continue
            for vertex in triangle.m_vertices:
                found = 0
                for bone_name, weight in vertex.m_bones_weights:
                    if weight == 0.0:
                        continue
                    if found > 3:
                        break
                    if bone_name in self.m_bone_names:
                        if self.m_bone_names[bone_name] == ExportArm.NEW_BONE:
                            self.m_bone_names[bone_name] = ExportArm.m_accumulated_bone
                            ExportArm.m_accumulated_bone += 1
                        vertex.m_joints[found] = self.m_bone_names[bone_name]
                        vertex.m_weights[found] = weight
                        found += 1

    def buildLocalId(self):
        for k, v in self.m_bone_names.items():
            self.m_bone_local_id.append([k, v])
        self.m_bone_local_id.sort(key = lambda x: x[1])
        unused_bone = 0
        for bone_tu in self.m_bone_local_id:
            if bone_tu[1] != ExportArm.NEW_BONE:
                bone_tu[1] = self.m_bone_in_use
                self.m_bone_in_use += 1
            else:
                bone_tu[1] = self.m_bone_in_use + unused_bone
                unused_bone += 1
        #print(self.m_bone_names)
        #print(unused_bone)
        #print(self.m_bone_in_use)
        #print(self.m_bone_local_id)

    def getBone(self, bone_id):
        for k, v in self.m_bone_names.items():
            if bone_id == v:
                return self.m_arm.data.bones[k]
        return None

    def writeArmature(self):
            tmp_buf = bytearray()
            tmp_buf += writeUint16(self.m_bone_in_use)
            tmp_buf += writeUint16(len(self.m_arm.data.bones))

            assert len(self.m_bone_local_id) == len(self.m_arm.data.bones)
            for bone_tu in self.m_bone_local_id:
                bone = self.m_arm.data.bones[bone_tu[0]]
                tmp_buf += writeLenString(bone_tu[0])
            for bone_tu in self.m_bone_local_id:
                bone = self.m_arm.data.bones[bone_tu[0]]
                bone_inv = bone.matrix_local.inverted_safe() @ self.m_real_inv_matrix
                tmp_buf += writeMatrixAsLocRotScale(bone_inv)

            local_id_dict = {}
            for bone_pair in self.m_bone_local_id:
                local_id_dict[bone_pair[0]] = bone_pair[1]

            assert len(self.m_arm.pose.bones) == len(local_id_dict)
            for bone_tu in self.m_bone_local_id:
                pose_bone = self.m_arm.pose.bones[bone_tu[0]]
                if pose_bone.parent:
                    tmp_buf += writeInt16(local_id_dict[pose_bone.parent.name])
                else:
                    tmp_buf += writeInt16(-1)

            unique_frame = getUniqueFrame(self.m_arm, self.m_keyframe_only)
            if unique_frame is None:
                return None

            tmp_buf += writeUint16(len(unique_frame))
            for frame in unique_frame:
                bpy.context.scene.frame_set(frame)
                tmp_buf += writeUint16(frame - 1)
                for bone_tu in self.m_bone_local_id:
                    pose_bone = self.m_arm.pose.bones[bone_tu[0]]
                    if pose_bone.parent:
                        bone_mat = pose_bone.parent.matrix.inverted_safe() @ pose_bone.matrix
                    else:
                        bone_mat = self.m_real_matrix @ pose_bone.matrix
                    tmp_buf += writeMatrixAsLocRotScale(bone_mat)
            self.m_arm.data.pose_position = self.m_original_pose_position
            return tmp_buf

class Vertex:
    def __init__(self):
        self.m_position = None
        self.m_normal = mathutils.Vector((0.0, 0.0, 1.0)).freeze()
        self.m_color = (255, 255, 255)
        self.m_all_uvs = None
        self.m_tangent = mathutils.Vector((1.0, 0.0, 0.0, 1.0)).freeze()
        self.m_bones_weights = None
        self.m_joints = [-1, -1, -1, -1]
        self.m_weights = [0.0, 0.0, 0.0, 0.0]

    def __hash__(self):
        def roundTuple(data, decimals = 3):
            if data is None:
                return ()
            return tuple(round(x, decimals) for x in data)
        return hash((
            roundTuple(self.m_position),
            roundTuple(self.m_normal),
            self.m_color,
            roundTuple(self.m_all_uvs),
            self.m_tangent.w,
            self.m_joints
        ))

    def __eq__(self, other):
        if not isinstance(other, Vertex):
            return NotImplemented
        return (
            vectorEquals(self.m_position, other.m_position) and
            vectorEquals(self.m_normal, other.m_normal) and
            self.m_color == other.m_color and
            vectorEquals(self.m_all_uvs, other.m_all_uvs) and
            vectorEquals(self.m_tangent, other.m_tangent) and
            self.m_joints == other.m_joints and
            vectorEquals(self.m_weights, other.m_weights)
        )

    def writeVertex(self, export_normal, uv_1, uv_2, vcolor, arm_dict, need_export_tangent):
        tmp_buf = bytearray()
        joint_matrix = None
        write_joints = arm_dict is not None
        if write_joints:
            for i in range(0, 4):
                if self.m_joints[i] == -1:
                    break
                bone = None
                for arm in arm_dict.values():
                    bone = arm.getBone(self.m_joints[i])
                    if bone is not None:
                        break
                pose_bone = arm.m_arm.pose.bones[bone.name]
                bone_inv = bone.matrix_local.inverted_safe() @ arm.m_real_inv_matrix
                bone_mat = arm.m_real_matrix @ pose_bone.matrix @ bone_inv
                if joint_matrix is None:
                    joint_matrix = bone_mat * self.m_weights[i]
                else:
                    joint_matrix += bone_mat * self.m_weights[i]
        out_vector = self.m_position
        if joint_matrix is not None:
            out_vector = joint_matrix @ self.m_position.to_4d()
        for i in [0, 2, 1]:
            tmp_buf += writeFloat(out_vector[i])
        if export_normal:
            out_vector = self.m_normal
            if joint_matrix is not None:
                out_vector = self.m_normal.to_4d()
                out_vector.w = 0.0
                out_vector = joint_matrix @ out_vector
                out_vector.normalize()
            tmp_buf += write2101010Rev(out_vector.xzy)
        if vcolor:
            if self.m_color[0] == 255 and self.m_color[1] == 255 and\
            self.m_color[2] == 255:
                tmp_buf += writeUint8(128)
            else:
                tmp_buf += writeUint8(255)
                tmp_buf += writeUint8(self.m_color[0])
                tmp_buf += writeUint8(self.m_color[1])
                tmp_buf += writeUint8(self.m_color[2])
        if uv_1:
            tmp_buf += writeHalfFloat(self.m_all_uvs[0])
            tmp_buf += writeHalfFloat(self.m_all_uvs[1])
            if uv_2:
                tmp_buf += writeHalfFloat(self.m_all_uvs[2])
                tmp_buf += writeHalfFloat(self.m_all_uvs[3])
            if need_export_tangent:
                out_vector = self.m_tangent
                if joint_matrix is not None:
                    out_vector = self.m_tangent.copy()
                    out_vector.w = 0.0
                    out_vector = joint_matrix @ out_vector
                    out_vector.normalize()
                    out_vector.w = self.m_tangent.w
                tmp_buf += write2101010Rev(out_vector.xzyw)
        if write_joints:
            tmp_buf += writeInt16(self.m_joints[0])
            tmp_buf += writeInt16(self.m_joints[1])
            tmp_buf += writeInt16(self.m_joints[2])
            tmp_buf += writeInt16(self.m_joints[3])
            tmp_buf += writeHalfFloat(self.m_weights[0])
            tmp_buf += writeHalfFloat(self.m_weights[1])
            tmp_buf += writeHalfFloat(self.m_weights[2])
            tmp_buf += writeHalfFloat(self.m_weights[3])
        return tmp_buf

class Triangle:
    def __init__(self):
        self.m_vertices = None
        self.m_texture_one = None
        self.m_texture_two = None
        self.m_texture_cmp = None
        self.m_armature_name = None

    def removeJointsData(self):
        for v in self.m_vertices:
            v.m_joints = None
            v.m_weights = None

def searchMaterialForImage(material, uv_num):
    # Check if there is a material
    # If so, search the STK shader node for an image
    if material is not None:
        try:
            node_tree = material.node_tree
            image_name = ""
            shader_node = node_tree.nodes['Principled BSDF']
            if shader_node.inputs['Base Color'].is_linked:
                # Get the connected node
                child = shader_node.inputs['Base Color'].links[0].from_node
                if type(child) is bpy.types.ShaderNodeTexImage and uv_num == 1:
                    image_name = os.path.basename(child.image.filepath)
                elif type(child) is bpy.types.ShaderNodeMixRGB:
                    uvOne = child.inputs['Color1'].links[0].from_node
                    uvTwo = child.inputs['Color2'].links[0].from_node
                    if type(uvOne) is bpy.types.ShaderNodeTexImage and uv_num == 1:
                        image_name = os.path.basename(uvOne.image.filepath)
                    elif type(uvTwo) is bpy.types.ShaderNodeTexImage and uv_num == 2:
                        image_name = os.path.basename(uvTwo.image.filepath)
                    else:
                        image_name = ""
            if image_name is not None:
                return image_name
            else:
                return ""
        except:
            return ""
    else:
        return ""

# ==== Write SPM File ====
# (main exporter function)
def writeSPMFile(filename, spm_parameters={}):
    bounding_boxes = None
    start = time.time()

    if spm_parameters.get("selection-type") == "selected":
        exp_obj = bpy.context.selected_objects
    elif spm_parameters.get("selection-type") == "scene":
        exp_obj = bpy.context.scene.objects
    elif spm_parameters.get("selection-type") == "view-layer":
        exp_obj = bpy.view_layer.objects
    else:
        exp_obj = bpy.data.objects

    has_vertex_color = False
    export_normal = spm_parameters.get("export-normal")
    need_export_tangent = spm_parameters.get("export-tangent")
    if need_export_tangent:
        export_normal = True
    arm_count = 0
    arm_dict = {}
    all_triangles = []
    static_mesh_frame = spm_parameters.get("static-mesh-frame")\
    if spm_parameters.get("static-mesh-frame") > 0 else bpy.context.scene.frame_start
    if static_mesh_frame < 1:
        print("static_mesh_frame is less than 1, changing it")
        static_mesh_frame = 1

    for obj in exp_obj:
        arm = obj.find_armature()
        if arm != None and not arm.data.name in arm_dict:
            arm_count += 1
            arm_dict[arm.data.name] = ExportArm(
                arm, obj, spm_parameters.get("local-space"),
                spm_parameters.get("keyframes-only"))

    all_no_tangents = True
    for obj in exp_obj:
        if obj.type != "MESH":
            continue

        if spm_parameters.get("local-space"):
            exported_matrix = mathutils.Matrix()
        else:
            exported_matrix = obj.matrix_world

        arm = obj.find_armature()
        if spm_parameters.get("apply-modifiers"):
            mesh = obj.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh()
        else:
            mesh = obj.to_mesh()
        if len(mesh.vertices) < 1:
            print('{} has no vertices, please check it'.format(obj.name))
            continue

        bm = bmesh.new()
        bm.from_mesh(mesh)
        bmesh.ops.transform(bm, matrix = exported_matrix, verts = bm.verts)
        if need_export_tangent:
            bmesh.ops.triangulate(bm, faces = bm.faces)
        bm.to_mesh(mesh)
        bm.free()

        if len(mesh.polygons) < 1:
            print('{} has no faces, please check it'.format(obj.name))
            continue

        if need_export_tangent:
            if len(mesh.uv_layers) >= 1:
                # Use smooth normals to calcuate tangents, this makes blender >= 4.1 export .spm with similar file size
                if bpy.app.version >= (4, 1, 0):
                    mesh.set_sharp_from_angle(angle = 3.14159)
                mesh.calc_tangents()
                all_no_tangents = False
                no_tangents = False
            else:
                no_tangents = True
                print('{} has no uvmap to calculate tangents'.format(obj.name))

        uv_one = mesh.uv_layers[0] if (len(mesh.uv_layers) >= 1) else None
        uv_two = mesh.uv_layers[1] if (len(mesh.uv_layers) >= 2) else None

        colors = mesh.vertex_colors[0] if (len(mesh.vertex_colors) >= 1) else None
        if colors:
            has_vertex_color = True

        mesh.calc_loop_triangles()
        for f in mesh.loop_triangles:
            if f.material_index < 0 or not obj.material_slots:
                texture_one = ""
            elif f.material_index < len(obj.material_slots):
                texture_one = searchMaterialForImage(obj.material_slots[f.material_index].material, 1)
            else:
                texture_one = searchMaterialForImage(obj.material_slots[-1].material, 1)

            if obj.material_slots and uv_two:
                texture_two = searchMaterialForImage(obj.material_slots[-1].material, 2)
            else:
                texture_two = ""

            texture_cmp = ''.join([texture_one, texture_two])
            spm_vertices = []
            for li in f.loops:
                v = mesh.loops[li].vertex_index
                vertices = mathutils.Vector(mesh.vertices[v].co).freeze()
                if bounding_boxes is None:
                    bounding_boxes = [0] * 6
                    bounding_boxes[0] = vertices[0]
                    bounding_boxes[1] = vertices[2]
                    bounding_boxes[2] = vertices[1]
                    bounding_boxes[3] = vertices[0]
                    bounding_boxes[4] = vertices[2]
                    bounding_boxes[5] = vertices[1]
                else:
                    # Min edge
                    if bounding_boxes[0] > vertices[0]:
                        bounding_boxes[0] = vertices[0]
                    if bounding_boxes[1] > vertices[2]:
                        bounding_boxes[1] = vertices[2]
                    if bounding_boxes[2] > vertices[1]:
                        bounding_boxes[2] = vertices[1]
                    # Max edge
                    if bounding_boxes[3] < vertices[0]:
                        bounding_boxes[3] = vertices[0]
                    if bounding_boxes[4] < vertices[2]:
                        bounding_boxes[4] = vertices[2]
                    if bounding_boxes[5] < vertices[1]:
                        bounding_boxes[5] = vertices[1]

                all_uvs = [0.0, 0.0, 0.0, 0.0]
                if uv_one:
                    all_uvs[0] = uv_one.data[li].uv[0]
                    all_uvs[1] = 1.0 - uv_one.data[li].uv[1]
                if uv_two:
                    all_uvs[2] = uv_two.data[li].uv[0]
                    all_uvs[3] = 1.0 - uv_two.data[li].uv[1]
                all_uvs = tuple(all_uvs)

                each_joint_data = []
                if arm_count != 0:
                    for group in mesh.vertices[v].groups:
                        each_joint_data.append((obj.vertex_groups[group.group].name, group.weight))
                    each_joint_data.sort(key = lambda x: x[1], reverse = True)

                spm_vertex = Vertex()
                spm_vertex.m_position = vertices
                if export_normal:
                    spm_vertex.m_normal = mathutils.Vector(mesh.vertices[v].normal).normalized().freeze()
                if colors:
                    vcolor = colors.data[li].color[:3]
                    spm_vertex.m_color = tuple(min(int(c * 255), 255) for c in vcolor)
                spm_vertex.m_all_uvs = all_uvs
                if need_export_tangent:
                    if not no_tangents:
                        tangent = mathutils.Vector(mesh.loops[li].tangent).normalized().to_4d()
                        tangent.w = -mesh.loops[li].bitangent_sign
                        spm_vertex.m_tangent = tangent.freeze()
                spm_vertex.m_bones_weights = each_joint_data
                spm_vertices.append(spm_vertex)

            triangle = Triangle()
            assert len(spm_vertices) == 3
            triangle.m_vertices = spm_vertices
            triangle.m_texture_one = texture_one
            triangle.m_texture_two = texture_two
            triangle.m_texture_cmp = texture_cmp
            triangle.m_armature_name = arm.data.name if arm != None else None
            all_triangles.append(triangle)

        if need_export_tangent:
            mesh.free_tangents()

    if all_no_tangents:
        need_export_tangent = False

    if arm_count != 0:
        ExportArm.m_accumulated_bone = 0
        for arm_name in sorted(arm_dict.keys()):
            arm_dict[arm_name].buildIndex(all_triangles)
            arm_dict[arm_name].buildLocalId()

        useless_arm = True
        for triangle in all_triangles:
            for vertex in triangle.m_vertices:
                total_weights = sum(vertex.m_weights)
                if total_weights > 0.0:
                    useless_arm = False
                    for i in range(0, 4):
                        vertex.m_weights[i] /= total_weights
                vertex.m_joints = tuple(vertex.m_joints)
                vertex.m_weights = tuple(vertex.m_weights)
        if useless_arm:
            arm_count = 0
    if arm_count == 0:
        for t in all_triangles:
            t.removeJointsData()

    assert len(all_triangles) > 0
    all_triangles.sort(key = lambda x: x.m_texture_cmp)
    spm_buffer = bytearray()

    # SP header
    spm_buffer += writeUint16(20563)

    # 5 bit version, 3 bit type : SPMS SPMA SPMN
    # SPMS (space partitioned split mesh not supported in python)
    byte = 0
    byte = spm_version << 3
    byte |= 1 if arm_count != 0 else 2
    spm_buffer += writeUint8(byte)

    # bit 0: export-normal
    # bit 1: export-vcolor
    # bit 2: export-tangent
    byte = 0
    if export_normal:
        byte = 1
    export_vcolor = spm_parameters.get("export-vcolor") and has_vertex_color
    if export_vcolor:
        byte = 1 << 1 | byte
    if need_export_tangent:
        byte = 1 << 2 | byte
    spm_buffer += writeUint8(byte)
    for position in bounding_boxes:
        spm_buffer += writeFloat(position)

    tex_cmp = None
    texture_list = []
    for triangle in all_triangles:
        if triangle.m_texture_cmp != tex_cmp:
            tex_cmp = triangle.m_texture_cmp
            texture_list.append(triangle.m_texture_one)
            texture_list.append(triangle.m_texture_two)
    material_count = len(texture_list) >> 1
    spm_buffer += writeUint16(material_count)
    #print(material_count)
    for texture_name in texture_list:
        spm_buffer += writeLenString(texture_name)

    # No SPMS so always 1 sector count
    spm_buffer += writeUint16(1)

    vbo_ibo = bytearray()
    vertices_dict = {}
    vertices = []
    indices = []
    tex_cmp = all_triangles[0].m_texture_cmp
    material_count = 0
    mesh_buffer_count = 0

    if arm_count != 0:
        bpy.context.scene.frame_set(static_mesh_frame)
    for t_idx in range(0, len(all_triangles) + 1):
        cur_cmp = all_triangles[t_idx].m_texture_cmp \
        if t_idx < len(all_triangles) else None
        if cur_cmp != tex_cmp or len(vertices) > 65532:
            tex_cmp = cur_cmp
            vbo_ibo += writeUint(len(vertices))
            vbo_ibo += writeUint(len(indices))
            vbo_ibo += writeUint16(material_count)
            #print(len(vertices))
            #print(len(indices))
            assert len(vertices) < 65536
            for vertex in vertices:
                vbo_ibo += vertex.writeVertex(export_normal,\
                all_triangles[t_idx -1].m_texture_one != "",\
                all_triangles[t_idx -1].m_texture_two != "",\
                export_vcolor, None if arm_count == 0 else arm_dict,\
                need_export_tangent)
            for index in indices:
                if len(vertices) > 255:
                    vbo_ibo += writeUint16(index)
                else:
                    vbo_ibo += writeUint8(index)
            if not len(vertices) > 65532:
                material_count = material_count + 1
            mesh_buffer_count += 1
            vertices_dict = {}
            vertices = []
            indices = []
        if t_idx >= len(all_triangles):
            break
        triangle = all_triangles[t_idx]
        for vertex in reversed(triangle.m_vertices):
            if vertex not in vertices_dict:
                vertex_location = len(vertices)
                indices.append(vertex_location)
                vertices.append(vertex)
                vertices_dict[vertex] = vertex_location
            else:
                indices.append(vertices_dict[vertex])

    spm_buffer += writeUint16(mesh_buffer_count)
    spm_buffer += vbo_ibo

    if arm_count != 0:
        spm_buffer += writeUint8(len(arm_dict))
        spm_buffer += writeUint16(static_mesh_frame - 1)
        for arm_name in sorted(arm_dict.keys()):
            armature = arm_dict[arm_name].writeArmature()
            if armature is not None:
                spm_buffer += armature

    spm = open(filename,'wb')
    spm.write(spm_buffer)
    spm.close()

    end = time.time()
    print("Exported in", (end - start))
