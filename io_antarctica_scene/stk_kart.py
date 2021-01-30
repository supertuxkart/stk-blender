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

import bpy, datetime, sys, os, shutil, traceback
from bpy_extras.io_utils import ExportHelper
from mathutils import *
from . import stk_utils, stk_panel

# ------------------------------------------------------------------------------
# Save nitro emitter
def saveNitroEmitter(self, f, lNitroEmitter, path):
    if len(lNitroEmitter) > 2:
        self.report({'WARNING'}, " %d nitro emitter specified. Up to 2 are allowed." % len(lNitroEmitter))
        return

    f.write('  <nitro-emitter>\n')
    f.write('    <nitro-emitter-a position = "%f %f %f" />\n' \
                % (lNitroEmitter[0].location.x, lNitroEmitter[0].location.z, lNitroEmitter[0].location.y))
    f.write('    <nitro-emitter-b position = "%f %f %f" />\n' \
                % (lNitroEmitter[1].location.x, lNitroEmitter[1].location.z, lNitroEmitter[1].location.y))
    f.write('  </nitro-emitter>\n')

# ------------------------------------------------------------------------------

def saveHeadlights(self, f, lHeadlights, path, straight_frame):
    if len(lHeadlights) == 0:
        return

    f.write('  <headlights>\n')
    instancing_objects = {}
    for obj in lHeadlights:
        bone_name = None
        if obj.parent and obj.parent_type == 'BONE':
            if straight_frame == -1:
                self.report({'WARNING'}, "Missing striaght frame for saving straight location")
                assert False
            bone_name = obj.parent_bone
            bpy.context.scene.frame_set(straight_frame)
        loc, rot, scale = obj.matrix_world.decompose()
        rot = rot.to_euler('XZY')
        rad2deg = -180.0 / 3.1415926535;
        flags = []
        flags.append('    <object position="%f %f %f"\n' % (loc[0], loc[2], loc[1]))
        flags.append('           rotation="%f %f %f"\n' % (rot[0] * rad2deg, rot[2] * rad2deg, rot[1] * rad2deg))
        flags.append('           scale="%f %f %f"\n' % (scale[0], scale[2], scale[1]))
        if bone_name:
            flags.append('           bone="%s"\n' % bone_name)
        headlight_color = stk_utils.getObjectProperty(obj, 'headlight_color', '255 255 255')
        if headlight_color != '255 255 255':
            flags.append('           color=\"%s\"\n' % headlight_color)

        exported_name = obj.name + ".spm"
        if obj.data.name in instancing_objects:
            exported_name = instancing_objects[obj.data.name] + ".spm"
        else:
            instancing_objects[obj.data.name] = obj.name

            obj.select_set(True)
            bpy.ops.screen.spm_export(localsp=True, filepath=path + "/" + exported_name, selection_type="selected", \
                                      export_tangent='precalculate_tangents' in bpy.context.scene\
                                      and bpy.context.scene['precalculate_tangents'] == 'true')
            obj.select_set(False)

        flags.append('           model="%s"/>\n' % exported_name)
        f.write('%s' % ' '.join(flags))
    f.write('  </headlights>\n')

