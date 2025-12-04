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

import bpy, datetime, sys, os, struct, math, string, re, random, shutil, traceback
from mathutils import *
from . import stk_utils, stk_panel, stk_track_utils

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

def writeIPO(self, f, anim_data):
    #dInterp = {IpoCurve.InterpTypes.BEZIER:        "bezier",
    #           IpoCurve.InterpTypes.LINEAR:        "linear",
    #           IpoCurve.InterpTypes.CONST:         "const"          }
    #dExtend = {IpoCurve.ExtendTypes.CONST:         "const",
    #           IpoCurve.ExtendTypes.EXTRAP:        "extrap",
    #           IpoCurve.ExtendTypes.CYCLIC_EXTRAP: "cyclic_extrap",
    #           IpoCurve.ExtendTypes.CYCLIC:        "cyclic"         }
    
    ipo = get_fcurves(anim_data)
    if ipo is None:
        return

    # ==== Possible values returned by blender ====
    # fcurves[0].data_path
    #    location, rotation_euler, scale
    # fcurves[0].extrapolation
    #    CONSTANT, LINEART
    # fcurves[0].keyframe_points[0].interpolation
    #    CONSTANT, LINEAR, BEZIER

    # Swap Y and Z axis
    axes = ['X', 'Z', 'Y']

    for curve in ipo:

        if curve.data_path == 'location':
            name = "Loc" + axes[curve.array_index]
        elif curve.data_path == 'rotation_euler':
            name = "Rot" + axes[curve.array_index]
        elif curve.data_path == 'scale':
            name = "Scale" + axes[curve.array_index]
        else:
            if "pose.bones" not in curve.data_path: # we ignore bone curves
                self.log.report({'WARNING'}, "Unknown curve type " + curve.data_path)
            continue

        extrapolation = "const"

        for modifier in curve.modifiers:
            if modifier.type == 'CYCLES':
                extrapolation = "cyclic"
                break

        # If any point is bezier we'll export as Bezier
        interpolation = "linear"
        for bez in curve.keyframe_points:
            if bez.interpolation=='BEZIER':
                interpolation = "bezier"
                break

        # Rotations are stored in randians
        if name[:3]=="Rot":
            factor=-57.29577951 # 180/PI
        else:
            factor=1
        f.write("    <curve channel=\"%s\" interpolation=\"%s\" extend=\"%s\">\n"% \
                (name, interpolation, extrapolation))
                #(name, dInterp[curve.interpolation], dExtend[curve.extend]))

        warning_shown = False

        for bez in curve.keyframe_points:
            if interpolation=="bezier":
                if bez.interpolation=='BEZIER':
                    f.write("      <p c=\"%.3f %.3f\" h1=\"%.3f %.3f\" h2=\"%.3f %.3f\"/>\n"%\
                            (bez.co[0],factor*bez.co[1],
                                bez.handle_left[0], factor*bez.handle_left[1],
                                bez.handle_right[0], factor*bez.handle_right[1]))
                else:
                    # point with linear IPO in bezier curve
                    f.write("      <p c=\"%.3f %.3f\" h1=\"%.3f %.3f\" h2=\"%.3f %.3f\"/>\n"%\
                            (bez.co[0], factor*bez.co[1],
                                bez.co[0] - 1, factor*bez.co[1],
                                bez.co[0] + 1, factor*bez.co[1]))

                    if not warning_shown:
                        try:
                            self.log.report({'WARNING'}, "You have an animation curve which contains a mix of mixture of Bezier and " +
                                        "linear interpolation, please convert everything to Bezier for best results")
                        except:
                            pass
                        warning_shown = True
            else:
                f.write("      <p c=\"%.3f %.3f\"/>\n"%(bez.co[0],
                                                        factor*bez.co[1]))
        f.write("    </curve>\n")


# ------------------------------------------------------------------------------
# Checks if there are any animated textures in any of the objects in the
# list l.
def checkForAnimatedTextures(self, lObjects):
    lAnimTextures = []
    for obj in lObjects:
        use_anim_texture = stk_utils.getObjectProperty(obj, "enable_anim_texture", "false")
        if use_anim_texture != 'true': continue

        anim_texture = stk_utils.getObjectProperty(obj, "anim_texture", None)

        if anim_texture is None or len(anim_texture) == 0:
            try:
                self.log.report({'WARNING'}, "object %s has an invalid animated-texture configuration" % obj.name)
            except:
                pass
            continue
        #if anim_texture == 'stk_animated_mudpot_a.png':
        print('Animated texture {} in {}.'.format(anim_texture, obj.name))
        dx = stk_utils.getObjectProperty(obj, "anim_dx", 0)
        dy = stk_utils.getObjectProperty(obj, "anim_dy", 0)
        dt = stk_utils.getObjectProperty(obj, "anim_dt", 0)

        use_anim_texture_by_step = stk_utils.getObjectProperty(obj, "enable_anim_by_step", "false")

        lAnimTextures.append( (anim_texture, dx, dy, dt, use_anim_texture_by_step) )
    return lAnimTextures

# ------------------------------------------------------------------------------
def writeAnimatedTextures(f, lAnimTextures):
    for (name, dx, dy, dt, use_anime_texture_by_step) in lAnimTextures:

        sdt=""
        if use_anime_texture_by_step == "true":
            sdt = ' animByStep="true" dt="%.3f" '%float(dt)
            dy = 1.0/dy

        sdx=""
        if dx: sdx = " dx=\"%.5f\" "%float(dx)
        sdy=""
        if dy: sdy = " dy=\"%.5f\" "%float(dy)

        if name is None or len(name) == 0:
            continue
        f.write("    <animated-texture name=\"%s\"%s%s%s/>\n"%(name, sdx, sdy, sdt) )

