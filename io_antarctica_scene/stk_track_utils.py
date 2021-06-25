#!BPY

# Copyright (c) 2020 SuperTuxKart author(s)
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

import bpy, math, re, random
from mathutils import *
from . import stk_utils

# --------------------------------------------------------------------------

def writeBezierCurve(f, curve, speed, extend="cyclic"):
    matrix = curve.matrix_world
    if len(curve.data.splines) > 1:
        self.log.report({'WARNING'}, curve.name + " contains multiple curves, will only export the first one")

    f.write('    <curve channel="LocXYZ" speed="%.2f" interpolation="bezier" extend="%s">\n'\
            %(speed, extend))
    if curve.data.splines[0].type != 'BEZIER':
        self.log.report({'WARNING'}, curve.name + " should be a bezier curve, not a " + curve.data.splines[0].type)
    else:
        for pt in curve.data.splines[0].bezier_points:
            v0 = matrix @ pt.handle_left
            v1 = matrix @ pt.co @ matrix
            v2 = matrix @ pt.handle_right
            f.write("      <point c=\"%f %f %f\" h1=\"%f %f %f\" h2=\"%f %f %f\" />\n"% \
                    ( v1[0],v1[2],v1[1],
                      v0[0],v0[2],v0[1],
                      v2[0],v2[2],v2[1] ) )
    f.write("    </curve>\n")

# ------------------------------------------------------------------------------
class ItemsExporter:

    def __init__(self):
        self.m_objects = []

    def processObject(self, object, stktype):

        if object.type=="EMPTY":
            # For backward compatibility test for the blender name
            # in case that there is no type property defined. This makes
            # it easier to port old style tracks without having to
            # add the property for all items.
            stktype = stk_utils.getObjectProperty(object, "type", object.name).upper()
            # Check for old and new style names
            if stktype[:8] in ["GHERRING", "RHERRING", "YHERRING", "SHERRING"] \
                or stktype[: 6]== "BANANA"     or stktype[:4]=="ITEM"           \
                or stktype[:11]=="NITRO-SMALL" or stktype[:9]=="NITRO-BIG"      \
                or stktype[:11]=="NITRO_SMALL" or stktype[:9]=="NITRO_BIG"      \
                or stktype[:11]=="SMALL-NITRO" or stktype[:9]=="BIG-NITRO"      \
                or stktype[: 6]=="ZIPPER":
                self.m_objects.append(object)
                return True
        return False

    def export(self, f):
        rad2deg = 180.0/3.1415926535
        scene = bpy.context.scene
        is_ctf = stk_utils.getSceneProperty(scene, "ctf",  "false") == "true"
        for obj in self.m_objects:
            item_type = stk_utils.getObjectProperty(obj, "type", "").lower()
            if item_type=="":
                # If the type is not specified in the property,
                # assume it's an old style item, which means the
                # blender object name is to be used
                l = obj.name.split(".")
                if len(l)!=1:
                    if l[-1].isdigit():   # Remove number appended by blender
                        l = l[:-1]
                    item_type = ".".join(l)
                else:
                    item_type = obj.name
                # Portability for old models:
                g=re.match("(.*) *{(.*)}", item_type)
                if g:
                    item_type = g.group(1)
                    specs = g.group(2).lower()
                    if specs.find("z")>=0: z=None
                    if specs.find("p")>=0: p=None
                    if specs.find("r")>=0: r=None
                if item_type=="GHERRING": item_type="banana"
                if item_type=="RHERRING": item_type="item"
                if item_type=="YHERRING": item_type="big-nitro"
                if item_type=="SHERRING": item_type="small-nitro"
            else:
                if item_type=="nitro-big": item_type="big-nitro"
                if item_type=="nitro_big": item_type="big-nitro"
                if item_type=="nitro-small": item_type="small-nitro"
                if item_type=="nitro_small": item_type="small-nitro"

            # Get the position of the item - first check if the item should
            # be dropped on the track, or stay at the position indicated.
            rx,ry,rz = map(lambda x: rad2deg*x, obj.rotation_euler)
            h,p,r    = map(lambda i: "%.2f"%i, [rz,rx,ry])
            x,y,z    = map(lambda i: "%.2f"%i, obj.location)
            drop     = stk_utils.getObjectProperty(obj, "dropitem", "true").lower()
            # Swap y and z axis to have the same coordinate system used in game.
            s        = "%s id=\"%s\" x=\"%s\" y=\"%s\" z=\"%s\"" % (item_type, obj.name, x, z, y)
            if h and h!="0.00": s = "%s h=\"%s\""%(s, h)
            if drop=="false":
                # Pitch and roll will be set automatically if dropped
                if p and p!="0.00": s="%s p=\"%s\""%(s, p)
                if r and r!="0.00": s="%s r=\"%s\""%(s, r)
                s="%s drop=\"false\""%s
            if is_ctf:
                f.write("  <%s ctf=\"%s\"/>\n" % (s, stk_utils.getObjectProperty(obj, "ctf_only", "false").lower()))
            else:
                f.write("  <%s />\n" % s)

# ------------------------------------------------------------------------------
class ParticleEmitterExporter:

    def __init__(self):
        self.m_objects = []

    def __init__(self, log):
        self.m_objects = []
        self.log = log

    def processObject(self, object, stktype):

        if object.type=="EMPTY" and stktype=="PARTICLE_EMITTER":
            self.m_objects.append(object)
            return True
        else:
            return False

    def export(self, f):
        for obj in self.m_objects:
            try:
                originXYZ = stk_utils.getNewXYZHString(obj)

                flags = []
                if len(stk_utils.getObjectProperty(obj, "particle_condition", "")) > 0:
                    flags.append('conditions="' + stk_utils.getObjectProperty(obj, "particle_condition", "") + '"')

                if stk_utils.getObjectProperty(obj, "clip_distance", 0) > 0 :
                    flags.append('clip_distance="%i"' % stk_utils.getObjectProperty(obj, "clip_distance", 0))

                if stk_utils.getObjectProperty(obj, "auto_emit", 'true') == 'false':
                    flags.append('auto_emit="%s"' % stk_utils.getObjectProperty(obj, "auto_emit", 'true'))

                f.write('  <particle-emitter kind="%s" id=\"%s\" %s %s>\n' %\
                        (stk_utils.getObjectProperty(obj, "kind", 0), obj.name, originXYZ, ' '.join(flags)))

                if obj.animation_data and obj.animation_data.action and obj.animation_data.action.fcurves and len(obj.animation_data.action.fcurves) > 0:
                    writeIPO(f, obj.animation_data)

                f.write('  </particle-emitter>\n')
            except:
                self.log.report({'ERROR'}, "Invalid particle emitter <" + stk_utils.getObjectProperty(obj, "name", obj.name) + "> ")

# ------------------------------------------------------------------------------
# Blender hair systems are usually used to automate the placement of plants on the ground
class BlenderHairExporter:

    def __init__(self):
        self.m_objects = []

    def __init__(self, log):
        self.m_objects = []
        self.log = log

    def processObject(self, object, stktype):

        if object.particle_systems is not None and len(object.particle_systems) >= 1 and \
           object.particle_systems[0].settings.type == 'EMITTER':
            if (object.particle_systems[0].settings.instance_object is not None): # or \
               #(object.particle_systems[0].settings.instance_collection is not None): #and stk_utils.getObjectProperty(object.particle_systems[0].settings.instance_object, "type", "") == "object":
                self.m_objects.append(object)
            else:
                self.log.report({'WARNING'}, "Ignoring invalid hair system <%s>" % object.name)

        return False # always return false so that the object is exported normally as a mesh too

    def export(self, f):
        rad2deg = 180.0/3.1415926535;

        for obj in self.m_objects:

            for particleSystem in obj.particle_systems:

                f.write('  <!-- Hair system %s, contains %i particles -->\n' % (obj.name, len(particleSystem.particles)))

                for particle in particleSystem.particles:
                    if particleSystem.settings.render_type == 'OBJECT':
                        instance_obj = particleSystem.settings.instance_object
                    # Currently we only support random picking from the group
                    elif particleSystem.settings.render_type == 'COLLECTION':
                        object_group = particleSystem.settings.instance_collection.objects
                        choice = random.randint(0, len(object_group) - 1)
                        instance_obj = object_group[choice]

                    loc = particle.location
                    hpr = particle.rotation.to_euler('XYZ')

                    # hack to get proper orientation
                    if (particleSystem.settings.normal_factor >= 0.5):
                        hpr.rotate_axis("Z", -1.57079633)

                    #print (particle.size)
                    si = particle.size #/ instance_obj.dimensions[2]
                    loc_rot_scale_str = "xyz=\"%.2f %.2f %.2f\" hpr=\"%.1f %.1f %.1f\" scale=\"%.2f %.2f %.2f\"" %\
                       (loc[0], loc[2], loc[1], -hpr[0]*rad2deg, -hpr[2]*rad2deg,
                        -hpr[1]*rad2deg, si, si, si)

                    if instance_obj.proxy is not None and instance_obj.proxy.library is not None:
                        path_parts = re.split("/|\\\\", instance_obj.proxy.library.filepath)
                        lib_name = path_parts[-2]
                        f.write('  <library name="%s" id=\"%s\" %s/>\n' % (lib_name, instance_obj.name, loc_rot_scale_str))
                    else:
                        name     = stk_utils.getObjectProperty(instance_obj, "name",   instance_obj.name )
                        if len(name) == 0:
                            name = instance_obj.name
                        f.write('  <object type="animation" %s interaction="ghost" model="%s.spm" skeletal-animation="false"></object>\n' % (loc_rot_scale_str, name))

            f.write('  <!-- END Hair system %s -->\n\n' % obj.name)