# ------------------------------------------------------------------------------
# Save speed weighted
def saveSpeedWeighted(self, f, lSpeedWeighted, path, straight_frame):
    if len(lSpeedWeighted) == 0:
        return

    f.write('  <speed-weighted-objects>\n')
    instancing_objects = {}
    for obj in lSpeedWeighted:
        bone_name = None
        if obj.parent and obj.parent_type == 'BONE':
            if straight_frame == -1:
                self.report({'WARNING'}, "Missing striaght frame for saving straight location")
                assert False
            bone_name = obj.parent_bone
            bpy.context.scene.frame_set(straight_frame)
        loc, rot, scale = obj.matrix_world.decompose()
        rot = rot.to_euler('XZY')
        rad2deg = -180.0 / 3.1415926535;
        flags = []
        flags.append('    <object position="%f %f %f"\n' % (loc[0], loc[2], loc[1]))
        flags.append('           rotation="%f %f %f"\n' % (rot[0] * rad2deg, rot[2] * rad2deg, rot[1] * rad2deg))
        flags.append('           scale="%f %f %f"\n' % (scale[0], scale[2], scale[1]))
        if bone_name:
            flags.append('           bone="%s"\n' % bone_name)

        strength_factor = float(stk_utils.getObjectProperty(obj, "speed-weighted-strength-factor", -1.0))
        speed_factor    = float(stk_utils.getObjectProperty(obj, "speed-weighted-speed-factor",    -1.0))
        texture_speed_x = float(stk_utils.getObjectProperty(obj, "speed-weighted-texture-speed-x", 0.0))
        texture_speed_y = float(stk_utils.getObjectProperty(obj, "speed-weighted-texture-speed-y", 0.0))

        attr = ""
        if strength_factor >= 0.0:
            attr = attr + ' strength-factor="%f"' % strength_factor
        if speed_factor >= 0.0:
            attr = attr + ' speed-factor="%f"' % speed_factor
        if texture_speed_x != 0.0 or texture_speed_y != 0.0:
            attr = attr + ' texture-speed-x="%f" texture-speed-y="%f"' % (texture_speed_x, texture_speed_y)
        flags.append('          %s\n' % attr)

        exported_name = obj.name + ".spm"
        if obj.data.name in instancing_objects:
            exported_name = instancing_objects[obj.data.name] + ".spm"
        else:
            instancing_objects[obj.data.name] = obj.name

            obj.select_set(True)
            bpy.ops.screen.spm_export(localsp=True, filepath=path + "/" + exported_name, selection_type="selected", \
                                      export_tangent='precalculate_tangents' in bpy.context.scene\
                                      and bpy.context.scene['precalculate_tangents'] == 'true')
            obj.select_set(False)

        flags.append('           model="%s"/>\n' % exported_name)
        f.write('%s' % ' '.join(flags))
    f.write('  </speed-weighted-objects>\n')

# ------------------------------------------------------------------------------
def saveWheels(self, f, lWheels, path):
    if len(lWheels) == 0:
        return

    if len(lWheels) > 4:
        self.report({'WARNING'}, "%d wheels specified. Up to 4 are allowed." % len(lWheels))

    lWheelNames = ("wheel-front-right.spm", "wheel-front-left.spm",
                   "wheel-rear-right.spm",  "wheel-rear-left.spm"   )
    lSides      = ('front-right', 'front-left', 'rear-right', 'rear-left')

    f.write('  <wheels>\n')
    for wheel in lWheels:
        name = wheel.name.upper()

        # The new style 'type=wheel' is always used. Use the x and
        #  y coordinates to determine where the wheel belongs to.
        x = wheel.location.x
        y = wheel.location.y
        index = 0
        if y<0:
            index=index+2
        if x<0: index=index+1

        f.write('    <%s position = "%f %f %f"\n' \
                % ( lSides[index], wheel.location.x, wheel.location.z, wheel.location.y))
        f.write('                 model    = "%s"       />\n'%lWheelNames[index])
        lOldPos = Vector([wheel.location.x, wheel.location.y, wheel.location.z])
        wheel.location = Vector([0, 0, 0])

        wheel.select_set(True)
        bpy.ops.screen.spm_export(localsp=False, filepath=path + "/" + lWheelNames[index], selection_type="selected", \
                                  export_tangent='precalculate_tangents' in bpy.context.scene\
                                  and bpy.context.scene['precalculate_tangents'] == 'true')
        wheel.select_set(False)

        wheel.location = lOldPos

    f.write('  </wheels>\n')

