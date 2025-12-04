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

import bpy, datetime, sys, os, shutil, traceback, math, platform
from bpy_extras.io_utils import ExportHelper
from mathutils import *
from . import stk_utils, stk_panel

def getSlashOS():
    slash = ""
    if platform.system() == "Windows":
        slash = "\\"
    else:
        slash = "/"
    return str(slash)

# ------------------------------------------------------------------------------
# Save nitro emitter
def saveNitroEmitter(self, f, lNitroEmitter, path):
    if len(lNitroEmitter) > 2:
        self.report({'WARNING'}, " %d nitro emitter specified. Up to 2 are allowed." % len(lNitroEmitter))
        return
    if len(lNitroEmitter) > 0:	
	    f.write('  <nitro-emitter>\n')
	    f.write('    <nitro-emitter-a position = "%f %f %f" />\n' \
	            % (lNitroEmitter[0].location.x, lNitroEmitter[0].location.z, lNitroEmitter[0].location.y))
	    f.write('    <nitro-emitter-b position = "%f %f %f" />\n' \
	            % (lNitroEmitter[1].location.x, lNitroEmitter[1].location.z, lNitroEmitter[1].location.y))
	    f.write('  </nitro-emitter>\n')
    #else:
     #   f.write('  <nitro-emitter>\n')
	  #  f.write('    <nitro-emitter-a position = "%f %f %f" />\n' \
	   #         % (lNitroEmitter[0].location.x, lNitroEmitter[0].location.z, lNitroEmitter[0].location.y))
	    #f.write('  </nitro-emitter>\n')
        

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
                self.report({'WARNING'}, "Missing straight frame for saving straight location")
                assert False
            bone_name = obj.parent_bone
            bpy.context.scene.frame_set(straight_frame)
        headlight_color = None
        headlight_type = None
        loc, rot, scale = obj.matrix_world.decompose()
        stktype = stk_utils.getObjectProperty(obj, "type", "").strip().upper()
        if stktype == 'HEADLIGHT':
            headlight_color = stk_utils.getObjectProperty(obj, 'headlight_color', None)
        else:
            headlight_type = obj.type.lower()
            if headlight_type == 'light':
                headlight_type = obj.data.type.lower()
                col_red = int(obj.data.color[0] * 255)
                col_green = int(obj.data.color[1] * 255)
                col_blue = int(obj.data.color[2] * 255)
                headlight_color = '%d %d %d' % (col_red, col_green, col_blue)
                if headlight_type == 'spot':
                    axis_conv = Quaternion((1.0, 0.0, 0.0), math.radians(-90.0))
                    rot = (rot @ axis_conv).normalized()
        rot = rot.to_euler('XZY')
        rad2deg = -180.0 / 3.1415926535;
        flags = []
        flags.append('    <object position="%f %f %f"\n' % (loc[0], loc[2], loc[1]))
        flags.append('           rotation="%f %f %f"\n' % (rot[0] * rad2deg, rot[2] * rad2deg, rot[1] * rad2deg))
        flags.append('           scale="%f %f %f"\n' % (scale[0], scale[2], scale[1]))
        if bone_name:
            flags.append('           bone="%s"\n' % bone_name)

        if headlight_color is not None and headlight_color != '255 255 255':
            flags.append('           color=\"%s\"\n' % headlight_color)
        if obj.type == 'LIGHT':
            flags.append('           radius="%.2f"\n' % obj.data.shadow_soft_size)
            flags.append('           energy="%.2f"\n' % obj.data.energy)
            if headlight_type == 'spot':
                flags.append('           inner-cone=\"%.3f\"\n' % (obj.data.spot_size * (1.0 - obj.data.spot_blend)))
                flags.append('           outer-cone=\"%.3f\"\n' % obj.data.spot_size)
        if headlight_type is not None:
            flags.append('           type=\"%s\"\n' % headlight_type)
        if obj.type == 'MESH':
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
            flags.append('           model="%s"\n' % exported_name)
        f.write('%s' % ' '.join(flags) + '    />\n')
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
                self.report({'WARNING'}, "Missing straight frame for saving straight location")
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
def saveAnimations(self, f, kart_version, export_version):
    first_frame = bpy.context.scene.frame_start
    last_frame  = bpy.context.scene.frame_end
    straight_frame = -1
    rename_count = 0
    # search for animation
    lAnims = []
    lMarkersFound = []
    for i in range(first_frame, last_frame+1):
        # Find markers at this frame
        for curr in bpy.context.scene.timeline_markers:
            if curr.frame == i:
                markerName = curr.name.lower()
                # We currently support export of both version 3 karts (for 1.x)
                # and version 4 karts (for STK Evolution).
                # A kart designed as v3 can be exported as v4 (it will miss the new animations
                # but otherwise work). A kart designed as v4 can be exported as v3
                # (again missing on the new animations), so kart designers can adopt the v4 format
                # in their blends but still make the kart available for 1.x users.
                # This will remain the case in the foreseeable future. 
                if export_version == 3:
                    if  markerName in \
                       ["straight", "right", "left", "start-winning", "start-winning-loop",
                        "end-winning", "end-winning-straight", "start-losing", "start-losing-loop", "end-losing", "end-losing-straight",
                        "start-jump", "start-jump-loop", "end-jump",
                        "backpedal-left", "backpedal", "backpedal-right", "selection-start", "selection-end",
                        "winning-start", "winning-loop-start", "winning-loop-end", "winning-to-straight",
                        "losing-start", "losing-loop-start", "losing-loop-end", "losing-to-straight",
                        "jump-start", "jump-loop-start", "jump-loop-end",
                        "selection-loop-start", "selection-loop-end"]:
                        if markerName=="straight" : straight_frame = i
                        # When exporting a v4 kart as a v3 kart, convert animation marker names
                        if markerName=="winning-start": markerName="start-winning"
                        if markerName=="winning-loop-start": markerName="start-winning-loop"
                        if markerName=="winning-loop-end": markerName="end-winning"
                        if markerName=="winning-to-straight": markerName="end-winning-straight"
                        if markerName=="losing-start": markerName="start-losing"
                        if markerName=="losing-loop-start": markerName="start-losing-loop"
                        if markerName=="losing-loop-end": markerName="end-losing"
                        if markerName=="losing-to-straight": markerName="end-losing-straight"
                        if markerName=="jump-start": markerName="start-jump"
                        if markerName=="jump-loop-start": markerName="start-jump-loop"
                        if markerName=="jump-loop-end": markerName="end-jump"
                        if (markerName=="selection-start" and kart_version == 4):
                            continue
                        if markerName=="selection-loop-start": markerName="selection-start"
                        if markerName=="selection-loop-end": markerName="selection-end"
                        lAnims.append( (markerName, i-1) )
                        lMarkersFound.append(markerName)
                        #self.report({'INFO'}, "Kart exported with animation marker " + markerName)
                    #else:
                        # Disable by default to not have spurious warnings when exporting a v4 kart as v3
                        #self.report({'INFO'}, "Unrecognized marker " + markerName)
                if export_version == 4:
                    if  markerName in \
                       ["straight", "right", "left", "start-winning", "start-winning-loop",
                        "end-winning", "end-winning-straight", "start-losing", "start-losing-loop", "end-losing", "end-losing-straight",
                        "start-jump", "start-jump-loop", "end-jump",
                        "backpedal-left", "backpedal", "backpedal-right", "selection-end",
                        "winning-start", "winning-loop-start", "winning-loop-end", "winning-to-straight",
                        "neutral-start", "neutral-loop-start", "neutral-loop-end",
                        "losing-start", "losing-loop-start", "losing-loop-end", "losing-to-straight",
                        "podium-start", "podium-loop-start", "podium-loop-end",
                        "jump-start", "jump-loop-start", "jump-loop-end",
                        "selection-start", "selection-loop-start", "selection-loop-end",
                        "bump-front", "bump-left", "bump-right", "bump-back",
                        "happy-start", "happy-end", "hit-start", "hit-end",
                        "false-accel-start", "false-accel-end"]:
                        if markerName=="straight" : straight_frame = i
                        # When exporting a v3 kart as a v4 kart, convert animation marker names
                        if markerName=="start-winning":
                            markerName="winning-start"
                            rename_count += 1
                        if markerName=="start-winning-loop":
                            markerName="winning-loop-start"
                            rename_count += 1
                        if markerName=="end-winning":
                            markerName="winning-loop-end"
                            rename_count += 1
                        if markerName=="end-winning-straight":
                            markerName="winning-to-straight"
                            rename_count += 1
                        if markerName=="start-losing":
                            markerName="losing-start"
                            rename_count += 1
                        if markerName=="start-losing-loop":
                            markerName="losing-loop-start"
                            rename_count += 1
                        if markerName=="end-losing" :
                            markerName="losing-loop-end"
                            rename_count += 1
                        if markerName=="end-losing-straight":
                            markerName="losing-to-straight"
                            rename_count += 1
                        if markerName=="start-jump":
                            markerName="jump-start"
                            rename_count += 1
                        if markerName=="start-jump-loop":
                            markerName="jump-loop-start"
                            rename_count += 1
                        if markerName=="end-jump":
                            markerName="jump-loop-end"
                            rename_count += 1
                        if (markerName=="selection-start" and kart_version == 3):
                            markerName="selection-loop-start"
                        if markerName=="selection-end":
                            markerName="selection-loop-end"
                            rename_count += 1
                        lAnims.append( (markerName, i-1) )
                        lMarkersFound.append(markerName)
                        #self.report({'INFO'}, "Kart exported with animation marker " + markerName)
                    else:
                        self.report({'WARNING'}, "Unrecognized marker " + markerName)

    # Warnings applicable for both v3 and v4 karts
    if (not "straight" in lMarkersFound):
        self.report({'ERROR'}, 'The marker straight is missing in frames %i to %i, the kart will not work properly.' %  (first_frame, last_frame))
    if (not "left" in lMarkersFound):
        self.report({'WARNING'}, 'The marker left is missing in frames %i to %i, steering animations may not work.' %  (first_frame, last_frame))
    if (not "right" in lMarkersFound):
        self.report({'WARNING'}, 'The marker right is missing in frames %i to %i, steering animations may not work.' %  (first_frame, last_frame))
    if (not "backpedal-left" in lMarkersFound):
        self.report({'WARNING'}, 'The marker backpedal-left is missing in frames %i to %i, '
            'backward steering animations may not work.' %  (first_frame, last_frame))
    if (not "backpedal-right" in lMarkersFound):
        self.report({'WARNING'}, 'The marker backpedal-right is missing in frames %i to %i, '
            'backward steering animations may not work.' %  (first_frame, last_frame))

    # Warnings when exporting as v3
    if export_version == 3:
        if (not "start-winning" in lMarkersFound) or (not "start-winning-loop" in lMarkersFound) or (not "end-winning" in lMarkersFound):
            self.report({'WARNING'}, 'Could not find all the markers for the win animation in frames %i to %i, '
                'the win animation may not work properly.' %  (first_frame, last_frame))
        if (not "start-losing" in lMarkersFound) or (not "start-losing-loop" in lMarkersFound) or (not "end-losing" in lMarkersFound):
            self.report({'WARNING'}, 'Could not find all the markers for the lose animation in frames %i to %i, '
                'the lose animation may not work properly.' %  (first_frame, last_frame))
        if (not "start-jump" in lMarkersFound) or (not "start-jump-loop" in lMarkersFound) or (not "end-jump" in lMarkersFound):
            self.report({'WARNING'}, 'Could not find all the markers for the jump animation in frames %i to %i, '
                'the jump animation may not work properly.' %  (first_frame, last_frame))
        if (not "selection-start" in lMarkersFound) or (not "selection-end" in lMarkersFound):
            self.report({'WARNING'}, 'Could not find all the markers for the selection animation in frames %i to %i, '
                'the selection animation may not work properly.' %  (first_frame, last_frame))

    #Warnings when exporting as v4
    if export_version == 4:
        if (not "winning-start" in lMarkersFound) or (not "winning-loop-start" in lMarkersFound) or (not "winning-loop-end" in lMarkersFound):
            self.report({'WARNING'}, 'Could not find all the markers for the win animation in frames %i to %i, '
                'the win animation may not work properly.' %  (first_frame, last_frame))
        if (not "losing-start" in lMarkersFound) or (not "losing-loop-start" in lMarkersFound) or (not "losing-loop-end" in lMarkersFound):
            self.report({'WARNING'}, 'Could not find all the markers for the lose animation in frames %i to %i, '
                'the lose animation may not work properly.' %  (first_frame, last_frame))
        if (not "jump-start" in lMarkersFound) or (not "jump-loop-start" in lMarkersFound) or (not "jump-loop-end" in lMarkersFound):
            self.report({'WARNING'}, 'Could not find all the markers for the jump animation in frames %i to %i, '
                'the jump animation may not work properly.' %  (first_frame, last_frame))
        if (not "selection-loop-start" in lMarkersFound) or (not "selection-loop-end" in lMarkersFound):
            self.report({'WARNING'}, 'Could not find all the markers for the selection animation in frames %i to %i, '
                'the selection animation may not work properly.' %  (first_frame, last_frame))
        # Warnings likely caused by incomplete conversions from v3 to v4
        if (rename_count > 0) and (kart_version == 4):
            self.report({'WARNING'}, 'This kart is marked as version 4, but %i markers are still using '
                'v3 naming conventions. Think of converting them' % (rename_count))
        if ("selection-start" in lMarkersFound) and (not "selection-loop-start" in lMarkersFound):
            self.report({'WARNING'}, 'The marker selection-start has been found without a matching selection-loop-start marker. '
                'You likely forgot to rename selection-start into selection-loop-start when updating a v3 kart to v4.')
        # It's expected for these animations to be missing in v3 karts exported as v4
        if kart_version == 4:
            if (not "neutral-start" in lMarkersFound) or (not "neutral-loop-start" in lMarkersFound) or (not "neutral-loop-end" in lMarkersFound):
                self.report({'WARNING'}, 'Could not find all the markers for the neutral animation in frames %i to %i, '
                    'the neutral animation may not work properly.' %  (first_frame, last_frame))
            if (not "podium-start" in lMarkersFound) or (not "podium-loop-start" in lMarkersFound) or (not "podium-loop-end" in lMarkersFound):
                self.report({'WARNING'}, 'Could not find all the markers for the podium animation in frames %i to %i, '
                    'the podium animation may not work properly.' %  (first_frame, last_frame))
            if (not "happy-start" in lMarkersFound) or (not "happy-end" in lMarkersFound):
                self.report({'WARNING'}, 'Could not find all the markers for the happy animation in frames %i to %i, '
                    'the happy animation may not work properly.' %  (first_frame, last_frame))
            if (not "hit-start" in lMarkersFound) or (not "hit-end" in lMarkersFound):
                self.report({'WARNING'}, 'Could not find all the markers for the hit animation in frames %i to %i, '
                    'the hit animation may not work properly.' %  (first_frame, last_frame))
            if (not "false-accel-start" in lMarkersFound) or (not "false-accel-end" in lMarkersFound):
                self.report({'WARNING'}, 'Could not find all the markers for the false start animation in frames %i to %i, '
                    'the false start animation may not work properly.' %  (first_frame, last_frame))
            if (not "bump-front" in lMarkersFound) or (not "bump-left" in lMarkersFound) or (not "bump-right" in lMarkersFound) or (not "bump-back" in lMarkersFound):
                self.report({'WARNING'}, 'Could not find all the markers for the bump animations in frames %i to %i, '
                    'the bump animations may not work properly.' %  (first_frame, last_frame))

    if lAnims:
        f.write('  <animations %s = "%s"' % (lAnims[0][0], lAnims[0][1]))
        for (marker, frame) in lAnims[1:]:
                f.write('\n              %s = "%s"'%(marker, frame))
        f.write('/>\n')
    return straight_frame