# ==============================================================================
# The actual exporter. It is using a class mainly to store some information
# between calls to different functions, e.g. a cache of exported objects.
class TrackExport:

    # Exports the models as spm object in local coordinate, i.e. with the object
    # center at (0,0,0).
    def exportLocalSPM(self, obj, sPath, name, applymodifiers=True):
        # If the name contains a ".spm" the model is assumed to be part of
        # the standard objects included in STK, so there is no need to
        # export the model.
        if re.search("\.spm$", name): return name

        name = name + ".spm"
        # If the object was already exported, we don't have to do it again.
        if name in self.dExportedObjects: return name

        obj.select_set(True)
        try:
            bpy.ops.screen.spm_export(localsp=True, filepath=sPath+"/"+name, selection_type="selected", \
                                      export_tangent=stk_utils.getSceneProperty(bpy.context.scene, 'precalculate_tangents', 'false') == 'true',
                                      applymodifiers=applymodifiers)
        except:
            self.log.report({'ERROR'}, "Failed to export " + name)
        obj.select_set(False)

        self.dExportedObjects[name]=1

        return name

    # ----------------------------------------------------------------------
    def writeTrackFile(self, sPath, nsBase):
        print("Writing track file --> \t")

        #start_time  = bsys.time()
        scene       = bpy.context.scene
        name        = stk_utils.getSceneProperty(scene, "name",   "Name of Track")
        groups      = stk_utils.getSceneProperty(scene, "groups", "standard"     )
        if 'is_wip_track' in scene and scene['is_wip_track'] == 'true':
            groups = 'wip-track'

        # Version 7 is the SPM track format used for 1.x
        # Version 8 is the SPM track format used for Evolution.
        # Specifications for version 8 are not final.
        track_version = bpy.context.scene['track_version']
        if ((track_version != 7) and (track_version != 8)):
            self.log.report({'ERROR'}, "The track.xml version is not specified or incorrect")
            return

        is_arena    = stk_utils.getSceneProperty(scene, "arena",      "n"            )
        if not is_arena:
            is_arena="n"
        is_arena = not (is_arena[0]=="n" or is_arena[0]=="N" or \
                        is_arena[0]=="f" or is_arena[0]=="F"      )

        is_soccer   = stk_utils.getSceneProperty(scene, "soccer",     "n"            )
        if not is_soccer:
            is_soccer="n"
        is_soccer = not (is_soccer[0]=="n" or is_soccer[0]=="N" or \
                         is_soccer[0]=="f" or is_soccer[0]=="F"      )

        is_ctf    = stk_utils.getSceneProperty(scene, "ctf",      "n"            )
        if not is_ctf:
            is_ctf="n"
        is_ctf = not (is_ctf[0]=="n" or is_ctf[0]=="N" or \
                      is_ctf[0]=="f" or is_ctf[0]=="F"      )

        is_cutscene = stk_utils.getSceneProperty(scene, "cutscene",  "false") == "true"
        is_internal = stk_utils.getSceneProperty(scene, "internal",   "n"            )
        is_internal = (is_internal == "true")
        if is_cutscene:
            is_internal = True

        push_back   = stk_utils.getSceneProperty(scene, "pushback",   "true"         )
        push_back   = (push_back != "false")

        auto_rescue = stk_utils.getSceneProperty(scene, "autorescue",   "true"       )
        auto_rescue = (auto_rescue != "false")

        designer    = stk_utils.getSceneProperty(scene, "designer",   ""             )

        # Support for multi-line descriptions:
        designer    = designer.replace("\\n", "\n")

        if not designer:
            designer    = stk_utils.getSceneProperty(scene, "description", "")
            if designer:
                self.log.report({'WARNING'}, "The 'Description' field is deprecated, please use 'Designer'")
            else:
                designer="?"

        music           = stk_utils.getSceneProperty(scene, "music", "")
        screenshot      = stk_utils.getSceneProperty(scene, "screenshot", "")
        smooth_normals  = stk_utils.getSceneProperty(scene, "smooth_normals", "false")
        #has_bloom       = (stk_utils.getSceneProperty(scene, "bloom", "false") == "true")
        bloom_threshold = stk_utils.getSceneProperty(scene, "bloom_threshold", "0.75")
        #has_lens_flare  = (stk_utils.getSceneProperty(scene, "sunlensflare", "false") == "true")
        has_shadows     = (stk_utils.getSceneProperty(scene, "shadows", "false") == "true")

        day_time        = stk_utils.getSceneProperty(scene, "duringday", "day")

        #has_colorlevel  = (stk_utils.getSceneProperty(scene, "colorlevel", "false") == "true")
        #colorlevel_inblack = stk_utils.getSceneProperty(scene, "colorlevel_inblack", "0.0")
        #colorlevel_ingamma = stk_utils.getSceneProperty(scene, "colorlevel_ingamma", "1.0")
        #colorlevel_inwhite = stk_utils.getSceneProperty(scene, "colorlevel_inwhite", "255.0")

        colorlevel_outblack = stk_utils.getSceneProperty(scene, "colorlevel_outblack", "0.0")
        colorlevel_outwhite = stk_utils.getSceneProperty(scene, "colorlevel_outwhite", "255.0")

        default_num_laps = int(stk_utils.getSceneProperty(scene, "default_num_laps",3))

        with open(sPath + "/track.xml", "w", encoding="utf8", newline="\n") as f:
            f.write("<?xml version=\"1.0\" encoding=\"utf-8\"?>\n")
            f.write("<track  name           = \"%s\"\n"%name)
            f.write("        version        = \"%i\"\n"%track_version)
            f.write("        groups         = \"%s\"\n"%groups)
            f.write("        designer       = \"%s\"\n"%designer)
            if music:
                f.write("        music          = \"%s\"\n"%music)
            else:
                self.log.report({'WARNING'}, "No music file defined. Default music will be used.")

            if is_arena:
                f.write("        arena          = \"Y\"\n")

                max_arena_players = 0
                for obj in bpy.data.objects:
                    stktype = stk_utils.getObjectProperty(obj, "type", "").strip().upper()
                    if obj.type=="EMPTY" and stktype[:5]=="START":
                        if is_ctf and stk_utils.getObjectProperty(obj, "ctf_only", "false").lower() == "true":
                            continue
                        max_arena_players += 1

                f.write("        max-arena-players = \"%d\"\n" % max_arena_players)

            if is_soccer:
                f.write("        soccer         = \"Y\"\n")

            if is_ctf:
                f.write("        ctf            = \"Y\"\n")

            if is_cutscene:
                f.write("        cutscene       = \"Y\"\n")

            if is_internal:
                f.write("        internal       = \"Y\"\n")

            if not push_back:
                f.write("        push-back      = \"N\"\n")

            if not auto_rescue:
                f.write("        auto-rescue    = \"N\"\n")

            if screenshot:
                f.write("        screenshot     = \"%s\"\n"%screenshot)
            else:
                self.log.report({'WARNING'}, "No screenshot defined")

            f.write("        smooth-normals = \"%s\"\n" % smooth_normals)
            f.write("        default-number-of-laps = \"%d\"\n" % default_num_laps)

            reverse = stk_utils.getSceneProperty(scene, "reverse", "false")
            if reverse == "true":
                f.write("        reverse        = \"Y\"\n")
            else:
                f.write("        reverse        = \"N\"\n")

            if (track_version == 8):
                no_dynamic_laps = stk_utils.getSceneProperty(scene, "no_dynamic_laps", "false")
                if no_dynamic_laps == "false":
                    f.write("        dynamic-laps   = \"Y\"\n")
                else:
                    f.write("        dynamic-laps   = \"N\"\n")

            #if has_bloom:
            #    f.write("        bloom          = \"Y\"\n")
            #    f.write("        bloom-threshold = \"%s\"\n" % bloom_threshold)
            #else:
            #    f.write("        bloom          = \"N\"\n")

            #if has_colorlevel:
            #    f.write("        color-level-in = \"" + str(colorlevel_inblack) + " " + str(colorlevel_ingamma) + " " + str(colorlevel_inwhite) + "\"\n")
            #    f.write("        color-level-out = \"" + str(colorlevel_outblack) + " " + str(colorlevel_outwhite) + "\"\n")

            #if has_lens_flare:
            #    f.write("        lens-flare     = \"Y\"\n")
            #else:
            #    f.write("        lens-flare     = \"N\"\n")

            if day_time == "day":
                f.write("        is-during-day  = \"Y\"\n")
            else:
                f.write("        is-during-day  = \"N\"\n")

            if has_shadows:
                f.write("        shadows        = \"Y\"\n")
            else:
                f.write("        shadows        = \"N\"\n")

            f.write(">\n")
            f.write("</track>\n")
        #print bsys.time() - start_time, "seconds"

    # --------------------------------------------------------------------------
    # Writes the animation for objects using IPOs:
    def writeAnimationWithIPO(self, f, name, obj, ipo, objectType="animation"):
        # An animated object can set the 'name' property, then this name will
        # be used to name the exported object (instead of the python name
        # which might be a default name with a number). Additionally, names
        # are cached so it can be avoided to export two or more identical
        # objects.
        parent = obj.parent

        flags = []

        # For now: armature animations are assumed to be looped
        if parent and parent.type=="ARMATURE":
            first_frame = bpy.context.scene.frame_start
            last_frame  = bpy.context.scene.frame_end
            frame_start = []
            frame_end = []
            for i in range(first_frame, last_frame + 1):
                for curr in bpy.context.scene.timeline_markers:
                    if curr.frame == i:
                        marker_name = curr.name.lower()
                        if marker_name == "start":
                            frame_start.append(i - 1)
                        if marker_name == "end":
                            frame_end.append(i - 1)
            if len(frame_start) > 0 and len(frame_end) > 0:
                flags.append('frame-start="%s"' % ' '.join(str(x) for x in frame_start))
                flags.append('frame-end="%s"' % ' '.join(str(x) for x in frame_end))
            is_cyclic = False
            parents = get_fcurves(parent.animation_data)
            if parents:
                for curve in parents:
                    for modifier in curve.modifiers:
                        if modifier.type == 'CYCLES':
                            is_cyclic = True
                            break
                    if is_cyclic:
                        break
            if is_cyclic:
                flags.append('looped="y"')

        interaction = stk_utils.getObjectProperty(obj, "interaction", 'static')
        flags.append('interaction="%s"' % interaction)
        # phyiscs only object can only have exact shape
        if interaction == "physicsonly":
            flags.append('shape="exact"')
        else:
            shape = stk_utils.getObjectProperty(obj, "shape", "")
            if shape and interaction != 'ghost':
                flags.append('shape="%s"'%shape)

        if not ipo: ipo=[]

        lodstring = self.getModelDefinitionString(obj)
        if len(lodstring) > 0:
            flags.append(lodstring)

        type = stk_utils.getObjectProperty(obj, "type", "")
        if type != "lod_instance":
            flags.append('model="%s"' % name)

        if interaction == 'reset':
            flags.append('reset="y"')
        elif interaction == 'explode':
            flags.append('explode="y"')
        elif interaction == 'flatten':
            flags.append('flatten="y"')

        if stk_utils.getObjectProperty(obj, "driveable", "false") == "true":
            flags.append('driveable="true"')

        if stk_utils.getObjectProperty(obj, "forcedbloom", "false") == "true":
            flags.append('forcedbloom="true"')

        if stk_utils.getObjectProperty(obj, "shadowpass", "true") == "false":
            flags.append('shadow-pass="false"')

        if len(stk_utils.getObjectProperty(obj, "outline", "")) > 0:
            flags.append('glow="%s"'%stk_utils.getObjectProperty(obj, "outline", ""))

        if stk_utils.getObjectProperty(obj, "displacing", "false") == "true":
            flags.append('displacing="true"')

        #if stk_utils.getObjectProperty(obj, "skyboxobject", "false") == "true":
        #    flags.append('renderpass="skybox"')

        if stk_utils.getObjectProperty(obj, "soccer_ball", "false") == "true":
            flags.append('soccer_ball="true"')

        uses_skeletal_animation = False

        # check if this object has an armature modifier
        for curr_mod in obj.modifiers:
            if curr_mod.type == 'ARMATURE':
                uses_skeletal_animation = True

        # check if this object has an armature parent (second way to do armature animations in blender)
        if obj.parent:
            if obj.parent.type == "ARMATURE":
                uses_skeletal_animation = True

        if uses_skeletal_animation:
            flags.append('skeletal-animation="true"')
        else:
            flags.append('skeletal-animation="false"')

        on_kart_collision = stk_utils.getObjectProperty(obj, "on_kart_collision", "")
        if len(on_kart_collision) > 0:
            flags.append("on-kart-collision=\"%s\""%on_kart_collision)

        custom_xml = stk_utils.getObjectProperty(obj, "custom_xml", "")
        if len(custom_xml) > 0:
            flags.append(custom_xml)

        if_condition = stk_utils.getObjectProperty(obj, "if", "")
        if len(if_condition) > 0:
            flags.append("if=\"%s\""%if_condition)

        lAnim = checkForAnimatedTextures(self, [obj])
        detail_level = 0
        if stk_utils.getObjectProperty(obj, "enable_geo_detail", "false") == 'true':
            detail_level = int(stk_utils.getObjectProperty(obj, "geo_detail_level", 0))
        if detail_level > 0:
            flags.append("geometry-level=\"%d\"" % detail_level)

        if parent and parent.type=="ARMATURE":
            f.write("  <object id=\"%s\" type=\"%s\" %s %s>\n"% (obj.name, objectType, stk_utils.getXYZHPRString(parent), ' '.join(flags)))
        else:
            f.write("  <object id=\"%s\" type=\"%s\" %s %s>\n"% (obj.name, objectType, stk_utils.getXYZHPRString(obj), ' '.join(flags)))

        if lAnim:
            writeAnimatedTextures(f, lAnim)

        writeIPO(self, f, ipo)
        f.write("  </object>\n")

    # --------------------------------------------------------------------------

    def writeLODModels(self, f, sPath, lLODModels):
        for props in lLODModels:
            obj = props['object']
            spm_name = self.exportLocalSPM(obj, sPath, props['filename'], props['modifiers'])

            skeletal_anim_str = ""
            uses_skeletal_animation = False

            # check if this object has an armature modifier
            for curr_mod in obj.modifiers:
                if curr_mod.type == 'ARMATURE':
                    uses_skeletal_animation = True

            # check if this object has an armature parent (second way to do armature animations in blender)
            if obj.parent:
                if obj.parent.type == "ARMATURE":
                    uses_skeletal_animation = True

            if uses_skeletal_animation:
                additional_prop_str = ' skeletal-animation="true"'
            else:
                additional_prop_str = ' skeletal-animation="false"'
            detail_level = 0
            if stk_utils.getObjectProperty(obj, "enable_geo_detail", "false") == 'true':
                detail_level = int(stk_utils.getObjectProperty(obj, "geo_detail_level", 0))
            if detail_level > 0:
                additional_prop_str += " geometry-level=\"%d\"" % detail_level

            f.write("    <static-object lod_distance=\"%i\" lod_group=\"%s\" model=\"%s\" %s interaction=\"%s\"%s/>\n" % (props['distance'], props['groupname'], spm_name, stk_utils.getXYZHPRString(obj), stk_utils.getObjectProperty(obj, "interaction", "static"), additional_prop_str) )

    # --------------------------------------------------------------------------
    # Write the objects that are part of the track (but not animated or
    # physical).
    def writeStaticObjects(self, f, sPath, lStaticObjects, lAnimTextures):
        for obj in lStaticObjects:

            lodstring = self.getModelDefinitionString(obj)

            # An object can set the 'name' property, then this name will
            # be used to name the exported object (instead of the python name
            # which might be a default name with a number). Additionally, names
            # are cached so it can be avoided to export two or more identical
            # objects.
            lAnim    = checkForAnimatedTextures(self, [obj])
            name     = stk_utils.getObjectProperty(obj, "name", obj.name)
            if len(name) == 0: name = obj.name

            type = stk_utils.getObjectProperty(obj, "type", "X")

            if type != "lod_instance":
                spm_name = self.exportLocalSPM(obj, sPath, name, True)
            kind = stk_utils.getObjectProperty(obj, "kind", "")

            attributes = []
            attributes.append(lodstring)

            if type != "lod_instance" and type != "single_lod":
                attributes.append("model=\"%s\""%spm_name)

            attributes.append(stk_utils.getXYZHPRString(obj))

            condition_if = stk_utils.getObjectProperty(obj, "if", "")
            if len(condition_if) > 0:
                attributes.append("if=\"%s\""%condition_if)

            challenge_val = stk_utils.getObjectProperty(obj, "challenge", "")
            if len(challenge_val) > 0:
                attributes.append("challenge=\"%s\""% challenge_val)
            detail_level = 0
            if stk_utils.getObjectProperty(obj, "enable_geo_detail", "false") == 'true':
                detail_level = int(stk_utils.getObjectProperty(obj, "geo_detail_level", 0))
            if detail_level > 0:
                attributes.append("geometry-level=\"%d\"" % detail_level)
            interaction = stk_utils.getObjectProperty(obj, "interaction", '??')
            if interaction == 'reset':
                attributes.append("reset=\"y\"")
            elif interaction == 'explode':
                attributes.append("explode=\"y\"")
            elif interaction == 'flatten':
                attributes.append("flatten=\"y\"")
            if interaction == 'physicsonly':
                attributes.append('interaction="physics-only"')

            if lAnim:
                f.write("    <static-object %s>\n" % ' '.join(attributes))
                writeAnimatedTextures(f, lAnim)
                f.write("    </static-object>\n")
            else:
                f.write("    <static-object %s/>\n" % ' '.join(attributes))
        writeAnimatedTextures(f, lAnimTextures)

    # --------------------------------------------------------------------------
    # Get LOD string for a given object (returns an empty string if object is not LOD)
    def getModelDefinitionString(self, obj):
        lodstring = ""
        type = stk_utils.getObjectProperty(obj, "type", "object")
        if type == "lod_model":
            pass
        #elif type == "object" and stk_utils.getObjectProperty(obj, "instancing", "false") == "true":
        #    group = type = stk_utils.getObjectProperty(obj, "name", "")
        #    if len(group) == 0:
        #        self.log.report({'WARNING'}, "Instancing object " + obj.name + " has no name property")
        #    lodstring = ' instancing="true" instancing_model="' + group + '"'
        elif type == "lod_instance":
            group = type = stk_utils.getObjectProperty(obj, "lod_name", "")
            if len(group) == 0:
                self.log.report({'WARNING'}, "LOD instance " + obj.name + " has no group property")
            lodstring = ' lod_instance="true" lod_group="' + group + '"'
        elif type == "single_lod":
            lodstring = ' lod_instance="true" lod_group="_single_lod_' + stk_utils.getObjectProperty(obj, "name", obj.name) + '"'
        return lodstring

    # --------------------------------------------------------------------------
    # Writes a non-static track object. The objects can be animated or
    # non-animated meshes, and physical or non-physical.
    # Type is either 'movable' or 'nophysics'.
    def writeObject(self, f, sPath, obj):
        name     = stk_utils.getObjectProperty(obj, "name", obj.name)
        if len(name) == 0: name = obj.name

        type = stk_utils.getObjectProperty(obj, "type", "X")

        if obj.type != "CAMERA":
            if type == "lod_instance":
                spm_name = None
            else:
                spm_name = self.exportLocalSPM(obj, sPath, name, True)

        interact = stk_utils.getObjectProperty(obj, "interaction", "none")

        if obj.type=="CAMERA":
            ipo  = obj.animation_data
            self.writeAnimationWithIPO(f, "", obj, ipo, objectType="cutscene_camera")
        # An object that can be moved by the player. This object
        # can not have an IPO, so no need to test this here.
        elif interact=="move":
            ipo = obj.animation_data
            if ipo and ipo.action:
                self.log.report({'WARNING'}, "Movable object %s has an ipo - ipo is ignored." \
                            %obj.name)
            shape = stk_utils.getObjectProperty(obj, "shape", "")
            if not shape:
                self.log.report({'WARNING'}, "Movable object %s has no shape - box assumed!" \
                            % obj.name)
                shape="box"
            mass  = stk_utils.getObjectProperty(obj, "mass", 10)

            flags = []

            lodstring = self.getModelDefinitionString(obj)
            if len(lodstring) > 0:
                flags.append(lodstring)

            type = stk_utils.getObjectProperty(obj, "type", "?")

            if type != "lod_instance":
                flags.append('model="%s"' % spm_name)

            if stk_utils.getObjectProperty(obj, "forcedbloom", "false") == "true":
                flags.append('forcedbloom="true"')

            if stk_utils.getObjectProperty(obj, "shadowpass", "true") == "false":
                flags.append('shadow-pass="false"')

            if len(stk_utils.getObjectProperty(obj, "outline", "")) > 0:
                flags.append('glow="%s"'%stk_utils.getObjectProperty(obj, "outline", ""))

            if stk_utils.getObjectProperty(obj, "displacing", "false") == "true":
                flags.append('displacing="true"')

            #if stk_utils.getObjectProperty(obj, "skyboxobject", "false") == "true":
            #    flags.append('renderpass="skybox"')

            if stk_utils.getObjectProperty(obj, "soccer_ball", "false") == "true":
                flags.append('soccer_ball="true"')

            on_kart_collision = stk_utils.getObjectProperty(obj, "on_kart_collision", "")
            if len(on_kart_collision) > 0:
                flags.append("on-kart-collision=\"%s\""%on_kart_collision)

            custom_xml = stk_utils.getObjectProperty(obj, "custom_xml", "")
            if len(custom_xml) > 0:
                flags.append(custom_xml)

            if_condition = stk_utils.getObjectProperty(obj, "if", "")
            if len(if_condition) > 0:
                flags.append("if=\"%s\""%if_condition)

            uses_skeletal_animation = False

            # check if this object has an armature modifier
            for curr_mod in obj.modifiers:
                if curr_mod.type == 'ARMATURE':
                    uses_skeletal_animation = True

            # check if this object has an armature parent (second way to do armature animations in blender)
            if obj.parent:
                if obj.parent.type == "ARMATURE":
                    uses_skeletal_animation = True

            if uses_skeletal_animation:
                flags.append('skeletal-animation="true"')
            else:
                flags.append('skeletal-animation="false"')

            detail_level = 0
            if stk_utils.getObjectProperty(obj, "enable_geo_detail", "false") == 'true':
                detail_level = int(stk_utils.getObjectProperty(obj, "geo_detail_level", 0))
            if detail_level > 0:
                flags.append("geometry-level=\"%d\"" % detail_level)

            f.write('  <object type="movable" id=\"%s\" %s\n'% (obj.name, stk_utils.getXYZHPRString(obj)))
            f.write('          shape="%s" mass="%s" %s/>\n' % (shape, mass, ' '.join(flags)))

        # Now the object either has an IPO, or is a 'ghost' object.
        # Either can have an IPO. Even if the objects don't move
        # they are saved as animations (with 0 IPOs).
        elif interact=="ghost" or interact=="none" or interact=="static" or interact=="reset" or interact=="explode" or interact=="flatten" or interact=="physicsonly":

            ipo = obj.animation_data

            # In objects with skeletal animations the actual armature (which
            # is a parent) contains the IPO. So check for this:
            if bpy.app.version < (5, 0, 0):
                if not ipo or not ipo.action or not ipo.action.fcurves or len(ipo.action.fcurves) == 0:
                    parent = obj.parent
                    if parent:
                        ipo = parent.animation_data
            else:
                if (not ipo or
                    not ipo.action or
                    not hasattr(ipo.action, "layers") or
                    not ipo.action.layers or
                    len(ipo.action.layers) == 0 or
                    not hasattr(ipo.action.layers[0], "strips") or
                    not ipo.action.layers[0].strips or
                    len(ipo.action.layers[0].strips) == 0 or
                    not hasattr(ipo.action.layers[0].strips[0], "channelbags") or
                    not ipo.action.layers[0].strips[0].channelbags or
                    len(ipo.action.layers[0].strips[0].channelbags) == 0 or
                    not hasattr(ipo.action.layers[0].strips[0].channelbags[0], "fcurves") or
                    len(ipo.action.layers[0].strips[0].channelbags[0].fcurves) == 0):

                    parent = obj.parent
                    if parent and parent.animation_data:
                        ipo = parent.animation_data.action.layers[0].strips[0].channelbags[0].fcurves
            self.writeAnimationWithIPO(f, spm_name, obj, ipo)

        else:
            self.log.report({'WARNING'}, "Unknown interaction '%s' - ignored!"%interact)


    # --------------------------------------------------------------------------
    def writeEasterEggsFile(self, sPath, lEasterEggs):
        with open(sPath + "/easter_eggs.xml", "w", encoding="utf8", newline="\n") as f:
            f.write("<?xml version=\"1.0\" encoding=\"utf-8\"?>\n")
            f.write("<EasterEggHunt>\n")

            #print("lEasterEggs : ", len(lEasterEggs), lEasterEggs);

            f.write("  <easy>\n")
            for obj in lEasterEggs:
                #print(stk_utils.getObjectProperty(obj, "easteregg_easy", "false"))
                if stk_utils.getObjectProperty(obj, "easteregg_easy", "false") == "true":
                    f.write("    <easter-egg %s />\n" % stk_utils.getXYZHString(obj))
            f.write("  </easy>\n")

            f.write("  <medium>\n")
            for obj in lEasterEggs:
                #print(stk_utils.getObjectProperty(obj, "easteregg_medium", "false"))
                if stk_utils.getObjectProperty(obj, "easteregg_medium", "false") == "true":
                    f.write("    <easter-egg %s />\n" % stk_utils.getXYZHString(obj))
            f.write("  </medium>\n")

            f.write("  <hard>\n")
            for obj in lEasterEggs:
                #print(stk_utils.getObjectProperty(obj, "easteregg_hard", "false"))
                if stk_utils.getObjectProperty(obj, "easteregg_hard", "false") == "true":
                    f.write("    <easter-egg %s />\n" % stk_utils.getXYZHString(obj))
            f.write("  </hard>\n")

            f.write("</EasterEggHunt>\n")


    # --------------------------------------------------------------------------
    # Writes the scene files, which includes all models, animations, and items
    def writeSceneFile(self, sPath, sTrackName, exporters, lTrack, lObjects, lSun):

        #start_time = bsys.time()
        print("Writing scene file --> \t")

        is_lib_node = (stk_utils.getSceneProperty(bpy.data.scenes[0], 'is_stk_node', 'false') == 'true')

        filename = "scene.xml"
        if is_lib_node:
            filename = "node.xml"

        with open(sPath + "/" + filename, "w", encoding="utf8", newline="\n") as f:
            f.write("<?xml version=\"1.0\" encoding=\"utf-8\"?>\n")
            f.write("<scene>\n")

            # Extract all static objects (which will be merged into one bullet object in stk):
            lStaticObjects = []
            # Include LOD models (i.e. the definition of a LOD group. Does not include LOD instances)
            lLODModels = {}
            #lInstancingModels = {}
            lOtherObjects  = []

            for obj in lObjects:
                type = stk_utils.getObjectProperty(obj, "type", "??")
                interact = stk_utils.getObjectProperty(obj, "interaction", "static")
                #if type == "lod_instance" or type == "lod_model" or type == "single_lod":
                #    interact = "static"

                # TODO: remove this fuzzy logic and let the artist clearly decide what is exported in the
                # track main model and what is exporter separately
                export_non_static = False
                if stk_utils.getObjectProperty(obj, "forcedbloom", "false") == "true":
                    export_non_static = True
                elif stk_utils.getObjectProperty(obj, "shadowpass", "true") == "false":
                    export_non_static = True
                elif len(stk_utils.getObjectProperty(obj, "outline", "")) > 0:
                    export_non_static = True
                elif stk_utils.getObjectProperty(obj, "displacing", "false") == "true":
                    export_non_static = True
                #elif stk_utils.getObjectProperty(obj, "skyboxobject", "false") == "true":
                #   export_non_static = True
                elif stk_utils.getObjectProperty(obj, "soccer_ball", "false") == "true":
                   export_non_static = True
                elif is_lib_node:
                    export_non_static = True
                elif interact=="reset" or interact=="explode" or interact=="flatten":
                    export_non_static = True
                elif len(stk_utils.getObjectProperty(obj, "on_kart_collision", "")) > 0:
                    export_non_static = True
                elif len(stk_utils.getObjectProperty(obj, "if", "")):
                    export_non_static = True

                #if type == "object" and stk_utils.getObjectProperty(obj, "instancing", "false") == "true":
                #    if is_lib_node:
                #        instancing_name = stk_utils.getObjectProperty(obj, 'name', '')
                #        if len(instancing_name) == 0:
                #            self.log.report({'WARNING'}, 'Object %s marked as instancing has no name' % obj.name)
                #            continue
                #        lInstancingModels[instancing_name] = obj
                #        lOtherObjects.append(obj)
                #    else:
                #        self.log.report({'WARNING'}, 'Object %s marked as instancing. Instancing only works with library nodes.' % obj.name)
                #elif
                if type == 'lod_model':
                    group_name = stk_utils.getObjectProperty(obj, 'lod_name', '')
                    if len(group_name) == 0:
                        self.log.report({'WARNING'}, 'Object %s marked as LOD but no LOD name specified' % obj.name)
                        continue
                    if group_name not in lLODModels:
                        lLODModels[group_name] = []

                    lod_model_name = stk_utils.getObjectProperty(obj, "name", obj.name)
                    loddistance = stk_utils.getObjectProperty(obj, "lod_distance", 60.0)
                    if len(lod_model_name) == 0: lod_model_name = obj.name
                    lLODModels[group_name].append({'object': obj, 'groupname': group_name, 'distance': loddistance, 'filename': lod_model_name, 'modifiers': True})

                elif type == 'single_lod':
                    lod_model_name = stk_utils.getObjectProperty(obj, "name", obj.name)
                    if len(lod_model_name) == 0: lod_model_name = obj.name

                    group_name = "_single_lod_" + lod_model_name
                    if group_name not in lLODModels:
                        lLODModels[group_name] = []

                    if stk_utils.getObjectProperty(obj, "nomodifierautolod", "false") == "true":
                        loddistance = stk_utils.getObjectProperty(obj, "nomodierlod_distance", 30.0)
                        lLODModels[group_name].append({'object': obj, 'groupname': group_name, 'distance': loddistance, 'filename': lod_model_name, 'modifiers': True})
                        loddistance = stk_utils.getObjectProperty(obj, "lod_distance", 60.0)
                        lLODModels[group_name].append({'object': obj, 'groupname': group_name, 'distance': loddistance, 'filename': lod_model_name + "_mid", 'modifiers': False})
                    else:
                        loddistance = stk_utils.getObjectProperty(obj, "lod_distance", 60.0)
                        lLODModels[group_name].append({'object': obj, 'groupname': group_name, 'distance': loddistance, 'filename': lod_model_name, 'modifiers': True})


                    # this object is both a model and an instance, so also add it to the list of objects, where it will be exported as a LOD instance
                    if export_non_static:
                        lOtherObjects.append(obj)
                    else:
                        lStaticObjects.append(obj)

                elif not export_non_static and (interact=="static" or type == "lod_model" or interact=="physicsonly"):

                    ipo = obj.animation_data
                    if obj.parent is not None and obj.parent.type=="ARMATURE" and obj.parent.animation_data is not None:
                        ipo = obj.parent.animation_data

                    # If an static object has an IPO, it will be moved, and
                    # can't be merged with the physics model of the track
                    if (ipo and ipo.action):
                        lOtherObjects.append(obj)
                    else:
                        lStaticObjects.append(obj)
                else:
                    lOtherObjects.append(obj)

            lAnimTextures  = checkForAnimatedTextures(self, lTrack)

            if len(lLODModels.keys()) > 0:
                f.write('  <lod>\n')
                for group_name in lLODModels.keys():
                    lLODModels[group_name].sort(key = lambda a: a['distance'])
                    f.write('   <group name="%s">\n' % group_name)
                    self.writeLODModels(f, sPath, lLODModels[group_name])
                    f.write('   </group>\n')
                f.write('  </lod>\n')

            #if len(lInstancingModels.keys()) > 0:
            #    f.write('  <instancing>\n')
            #    for instancing_name in lInstancingModels.keys():
            #        f.write('   <group name="%s">\n' % instancing_name)
            #        self.writeInstancingModel(f, sPath, instancing_name, lInstancingModels[instancing_name])
            #        f.write('   </group>\n')
            #    f.write('  </instancing>\n')

            if stk_utils.getSceneProperty(bpy.data.scenes[0], 'is_stk_node', 'false') != 'true':
                if lStaticObjects or lAnimTextures:
                    f.write("  <track model=\"%s\" x=\"0\" y=\"0\" z=\"0\">\n"%sTrackName)
                    self.writeStaticObjects(f, sPath, lStaticObjects, lAnimTextures)
                    f.write("  </track>\n")
                else:
                    f.write("  <track model=\"%s\" x=\"0\" y=\"0\" z=\"0\"/>\n"%sTrackName)

            for obj in lOtherObjects:
                self.writeObject(f, sPath, obj)

            # Subtitles
            subtitles = []
            end_time = bpy.data.scenes[0].frame_end
            for marker in reversed(bpy.data.scenes[0].timeline_markers):
                if marker.name.startswith("subtitle"):
                    subtitle_text = bpy.data.scenes[0][marker.name]
                    subtitles.insert(0, [marker.frame, end_time - 1, subtitle_text])
                end_time = marker.frame

            if len(subtitles) > 0:
                f.write("  <subtitles>\n")

                for subtitle in subtitles:
                    f.write("        <subtitle from=\"%i\" to=\"%i\" text=\"%s\"/>\n" % (subtitle[0], subtitle[1], subtitle[2]))

                f.write("  </subtitles>\n")


            # Assemble all sky/fog related parameters
            # ---------------------------------------

            # We do not export sky, sun, etc if its a lib node. Those are objects not scenes.
            if not is_lib_node:
                if len(lSun) > 1:
                    self.log.report({'WARNING'}, "Warning: more than one Sun defined, only the first will be used."   )
                sSky=""
                scene = bpy.context.scene
                s = stk_utils.getSceneProperty(scene, "fog", 0)
                if s == "yes" or s == "true":
                    sSky="%s fog=\"true\""%sSky
                    s=stk_utils.getSceneProperty(scene, "fog_color", 0)
                    if s: sSky="%s fog-color=\"%s\""%(sSky, s)
                    s=float(stk_utils.getSceneProperty(scene, "fog_max", 0))
                    if s: sSky="%s fog-max=\"%s\""%(sSky, s)
                    s=float(stk_utils.getSceneProperty(scene, "fog_start", 0))
                    if s: sSky="%s fog-start=\"%.2f\""%(sSky, s)
                    s=float(stk_utils.getSceneProperty(scene, "fog_end", 0))
                    if s: sSky="%s fog-end=\"%.2f\""%(sSky, s)

                # If there is a sun:
                if len(lSun) > 0:
                    sun = lSun[0]
                    xyz=sun.location
                    sSky="%s xyz=\"%.2f %.2f %.2f\""%(sSky, float(xyz[0]), float(xyz[2]), float(xyz[1]))
                    s=stk_utils.getObjectProperty(sun, "color", 0)
                    if s: sSky="%s sun-color=\"%s\""%(sSky, s)
                    s=stk_utils.getObjectProperty(sun, "specular", 0)
                    if s: sSky="%s sun-specular=\"%s\""%(sSky, s)
                    s=stk_utils.getObjectProperty(sun, "diffuse", 0)
                    if s: sSky="%s sun-diffuse=\"%s\""%(sSky, s)
                    s=stk_utils.getObjectProperty(sun, "ambient", 0)
                    if s: sSky="%s ambient=\"%s\""%(sSky, s)

                if sSky:
                    f.write("  <sun %s/>\n"%sSky)

                sky_color=stk_utils.getSceneProperty(scene, "sky_color", None)
                if sky_color:
                    f.write("  <sky-color rgb=\"%s\"/>\n"%sky_color)

                weather = ""
                weather_type = stk_utils.getSceneProperty(scene, "weather_type", "none")
                if weather_type != "none":
                    if weather_type[:4] != ".xml":
                        weather_type = weather_type + ".xml"
                    weather = " particles=\"" + weather_type + "\""

                lightning = stk_utils.getSceneProperty(scene, "weather_lightning", "false")
                if lightning == "true":
                    weather = weather + " lightning=\"true\""

                weather_sound = stk_utils.getSceneProperty(scene, "weather_sound", "")
                if weather_sound != "":
                    weather = weather + " sound=\"" + weather_sound + "\""

                if weather != "":
                    f.write("  <weather%s/>\n"%weather)

                rad2deg = 180.0/3.1415926

                sky     = stk_utils.getSceneProperty(scene, "sky_type", None)

                sphericalHarmonicsStr = ""
                if stk_utils.getSceneProperty(scene, "ambientmap", "false") == "true":
                    sphericalHarmonicsTextures = []
                    s = stk_utils.getSceneProperty(scene, "ambientmap_texture2", "")
                    if len(s) > 0: sphericalHarmonicsTextures.append(s)
                    s = stk_utils.getSceneProperty(scene, "ambientmap_texture3", "")
                    if len(s) > 0: sphericalHarmonicsTextures.append(s)
                    s = stk_utils.getSceneProperty(scene, "ambientmap_texture4", "")
                    if len(s) > 0: sphericalHarmonicsTextures.append(s)
                    s = stk_utils.getSceneProperty(scene, "ambientmap_texture5", "")
                    if len(s) > 0: sphericalHarmonicsTextures.append(s)
                    s = stk_utils.getSceneProperty(scene, "ambientmap_texture6", "")
                    if len(s) > 0: sphericalHarmonicsTextures.append(s)
                    s = stk_utils.getSceneProperty(scene, "ambientmap_texture1", "")
                    if len(s) > 0: sphericalHarmonicsTextures.append(s)
                    if len(sphericalHarmonicsTextures) == 6:
                        sphericalHarmonicsStr = 'sh-texture="' + " ".join(sphericalHarmonicsTextures) + '"'
                    else:
                        self.log.report({'WARNING'}, 'Invalid ambient map textures')

                # Note that there is a limit to the length of id properties,
                # which can easily be exceeded by 6 sky textures for a full sky box.
                # Therefore also check for sky-texture1 and sky-texture2.
                texture = stk_utils.getSceneProperty(scene, "sky_texture", "")
                s       = stk_utils.getSceneProperty(scene, "sky_texture1", "")
                if s: texture = "%s %s"%(texture, s)
                s       = stk_utils.getSceneProperty(scene, "sky_texture2", "")
                if s: texture = "%s %s"%(texture, s)
                if sky and texture:
                    if sky=="box":
                        lTextures = [stk_utils.getSceneProperty(scene, "sky_texture2", ""),
                                    stk_utils.getSceneProperty(scene, "sky_texture3", ""),
                                    stk_utils.getSceneProperty(scene, "sky_texture4", ""),
                                    stk_utils.getSceneProperty(scene, "sky_texture5", ""),
                                    stk_utils.getSceneProperty(scene, "sky_texture6", ""),
                                    stk_utils.getSceneProperty(scene, "sky_texture1", "")]
                        f.write("  <sky-box texture=\"%s\" %s/>\n" % (" ".join(lTextures), sphericalHarmonicsStr))

                camera_far  = stk_utils.getSceneProperty(scene, "camera_far", ""             )
                if camera_far:
                    f.write("  <camera far=\"%s\"/>\n"%camera_far)

            for exporter in exporters:
                exporter.export(f)

            f.write("</scene>\n")
        #print bsys.time()-start_time,"seconds"


    def __init__(self, log, sFilePath, exportImages, exportDrivelines, exportScene, exportMaterials):
        self.dExportedObjects = {}
        self.log = log

        sBase = os.path.basename(sFilePath)
        sPath = os.path.dirname(sFilePath)

        stk_delete_old_files_on_export = False
        try:
            stk_delete_old_files_on_export = bpy.context.preferences.addons[os.path.basename(os.path.dirname(__file__))].preferences.stk_delete_old_files_on_export
        except:
            pass

        if stk_delete_old_files_on_export:
            os.chdir(sPath)
            old_model_files = [ f for f in os.listdir(sPath) if f.endswith(".spm") ]
            for f in old_model_files:
                print("Deleting ", f)
                os.remove(f)
        ###
        if exportImages:
            for i,curr in enumerate(bpy.data.images):
                try:
                    if curr.filepath is None or len(curr.filepath) == 0:
                        continue

                    abs_texture_path = bpy.path.abspath(curr.filepath)
                    shutil.copy(abs_texture_path, sPath)
                    print(f"Copy Texture {abs_texture_path} to {sPath}")
                    self.log.report({'INFO'}, 'copy texture ' + abs_texture_path + ' to ' + sPath)
                except:
                    traceback.print_exc(file=sys.stdout)
                    self.log.report({'WARNING'}, 'Failed to copy texture ' + curr.filepath)
        ###
        drivelineExporter = stk_track_utils.DrivelineExporter(self.log)
        navmeshExporter = stk_track_utils.NavmeshExporter(self.log)
        exporters = [drivelineExporter, stk_track_utils.ParticleEmitterExporter(self.log), stk_track_utils.BlenderHairExporter(self.log), stk_track_utils.SoundEmitterExporter(self.log),
                     stk_track_utils.ActionTriggerExporter(self.log), stk_track_utils.ItemsExporter(), stk_track_utils.BillboardExporter(self.log), stk_track_utils.LightsExporter(self.log), stk_track_utils.LightShaftExporter(),
                     stk_track_utils.StartPositionFlagExporter(self.log), stk_track_utils.LibraryNodeExporter(self.log), navmeshExporter]

        # Collect the different kind of meshes this exporter handles
        # ----------------------------------------------------------
        lObj = bpy.context.scene.objects

        lTrack               = []                    # All main track objects
        lCameraCurves        = []                    # Camera curves (unused atm)
        lObjects             = []                    # All special objects
        lSun                 = []
        lEasterEggs          = []

        for obj in lObj:
            # Try to get the supertuxkart type field. If it's not defined,
            # use the name of the objects as type.
            stktype = stk_utils.getObjectProperty(obj, "type", "").strip().upper()

            #print("Checking object",obj.name,"which has type",stktype)

            # Make it possible to ignore certain objects, e.g. if you keep a
            # selection of 'templates' (ready to go models) around to be
            # copied into the main track.
            # This also works with objects that have hide_render enabled.
            # Do not export linked objects if part of the STK object library;
            # linked objects will be used as templates to create instances from.
            if obj.hide_render or stktype == "IGNORE" or \
            (obj.name.startswith("stklib_") and obj.library is not None):
                continue

            if stktype=="EASTEREGG":
                lEasterEggs.append(obj)
                continue

            objectProcessed = False
            for exporter in exporters:
                if exporter.processObject(obj, stktype):
                    objectProcessed = True
                    break
            if objectProcessed:
                continue

            if obj.type=="LIGHT" and stktype == "SUN":
                lSun.append(obj)
                continue
            elif obj.type=="CAMERA" and stktype == 'CUTSCENE_CAMERA':
                lObjects.append(obj)
                continue
            elif obj.type!="MESH":
                #print "Non-mesh object '%s' (type: '%s') is ignored!"%(obj.name, stktype)
                continue

            if stktype=="OBJECT" or stktype=="SPECIAL_OBJECT" or stktype=="LOD_MODEL" or stktype=="LOD_INSTANCE" or stktype=="SINGLE_LOD":
                lObjects.append(obj)
            elif stktype=="CANNONEND":
                pass # cannon ends are handled with cannon start objects
            elif stktype=="NONE":
                lTrack.append(obj)
            else:
                s = stk_utils.getObjectProperty(obj, "type", None)
                if s:
                    self.log.report({'WARNING'}, "object " + obj.name + " has type property '%s', which is not supported.\n"%s)
                lTrack.append(obj)

        is_arena = stk_utils.getSceneProperty(bpy.data.scenes[0], "arena", "false") == "true"
        is_soccer = stk_utils.getSceneProperty(bpy.data.scenes[0], "soccer", "false") == "true"
        is_cutscene = stk_utils.getSceneProperty(bpy.data.scenes[0], "cutscene",  "false") == "true"

        # Now export the different parts: track file
        # ------------------------------------------
        if exportScene and stk_utils.getSceneProperty(bpy.data.scenes[0], 'is_stk_node', 'false') != 'true':
            self.writeTrackFile(sPath, sBase)

        # Quads and mapping files
        # -----------------------
        scene = bpy.context.scene

        is_arena = stk_utils.getSceneProperty(scene, "arena", "n")
        if not is_arena: is_arena="n"
        is_arena = not (is_arena[0]=="n" or is_arena[0]=="N" or \
                        is_arena[0]=="f" or is_arena[0]=="F"     )

        is_soccer = stk_utils.getSceneProperty(scene, "soccer", "n")
        if not is_soccer: is_soccer="n"
        is_soccer = not (is_soccer[0]=="n" or is_soccer[0]=="N" or \
                         is_soccer[0]=="f" or is_soccer[0]=="F"     )

        if exportDrivelines and not is_arena and not is_soccer and not is_cutscene:
            drivelineExporter.writeQuadAndGraph(sPath)
        if (is_arena or is_soccer):
            navmeshExporter.exportNavmesh(sPath)

        sTrackName = sBase+"_track.spm"

        stk_utils.unhideObjectsTransiently();
        stk_utils.selectObjectsInList(lTrack)
        if exportScene and stk_utils.getSceneProperty(bpy.data.scenes[0], 'is_stk_node', 'false') != 'true':
            bpy.ops.screen.spm_export(localsp=False, filepath=sPath+"/"+sTrackName, selection_type="selected", \
                                      export_tangent=stk_utils.getSceneProperty(scene, 'precalculate_tangents', 'false') == 'true')
        bpy.ops.object.select_all(action='DESELECT')
        stk_utils.hideTransientObjects();

        # scene file
        # ----------
        if exportScene:
            self.writeSceneFile(sPath, sTrackName, exporters, lTrack, lObjects, lSun)

            if len(lEasterEggs) > 0 and stk_utils.getSceneProperty(scene, 'is_stk_node', 'false') != 'true':
                self.writeEasterEggsFile(sPath, lEasterEggs)

        # materials file
        # ----------
        if 'stk_material_export' not in dir(bpy.ops.screen):
            self.log.report({'ERROR'}, "Cannot find the material exporter, make sure you installed it properly")
            return
        if exportMaterials:
            bpy.ops.screen.stk_material_export(filepath=sPath + "/materials.xml")



