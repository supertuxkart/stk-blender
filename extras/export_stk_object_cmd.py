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

# This script allows exporting SuperTuxKart objects from the command line
# (in background mode with no interface) to automate tasks. Supported objects
# include karts, tracks, library nodes, and standalone SPM models. The object to
# export is automatically determined by default, but it is possible to force
# specifying what kind of object to export.
#
# It is not possible to select individual objects to be exported; all objects
# that are not marked as 'ignore' or having 'hide_render' are exported.

import bpy, os, sys, argparse

def main():
    # get the args passed to blender after "--", all of which are ignored by
    # blender so scripts may receive their own arguments
    argv = sys.argv

    if "--" not in argv:
        argv = []  # as if no args are passed
    else:
        argv = argv[argv.index("--") + 1:]  # get all args after "--"

    # When --help or no args are given, print this help
    usage_text = (
        "Export a SuperTuxKart (STK) object in background mode with this script. Supported objects include karts, tracks, library nodes, and standalone SPM models:"
        "  blender --background --python " + __file__ + " -- [options]"
    )

    parser = argparse.ArgumentParser(description=usage_text)

    parser.add_argument(
        "file", type=str,
        help="The file to export data from",
    )

    parser.add_argument(
        "-k", "--kart", dest="kart", action='store_true',
        help="Force exporting a kart",
    )

    parser.add_argument(
        "-t", "--track", dest="track", action='store_true',
        help="Force exporting a track or library node",
    )

    parser.add_argument(
        "-m", "--materials", dest="materials", action='store_true',
        help="Force exporting materials.xml",
    )

    parser.add_argument(
        "-s", "--spm", dest="spm", action='store_true',
        help="Force exporting the whole scene as an SPM model",
    )

    parser.add_argument(
        "-o", "--output", dest="save_path", metavar='FILE',
        help="Export to the specified path",
    )

    args = parser.parse_args(argv)

    if 'spm_export' not in dir(bpy.ops.screen):
        print("Error: Cannot find the SPM exporter. Make sure it is installed properly and enabled.")
        return

    if 'stk_material_export' not in dir(bpy.ops.screen) and \
       'stk_kart_export' not in dir(bpy.ops.screen) and \
       'stk_track_export' not in dir(bpy.ops.screen):
        print("Error: Cannot find the SuperTuxKart exporters. Make sure they are installed properly and enabled.")
        return

    # Use the current working directory for object export if not specified
    if not args.save_path:
        args.save_path = os.getcwd()

    if not os.path.exists(args.file):
        print("Error: " + args.file + " does not lead to a valid file")
        return

    if not os.path.isfile(args.file):
        print("Error: " + args.file + " is not a valid file")
        return

    bpy.ops.wm.open_mainfile(filepath=args.file)

    # If no options given, try to automatically guess the object to export
    if not args.kart and not args.track and not args.materials and not args.spm:
        try:
            if bpy.context.scene['is_stk_kart'] == "true":
                print("Exporting " + args.file + " as a kart")
                bpy.ops.screen.stk_kart_export(filepath=args.save_path)
            elif bpy.context.scene['is_stk_track'] == "true" or bpy.context.scene['is_stk_node'] == "true":
                if bpy.context.scene['is_stk_track'] == "true":
                    print("Exporting " + args.file + " as a track")
                elif bpy.context.scene['is_stk_node'] == "true":
                    print("Exporting " + args.file + " as a library node")
                bpy.ops.screen.stk_track_export(filepath=args.save_path, exportScene=True, exportDrivelines=True, exportMaterials=True)
        except:
            print("Warning: File " + args.file + " does not contain a SuperTuxKart object, exporting as an SPM model")
            bpy.ops.screen.spm_export(localsp=False, filepath=args.save_path, selected=False, \
                                  export_tangent=True)
    elif args.spm and not args.kart and not args.track and not args.materials:
        bpy.ops.screen.spm_export(localsp=False, filepath=args.save_path, selected=False, \
                                  export_tangent=True)
    elif args.kart and not args.track and not args.materials and not args.spm:
        bpy.ops.screen.stk_kart_export(filepath=args.save_path)
    elif args.track and not args.kart and not args.materials and not args.spm:
        bpy.ops.screen.stk_track_export(filepath=args.save_path, exportScene=True, exportDrivelines=True, exportMaterials=True)
    elif args.materials and not args.kart and not args.track and not args.spm:
        bpy.ops.screen.stk_material_export(filepath=args.save_path)

    print("Exported file " + args.file + " to " + args.save_path)

if __name__ == "__main__":
    main()