# ------------------------------------------------------------------------------
# Saves any defined animations to the kart.xml file.
def saveAnimations(self, f):
    first_frame = bpy.context.scene.frame_start
    last_frame  = bpy.context.scene.frame_end
    straight_frame = -1
    # search for animation
    lAnims = []
    lMarkersFound = []
    for i in range(first_frame, last_frame+1):

        # Find markers at this frame
        for curr in bpy.context.scene.timeline_markers:
            if curr.frame == i:
                markerName = curr.name.lower()
                if  markerName in \
                   ["straight", "right", "left", "start-winning", "start-winning-loop",
                    "end-winning", "start-losing", "start-losing-loop", "end-losing",
                    "start-explosion", "end-explosion", "start-jump", "start-jump-loop", "end-jump",
                    "turning-l", "center", "turning-r", "repeat-losing", "repeat-winning",
                    "backpedal-left", "backpedal", "backpedal-right", "selection-start", "selection-end"]:
                    if markerName=="turning-l": markerName="left"
                    if markerName=="turning-r": markerName="right"
                    if markerName=="center": markerName="straight"
                    if markerName=="straight" : straight_frame = i
                    if markerName=="repeat-losing": markerName="start-losing-loop"
                    if markerName=="repeat-winning": markerName="start-winning-loop"
                    lAnims.append( (markerName, i-1) )
                    lMarkersFound.append(markerName)

    if (not "straight" in lMarkersFound) or (not "left" in lMarkersFound) or (not "right" in lMarkersFound):
        self.report({'WARNING'}, 'Could not find markers left/straight/right in frames %i to %i, steering animations may not work.' %  (first_frame, last_frame))

    if (not "start-winning" in lMarkersFound) or (not "start-losing" in lMarkersFound) or (not "end-winning" in lMarkersFound) or (not "end-losing" in lMarkersFound):
        self.report({'WARNING'}, 'Could not find markers for win/lose animations in frames %i to %i, win/lose animations may not work.' %  (first_frame, last_frame))


    if lAnims:
        f.write('  <animations %s = "%s"' % (lAnims[0][0], lAnims[0][1]))
        for (marker, frame) in lAnims[1:]:
                f.write('\n              %s = "%s"'%(marker, frame))
        f.write('/>\n')
    return straight_frame

# ------------------------------------------------------------------------------
# Code for saving kart specific sounds. This is not yet supported, but for
# now I'll leave the code in place
def saveSounds(f, engine_sfx):
    lSounds = []
    if  engine_sfx:                 lSounds.append( ("engine",     engine_sfx) );
    #if kart_sound_horn.val  != "": lSounds.append( ("horn-sound", kart_sound_horn.val ))
    #if kart_sound_crash.val != "": lSounds.append( ("crash-sound",kart_sound_crash.val))
    #if kart_sound_shoot.val != "" :lSounds.append( ("shoot-sound",kart_sound_shoot.val))
    #if kart_sound_win.val   != "" :lSounds.append( ("win-sound",  kart_sound_win.val  ))
    #if kart_sound_explode.val!="" :lSounds.append( ("explode-sound",kart_sound_explode.val))
    #if kart_sound_goo.val   != "" :lSounds.append( ("goo-sound",  kart_sound_goo.val))
    #if kart_sound_pass.val  != "" :lSounds.append( ("pass-sound", kart_sound_pass.val))
    #if kart_sound_zipper.val!= "" :lSounds.append( ("zipper-sound",kart_sound_zipper.val))
    #if kart_sound_name.val  != "" :lSounds.append( ("name-sound", kart_sound_name.val))
    #if kart_sound_attach.val!= "" :lSounds.append( ("attach-sound",kart_sound_attach.val))

    if lSounds:
        f.write('  <sounds %s = "%s"'%(lSounds[0][0], lSounds[0][1]))
        for (name, sound) in lSounds[1:]:
            f.write('\n          %s = "%s"'%(name, sound))
        f.write('/>\n')