# ==============================================================================
def savescene_callback(self, sFilePath, exportImages, exportDrivelines, exportScene, exportMaterials):
    if 'spm_export' not in dir(bpy.ops.screen):
        self.report({'ERROR'}, "Cannot find the spm exporter, make sure you installed it properly")
        return

    # Export the actual track and any individual objects
    TrackExport(self, sFilePath, exportImages, exportDrivelines and stk_utils.getSceneProperty(bpy.data.scenes[0], 'is_stk_node', 'false') != 'true', exportScene, exportMaterials)

    now = datetime.datetime.now()
    self.report({'INFO'}, "Track export completed on " + now.strftime("%Y-%m-%d %H:%M"))

# ==== EXPORT OPERATOR ====
class STK_Track_Export_Operator(bpy.types.Operator):
    """Export current scene to a STK track or library node"""

    bl_idname = ("screen.stk_track_export")
    bl_label = ("Export STK Track")
    filepath: bpy.props.StringProperty(subtype="FILE_PATH")
    exportScene: bpy.props.BoolProperty(name="Export scene", default=True)
    exportDrivelines: bpy.props.BoolProperty(name="Export drivelines", default=True)
    exportMaterials: bpy.props.BoolProperty(name="Export materials", default=True)

    def invoke(self, context, event):
        isATrack = ('is_stk_track' in context.scene) and (context.scene['is_stk_track'] == 'true')
        isANode = ('is_stk_node' in context.scene) and (context.scene['is_stk_node'] == 'true')

        if not isATrack and not isANode:
            self.report({'ERROR'}, "Not a STK library node or a track!")
            return {'FINISHED'}

        # FIXME: in library nodes it's "name", in tracks it's "code"
        if isANode:
            if 'name' not in context.scene or len(context.scene['name']) == 0:
                self.report({'ERROR'}, "Please specify a name")
                return {'FINISHED'}
            code = context.scene['name']
        else:
            if 'code' not in context.scene or len(context.scene['code']) == 0:
                self.report({'ERROR'}, "Please specify a code name (folder name)")
                return {'FINISHED'}
            code = context.scene['code']

        assets_path = ""
        try:
            assets_path = bpy.context.preferences.addons[os.path.basename(os.path.dirname(__file__))].preferences.stk_assets_path
        except:
            pass

        if assets_path is None or len(assets_path) < 0:
            self.report({'ERROR'}, "Please select the export path in the add-on preferences or quick exporter panel")
            return {'FINISHED'}

        if isANode:
            folder = os.path.join(assets_path, 'library', code)
        else:
            if 'is_wip_track' in context.scene and context.scene['is_wip_track'] == 'true':
                folder = os.path.join(assets_path, 'wip-tracks', code)
            else:
                folder = os.path.join(assets_path, 'tracks', code)

        if not os.path.exists(folder):
            os.makedirs(folder)
        self.filepath = os.path.join(folder, code)
        return self.execute(context)

    def execute(self, context):
        if bpy.context.mode != 'OBJECT':
            # Return to object mode before exporting
            bpy.ops.object.mode_set(mode='OBJECT')

        isNotATrack = ('is_stk_track' not in context.scene) or (context.scene['is_stk_track'] != 'true')
        isNotANode = ('is_stk_node' not in context.scene) or (context.scene['is_stk_node'] != 'true')

        if self.filepath == "" or (isNotATrack and isNotANode):
            return {'FINISHED'}

        exportImages = context.preferences.addons[os.path.basename(os.path.dirname(__file__))].preferences.stk_export_images
        savescene_callback(self, self.filepath, exportImages, self.exportDrivelines, self.exportScene, self.exportMaterials)
        return {'FINISHED'}

    @classmethod
    def poll(self, context):
        if ('is_stk_track' in context.scene and context.scene['is_stk_track'] == 'true') or \
        ('is_stk_node' in context.scene and context.scene['is_stk_node'] == 'true'):
            return True
        else:
            return False