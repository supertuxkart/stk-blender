# SuperTuxKart Blender Addons

This repository contains a series of custom scripts made to help in the creation of custom SuperTuxKart karts and tracks.

  - Exporting from Blender to SuperTuxKart.
  - Importing SuperTuxKart (SPM) mesh format to Blender.
  - Script to create objects with various Level of Details.
  - Scripts to help in creating karts and tracks.
  - A script to convert materials in files created in Blender 2.79 and older.
  - A script to export STK objects from the command line.
  - A space node for test assets/production artists

### Minimum Requirements

  - Blender 3.0 or later (see [here](https://github.com/supertuxkart/stk-blender/tree/183e7bb4355d3d1268e0126418ed643e4544f718) for Blender 2.80 addon)
  - SuperTuxKart 1.0 or later

If `Proxy to Override Auto Conversion` has been disabled (a requirement for older versions of this addon), you must re-enable it in the [debug menu](https://docs.blender.org/manual/en/3.0/editors/preferences/experimental.html#debugging).

## Installation
This set of two modules requires Blender 3.0 or later.

1. Clone or download this repository. If downloaded, extract the files after that.

2. Navigate to the add-ons directory (location depends on OS and setup, see <https://docs.blender.org/manual/en/dev/advanced/blender_directory_layout.html> to find out where) at `./scripts/addons/`. If this directory hierarchy does not exist, create it. Copy or symlink the two directories `io_scene_spm` and `io_antarctica_scene` to this directory.

3. Open the preferences window by `Edit -> Preferences -> Add-ons`. Filter to show `User` add-ons.

4. Enable the add-ons `SPM (Space paritioned mesh) format` and `SuperTuxKart Exporter Tools` by clicking the checkbox next to each add-on name.

5. (Optional) After enabling `SuperTuxKart Exporter Tools`, expand its entry to find the preferences area. A few settings can be configured here, but `Assets (data) path` must be configured in order to use the track exporter. Either type in the full path to the assets, or use the button below to graphically choose the path.

It is possible to use `SPM (Space paritioned mesh) format` by itself without the `SuperTuxKart Exporter Tools`, but the latter cannot be used without the SPM scripts.

## Removal
1. Open Blender and select `Edit -> Preferences -> Add-ons`. Filter to show `User` add-ons.

2. Disable the add-ons `SPM (Space paritioned mesh) format` and/or `SuperTuxKart Exporter Tools` by clicking the checkbox next to each add-on name, or uninstall them by clicking `Remove`.

3. Alternate removal method: Navigate to the add-ons directory (location depends on OS and setup, see <https://docs.blender.org/manual/en/dev/getting_started/installing/configuration/directories.html> to find out where) at `./scripts/addons/`. Delete the two directories `io_scene_spm` and `io_antarctica_scene`.

## Exporting your Blender file
SuperTuxKart uses a custom Irrlicht-based engine called Antarctica. We provide an exporter to convert a Blender file into the Antarctica format.

To configure materials, node-based materials must be used, and the shader used must be a `Principled BSDF` node. Either an image or vertex color node needs to be connected to the `Base Color` input. It is also possible to attach a MixRGB node, which will enable using two-UV (one image overlaid on top of another) materials using the decal shader.

Once the asset is ready to be exported, either of these two places can be used to access the kart and track exporters (but both will usually not be enabled at the same time):
* The file export menu. `Export -> STK Kart/Track`

* The `Quick Exporter` panel found in scene properties. Click on either `Export Kart`, `Export Track`, or `Export Library Node`, depending on the type of STK asset being edited.

The export location can be chosen for a kart, but nor for a track or library  node.

It is also possible to export only SPM files. However, it is available only through the file export menu. `Export -> SPM (.spm)` Any SPM files can be imported back into Blender through this menu, should a situation arise where a source Blender file becomes inaccessible. `Import -> SPM (.spm)`

It is also possible to export just `materials.xml`. However, it is available only through the file export menu. `Export -> STK Materials`.

## Importing Blender files created from older Blender versions
**This process is one-way. Once the converted file is opened in Blender 2.80 or later and then saved again, Blender 2.79 and older will be unable to open them at all; attempting to do so will lead to nothing appearing in the 3D view.**

In Blender 2.79:
1. Open an existing asset that is to be converted. Then open a text editor window (the one built into Blender).

2. Open the script located at <extras/uv_textures_to_materials.py> Edit it if needed.

3. Run the script. This script searches for UV textures, creates materials out of them, and assigns those materials to all meshes using them.

4. Anything else can be done. but the file must be saved, or a copy of it saved, before the asset can be migrated.

In Blender 2.80+:
1. Open the converted asset. Most meshes should have their materials assigned.

2. Certain items including vertex colors and secondary UV textures are not supported in the migration, but they can be set up manually. In the case of vertex colors, they have not been lost, but they can be displayed separately.

3. (If you use any point lights) Run the <extras/convert_lights.py>

### Materials
See <https://supertuxkart.net/Materials> for more information about materials.

### Objects (SPM)
Space-Partitioned Mesh format. The default and preferred 3D file format for the Antarctica engine. It is basically a OpenGL vertex buffer written into a file. Currently documentation about this format is scarce, but the following in-game source files may help in understanding this format better:

* <https://github.com/supertuxkart/stk-code/blob/master/src/graphics/sp_mesh_loader.cpp>

* <https://github.com/supertuxkart/stk-code/blob/master/src/graphics/sp_mesh_loader.hpp>

### Tutorials
Note that these tutorials may not yet be updated for Blender 2.80 and later, but most of the workflow still applies. One major difference is that images themselves are not configured anymore, but their configuration has been moved to the materials section.

* Library nodes: <https://supertuxkart.net/Making_Library_Nodes>

* Karts: <https://supertuxkart.net/Making_Karts>

* Tracks: <https://supertuxkart.net/Making_Tracks>

## io_artiste

### personnal editor

🟢 good
🟠 warning
🔴 bad

- menu:
  - STK MODE:
    - node:
      - 🟠 Battle
      - 🔴 Capture Flag
      - 🔴 CutScene
      - 🟠 Leader
      - 🟠 Racing
      - 🔴 Soccer
      - 🔴 Egg Party
  - STK OPTION:
    - node:
      - 🟢 CLI
      - 🟢 DEMO Mode
      - 🟠 Global info
      - 🔴 Graphic
      - 🟠 Init
      - 🟠 Windows
  - STK RUN
    - node:
      - 🟢 Info
      - 🟢 Go Run Test