# ------------------------------------------------------------------------------
class SoundEmitterExporter:

    def __init__(self):
        self.m_objects = []

    def __init__(self, log):
        self.m_objects = []
        self.log = log

    def processObject(self, object, stktype):

        if object.type=="EMPTY" and stktype=="SFX_EMITTER":
            self.m_objects.append(object)
            return True
        else:
            return False

    def export(self, f):
        for obj in self.m_objects:
            try:
                # origin
                originXYZ = stk_utils.getXYZHPRString(obj)

                play_near_string = ""
                if stk_utils.getObjectProperty(obj, "play_when_near", "false") == "true":
                    dist = stk_utils.getObjectProperty(obj, "play_distance", 1.0)
                    play_near_string = " play-when-near=\"true\" distance=\"%.1f\"" % dist

                conditions_string = ""
                if len(stk_utils.getObjectProperty(obj, "sfx_conditions", "")) > 0:
                    conditions_string = ' conditions="' + stk_utils.getObjectProperty(obj, "sfx_conditions", "") + '"'


                f.write('  <object type="sfx-emitter" id=\"%s\" sound="%s" rolloff="%.3f" volume="%s" max_dist="%.1f" %s%s%s>\n' %\
                        (obj.name,
                         stk_utils.getObjectProperty(obj, "sfx_filename", "some_sound.ogg"),
                         stk_utils.getObjectProperty(obj, "sfx_rolloff", 0.05),
                         stk_utils.getObjectProperty(obj, "sfx_volume", 0),
                         stk_utils.getObjectProperty(obj, "sfx_max_dist", 500.0), originXYZ, play_near_string, conditions_string))

                if obj.animation_data and obj.animation_data.action and obj.animation_data.action.fcurves and len(obj.animation_data.action.fcurves) > 0:
                    writeIPO(f, obj.animation_data)

                f.write('  </object>\n')
            except:
                self.log.report({'ERROR'}, "Invalid sound emitter <" + stk_utils.getObjectProperty(obj, "name", obj.name) + "> ")


# ------------------------------------------------------------------------------
class ActionTriggerExporter:

    def __init__(self):
        self.m_objects = []

    def __init__(self, log):
        self.m_objects = []
        self.log = log

    def processObject(self, object, stktype):

        if stktype=="ACTION_TRIGGER":
            self.m_objects.append(object)
            return True
        else:
            return False

    def export(self, f):
        for obj in self.m_objects:
            try:
                # origin
                originXYZ = stk_utils.getXYZHPRString(obj)
                trigger_type = stk_utils.getObjectProperty(obj, "trigger_type", "point")

                #if trigger_type == "sphere":
                #    radius = (obj.dimensions.x + obj.dimensions.y + obj.dimensions.z)/6 # divide by 3 to get average size, divide by 2 to get radius from diameter
                #    f.write("    <check-sphere xyz=\"%.2f %.2f %.2f\" radius=\"%.2f\"/>\n" % \
                #            (obj.location[0], obj.location[2], obj.location[1], radius) )
                if trigger_type == "point":
                    f.write('  <object type="action-trigger" trigger-type="point" id=\"%s\" action="%s" distance="%s" reenable-timeout="%s" triggered-object="%s" %s/>\n' %\
                        (obj.name,
                         stk_utils.getObjectProperty(obj, "action", ""),
                         stk_utils.getObjectProperty(obj, "trigger_distance", 5.0),
                         stk_utils.getObjectProperty(obj, "reenable_timeout", 999999.9),
                         stk_utils.getObjectProperty(obj, "triggered_object", ""),
                         originXYZ))
                elif trigger_type == "cylinder":
                    radius = (obj.dimensions.x + obj.dimensions.y)/4 # divide by 2 to get average size, divide by 2 to get radius from diameter
                    f.write("  <object type=\"action-trigger\" trigger-type=\"cylinder\" action=\"%s\" xyz=\"%.2f %.2f %.2f\" radius=\"%.2f\" height=\"%.2f\"/>\n" % \
                            (stk_utils.getObjectProperty(obj, "action", ""), obj.location[0], obj.location[2], obj.location[1], radius, obj.dimensions.z) )
            except:
                self.log.report({'ERROR'}, "Invalid action <" + stk_utils.getObjectProperty(obj, "name", obj.name) + "> ")


# ------------------------------------------------------------------------------
class StartPositionFlagExporter:

    def __init__(self):
        self.m_objects = []
        self.m_red_flag = None
        self.m_blue_flag = None

    def __init__(self, log):
        self.m_objects = []
        self.m_red_flag = None
        self.m_blue_flag = None
        self.log = log

    def processObject(self, object, stktype):
        if object.type=="EMPTY" and stktype[:5]=="START":
            self.m_objects.append(object)
            return True
        elif object.type=="EMPTY" and stktype[:8]=="RED_FLAG":
            self.m_red_flag = object
            return True
        elif object.type=="EMPTY" and stktype[:9]=="BLUE_FLAG":
            self.m_blue_flag = object
            return True
        else:
            return False

    def export(self, f):
        scene = bpy.context.scene
        karts_per_row      = int(stk_utils.getSceneProperty(scene, "start_karts_per_row",      2))
        distance_forwards  = float(stk_utils.getSceneProperty(scene, "start_forwards_distance",  1.5))
        distance_sidewards = float(stk_utils.getSceneProperty(scene, "start_sidewards_distance", 3.0))
        distance_upwards   = float(stk_utils.getSceneProperty(scene, "start_upwards_distance",   0.1))
        if stk_utils.getSceneProperty(bpy.data.scenes[0], 'is_stk_node', 'false') != 'true':
            f.write("  <default-start karts-per-row     =\"%i\"\n"%karts_per_row     )
            f.write("                 forwards-distance =\"%.2f\"\n"%distance_forwards )
            f.write("                 sidewards-distance=\"%.2f\"\n"%distance_sidewards)
            f.write("                 upwards-distance  =\"%.2f\"/>\n"%distance_upwards)

        is_ctf = self.m_red_flag is not None and self.m_blue_flag is not None \
            and stk_utils.getSceneProperty(scene, "ctf",  "false") == "true"
        dId2Obj_ctf = {}
        dId2Obj = {}
        for obj in self.m_objects:
            stktype = stk_utils.getObjectProperty(obj, "type", obj.name).upper()
            id = int(stk_utils.getObjectProperty(obj, "start_index", "-1"))
            if id == "-1":
                self.log.report({'WARNING'}, "Invalid start position " + id)
            if is_ctf and stk_utils.getObjectProperty(obj, "ctf_only", "false").lower() == "true":
                dId2Obj_ctf[id] = obj
            else:
                dId2Obj[id] = obj

        l = dId2Obj.keys()

        if len(l) < 4 and stk_utils.getSceneProperty(scene, "arena",  "false") == "true":
            self.log.report({'WARNING'}, "You should define at least 4 start positions")
        if is_ctf and len(dId2Obj_ctf.keys()) < 16:
            self.log.report({'WARNING'}, "You should define at least 16 ctf start positions, odd"
                " / even index alternatively for blue and red team.")

        for key, value in sorted(dId2Obj.items()):
            f.write("  <start %s/>\n" % stk_utils.getXYZHString(value))
        for key, value in sorted(dId2Obj_ctf.items()):
            f.write("  <ctf-start %s/>\n" % stk_utils.getXYZHString(value))
        if is_ctf:
            f.write("  <red-flag %s/>\n" % stk_utils.getXYZHString(self.m_red_flag))
            f.write("  <blue-flag %s/>\n" % stk_utils.getXYZHString(self.m_blue_flag))