# ------------------------------------------------------------------------------
# Code for saving kart specific sounds. This is not yet supported, but for
# now I'll leave the code in place
def saveSounds(f, engine_sfx, skid_sound):
    #lSounds = []
    #if  engine_sfx:                 lSounds.append( ("engine",     engine_sfx) );
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

    #if lSounds:
        #f.write('  <sounds %s = "%s"'%(lSounds[0][0], lSounds[0][1]))
        #for (name, sound) in lSounds[1:]:
        #    f.write('\n          %s = "%s"'%(name, sound))
    f.write('  <sounds engine = "%s">\n'%(engine_sfx))
    f.write('      %s\n'%(skid_sound))
    f.write('  </sounds>\n')

# ------------------------------------------------------------------------------
# Exports the actual kart.
def exportKart(self, path):
    kart_name_string = bpy.context.scene['name']

    if not kart_name_string or len(kart_name_string) == 0:
        self.report({'ERROR'}, "No kart name specified")
        return

    kart_version = bpy.context.scene['kart_version']
    if ((kart_version != 3) and (kart_version != 4)):
        self.report({'ERROR'}, "The kart.xml version is not specified or incorrect")
        return

    export_version = bpy.context.scene['export_version']
    if ((export_version != 3) and (export_version != 4)):
        self.report({'ERROR'}, "The kart.xml export version is not specified or incorrect")
        return

    self.report({'INFO'}, "Kart designed as version " + str(kart_version) + " and exported as version " + str(export_version))

    if (kart_version == 3):
        self.report({'INFO'}, "Think of updating this kart to the v4 format!")

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
    lObj = bpy.context.scene.objects

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
        elif stktype=="HEADLIGHT" or stktype=="AUTO-HEADLIGHT":
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

    if 'skid_sound' in bpy.context.scene:
        skid_sound = bpy.context.scene['skid_sound']
    else:
        # Backwards compatibility
        skid_sound = "default"

    if len(skid_sound) == 0:
        skid_sound = '<skid name=""/>'
    if skid_sound == "default":
        skid_sound = '<skid name="default"/>'

    kart_type = 'medium'
    if 'karttype' in bpy.context.scene:
        kart_type = bpy.context.scene['karttype']

    stk_utils.unhideObjectsTransiently();
    with open(path + "/kart.xml", "w", encoding="utf8", newline="\n") as f:
        f.write('<?xml version="1.0" encoding=\"utf-8\"?>\n')
        rgb = (0.7, 0.0, 0.0)
        model_file = kart_name_string.lower()+".spm"
        f.write('<kart name              = "%s"\n' % kart_name_string)
        f.write('      version           = "%i"\n' % export_version)
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

        saveSounds(f, kart_engine_sfx, skid_sound)
        straight_frame = saveAnimations(self, f, kart_version, export_version)
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
                #print('abs_texture_path', abs_texture_path, blendfile_dir)
                #if bpy.path.is_subdir(abs_texture_path, blendfile_dir): shutil.copy(abs_texture_path, sPath)
                shutil.copy(abs_texture_path, self.filepath)
                print(f"Copy Texture {abs_texture_path} to {self.filepath}")
                self.report({'INFO'}, 'copy texture ' + abs_texture_path + ' to ' + self.filepath)
                
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

        try:
            assets_path = bpy.context.preferences.addons[os.path.basename(os.path.dirname(__file__))].preferences.stk_assets_path
        except: 
            pass
        
        if assets_path is None or len(assets_path) < 0:
            self.report({'ERROR'}, "Please select the export path in the add-on preferences or quick exporter panel")
            return {'FINISHED'}
        
        blend_filepath = context.blend_data.filepath
        if blend_filepath:
            blend_filepath = blend_filepath.split(getSlashOS())[-1].replace(".blend", "")
        folder = os.path.join(assets_path, 'karts')

        if not os.path.exists(folder): 
            os.makedirs(folder, exist_ok=True)
        self.filepath = os.path.join(folder, blend_filepath)
        if not os.path.exists(self.filepath): os.makedirs(self.filepath, exist_ok=True)
         
        return self.execute(context)

    def execute(self, context):
        if bpy.context.mode != 'OBJECT':
            # Return to object mode before exporting
            bpy.ops.object.mode_set(mode='OBJECT')

        if self.filepath == "":
            return {'FINISHED'}
            
        savescene_callback(self, context, self.filepath)
        return {'FINISHED'}

    @classmethod
    def poll(self, context):
        if 'is_stk_kart' in context.scene and \
        context.scene['is_stk_kart'] == 'true':
            return True
        else:
            return False