# ------------------------------------------------------------------------------
# Exports the actual kart.
def exportKart(self, path):
    kart_name_string = bpy.context.scene['name']

    if not kart_name_string or len(kart_name_string) == 0:
        self.report({'ERROR'}, "No kart name specified")
        return

    color = bpy.context.scene['color']
    if color is None:
        self.report({'ERROR'}, "Incorrect kart color")
        return

    split_color = color.split()
    if len(split_color) != 3:
        self.report({'ERROR'}, "Incorrect kart color")
        return

    try:
        split_color[0] = "%.2f" % (int(split_color[0]) / 255.0)
        split_color[1] = "%.2f" % (int(split_color[1]) / 255.0)
        split_color[2] = "%.2f" % (int(split_color[2]) / 255.0)
    except:
        self.report({'ERROR'}, "Incorrect kart color")
        return

    # Get the kart and all wheels
    # ---------------------------
    objSel = bpy.context.preferences.addons[os.path.basename(os.path.dirname(__file__))].preferences.stk_object_selection
    if objSel == "selected":
        lObj = bpy.context.selected_objects
    elif objSel == "scene":
        lObj = bpy.context.scene.objects
    elif objSel == "view-layer":
        lObj = bpy.view_layer.objects
    else:
        lObj = bpy.data.objects

    lWheels       = []
    lKart         = []
    lNitroEmitter = []
    lSpeedWeighted = []
    lHeadlights = []
    hat_object = None
    for obj in lObj:
        stktype = stk_utils.getObjectProperty(obj, "type", "").strip().upper()
        name    = obj.name.upper()
        if stktype=="WHEEL":
            lWheels.append(obj)
        elif stktype=="NITRO-EMITTER":
            lNitroEmitter.append(obj)
        elif stktype=="SPEED-WEIGHTED":
            lSpeedWeighted.append(obj)
        elif stktype=="IGNORE" or obj.hide_render:
            pass
        elif stktype=="HEADLIGHT":
            lHeadlights.append(obj)
        elif stktype=="HAT":
            hat_object = obj
        else:
            # Due to limitations with the spm exporter animated
            # objects must be first in the list of objects to export:
            if obj.parent and obj.parent.type=="Armature":
                lKart.insert(0, obj)
            else:
                lKart.append(obj)

    # Write the xml file
    # ------------------
    kart_shadow = bpy.context.scene['shadow']
    if not kart_shadow or len(kart_shadow) == 0:
        kart_shadow = kart_name_string.lower() + "_shadow.png"

    kart_icon = bpy.context.scene['icon']
    if not kart_icon or len(kart_icon) == 0:
        kart_icon = kart_name_string.lower() + "_icon.png"

    kart_map_icon = bpy.context.scene['minimap_icon']
    if not kart_map_icon or len(kart_map_icon) == 0:
        kart_map_icon = kart_name_string.lower() + "_map_icon.png"

    kart_group = bpy.context.scene['group']
    if not kart_group or len(kart_group) == 0:
        kart_group = "default"

    kart_engine_sfx = bpy.context.scene['engine_sfx']
    if not kart_engine_sfx or len(kart_engine_sfx) == 0:
        kart_engine_sfx = "small"

    kart_type = 'medium'
    if 'karttype' in bpy.context.scene:
        kart_type = bpy.context.scene['karttype']

    stk_utils.unhideObjectsTransiently();
    with open(path + "/kart.xml", "w", encoding="utf8", newline="\n") as f:
        f.write('<?xml version="1.0" encoding=\"utf-8\"?>\n')
        rgb = (0.7, 0.0, 0.0)
        model_file = kart_name_string.lower()+".spm"
        f.write('<kart name              = "%s"\n' % kart_name_string)
        f.write('      version           = "3"\n' )
        f.write('      model-file        = "%s"\n' % model_file)
        f.write('      icon-file         = "%s"\n' % kart_icon)
        f.write('      minimap-icon-file = "%s"\n' % kart_map_icon)
        f.write('      shadow-file       = "%s"\n' % kart_shadow)
        f.write('      type              = "%s"\n' % kart_type)

        center_shift = bpy.context.scene['center_shift']
        if center_shift and center_shift != 0:
            f.write('      center-shift      = "%.2f"\n' % center_shift)

        f.write('      groups            = "%s"\n' % kart_group)
        f.write('      rgb               = "%s %s %s" >\n' % tuple(split_color))

        saveSounds(f, kart_engine_sfx)
        straight_frame = saveAnimations(self, f)
        bpy.ops.object.select_all(action='DESELECT')
        saveWheels(self, f, lWheels, path)
        saveSpeedWeighted(self, f, lSpeedWeighted, path, straight_frame)
        saveNitroEmitter(self, f, lNitroEmitter, path)
        saveHeadlights(self, f, lHeadlights, path, straight_frame)

        if hat_object:
            if hat_object.parent and hat_object.parent_type == 'BONE':
                if straight_frame == -1:
                    print("Missing striaght frame for saving straight location")
                    assert False
                bpy.context.scene.frame_set(straight_frame)
                loc, rot, scale = hat_object.matrix_world.decompose()
                rot = rot.to_euler('XZY')
                rad2deg = -180.0 / 3.1415926535;
                f.write('  <hat position="%f %f %f"\n       rotation="%f %f %f"'
                    '\n       scale="%f %f %f"\n       bone="%s"/>\n' \
                    % (loc[0], loc[2], loc[1], rot[0] * rad2deg, rot[2] * rad2deg, rot[1] * rad2deg,\
                    scale[0], scale[2], scale[1], hat_object.parent_bone))
            else:
                loc, rot, scale = hat_object.matrix_world.decompose()
                rad2deg = -180.0 / 3.1415926535;
                rot = rot.to_euler('XZY')
                f.write('  <hat position="%f %f %f"\n       rotation="%f %f %f"'
                    '\n       scale="%f %f %f"/>\n' \
                    % (loc[0], loc[2], loc[1], rot[0] * rad2deg, rot[2] * rad2deg, rot[1] * rad2deg,\
                    scale[0], scale[2], scale[1]))

        if 'kartLean' in bpy.context.scene and len(bpy.context.scene['kartLean']) > 0:
            f.write('  <lean max="' + bpy.context.scene['kartLean'] + '"/>\n')
        if 'exhaust_xml' in bpy.context.scene and len(bpy.context.scene['exhaust_xml']) > 0:
            f.write('  <exhaust file="' + bpy.context.scene['exhaust_xml'] + '"/>\n')

        f.write('</kart>\n')

    stk_utils.selectObjectsInList(lKart)
    bpy.ops.screen.spm_export(localsp=False, filepath=path+"/"+model_file, selection_type="selected", \
                              export_tangent='precalculate_tangents' in bpy.context.scene\
                              and bpy.context.scene['precalculate_tangents'] == 'true', \
                              static_mesh_frame = straight_frame)
    bpy.ops.object.select_all(action='DESELECT')
    stk_utils.hideTransientObjects();

    # materials file
    # ----------
    if 'stk_material_export' not in dir(bpy.ops.screen):
        self.report({'ERROR'}, "Cannot find the material exporter, make sure you installed it properly")
        return
    bpy.ops.screen.stk_material_export(filepath=path + "/materials.xml")