# ------------------------------------------------------------------------------
class LibraryNodeExporter:

    def __init__(self):
        self.m_objects = []

    def __init__(self, log):
        self.m_objects = []
        self.log = log

    def processObject(self, object, stktype):

        if object.proxy is not None and object.proxy.library is not None:
            self.m_objects.append(object)
            return True
        else:
            return False

    def export(self, f):
        import re
        for obj in self.m_objects:
            try:
                path_parts = re.split("/|\\\\", obj.proxy.library.filepath)
                lib_name = path_parts[-2]

                # origin
                originXYZ = stk_utils.getXYZHPRString(obj)

                f.write('  <library name="%s" id=\"%s\" %s>\n' % (lib_name, obj.name, originXYZ))
                if obj.animation_data and obj.animation_data.action and obj.animation_data.action.fcurves and len(obj.animation_data.action.fcurves) > 0:
                    writeIPO(f, obj.animation_data)
                f.write('  </library>\n')
            except:
                self.log.report({'ERROR'}, "Invalid linked object <" + stk_utils.getObjectProperty(obj, "name", obj.name) + "> ")


# ------------------------------------------------------------------------------
class BillboardExporter:

    def __init__(self):
        self.m_objects = []

    def __init__(self, log):
        self.m_objects = []
        self.log = log

    def processObject(self, object, stktype):

        if stktype=="BILLBOARD":
            self.m_objects.append(object)
            return True
        else:
            return False

    def export(self, f):
        for obj in self.m_objects:
            data = obj.data

            # check the face
            face_len = len(data.polygons)
            if face_len == 0:
                self.log.report({'ERROR'}, "Billboard <" + stk_utils.getObjectProperty(obj, "name", obj.name) \
                    + "> must have at least one face")
                return
            if face_len > 1:
                self.log.report({'ERROR'}, "Billboard <" + stk_utils.getObjectProperty(obj, "name", obj.name) \
                    + "> has more than ONE face")
                return

            # check the points
            if len(data.polygons[0].vertices) > 4:
                self.log.report({'ERROR'}, "Billboard <" + stk_utils.getObjectProperty(obj, "name", obj.name)\
                        + "> has more than 4 points")
                return

            if len(obj.material_slots) < 1:
                self.log.report({'ERROR'}, "Billboard <" + stk_utils.getObjectProperty(obj, "name", obj.name)\
                        + "> has no materials")
                return


            try:
                # write in the XML
                # calcul the size and the position
                x_min = data.vertices[0].co[0]
                x_max = x_min
                y_min = data.vertices[0].co[2]
                y_max = y_min
                z_min = data.vertices[0].co[1]
                z_max = z_min
                for i in range(1, 4):
                    x_min = min(x_min, data.vertices[i].co[0])
                    x_max = max(x_max, data.vertices[i].co[0])
                    y_min = min(y_min, data.vertices[i].co[2])
                    y_max = max(y_max, data.vertices[i].co[2])
                    z_min = min(z_min, data.vertices[i].co[1])
                    z_max = max(z_max, data.vertices[i].co[1])

                fadeout_str = ""
                fadeout = stk_utils.getObjectProperty(obj, "fadeout", "false")
                if fadeout == "true":
                    start = float(stk_utils.getObjectProperty(obj, "start", 1.0))
                    end = float(stk_utils.getObjectProperty(obj, "end", 15.0))
                    fadeout_str = "fadeout=\"true\" start=\"%.2f\" end=\"%.2f\""%(start,end)

                node_tree = obj.material_slots[data.polygons[0].material_index].material.node_tree
                f.write('  <object type="billboard" id=\"%s\" texture="%s" xyz="%.2f %.2f %.2f" \n'%
                        (obj.name, stk_utils.searchNodeTreeForImage(node_tree, 1),
                        obj.location[0], obj.location[2], obj.location[1]))
                f.write('             width="%.3f" height="%.3f" %s>\n' %(max(x_max-x_min, z_max-z_min), y_max-y_min, fadeout_str) )
                if obj.animation_data and obj.animation_data.action and obj.animation_data.action.fcurves and len(obj.animation_data.action.fcurves) > 0:
                    writeIPO(f, obj.animation_data)
                f.write('  </object>\n')

            except:
                self.log.report({'ERROR'}, "Invalid billboard <" + stk_utils.getObjectProperty(obj, "name", obj.name) + "> ")


# ------------------------------------------------------------------------------
class LightsExporter:

    def __init__(self):
        self.m_objects = []

    def processObject(self, object, stktype):

        if object.type=="LIGHT" and stktype == "LIGHT":
            self.m_objects.append(object)
            return True
        else:
            return False

    def export(self, f):
        for obj in self.m_objects:
            colR = int(obj.data.color[0] * 255)
            colG = int(obj.data.color[1] * 255)
            colB = int(obj.data.color[2] * 255)

            f.write('  <light %s id=\"%s\" distance="%.2f" energy="%.2f" color="%i %i %i"' \
                    % (stk_utils.getXYZString(obj), obj.name, obj.data.shadow_soft_size, obj.data.energy, colR, colG, colB))
            if_condition = stk_utils.getObjectProperty(obj, "if", "")
            if len(if_condition) > 0:
                f.write(' if=\"%s\"' % if_condition)
            f.write('>\n')
            if obj.animation_data and obj.animation_data.action and obj.animation_data.action.fcurves and len(obj.animation_data.action.fcurves) > 0:
                writeIPO(f, obj.animation_data)
            f.write('  </light>\n')

# ------------------------------------------------------------------------------
class LightShaftExporter:

    def __init__(self):
        self.m_objects = []

    def processObject(self, object, stktype):

        if object.type=="LIGHT" and stktype == "LIGHTSHAFT_EMITTER":
            self.m_objects.append(object)
            return True
        else:
            return False

    def export(self, f):
        for obj in self.m_objects:
            f.write('  <lightshaft %s id=\"%s\" opacity="%.2f" color="%s"/>\n' \
                    % (stk_utils.getXYZString(obj), obj.name, stk_utils.getObjectProperty(obj, "lightshaft_opacity", 0.7), stk_utils.getObjectProperty(obj, "lightshaft_color", "255 255 255")))

# ------------------------------------------------------------------------------
class NavmeshExporter:

    def __init__(self):
        self.m_objects = []

    def __init__(self, log):
        self.m_objects = []
        self.log = log

    def processObject(self, object, stktype):

        if stktype=="NAVMESH":
            is_arena = stk_utils.getSceneProperty(bpy.data.scenes[0], "arena", "false") == "true"
            is_soccer = stk_utils.getSceneProperty(bpy.data.scenes[0], "soccer", "false") == "true"
            if (is_arena or is_soccer):
                self.m_objects.append(object)
            else:
                self.log.report({'WARNING'}, "Navmesh may only be used in battle arenas or soccer field")

            if len(self.m_objects) > 1:
                self.log.report({'WARNING'}, "Cannot have more than 1 navmesh")

            print("exportNavmesh 1")
            return True
        else:
            return False

    def export(self, f):
        return None

    def exportNavmesh(self, sPath):
        print("exportNavmesh 2")
        import bmesh
        if len(self.m_objects) > 0:
            print("exportNavmesh 3")
            with open(sPath+"/navmesh.xml", "w", encoding="utf8", newline="\n") as navmeshfile:
                navmesh_obj = self.m_objects[0]
                bm = bmesh.new()
                mm = navmesh_obj.to_mesh()
                bm.from_mesh(mm)
                om = navmesh_obj.matrix_world
                navmesh_obj.to_mesh_clear()

                navmeshfile.write('<?xml version="1.0" encoding=\"utf-8\"?>\n')
                navmeshfile.write('<navmesh>\n')
                min_height_testing = stk_utils.getObjectProperty(navmesh_obj, "min_height_testing", -1.0)
                max_height_testing = stk_utils.getObjectProperty(navmesh_obj, "max_height_testing", 5.0)
                navmeshfile.write('<height-testing min="%f" max="%f"/>\n' % (min_height_testing, max_height_testing))
                navmeshfile.write('<MaxVertsPerPoly nvp="4" />\n')
                navmeshfile.write('<vertices>\n')

                for vert in bm.verts:
                    navmeshfile.write('<vertex x="%f" y="%f" z="%f" />\n' % ((om@vert.co).x, (om@vert.co).z, (om@vert.co).y))

                navmeshfile.write('</vertices>\n')
                navmeshfile.write('<faces>\n')

                for face in bm.faces:
                    navmeshfile.write('<face indices="')
                    if len(face.verts) != 4:
                        self.log.report({'ERROR'}, 'Use only quad for navmesh, face %d not quad!' % face.index)
                        self.log.report({'ERROR'}, 'To find it out, select the navmesh object and toggle edit mode, than in python console:')
                        self.log.report({'ERROR'}, 'me = bpy.data.objects[\'%s\'].data' % self.m_objects[0].name)
                        self.log.report({'ERROR'}, 'import bmesh')
                        self.log.report({'ERROR'}, 'bm = bmesh.from_edit_mesh(me)')
                        self.log.report({'ERROR'}, 'bm.faces[%d].select = True' % face.index)
                        self.log.report({'ERROR'}, 'bmesh.update_edit_mesh(me, True)')
                        assert False
                    for vert in face.verts:
                        navmeshfile.write('%d ' % vert.index)

                    list_face = []
                    unique_face = []
                    for edge in face.edges:
                        for l_face in edge.link_faces:
                            list_face.append(l_face.index)

                    [unique_face.append(item) for item in list_face if item not in unique_face]
                    unique_face.remove(face.index) #remove current face index

                    navmeshfile.write('" adjacents="')
                    for num in unique_face:
                        navmeshfile.write('%d ' % num)
                    navmeshfile.write('" />\n')

                navmeshfile.write('</faces>\n')
                navmeshfile.write('</navmesh>\n')

