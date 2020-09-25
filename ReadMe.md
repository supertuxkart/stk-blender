# SuperTuxKart Blender Addons

This repository contains a series of custom scripts made to help in the creation of custom SuperTuxKart karts and tracks.

  - Exporting from Blender to SuperTuxKart
  - Importing SuperTuxKart (SPM) mesh format to Blender
  - Script to create objects with various Level of Details
  - Scripts to help in creating karts and tracks

### Minimum Requirements

  - Blender 2.80
  - SuperTuxKart 1.0

# Exporting your blender file
> SuperTuxKart uses a custom Irrlicht-based engine called Antarctica. We provide an exporter to convert a blender file into the Antarctica format.

### Materials
See <https://supertuxkart.net/Materials> for more information about materials. Note that the information has not yet been updated for Blender 2.80 and later,  but most of it still applies.

### Objects (SPM)
Space-Partitioned Mesh format. The default and preferred 3D file format for the Antarctica engine. It is basically a OpenGL vertex buffer written into a file. Currently documentation about this format is scarce, but the following in-game source files may help in understanding this format better:

* <https://github.com/supertuxkart/stk-code/blob/master/src/graphics/sp_mesh_loader.cpp>

* <https://github.com/supertuxkart/stk-code/blob/master/src/graphics/sp_mesh_loader.hpp>