# ==============================================================================
def savescene_callback(self, context, sPath):
    if 'spm_export' not in dir(bpy.ops.screen):
        self.report({'ERROR'}, "Cannot find the spm exporter, make sure you installed it properly")
        return

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

    # Export the actual kart
    exportKart(self, sPath)

    exportImages = context.preferences.addons[os.path.basename(os.path.dirname(__file__))].preferences.stk_export_images
    if exportImages:
            for i,curr in enumerate(bpy.data.images):
                try:
                    if curr.filepath is None or len(curr.filepath) == 0:
                        continue

                    abs_texture_path = bpy.path.abspath(curr.filepath)
                    print('abs_texture_path', abs_texture_path, blendfile_dir)
                    if bpy.path.is_subdir(abs_texture_path, blendfile_dir):
                        shutil.copy(abs_texture_path, sPath)
                except:
                    traceback.print_exc(file=sys.stdout)
                    self.report({'WARNING'}, 'Failed to copy texture ' + curr.filepath)

    now = datetime.datetime.now()
    self.report({'INFO'}, "Kart export completed on " + now.strftime("%Y-%m-%d %H:%M"))

# ==== EXPORT OPERATOR ====
class STK_Kart_Export_Operator(bpy.types.Operator):
    """Export current scene to a STK kart"""

    bl_idname = ("screen.stk_kart_export")
    bl_label = ("Export STK Kart")
    filepath: bpy.props.StringProperty(subtype="FILE_PATH")

    def invoke(self, context, event):
        if 'is_stk_kart' not in context.scene or context.scene['is_stk_kart'] != 'true':
            self.report({'ERROR'}, "Not a STK kart!")
            return {'FINISHED'}

        blend_filepath = context.blend_data.filepath
        if not blend_filepath:
            blend_filepath = "Untitled"
        else:
            import os
            blend_filepath = os.path.splitext(blend_filepath)[0]
        self.filepath = blend_filepath

        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        if bpy.context.mode != 'OBJECT':
            # Return to object mode before exporting
            bpy.ops.object.mode_set(mode='OBJECT')

        if self.filepath == "" or 'is_stk_kart' not in context.scene or context.scene['is_stk_kart'] != 'true':
            return {'FINISHED'}

        savescene_callback(self, context, os.path.dirname(self.filepath))
        return {'FINISHED'}

    @classmethod
    def poll(self, context):
        try:
            if context.scene['is_stk_kart'] == 'true':
                return True
            else:
                return False
        except:
            return False