# ------------------------------------------------------------------------------
class DrivelineExporter:

    def __init__(self):
        self.lChecks = []
        self.lCannons = []
        self.lDrivelines = []
        self.found_main_driveline = False
        self.lEndCameras = []

    def __init__(self, log):
        self.lChecks = []
        self.lCannons = []
        self.lDrivelines = []
        self.found_main_driveline = False
        self.lEndCameras = []
        self.log = log

    def processObject(self, obj, stktype):

        if stktype=="CHECK" or stktype=="LAP" or stktype=="GOAL":
            self.lChecks.append(obj)
            return True
        if stktype=="CANNONSTART":
            self.lCannons.append(obj)
            return True
        # Check for new drivelines
        elif stktype=="MAIN-DRIVELINE" or \
                stktype=="MAINDRIVELINE"  or \
                stktype=="MAINDL":
            # Main driveline must be the first entry in the list
            self.lDrivelines.insert(0, Driveline(obj, 1, self.log))
            self.found_main_driveline = True
            return True
        elif stktype=="DRIVELINE":
            self.lDrivelines.append(Driveline(obj, 0, self.log))
            return True
        elif obj.type=="CAMERA" and stktype in ['FIXED', 'AHEAD']:
            self.lEndCameras.append(obj)
            return True

        return False

    def export(self, f):
        is_arena = stk_utils.getSceneProperty(bpy.data.scenes[0], "arena", "false") == "true"
        is_soccer = stk_utils.getSceneProperty(bpy.data.scenes[0], "soccer", "false") == "true"
        is_cutscene = stk_utils.getSceneProperty(bpy.data.scenes[0], "cutscene",  "false") == "true"
        if not self.found_main_driveline and not is_arena and not is_soccer and not is_cutscene:
            if len(self.lDrivelines) > 0:
                self.log.report({'WARNING'}, "Main driveline missing, using first driveline as main!")
            elif stk_utils.getSceneProperty(bpy.data.scenes[0], 'is_stk_node', 'false') != 'true':
                self.log.report({'ERROR'}, "No driveline found")

        if len(self.lDrivelines) == 0:
            self.lDrivelines=[None]

        mainDriveline = self.lDrivelines[0]
        if mainDriveline is None and stk_utils.getSceneProperty(bpy.data.scenes[0], 'is_stk_node', 'false') != 'true' and not (is_arena or is_soccer):
            self.log.report({'ERROR'}, "No main driveline found")

        self.lChecks = self.lChecks + self.lCannons # cannons at the end, see #1386

        if self.lChecks or mainDriveline:
            if not self.lChecks:
                self.log.report({'WARNING'}, "No check defined, lap counting will not work properly!")
            self.writeChecks(f, self.lChecks, mainDriveline)

        if self.lEndCameras:
            f.write("  <end-cameras>\n")
            for i in self.lEndCameras:
                type = stk_utils.getObjectProperty(i, "type", "ahead").lower()
                if type=="ahead":
                    type="ahead_of_kart"
                elif type=="fixed":
                    type="static_follow_kart"
                else:
                    log_warning ("Unknown camera type %s - ignored." % type)
                    continue
                xyz = "%f %f %f" % (i.location[0], i.location[2], i.location[1])
                start = stk_utils.getObjectProperty(i, "start", 5)
                f.write("    <camera type=\"%s\" xyz=\"%s\" distance=\"%s\"/> <!-- %s -->\n"%
                        (type, xyz, start, i.name) )
            f.write("  </end-cameras>\n")


    # --------------------------------------------------------------------------
    # Finds the closest driveline from the list lDrivelines to the point p (i.e.
    # the driveline for which the distance between p and the drivelines start
    # point is as small as possible. Returns the index of the closest drivelines.
    def findClosestDrivelineToPoint(self, lDrivelines, p):
        min_index = 0
        min_dist  = lDrivelines[0].getStartDistanceTo(p)
        for i in range(1,len(lDrivelines)):
            driveline=lDrivelines[i]
            dist_new = driveline.getStartDistanceTo(p)
            if dist_new<min_dist:
                min_dist  = dist_new
                min_index = i

        return min_index

    # --------------------------------------------------------------------------
    # Find the driveline from lRemain that is closest to any of the drivelines
    # in lSorted.
    def findClosestDrivelineToDrivelines(self, lRemain, lSorted):
        remain_index                    = 0
        (min_dist, sorted_index, min_quad) = lRemain[0].getDistanceToStart(lSorted)
        for i in range(1, len(lRemain)):
            (dist, index, quad) = lRemain[i].getDistanceToStart(lSorted)
            if dist<min_dist:
                min_dist     = dist
                sorted_index = index
                min_quad     = quad
                remain_index = i
        return (remain_index, sorted_index, min_quad)

    # --------------------------------------------------------------------------
    # Converts a new drivelines. New drivelines have the following structure:
    #   +---+---+--+--...--+--
    #   |   |      |       |
    #   +---+--+---+--...--+--
    # The starting quad of the drivelines is marked by two edges ending in a
    # single otherwise unconnected vertex. These two vertices (and edges) are
    # not used in the actual driveline, they are only used to indicate where
    # the drivelines starts. This data structure is handled in the Driveline
    # class.
    # Additionally, this function sorts the end cameras according to distance
    # to the main driveline - so the first end camera will be the camera
    # closest to the start line etc.
    def convertDrivelinesAndSortEndCameras(self, lDrivelines, lSorted,
                                           lEndCameras):
        # First collect all main drivelines, and all remaining drivelines
        # ---------------------------------------------------------------
        lMain     = []
        lRemain   = []
        for driveline in lDrivelines:
            if driveline.isMain():
                lMain.append(driveline)
            else:
                lRemain.append(driveline)

        # Now collect all main drivelines in one list starting
        # with the closest to 0, then the one closest to the
        # end of the first one, etc
        p          = (0,0,0)
        quad_index = 0
        while lMain:
            min_index = self.findClosestDrivelineToPoint(lMain, p)
            # Move the main driveline with minimal distance to the
            # sorted list.
            lSorted.append(lMain[min_index])
            del lMain[min_index]

            # Set the start quad index for all quads.
            lSorted[-1].setStartQuadIndex(quad_index)
            quad_index = quad_index + lSorted[-1].getNumberOfQuads()

            p = lSorted[-1].getEndPoint()

        # Create a new list for all cameras, which also stores the
        # quad index to which the camera is closest to, the distance
        # to the quad, and the camera object. The order is important
        # since this list is later sorted by quad index, so that the
        # first camera is the first in the list.
        lCamerasDistance = []
        for i in range(len(lEndCameras)):
            cam = lEndCameras[i]
            try:
                (distance, driveline_index, quad_index_camera) = \
                           lSorted[0].getDistanceTo(cam.location, lSorted)
                # Each list contains the index of the closest quad, the
                # distance, and then the camera
                lEndCameras[i] = (driveline_index, quad_index_camera, cam)
            except:
                self.log.report({'WARNING'}, "Problem with the end camera '%s'. Check if the main driveline is " +\
                            "properly defined (check warning messages), and the " +\
                            "settings of the camera."%cam.name)

        lEndCameras.sort()

        # After sorting remove the unnecessary distance and quad index
        for i in range(len(lEndCameras)):
            # Avoid crash in case that some problem with the camera happened,
            # and lEndCameras is just the blender camera, not the tuple
            if type(lEndCameras[i])==type(()):
                lEndCameras[i] = lEndCameras[i][2]

        # There were already two warning messages printed at this stage, so just
        # ignore this to avoid further crashes
        if len(lSorted) < 1:
            return

        # The last main driveline needs to be closed to the first quad.
        # So set a flag in that driveline that it is the last one.
        lSorted[-1].setIsLastMain(lSorted[0])
        quad_index = quad_index + 1

        # Now add the remaining drivelines one at a time. From all remaining
        # drivelines we pick the one closest to the drivelines contained in
        # lSorted.
        while lRemain:
            t = self.findClosestDrivelineToDrivelines(lRemain, lSorted)
            (remain_index, sorted_index, quad_to_index) = t
            lRemain[remain_index].setFromQuad(lSorted[sorted_index],
                                              quad_to_index)
            lSorted.append(lRemain[remain_index])
            del lRemain[remain_index]

            # Set the start quad index for all quads.
            lSorted[-1].setStartQuadIndex(quad_index)
            quad_index = quad_index + lSorted[-1].getNumberOfQuads()

    # --------------------------------------------------------------------------
    # Writes the track.quad file with the list of all quads, and the track.graph
    # file defining a graph node for each quad and a basic connection between
    # all graph nodes.
    def writeQuadAndGraph(self, sPath):
        #start_time = bsys.time()

        lDrivelines = self.lDrivelines
        lEndCameras = self.lEndCameras

        print("Writing quad file --> \t")
        if not lDrivelines:
            print("No main driveline defined, no driveline information exported!!!")
            return

        lSorted = []
        self.convertDrivelinesAndSortEndCameras(lDrivelines, lSorted, lEndCameras)

        # That means that there were some problems with the drivelines, and
        # it doesn't make any sense to continue anyway
        if not lSorted:
            return

        # Stores the first quad number (and since quads = graph nodes the node
        # number) of each section of the track. I.e. the main track starts with
        # quad 0, then the first alternative way, ...
        lStartQuad         = [0]
        dSuccessor         = {}
        last_main_lap_quad = 0
        count              = 0

        with open(sPath + "/quads.xml", "w", encoding="utf8", newline="\n") as f:
            f.write("<?xml version=\"1.0\" encoding=\"utf-8\"?>\n")
            f.write("<quads>\n")
            f.write('  <height-testing min="%f" max="%f"/>\n' %\
            (lSorted[0].min_height_testing, lSorted[0].max_height_testing))

            for driveline in lSorted:
                driveline.writeQuads(f)

            f.write("</quads>\n")
            #print bsys.time() - start_time,"seconds. "

        #start_time = bsys.time()
        print("Writing graph file --> \t")
        with open(sPath + "/graph.xml", "w", encoding="utf8", newline="\n") as f:
            f.write("<?xml version=\"1.0\"?> encoding=\"utf-8\"?>\n")
            f.write("<graph>\n")
            f.write("  <!-- First define all nodes of the graph, and what quads they represent -->\n")
            f.write("  <node-list from-quad=\"%d\" to-quad=\"%d\"/>  <!-- map each quad to a node  -->\n"\
                    %(0, lSorted[-1].getLastQuadIndex()))

            f.write("  <!-- Define the main loop -->\n");
            last_main = None
            for i in lSorted:
                if i.isMain():
                    last_main = i
                else:
                    break

            # The main driveline is written as a simple loop
            f.write("  <edge-loop from=\"%d\" to=\"%d\"/>\n" %
                    (0, last_main.getLastQuadIndex()) )

            # Each non-main driveline writes potentially three entries in the
            # graph file: connection to the beginning of this driveline, the
            # driveline quads themselves, and a connection from the end of the
            # driveline to another driveline. But this can result in edged being
            # written more than once: consider two non-main drivelines A and B
            # which are connected to each other. Then A will write the edge from
            # A to B as its end connection, and B will write the same connection
            # as its begin connection. To avoid this, we keep track of all
            # written from/to edges, and only write one if it hasn't been written.
            dWrittenEdges={}
            # Now write the remaining drivelines
            for driveline in lSorted:
                # Mainline was already written, so ignore it
                if driveline.isMain(): continue

                f.write("  <!-- Shortcut %s -->\n"%driveline.getName())
                # Write the connection from an already written quad to this
                fr = driveline.getFromQuad()
                to = driveline.getFirstQuadIndex()
                if (fr,to) not in dWrittenEdges:
                    f.write("  <edge from=\"%d\" to=\"%d\"/>\n" %(fr, to))
                    #if to.isEnabled() and fr.isEnabled():
                    #    f.write("  <edge from=\"%d\" to=\"%d\"/>\n" %(fr, to))
                    #elif to.isEnabled():
                    #    f.write("  <!-- %s disabled <edge from=\"%d\" to=\"%d\"/> -->\n" \
                    #            %(fr.getName(), fr, to))
                    #else:
                    #    f.write("  <!-- %s disabled <edge from=\"%d\" to=\"%d\"/> -->\n"
                    #            %(to.getName(), fr, to))
                    dWrittenEdges[ (fr, to) ] = 1
                if driveline.getFirstQuadIndex()< driveline.getLastQuadIndex():
                    f.write("  <edge-line from=\"%d\" to=\"%d\"/>\n" \
                            %(driveline.getFirstQuadIndex(),
                              driveline.getLastQuadIndex()))
                fr = driveline.getLastQuadIndex()
                to = driveline.computeSuccessor(lSorted)
                if (fr, to) not in dWrittenEdges:
                    f.write("  <edge from=\"%d\" to=\"%d\"/>\n" %(fr, to))
                    dWrittenEdges[ (fr, to) ] = 1
            f.write("</graph>\n")
        #print bsys.time()-start_time,"seconds. "

    # Write out a goal line
    def writeGoal(self, f, goal):
        if len(goal.data.vertices) != 2:
            self.log.report({'WARNING'}, "Goal line is not a line made of 2 vertices as expected")

        goal_matrix = goal.rotation_euler.to_matrix()

        goal_pt1 = goal.data.vertices[0].co @ goal_matrix + goal.location
        goal_pt2 = goal.data.vertices[1].co @ goal_matrix + goal.location

        first_goal_string = ""
        if stk_utils.getObjectProperty(goal, "first_goal", "false") == "true":
            first_goal_string=" first_goal=\"true\" "

        f.write('    <goal p1="%.2f %.2f %.2f" p2="%.2f %.2f %.2f" %s/>\n'%\
                (goal_pt1[0], goal_pt1[2], goal_pt1[1],
                 goal_pt2[0], goal_pt2[2], goal_pt2[1],
                 first_goal_string))

    # Writes out all cannon checklines.
    def writeCannon(self, f, cannon):

        start = cannon

        endSegmentName = stk_utils.getObjectProperty(start, "cannonend", "")
        if len(endSegmentName) == 0 or endSegmentName not in bpy.data.objects:
            self.log.report({'ERROR'}, "Cannon " + cannon.name + " end is not defined")
            return

        end = bpy.data.objects[endSegmentName]

        if len(start.data.vertices) != 2:
            self.log.report({'WARNING'}, "Cannon start " + start.name + " is not a line made of 2 vertices as expected")
        if len(end.data.vertices) != 2:
            self.log.report({'WARNING'}, "Cannon end " + end.name + " is not a line made of 2 vertices as expected")

        curvename = stk_utils.getObjectProperty(start, "cannonpath", "")
        start_pt1 = start.matrix_world @ start.data.vertices[0].co
        start_pt2 = start.matrix_world @ start.data.vertices[1].co
        end_pt1 = end.matrix_world @ end.data.vertices[0].co
        end_pt2 = end.matrix_world @ end.data.vertices[1].co

        f.write('    <cannon p1="%.2f %.2f %.2f" p2="%.2f %.2f %.2f" target-p1="%.2f %.2f %.2f" target-p2="%.2f %.2f %.2f">\n'%\
                (start_pt1[0], start_pt1[2], start_pt1[1],
                 start_pt2[0], start_pt2[2], start_pt2[1],
                 end_pt1[0],   end_pt1[2],   end_pt1[1],
                 end_pt2[0],   end_pt2[2],   end_pt2[1]))

        if len(curvename) > 0:
            writeBezierCurve(f, bpy.data.objects[curvename], \
                             stk_utils.getObjectProperty(start, "cannonspeed", 50.0), "const" )

        f.write('    </cannon>\n')

    # --------------------------------------------------------------------------
    # Writes out all checklines.
    # \param lChecks All check meshes
    # \param mainDriveline The main driveline, from which the lap
    #        counting check line is determined.
    def writeChecks(self, f, lChecks, mainDriveline):
        f.write("  <checks>\n")

        # A dictionary containing a list of indices of check structures
        # that belong to this group.
        dGroup2Indices = {"lap":[0]}
        # Collect the indices of all check structures for all groups
        ind = 1
        for obj in lChecks:
            name = stk_utils.getObjectProperty(obj, "type", obj.name.lower()).lower()
            if len(name) == 0: name = obj.name.lower()

            type = stk_utils.getObjectProperty(obj, "type", "")
            if type == "cannonstart" or type == "cannonend":
                continue

            if name!="lap":
                name = stk_utils.getObjectProperty(obj, "name", obj.name.lower()).lower()
            if name in dGroup2Indices:
                dGroup2Indices[name].append(ind)
            else:
                dGroup2Indices[name] = [ ind ]
            ind = ind + 1

        print("**** dGroup2Indices:", dGroup2Indices)

        if mainDriveline:
            lap = mainDriveline.getStartEdge()

            strict_lapline = mainDriveline.isStrictLapline()

            if lap[0] is None:
                return # Invalid driveline (a message will have been printed)

            coord = lap[0]
            min_h = coord[2]
            if coord[2] < min_h: min_h = coord[2]

            # The main driveline is always the first entry, so remove
            # only the first entry to get the list of all other lap lines
            l = dGroup2Indices["lap"]

            from functools import reduce
            sSameGroup = reduce(lambda x,y: str(x)+" "+str(y), l, "")

            activate = mainDriveline.getActivate()
            if activate:
                group = activate.lower()

                if not group or group not in dGroup2Indices:
                    self.log.report({'WARNING'}, "Activate group '%s' not found!"%group)
                    print("Ignored - but lap counting might not work correctly.")
                    print("Make sure there is an object of type 'check' with")
                    print("the name '%s' defined."%group)
                    activate = ""
                else:
                    activate = reduce(lambda x,y: str(x)+" "+str(y), dGroup2Indices[group])
            else:
                group = ""
                activate = ""
                self.log.report({'WARNING'}, "Warning : the main driveline does not activate any checkline. Lap counting and kart rescue will not work correctly.")
        else:
            # No main drive defined, print a warning and add some dummy
            # driveline (makes the rest of this code easier)
            lap        = [ [-1, 0], [1, 0] ]
            min_h      = 0
            sSameGroup = ""
            activate = ""
            strict_lapline = True

        if sSameGroup:
            sSameGroup="same-group=\"%s\""%sSameGroup.strip()

        if activate:
            activate = "other-ids=\"%s\""%activate

        if not strict_lapline:
            f.write("    <check-lap kind=\"lap\" %s %s />\n"%(sSameGroup, activate))
        else:
            f.write("    <check-line kind=\"lap\" p1=\"%.2f %.2f\" p2=\"%.2f %.2f\"\n"% \
                    (lap[0][0], lap[0][1],
                     lap[1][0], lap[1][1] )  )
            f.write("                min-height=\"%.2f\" %s %s/>\n"% (min_h, sSameGroup, activate) )

        ind = 1
        for obj in lChecks:
            try:
                type = stk_utils.getObjectProperty(obj, "type", "")
                if type == "cannonstart":
                    self.writeCannon(f, obj)
                    continue
                elif type == "cannonend":
                    continue
                elif type == "goal":
                    self.writeGoal(f, obj)
                    continue

                mesh = obj.data.copy()
                # Convert to world space
                mesh.transform(obj.matrix_world)
                # One of lap, activate, toggle, ambient
                activate = stk_utils.getObjectProperty(obj, "activate", "")
                kind=" "
                if activate:
                    group = activate.lower()
                    if group not in dGroup2Indices:
                        self.log.report({'WARNING'}, "Activate group '%s' not found!"%group)
                        print("Ignored - but lap counting might not work correctly.")
                        print("Make sure there is an object of type 'check' with")
                        print("the name '%s' defined."%group)
                        continue
                    s = reduce(lambda x,y: str(x)+" "+str(y), dGroup2Indices[group])
                    kind = " kind=\"activate\" other-ids=\"%s\" "% s

                toggle = stk_utils.getObjectProperty(obj, "toggle", "")
                if toggle:
                    group = toggle.lower()
                    if group not in dGroup2Indices:
                        self.log.report({'WARNING'}, "Toggle group '%s' not found!"%group)
                        print("Ignored - but lap counting might not work correctly.")
                        print("Make sure there is an object of type 'check' with")
                        print("the name '%s' defined."%group)
                        continue
                    s = reduce(lambda x,y: str(x)+" "+str(y), dGroup2Indices[group])
                    kind = " kind=\"toggle\" other-ids=\"%s\" "% s

                lap = stk_utils.getObjectProperty(obj, "type", obj.name).upper()
                if lap[:3]=="LAP":
                    kind = " kind=\"lap\" "  # xml needs a value for an attribute
                    activate = stk_utils.getObjectProperty(obj, "activate", "")
                    if activate:
                        group = activate.lower()
                        if group not in dGroup2Indices:
                            self.log.report({'WARNING'}, "Activate group '%s' not found for lap line!"%group)
                            print("Ignored - but lap counting might not work correctly.")
                            print("Make sure there is an object of type 'check' with")
                            print("the name '%s' defined."%group)
                            continue
                        s = reduce(lambda x,y: str(x)+" "+str(y), dGroup2Indices[group])
                        kind = "%sother-ids=\"%s\" "% (kind, s)

                ambient = stk_utils.getObjectProperty(obj, "ambient", "").upper()
                if ambient:
                    kind=" kind=\"ambient-light\" "

                # Get the group name this object belongs to. If the objects
                # is of type lap then 'lap' is the group name, otherwise
                # it's taken from the name property (or the object name).
                name = stk_utils.getObjectProperty(obj, "type", obj.name.lower()).lower()
                if name!="lap":
                    name = stk_utils.getObjectProperty(obj, "name", obj.name.lower()).lower()
                    if len(name) == 0: name = obj.name.lower()

                # Get the list of indices of this group, excluding
                # the index of the current object. So create a copy
                # of the list and remove the current index
                l = dGroup2Indices[name][:]
                sSameGroup = reduce(lambda x,y: str(x)+" "+str(y), l, "")
                ind = ind + 1

                if len(mesh.vertices)==2:   # Check line
                    f.write("    <check-line%sp1=\"%.2f %.2f %.2f\" p2=\"%.2f %.2f %.2f\"\n" %
                            (kind, mesh.vertices[0].co[0], mesh.vertices[0].co[2], mesh.vertices[0].co[1],
                             mesh.vertices[1].co[0], mesh.vertices[1].co[2], mesh.vertices[1].co[1]   )  )

                    f.write("                same-group=\"%s\"/>\n" \
                            % sSameGroup.strip()  )
                else:
                    radius = 0
                    for v in mesh.vertices:
                        r = (obj.location[0]-v[0])*(obj.location[0]-v[0]) + \
                            (obj.location[1]-v[1])*(obj.location[1]-v[1]) + \
                            (obj.location[2]-v[2])*(obj.loc[2]-v[2])
                        if r > radius:
                            radius = r

                    radius = math.sqrt(radius)
                    inner_radius = stk_utils.getObjectProperty(obj, "inner_radius", radius)
                    color = stk_utils.getObjectProperty(obj, "color", "255 120 120 120")
                    f.write("    <check-sphere%sxyz=\"%.2f %.2f %.2f\" radius=\"%.2f\"\n" % \
                            (kind, obj.location[0], obj.location[2], obj.location[1], radius) )
                    f.write("                  same-group=\"%s\"\n"%sSameGroup.strip())
                    f.write("                  inner-radius=\"%.2f\" color=\"%s\"/>\n"% \
                            (inner_radius, color) )
            except:
                self.log.report({'ERROR'}, "Error exporting checkline " + obj.name + ", make sure it is properly formed")
        f.write("  </checks>\n")

# ==============================================================================
# A special class to store a driveline.
class Driveline:
    def __init__(self, driveline, is_main, log):
        self.name      = driveline.name
        self.is_main   = is_main
        self.log = log
        # Transform the mesh to the right coordinates.
        self.mesh      = driveline.data.copy()
        self.mesh.transform(driveline.matrix_world)
        # Convert the mesh into a dictionary: each vertex is a key to a
        # list of neighbours.
        self.createNeighbourDict()
        self.defineStartVertex()
        self.convertToLists()
        self.from_quad=None
        self.from_driveline=None
        self.to_driveline=None
        self.is_last_main = 0
        # Invisible drivelines are not shown in the minimap
        self.invisible = stk_utils.getObjectProperty(driveline, "invisible", "false")
        self.ai_ignore = stk_utils.getObjectProperty(driveline, "ai_ignore", "false")
        self.direction = stk_utils.getObjectProperty(driveline, "direction", "both")
        self.enabled   = not stk_utils.getObjectProperty(driveline, "disable",   0)
        self.activate  = stk_utils.getObjectProperty(driveline, "activate", None)
        self.strict_lap = stk_utils.convertTextToYN(stk_utils.getObjectProperty(driveline,
                                                      "strict_lapline", "N") ) \
                           == "Y"
        self.min_height_testing = stk_utils.getObjectProperty(driveline, "min_height_testing", -1.0)
        self.max_height_testing = stk_utils.getObjectProperty(driveline, "max_height_testing", 5.0)

    # --------------------------------------------------------------------------
    # Returns the name of the driveline
    def getName(self):
        return self.name
    # --------------------------------------------------------------------------
    # Returns if this is a main driveline or not.
    def isMain(self):
        return self.is_main
    # --------------------------------------------------------------------------
    # Returns if this driveline is disabled.
    def isEnabled(self):
        return self.enabled
    # --------------------------------------------------------------------------
    # Returns the 'activate' property of the driveline object.
    def getActivate(self):
        return self.activate
    # --------------------------------------------------------------------------
    # Returns if this driveline requests strict lap counting (i.e. exactly
    # crossing the line between the start vertices)
    def isStrictLapline(self):
        return self.strict_lap
    # --------------------------------------------------------------------------
    # Stores that the start quad of this driveline is connected to quad
    # quad_index of quad driveline.
    def setFromQuad(self, driveline, quad_index):
        # Convert the relative to driveline quad index to the global index:
        self.from_quad      = driveline.getFirstQuadIndex()+quad_index
        self.from_driveline = driveline
    # --------------------------------------------------------------------------
    def setToDriveline(self, driveline):
        self.to_driveline = driveline
    # --------------------------------------------------------------------------
    # Returns the global index of the quad this start point is connected to.
    def getFromQuad(self):
        return self.from_quad
    # --------------------------------------------------------------------------
    # Returns the number of quads of this driveline
    def getNumberOfQuads(self):
        return len(self.lCenter)
    # --------------------------------------------------------------------------
    # Stores the index of the first quad in this driveline in the global
    # quad index.
    def setStartQuadIndex(self, n):
        self.global_quad_index_start = n
    # --------------------------------------------------------------------------
    # Returns the start index for this driveline in the global numbering of
    # all quads
    def getFirstQuadIndex(self):
        return self.global_quad_index_start
    # --------------------------------------------------------------------------
    # Returns the global index of the last quad in this driveline.
    def getLastQuadIndex(self):
        return self.global_quad_index_start+len(self.lCenter)-1
    # --------------------------------------------------------------------------
    # Returns the start edge, which is the lap counting line for the main
    # drivelines. See defineStartVertex() for setting self.start_line.
    def getStartEdge(self):
        return self.start_line
    # --------------------------------------------------------------------------
    # This driveline is the last main driveline. This means that it will get
    # one additional quad added to connect this to the very first quad. Since
    # the values are not actually needed (see write function), the arrays have
    # to be made one element larger to account for this additional quad (e.g.
    # in calls to getNumberOfQuads etc).
    def setIsLastMain(self, first_driveline):
        self.is_last_main = 1
        cp=[]

        for i in range(3):

            if self.lRight[-1] is None or self.lLeft[-1] is None:
                return # Invalid driveline (an error message will have been printed)

            cp.append((self.mesh.vertices[self.lLeft[-1]].co[i] +
                       first_driveline.mesh.vertices[first_driveline.lLeft[0]].co[i]+
                       self.mesh.vertices[self.lRight[-1]].co[i] +
                       first_driveline.mesh.vertices[first_driveline.lRight[0]].co[i])*0.25)

        self.lCenter.append(cp)
        self.lLeft.append(None)
        self.lRight.append(None)

    # --------------------------------------------------------------------------
    # This creates a dictionary for a mesh which contains for each vertex a list
    # of all its neighbours.
    def createNeighbourDict(self):
        self.dNext = {}
        for e in self.mesh.edges:
            if e.vertices[0] in self.dNext:
                self.dNext[e.vertices[0]].append(e.vertices[1])
            else:
                self.dNext[e.vertices[0]] = [e.vertices[1]]

            if e.vertices[1] in self.dNext:
                self.dNext[e.vertices[1]].append(e.vertices[0])
            else:
                self.dNext[e.vertices[1]] = [e.vertices[0]]

    # --------------------------------------------------------------------------
    # This helper function determines the start vertex for a driveline.
    # Details are documented in convertDrivelines. It returns as list with
    # the two starting lines.
    def defineStartVertex(self):
        # Find all vertices with exactly two neighbours
        self.lStart = []
        for i in self.dNext.keys():
            if len(self.dNext[i])==1:
                self.lStart.append( i )

        if len(self.lStart)!=2:
            self.log.report({'ERROR'}, "Driveline '%s' is incorrectly formed, cannot find the two 'antennas' that indicate where the driveline starts." % self.name)
            self.start_point = (0,0,0)
            return

        print("self.lStart[0] =", self.lStart[0])
        print("self.lStart[1] =", self.lStart[1])

        start_coord_1 = self.mesh.vertices[self.lStart[0]].co
        start_coord_2 = self.mesh.vertices[self.lStart[1]].co

        # Save the middle of the first quad, which is used later for neareast
        # quads computations.
        self.start_point = ((start_coord_1[0] + start_coord_2[0])*0.5,
                            (start_coord_1[1] + start_coord_2[1])*0.5,
                            (start_coord_1[2] + start_coord_2[2])*0.5 )

    # --------------------------------------------------------------------------
    # Returns the startline of this driveline
    def getStartPoint(self):
        return self.start_point
    # --------------------------------------------------------------------------
    # Returns the distance of the start point from a given point
    def getStartDistanceTo(self, p):
        dx=self.start_point[0]-p[0]
        dy=self.start_point[1]-p[1]
        dz=self.start_point[2]-p[2]
        return dx*dx+dy*dy+dz*dz
    # --------------------------------------------------------------------------
    # Convert the dictionary of list of neighbours to two lists - one for the
    # left side, one for the right side.
    def convertToLists(self):

        if len(self.lStart) < 2:
            self.lLeft = [None, None]
            self.lRight = [None, None]
            self.start_line = (None, None)
            self.end_point = (0,0,0)
            self.lCenter = []
            return

        self.lLeft   = [self.lStart[0], self.dNext[self.lStart[0]][0]]
        self.lRight  = [self.lStart[1], self.dNext[self.lStart[1]][0]]
        self.lCenter = []

        # this is for error handling only
        processed_vertices = {}
        processed_vertices[self.lStart[0]] = True
        processed_vertices[self.lStart[1]] = True

        # The quads can be either clockwise or counter-clockwise oriented. STK
        # expectes counter-clockwise, so if the orientation is wrong, swap
        # left and right side.

        left_0_coord = self.mesh.vertices[self.lLeft[0]].co
        #left_1_coord = self.mesh.vertices[self.lLeft[1]].co
        right_0_coord = self.mesh.vertices[self.lRight[0]].co
        right_1_coord = self.mesh.vertices[self.lRight[1]].co

        if (right_1_coord[0] - left_0_coord[0])*(right_0_coord[1] - left_0_coord[1]) \
         - (right_1_coord[1] - left_0_coord[1])*(right_0_coord[0] - left_0_coord[0]) > 0:
            r   = self.lRight
            self.lRight = self.lLeft
            self.lLeft  = r

        # Save start edge, which will become the main lap counting line
        # (on the main driveline). This must be done here after potentially
        # switching since STK assumes that the first point of a check line (to
        # which the first line of the main driveline is converted) is on the
        # left side (this only applies for the lap counting line, see
        # Track::setStartCoordinates/getStartTransform).
        self.start_line = (self.mesh.vertices[self.lLeft[1]].co, self.mesh.vertices[self.lRight[1]].co)

        count=0
        # Just in case that we have an infinite loop due to a malformed graph:
        # stop after 10000 vertices
        max_count = 10000
        warning_printed = 0

        while count < max_count:
            count = count + 1

            processed_vertices[self.lLeft[-1]] = True

            # Get all neighbours. One is the previous point, one
            # points to the opposite side - we need the other one.
            neighb = self.dNext[self.lLeft[-1]]
            next_left = []
            for i in neighb:
                if i==self.lLeft[-2]: continue   # pointing backwards
                if i==self.lRight[-1]: continue  # to opposite side
                next_left.append(i)

            if len(next_left) == 0:
                # No new element found --> this must be the end
                # of the list!!
                break

            if len(next_left)!=1 and not warning_printed:
                lcoord = self.mesh.vertices[self.lLeft[-1]].co
                rcoord = self.mesh.vertices[self.lRight[-1]].co
                self.log.report({'WARNING'}, "Broken driveline at or around point ({0}, {1}, {2})".format\
                            (lcoord[0], lcoord[1], lcoord[2]))
                print("Potential successors :")
                for i in range(len(next_left)):
                    nextco = self.mesh.vertices[next_left[i]].co
                    print ("Successor %d: %f %f %f" % \
                          (i, nextco[0], nextco[1], nextco[2]))
                print ("It might also possible that the corresponding right driveline point")
                print (rcoord[0],rcoord[1],rcoord[2])
                print ("has some inconsistencies.")
                print ("The drivelines will most certainly not be useable.")
                print ("Further warnings are likely and will be suppressed.")
                warning_printed = 1
                self.log.report({'ERROR'}, "Problems with driveline detected, check console for details!")
                return

            self.lLeft.append(next_left[0])


            processed_vertices[self.lRight[-1]] = True

            # Same for other side:
            neighb = self.dNext[self.lRight[-1]]
            next_right = []

            for i in neighb:
                if i==self.lRight[-2]: continue   # pointing backwards
                # Note lLeft has already a new element appended,
                # so we have to check for the 2nd last element!
                if i==self.lLeft[-2]: continue  # to opposite side
                next_right.append(i)

            if len(next_right)==0:
                lcoord = self.mesh.vertices[self.lLeft[-1]].co
                rcoord = self.mesh.vertices[self.lRight[-1]].co
                self.log.report({'WARNING'}, "Malformed driveline at or around points ({0}, {1}, {2}) and ({3}, {4}, {5})".format\
                             (lcoord[0],lcoord[1],lcoord[2],
                              rcoord[0],rcoord[1],rcoord[2]))
                print ("No more vertices on right side of quad line, but there are")
                print ("still points on the left side. Check the points:")
                print ("left: ", lcoord[0],lcoord[1],lcoord[2])
                print ("right: ", rcoord[0],rcoord[1],rcoord[2])
                print ("Last left point is ignored.")
                break

            if len(next_right)!=1 and not warning_printed:
                lcoord = self.mesh.vertices[self.lLeft[-1]].co
                rcoord = self.mesh.vertices[self.lRight[-1]].co

                self.log.report({'ERROR'}, "Invalid driveline at or around point ({0}, {1}, {2})".format\
                          (rcoord[0],rcoord[1],rcoord[2]))
                print ("Warning: More than one potential succesor found for right driveline point")
                print (rcoord[0],rcoord[1],rcoord[2],":")
                #for i in range(len(next_right)):
                #    print ("Successor %d: %f %f %f" % \
                #          (i,next_right[i][0],next_right[i][1],next_right[i][2]))
                print ("It might also possible that the corresponding left driveline point")
                print (lcoord[0],lcoord[1],lcoord[2])
                print ("has some inconsistencies.")
                print ("The drivelines will most certainly not be useable.")
                print ("Further warnings are likely and will be suppressed.")
                warning_printed = 1
                self.log.report({'ERROR'}, "Problems with driveline detected!")
                return
            self.lRight.append(next_right[0])

            processed_vertices[self.lRight[-1]] = True
            processed_vertices[self.lLeft[-1]] = True
            processed_vertices[self.lRight[-2]] = True
            processed_vertices[self.lLeft[-2]] = True

            cp=[]
            for i in range(3):
                cp.append((self.mesh.vertices[self.lLeft[-2]].co[i] +
                           self.mesh.vertices[self.lLeft[-1]].co[i] +
                           self.mesh.vertices[self.lRight[-2]].co[i] +
                           self.mesh.vertices[self.lRight[-1]].co[i])*0.25)
            self.lCenter.append(cp)

        if count>=max_count and not warning_printed:
            self.log.report({'WARNING'}, "Warning, Only the first %d vertices of driveline '%s' are exported" %\
                        (max_count, self.name))

        if warning_printed != 1:

            not_connected = None
            not_connected_distance = 99999

            for v in self.dNext:
                if not v in processed_vertices:

                    # find closest connected vertex (this is only to improve the error message)
                    for pv in processed_vertices:
                        dist = (self.mesh.vertices[v].co - self.mesh.vertices[pv].co).length
                        if dist < not_connected_distance:
                            not_connected_distance = dist
                            not_connected = v

            if not_connected:
                self.log.report({'WARNING'}, "Warning, driveline '%s' appears to be broken in separate sections. Vertex at %f %f %f is not connected with the rest" % \
                                    (self.name,
                                     self.mesh.vertices[not_connected].co[0],
                                     self.mesh.vertices[not_connected].co[1],
                                     self.mesh.vertices[not_connected].co[2]))


        # Now remove the first two points, which are only used to indicate
        # the starting point:
        del self.lLeft[0]
        del self.lRight[0]
        self.end_point =((self.mesh.vertices[self.lLeft[-1]].co[0] +
                          self.mesh.vertices[self.lRight[-1]].co[0])*0.5,
                         (self.mesh.vertices[self.lLeft[-1]].co[1] +
                          self.mesh.vertices[self.lRight[-1]].co[1])*0.5,
                         (self.mesh.vertices[self.lLeft[-1]].co[2] +
                          self.mesh.vertices[self.lRight[-1]].co[2])*0.5 )

    # --------------------------------------------------------------------------
    # Returns the end point of this driveline
    def getEndPoint(self):
        return self.end_point

    # --------------------------------------------------------------------------
    def getDistanceToStart(self, lDrivelines):
        return self.getDistanceTo(self.start_point, lDrivelines)

    # --------------------------------------------------------------------------
    # Returns the shortest distance to any of the drivelines in the list
    # lDrivelines from the given point p (it's actually a static function).
    # The distance is defined to be the shortest distance from the
    # start point of this driveline to all quads of all drivelines in
    # lDrivelines. This function returns the distance, the index of the
    # driveline in lDrivelines, and the local index of the quad within this
    # driveline as a tuple.
    def getDistanceTo(self, p, lDrivelines):
        if not lDrivelines: return (None, None, None)

        (min_dist, min_quad_index) = lDrivelines[0].getMinDistanceToPoint(p)
        min_driveline_index        = 0
        for i in range(1, len(lDrivelines)):
            if lDrivelines[i]==self: continue   # ignore itself
            (dist, quad_index) = lDrivelines[i].getMinDistanceToPoint(p)
            if dist < min_dist:
                min_dist            = dist
                min_quad_index      = quad_index
                min_driveline_index = i
        return (min_dist, min_driveline_index, min_quad_index)

    # --------------------------------------------------------------------------
    # Returns the minimum distance from the center point of each quad to the
    # point p.
    def getMinDistanceToPoint(self, p):
        pCenter   = self.lCenter[0]
        dx        = pCenter[0]-p[0]
        dy        = pCenter[1]-p[1]
        dz        = pCenter[2]-p[2]
        min_dist  = dx*dx+dy*dy+dz*dz
        min_index = 0
        for i in range(1, len(self.lCenter)):
            pCenter = self.lCenter[i]
            dx      = pCenter[0]-p[0]
            dy      = pCenter[1]-p[1]
            dz      = pCenter[2]-p[2]
            d       = dx*dx+dy*dy+dz*dz
            if d<min_dist:
                min_dist  = d
                min_index = i
        return (min_dist, min_index)

    # --------------------------------------------------------------------------
    # Determine the driveline from lSorted which is closest to this driveline's
    # endpoint (closest meaning: having a quad that is closest).
    def computeSuccessor(self, lSorted):
        (dist, driveline_index, quad_index)=self.getDistanceTo(self.end_point,
                                                               lSorted)
        return quad_index + lSorted[driveline_index].getFirstQuadIndex()

    # --------------------------------------------------------------------------
    # Writes the quads into a file.
    def writeQuads(self, f):

        if self.lLeft[0] is None or self.lRight[0] is None:
            return # Invalid driveline (a message will have been printed)
        if self.lLeft[1] is None or self.lRight[1] is None:
            return # Invalid driveline (a message will have been printed)

        l   = self.mesh.vertices[self.lLeft[0]].co
        r   = self.mesh.vertices[self.lRight[0]].co
        l1  = self.mesh.vertices[self.lLeft[1]].co
        r1  = self.mesh.vertices[self.lRight[1]].co

        if self.invisible and self.invisible=="true":
            sInv = " invisible=\"yes\" "
        else:
            sInv = " "

        # AI-ignore will be applied to the first and last quad (to account for forward and reverse mode)
        if self.ai_ignore and self.ai_ignore=="true":
            sAIIgnore = "ai-ignore=\"yes\" "
        else:
            sAIIgnore = " "

        if self.direction and self.direction != "both":
            sDirection = "direction=\"" + self.direction + "\" "
        else:
            sDirection = " "

        max_index = len(self.lLeft) - 1

        # If this is the last main driveline, the last quad is a dummy element
        # added by setLastMain(). So the number of elements is decreased by
        # one.
        if self.is_last_main:
            max_index = max_index - 1

        f.write("  <!-- Driveline: %s -->\n"%self.name)
        # Note that only the first quad must be marked with ai-ignore
        # (this results that the AI will not go to the first quad, but
        # if it should end up somewhere on the shortcut, it will
        # continue to drive on the shortcut.
        f.write("  <quad%s%s%sp0=\"%.3f %.3f %.3f\" p1=\"%.3f %.3f %.3f\" p2=\"%.3f %.3f %.3f\" p3=\"%.3f %.3f %.3f\"/>\n" \
            %(sInv, sAIIgnore, sDirection, l[0],l[2],l[1], r[0],r[2],r[1], r1[0],r1[2],r1[1], l1[0],l1[2],l1[1]) )
        for i in range(1, max_index):
            if self.lRight[i+1] is None: return # broken driveline (messages will already have been printed)

            l1  = self.mesh.vertices[self.lLeft[i+1]].co
            r1  = self.mesh.vertices[self.lRight[i+1]].co
            f.write("  <quad%s%s%sp0=\"%d:3\" p1=\"%d:2\" p2=\"%.3f %.3f %.3f\" p3=\"%.3f %.3f %.3f\"/>\n" \
                    %(sInv,sAIIgnore if i == max_index - 1 else "",sDirection,self.global_quad_index_start+i-1, self.global_quad_index_start+i-1, \
                  r1[0],r1[2],r1[1], l1[0],l1[2],l1[1]) )
        if self.is_last_main:
            f.write("  <quad%sp0=\"%d:3\" p1=\"%d:2\" p2=\"0:1\" p3=\"0:0\"/>\n"\
                    % (sInv, self.global_quad_index_start+max_index-1, \
                             self.global_quad_index_start+max_index-1))
