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

import bpy, os, base64, getpass, hashlib, xml.dom.minidom
from collections import OrderedDict
from xml.sax.saxutils import escape

CONTEXT_OBJECT = 0
CONTEXT_SCENE  = 1
CONTEXT_MATERIAL  = 2

def getObject(context, contextLevel):
    if contextLevel == CONTEXT_OBJECT:
        return context.object
    if contextLevel == CONTEXT_SCENE:
        return context.scene
    if contextLevel == CONTEXT_MATERIAL:
        return context.object.active_material
        #if 'selected_image' in context.scene:
        #    selected_image = context.scene['selected_image']
        #    if selected_image in bpy.data.images:
        #        return bpy.data.images[selected_image]

    return None

# ------------------------------------------------------------------------------
# Gets a custom property of a scene, returning the default if the id property
# is not set. If set_value_if_undefined is set and the property is not
# defined, this function will also set the property to this default value.
def getSceneProperty(scene, name, default="", set_value_if_undefined=1):
    import traceback
    try:
        prop = scene[name]
        if isinstance(prop, str):
            # + "" is used to force a copy of the string AND to convert from binary format to string format
            # escape formats the string for XML
            return (escape(prop + "") + "").encode('ascii', 'xmlcharrefreplace').decode("ascii")
        else:
            return prop
    except:
        if default!=None and set_value_if_undefined:
            scene[name] = default
    return default

# ------------------------------------------------------------------------------
# Gets a custom property of an object
def getObjectProperty(obj, name, default=""):
    if obj.proxy is not None:
        try:
            return obj.proxy[name]
        except:
            pass

    try:
        return obj[name]
    except:
        return default

# ------------------------------------------------------------------------------
# Gets an id property of an object, returning the default if the id property
# is not set. If set_value_if_undefined is set and the property is not
# defined, this function will also set the property to this default value.
def getIdProperty(obj, name, default="", set_value_if_undefined=1):
    import traceback
    try:
        prop = obj[name]
        if isinstance(prop, str):
            return obj[name].replace('&', '&amp;') # this is XML
        else:
            return prop
    except:
        if default!=None and set_value_if_undefined:
            obj[name] = default
    return default

# --------------------------------------------------------------------------
# Write several ways of writing true/false as Y/N
def convertTextToYN(sText):
    sTemp = sText.strip().upper()
    if sTemp=="0" or sTemp[0]=="N" or sTemp=="FALSE":
        return "N"
    else:
        return "Y"

def merge_materials(x, y):
    z = x.copy()
    z.update(y)
    return z

def getXYZString(obj):
    loc = obj.location
    s = "xyz=\"%.2f %.2f %.2f\"" % (loc[0], loc[2], loc[1])
    return s

# ------------------------------------------------------------------------------
# FIXME: should use xyz="..." format
# Returns a string 'x="1" y="2" z="3" h="4"', where 1, 2, ...are the actual
# location and rotation of the given object. The location has a swapped
# y and z axis (so that the same coordinate system as in-game is used).
def getXYZHString(obj):
    loc     = obj.location
    hpr     = obj.rotation_euler
    rad2deg = 180.0/3.1415926535;
    s="x=\"%.2f\" y=\"%.2f\" z=\"%.2f\" h=\"%.2f\"" %\
       (loc[0], loc[2], loc[1], -hpr[2]*rad2deg)
    return s

# ------------------------------------------------------------------------------
# Returns a string 'xyz="1 2 3" h="4"', where 1, 2, ...are the actual
# location and rotation of the given object. The location has a swapped
# y and z axis (so that the same coordinate system as in-game is used).
def getNewXYZHString(obj):
    loc     = obj.location
    hpr     = obj.rotation_euler
    rad2deg = 180.0/3.1415926535;
    s="xyz=\"%.2f %.2f %.2f\" h=\"%.2f\"" %\
       (loc[0], loc[2], loc[1], hpr[2]*rad2deg)
    return s

# ------------------------------------------------------------------------------
# Returns a string 'xyz="1 2 3" hpr="4 5 6"' where 1,2,... are the actual
# location and rotation of the given object. The location has a swapped
# y and z axis (so that the same coordinate system as in-game is used), and
# rotations are multiplied by 10 (since bullet stores the values in units
# of 10 degrees.)
def getXYZHPRString(obj):
    loc     = obj.location
    # irrlicht uses XZY
    hpr     = obj.rotation_euler.to_quaternion().to_euler('XZY')
    si      = obj.scale
    rad2deg = 180.0/3.1415926535;
    s="xyz=\"%.2f %.2f %.2f\" hpr=\"%.1f %.1f %.1f\" scale=\"%.2f %.2f %.2f\"" %\
       (loc[0], loc[2], loc[1], -hpr[0]*rad2deg, -hpr[2]*rad2deg,
        -hpr[1]*rad2deg, si[0], si[2], si[1])
    return s

def selectObjectsInList(obj_list):
    bpy.ops.object.select_all(action='DESELECT')
    for obj in obj_list:
        if not obj.select_get():
            obj.select_set(True)

def searchNodeTreeForImage(node_tree, uv_num):
    # Check if there is a node tree
    # If so, search the STK shader node for an image
    if node_tree is not None:
        try:
            shader_node = node_tree.nodes['Principled BSDF']
            if shader_node.inputs['Base Color'].is_linked:
                # Get the connected node
                child = shader_node.inputs['Base Color'].links[0].from_node
                if type(child) is bpy.types.ShaderNodeTexImage and uv_num == 1:
                    return os.path.basename(child.image.filepath)
                elif type(child) is bpy.types.ShaderNodeMixRGB:
                    uvOne = child.inputs['Color1'].links[0].from_node
                    uvTwo = child.inputs['Color2'].links[0].from_node
                    if type(uvOne) is bpy.types.ShaderNodeTexImage and uv_num == 1:
                        return os.path.basename(uvOne.image.filepath)
                    if type(uvTwo) is bpy.types.ShaderNodeTexImage and uv_num == 2:
                        return os.path.basename(uvTwo.image.filepath)
            else:
                #print("Texture node not found, skipping this input node")
                return ""
        except:
            return ""
    else:
        return ""

# ------------------------------------------------------------------------------
#! Utility function, creates all properties in a given object
#!
#! object   the object to create properties in
#! props    a list of properties to create
def createProperties(object, props):

    if not "_RNA_UI" in object:
        object["_RNA_UI"] = {}

    for p in props.keys():

        if isinstance(props[p], StkLabelPseudoProperty):
            continue

        elif isinstance(props[p], StkPropertyGroup):
            createProperties(object, props[p].subproperties)

        elif not p in object:

            # create property by setting default value
            v = props[p].default
            object[p] = v

            if isinstance(props[p], StkEnumProperty):
                if v in props[p].values:
                    createProperties(object, props[p].values[v].subproperties)
            elif isinstance(props[p], StkBoolProperty):
                if v == "true":
                    createProperties(object, props[p].subproperties)

        # check the property has the right type
        elif isinstance(props[p], StkFloatProperty) :

            if not isinstance(object[p], float):
                try:
                    object[p] = float(object[p])
                except:
                    object[p] = props[p].default

        elif isinstance(props[p], StkIntProperty):

            if not isinstance(object[p], int):
                try:
                    object[p] = int(object[p])
                except:
                    object[p] = props[p].default

        elif isinstance(props[p], StkProperty) and not isinstance(object[p], str):
            try:
                object[p] = str(object[p])
            except:
                object[p] = props[p].default


        rna_ui_dict = {}
        try:
            rna_ui_dict["description"] = props[p].doc
        except:
            pass

        try:
            if props[p].min is not None:
                rna_ui_dict["min"] = props[p].min
                rna_ui_dict["soft_min"] = rops[p].min
        except:
            pass

        try:
            if props[p].max is not None:
                rna_ui_dict["max"] = props[p].max
                rna_ui_dict["soft_max"] = props[p].max
        except:
            pass

        object["_RNA_UI"][p] = rna_ui_dict

        if isinstance(props[p], StkEnumProperty):
            if object[p] in props[p].values:
                createProperties(object, props[p].values[object[p]].subproperties)
        elif isinstance(props[p], StkBoolProperty):
            if object[p] == "true":
                createProperties(object, props[p].subproperties)


def simpleHash(x):
    m = hashlib.md5()
    m.update(x.encode('ascii'))
    return base64.b64encode(m.digest()).decode('ascii').replace('=', '').replace('/', '_').replace('+', '_').lower()[0:15]

def generateOpName(prefix, fullid, id):
    if len(prefix + fullid + '_' + id) > 60:
        return prefix + simpleHash(fullid) + '_' + id
    else:
        return prefix + fullid + '_' + id

# ------------------------------------------------------------------------------
#! The base class for all properties.
#! If you use this property directly (and not a subclass), you get a simple text box
class StkProperty:
    def __init__(self, id, name, default, fullid, doc="(No documentation was defined for this item)"):
        self.name = name
        self.id = id
        self.fullid = fullid
        self.default = default
        self.doc = doc


# ------------------------------------------------------------------------------
#! A text field where you can type a reference to another object (or a property
#! of another object) with an optional dropdown button to see current choices
#!
#! id               the id of the blender id-property
#! name             user-visible name
#! contextLevel     object, scene, material level?
#! default          default value for this property
#! filter           a lambda taking arguments "self" and "object", and that returns
#!                  parameter 'object' is to be displayed in the dropdown of this property
#! doc              documentation to show in the tooltip
#! static_objects   items to append to the menu unconditionally (a list of tuples of
#!                  form 'id', 'visible name')
#! obj_identifier   a lambda taking arguments "self" and "object", and that returns
#!                  the id (value) of an object that should be put in this property when
#!                  the object is selected
#! obj_text         a lambda taking arguments "self" and "object", and that returns
#!                  the user-visible string to apear in the dropdown for an object
class StkObjectReferenceProperty(StkProperty):

    def __init__(self, id, fullid, name, contextLevel, default, filter, doc="Select an object",
                 static_objects=[],
                 obj_identifier=lambda self, obj: obj.name,
                 obj_text=lambda self, obj: (obj.name + ((" (" + obj["name"] + ")") if "name" in obj else ""))):
        super(StkObjectReferenceProperty, self).__init__(id=id, name=name, default=default, fullid=fullid)
        self.doc = doc

        if filter is None:
            raise Exception("Filter may not be None")

        select_op_name = generateOpName("screen.stk_select_object_", fullid, id)
        class SelectObjectOperator(bpy.types.Operator):
            bl_idname = select_op_name
            bl_label = "Select Object Operator"
            __doc__ = doc

            m_id = id
            m_context_level = contextLevel

            # name of the object to select
            name: bpy.props.StringProperty()

            def execute(self, context):
                object = getObject(context, self.m_context_level)
                object[self.m_id] = self.name
                return {'FINISHED'}

        bpy.utils.register_class(SelectObjectOperator)

        op_name = generateOpName("STK_MT_object_menu_", fullid, id)
        class ObjectPickerMenu(bpy.types.Menu):
            m_filter = filter
            m_obj_identifier = obj_identifier
            m_obj_text = obj_text
            m_static_objects = static_objects
            m_fullid = fullid
            bl_idname = op_name
            bl_label  = ("SuperTuxKart Object Picker Menu (" + id + ")")
            m_property_id = id

            def draw(self, context):
                objects = context.scene.objects

                seen_objs = {}

                layout = self.layout
                for object in objects:
                    if self.m_filter(object):
                        text = self.m_obj_text(object)
                        object_id = self.m_obj_identifier(object)

                        if object_id is not None and object_id not in seen_objs:
                            layout.operator(select_op_name, text=text).name = object_id
                            seen_objs[object_id] = True

                for curr in self.m_static_objects:
                    layout.operator("scene.stk_select_object_"+self.m_property_id, text=curr[1]).name=curr[0]


        bpy.utils.register_class(ObjectPickerMenu)


# ------------------------------------------------------------------------------
#! One entry in a StkEnumProperty
class StkEnumChoice:

    #! @param name          User-visible name for this property
    #! @param subproperties A list of StkProperty's. Contains the properties
    #                       that are to be shown when this enum item is selected
    def __init__(self, name, subproperties, id, fullid, doc="(No documentation was defined for this item)"):
        self.name = name
        self.id = id
        self.fullid = fullid

        self.subproperties = OrderedDict([])
        for curr in subproperties:
            self.subproperties[curr.id] = curr

        self.doc = doc


# ------------------------------------------------------------------------------
#! An enum property
#!
#! id               the id of the blender id-property
#! name             user-visible name
#! values           the choices offered by this enum, as a list of 'StkEnumChoice' objects
#! contextLevel     object, scene, material level?
#! default          default value for this property
class StkEnumProperty(StkProperty):

    def getOperatorName(self):
        return self.operator_name

    #! @param name   User-visible name for this property
    #! @param values A dictionnary of type { 'value' : StkEnumChoice(...) }
    #! @note         The first value will be used by default
    def __init__(self, id, name, values, contextLevel, default, fullid, doc="(No documentation for this item)"):
        super(StkEnumProperty, self).__init__(id=id, name=name, default=default, fullid=fullid)
        self.values = values
        self.fullid = fullid
        self.operator_name = generateOpName("STK_OT_set_", fullid, id)
        self.menu_operator_name = generateOpName("STK_MT_menu_set_", fullid, id)
        self.doc = doc
        default_value = default

        values_for_blender_unsorted = []
        for curr_val in values.keys():
            if len(curr_val) > 0:
                curr_obj = values[curr_val]
                values_for_blender_unsorted.append( (curr_val, curr_obj.name, curr_obj.name + " : " + curr_obj.doc) )

        #values_for_blender = sorted(values_for_blender_unsorted, key=lambda k: k[1])
        values_for_blender = values_for_blender_unsorted

        class STK_CustomMenu(bpy.types.Menu):
            bl_idname = generateOpName("STK_MT_menu_set_", fullid, id)
            bl_label  = ("SuperTuxKart set " + id)
            __doc__ = doc

            def draw(self, context):
                import bpy.path

                layout = self.layout
                row = layout.row()
                col = row.column()

                for curr in values_for_blender_unsorted:
                    if curr[0].startswith('__category__'):
                        col.label(text = curr[1])
                    elif curr[0].startswith('__column_break__'):
                        col = row.column()
                    else:
                        col.operator(generateOpName("screen.stk_set_", fullid, id), text=curr[1]).value=curr[0]
        bpy.utils.register_class(STK_CustomMenu)

        # Create operator for this combo
        class STK_SetComboValue(bpy.types.Operator):

            value: bpy.props.EnumProperty(attr="values", name="values", default=default_value + "",
                                           items=values_for_blender)

            bl_idname = generateOpName("screen.stk_set_", fullid, id)
            bl_label  = ("SuperTuxKart set " + id)
            __doc__ = doc

            m_property_id = id
            m_items_val = values_for_blender
            m_values = values
            m_context_type = contextLevel

            def execute(self, context):

                # Set the property
                object = getObject(context, self.m_context_type)
                if object is None:

                    return

                object[self.m_property_id] = self.value

                # If sub-properties are needed, create them
                if self.value in self.m_values:
                    createProperties(object, self.m_values[self.value].subproperties)

                return {'FINISHED'}

        bpy.utils.register_class(STK_SetComboValue)

# ------------------------------------------------------------------------------
#! A combinable enum property (each value can be checked or unchecked, and
#! several values can be selected at once. gives a text property containing
#! the IDs of the selected values, separated by spaces)
#!
#! id               the id of the blender id-property
#! name             user-visible name
#! values           the choices offered by this enum, as a list of 'StkEnumChoice' objects
#! contextLevel     object, scene, material level?
#! default          default value for this property
class StkCombinableEnumProperty(StkProperty):

    #! @param name   User-visible name for this property
    #! @param values A dictionnary of type { 'value' : StkEnumChoice(...) }
    #! @note         The first value will be used by default
    def __init__(self, id, name, values, contextLevel, default, fullid):
        super(StkCombinableEnumProperty, self).__init__(id=id, name=name, default=default, fullid=fullid)
        self.values = values

        default_value = default

        values_for_blender = []
        for curr_val in values.keys():
            curr_obj = values[curr_val]
            values_for_blender.append( curr_val )

        for curr in values_for_blender:
            # Create operator for this combo
            class STK_SetEnumComboValue(bpy.types.Operator):

                bl_idname = generateOpName("screen.stk_set_", fullid, id + "_" + curr)
                bl_label  = ("SuperTuxKart set " + id + " = " + curr)

                if values[curr].doc is not None:
                    __doc__ = values[curr].doc + ""

                m_property_id = id
                m_items_val = values_for_blender
                m_values = values
                m_context_type = contextLevel
                m_curr = curr

                def execute(self, context):

                    # Set the property
                    object = getObject(context, self.m_context_type)
                    if object is None:
                        return

                    if self.m_property_id not in object:
                        object[self.m_property_id] = ""

                    if self.m_curr in object[self.m_property_id]:
                        # Remove selected value
                        l = object[self.m_property_id].split()
                        l.remove( self.m_curr )
                        object[self.m_property_id] = " ".join(l)
                    else:
                        # Add selected value
                        object[self.m_property_id] = object[self.m_property_id] + " " + self.m_curr

                    return {'FINISHED'}

            bpy.utils.register_class(STK_SetEnumComboValue)


# ------------------------------------------------------------------------------
#! A pseudo-property that only displays some text
class StkLabelPseudoProperty(StkProperty):

    def __init__(self, id, name, default=0.0, doc="(No documentation defined for this element)", fullid="", min = None, max = None):
        super(StkLabelPseudoProperty, self).__init__(id=id, name=name, default=default, fullid=fullid)
        self.default
        self.doc = doc


# ------------------------------------------------------------------------------
#! A floating-point property
#!
#! id               the id of the blender id-property
#! name             user-visible name
#! default          default value for this property
#! doc              documentation shown to the user in a tooltip
#! min              minimum accepted value
#! max              maximum accepted value
class StkFloatProperty(StkProperty):

    #! @param name   User-visible name for this property
    def __init__(self, id, name, default=0.0, doc="(No documentation defined for this element)", fullid="", min = None, max = None):
        super(StkFloatProperty, self).__init__(id=id, name=name, default=default, fullid=fullid)
        self.default
        self.doc = doc
        self.min = min
        self.max = max


# ------------------------------------------------------------------------------
#! An integer property
#!
#! id               the id of the blender id-property
#! name             user-visible name
#! default          default value for this property
#! doc              documentation shown to the user in a tooltip
#! min              minimum accepted value
#! max              maximum accepted value
class StkIntProperty(StkProperty):

    #! @param name   User-visible name for this property
    def __init__(self, id, name, default=0, doc="(No documentation defined for this element)", fullid="", min=None, max=None):
        super(StkIntProperty, self).__init__(id=id, name=name, default=default, fullid=fullid)
        self.doc = doc
        self.min = min
        self.max = max

# ------------------------------------------------------------------------------
class StkPropertyGroup(StkProperty):

    #! A floating-point property
    def __init__(self, id, name, contextLevel, default="false", subproperties=[], fullid="", doc="(No documentation defined for this element)"):
        super(StkPropertyGroup, self).__init__(id=id, name=name, default=default, fullid=fullid)

        self.contextLevel = contextLevel

        self.subproperties = OrderedDict([])
        for curr in subproperties:
            self.subproperties[curr.id] = curr

        self.doc = doc
        super_self = self

        # Create operator for this bool
        class STK_TogglePropGroupValue(bpy.types.Operator):

            bl_idname = generateOpName("screen.stk_tglbool_", fullid, id)
            bl_label  = ("SuperTuxKart toggle " + id)
            __doc__ = doc

            m_context_level = contextLevel
            m_property_id = id
            m_super_self = super_self

            def execute(self, context):

                # Set the property

                object = bpy.data.scenes[0]
                if object is None:
                    return

                curr_val = True
                if self.m_property_id in object:
                    curr_val = (object[self.m_property_id] == "true")

                new_val = not curr_val

                if curr_val :
                    object[self.m_property_id] = "false"
                else:
                    object[self.m_property_id] = "true"

                propobject = getObject(context, self.m_context_level)
                if propobject is None:
                    return

                # If sub-properties are needed, create them
                if object[self.m_property_id] == "true":
                    createProperties(propobject, self.m_super_self.subproperties)

                return {'FINISHED'}

        bpy.utils.register_class(STK_TogglePropGroupValue)

# ------------------------------------------------------------------------------
#! A boolean property (appears as a checkbox)
#!
#! id                   the id of the blender id-property
#! name                 user-visible name
#! contextLevel         object, scene, material level?
#! default              default value for this property
#! @param subproperties A list of StkProperty's. Contains the properties
#                       that are to be shown when this checkbox is checked
#! box                  if True, the properties from 'subproperties' are
#!                      displayed in a box
#! doc                  documentation shown to the user in a tooltip
class StkBoolProperty(StkProperty):

    # (self, id, name, values, default):
    box = True

    #! A floating-point property
    def __init__(self, id, name, contextLevel, default="false", subproperties=[], box = True, fullid="", doc="(No documentation defined for this element)"):
        super(StkBoolProperty, self).__init__(id=id, name=name, default=default, fullid=fullid)

        self.box = box
        self.contextLevel = contextLevel

        self.subproperties = OrderedDict([])
        for curr in subproperties:
            self.subproperties[curr.id] = curr

        self.doc = doc
        super_self = self

        # Create operator for this bool
        class STK_ToggleBoolValue(bpy.types.Operator):

            bl_idname = generateOpName("screen.stk_tglbool_", fullid, id)
            bl_label  = ("SuperTuxKart toggle " + id)
            __doc__ = doc

            m_context_level = contextLevel
            m_property_id = id
            m_super_self = super_self

            def execute(self, context):

                # Set the property

                object = getObject(context, self.m_context_level)
                if object is None:
                    return

                curr_val = False
                if self.m_property_id in object:
                    curr_val = (object[self.m_property_id] == "true")

                new_val = not curr_val

                if curr_val :
                    object[self.m_property_id] = "false"
                else:
                    object[self.m_property_id] = "true"


                # If sub-properties are needed, create them
                if object[self.m_property_id] == "true":
                    createProperties(object, self.m_super_self.subproperties)

                return {'FINISHED'}

        bpy.utils.register_class(STK_ToggleBoolValue)


# ------------------------------------------------------------------------------
#! A color property
#!
#! id               the id of the blender id-property
#! name             user-visible name
#! contextLevel     object, scene, material level?
#! default          default value for this property
#! doc              documentation shown to the user in a tooltip
class StkColorProperty(StkProperty):

    #! A floating-point property
    def __init__(self, id, name, contextLevel, default="255 255 255", fullid="", doc="(No documentation defined for this item)"):
        super(StkColorProperty, self).__init__(id=id, name=name, default=default, fullid=fullid)

        #! Color picker operator (TODO: this operator is mostly for backwards compatibility with our
        #                               blend files that come from 2.4; blender 2.5 has a color property
        #                               type we could use)
        class Apply_Color_Operator(bpy.types.Operator):
            bl_idname = generateOpName("screen.stk_apply_color_", fullid, id)
            bl_label = ("Apply Color")
            __doc__ = doc

            property_id = id

            m_context_level = contextLevel

            temp_color: bpy.props.FloatVectorProperty(
               name= "temp_color",
               description= "Temp Color.",
               subtype= 'COLOR',
               min= 0.0,
               max= 1.0,
               soft_min= 0.0,
               soft_max= 1.0,
               default= (1.0,1.0,1.0)
            )

            def invoke(self, context, event):

                currcol = [1.0, 1.0, 1.0]
                try:

                    object = getObject(context, self.m_context_level)
                    if object is None:
                        return

                    currcol = list(map(eval, object[self.property_id].split()))
                    currcol[0] = currcol[0]/255.0
                    currcol[1] = currcol[1]/255.0
                    currcol[2] = currcol[2]/255.0
                except:
                    pass

                if currcol is not None and len(currcol) > 2:
                    self.temp_color = currcol
                context.window_manager.invoke_props_dialog(self)
                return {'RUNNING_MODAL'}


            def draw(self, context):

                layout = self.layout

                # ==== Types group ====
                box = layout.box()
                row = box.row()
                try:
                    row.template_color_picker(self, "temp_color", value_slider=True, cubic=False)
                except Exception as ex:
                    import sys
                    print("Except :(", type(ex), ex, "{",ex.args,"}")
                    pass

                row = layout.row()
                row.prop(self, "temp_color", text="Selected Color")

            def execute(self, context):

                object = getObject(context, self.m_context_level)
                if object is None:
                    return

                object[self.property_id] = "%i %i %i" % (self.temp_color[0]*255, self.temp_color[1]*255, self.temp_color[2]*255)
                return {'FINISHED'}

        bpy.utils.register_class(Apply_Color_Operator)


# ------------------------------------------------------------------------------
#                                  THE PROPERTIES
# ------------------------------------------------------------------------------

def readEnumValues(valueNodes, contextLevel, idprefix):
    import collections
    out = collections.OrderedDict()

    for node in valueNodes:
        if node.localName == None:
            continue
        elif node.localName == "EnumChoice":
            args = dict()
            args["id"] = node.getAttribute("id")
            args["fullid"] = idprefix + '_' + node.getAttribute("id")
            args["name"] = node.getAttribute("label")
            args["subproperties"] = parseProperties(node, contextLevel, idprefix + '_' + node.getAttribute("id"))

            if node.hasAttribute("doc"):
                args["doc"] = node.getAttribute("doc")

            out[node.getAttribute("id")] = StkEnumChoice(**args)
        else:
            print("INTERNAL ERROR : Unexpected tag " + str(node.localName) + " in enum '" + str(node.localName) + "'")

    return out

def parseProperties(node, contextLevel, idprefix):

    props = []

    for e in node.childNodes:
        if e.localName == None:
            continue

        elif e.localName == "StringProp":
            defaultval = e.getAttribute("default")
            if defaultval == "$user":
                defaultval = getpass.getuser()

            if e.hasAttribute("doc"):
                props.append(StkProperty(id=e.getAttribute("id"), fullid=idprefix+'_'+e.getAttribute("id"),
                                         name=e.getAttribute("name"), default=defaultval,
                                         doc=e.getAttribute("doc")))
            else:
                props.append(StkProperty(id=e.getAttribute("id"), fullid=idprefix+'_'+e.getAttribute("id"),
                                         name=e.getAttribute("name"), default=defaultval))

        elif e.localName == "EnumProp":

            args = dict()
            args["id"] = e.getAttribute("id")
            args["fullid"] = idprefix + '_' + e.getAttribute("id")
            args["name"] = e.getAttribute("name")
            args["default"] = e.getAttribute("default")

            #if e.hasAttribute("unique_prefix"):
            #    args["unique_prefix"] = e.getAttribute("unique_prefix")

            if e.hasAttribute("doc"):
                args["doc"] = e.getAttribute("doc")

            args["values"] = readEnumValues(e.childNodes, contextLevel, args["fullid"])
            args["contextLevel"] = contextLevel

            props.append(StkEnumProperty(**args))

        elif e.localName == "CombinableEnumProp":

            args = dict()
            args["id"] = e.getAttribute("id")
            args["fullid"] = idprefix + '_' + e.getAttribute("id")
            args["name"] = e.getAttribute("name")
            args["default"] = e.getAttribute("default")

            #if e.hasAttribute("unique_prefix"):
            #    args["unique_prefix"] = e.getAttribute("unique_prefix")

            args["values"] = readEnumValues(e.childNodes, contextLevel, args["fullid"])
            args["contextLevel"] = contextLevel

            props.append(StkCombinableEnumProperty(**args))

        elif e.localName == "IntProp":
            if e.hasAttribute("doc"):
                props.append(StkIntProperty(id=e.getAttribute("id"), fullid = idprefix + '_' + e.getAttribute("id"),
                                            name=e.getAttribute("name"), default=int(e.getAttribute("default")),
                                            doc=e.getAttribute("doc")))
            else:
                props.append(StkIntProperty(id=e.getAttribute("id"), fullid = idprefix + '_' + e.getAttribute("id"),
                                            name=e.getAttribute("name"), default=int(e.getAttribute("default"))))

        elif e.localName == "FloatProp":
            args = dict()
            args["id"] = e.getAttribute("id")
            args["fullid"] = idprefix + '_' + e.getAttribute("id")
            args["name"] = e.getAttribute("name")
            args["default"] = float(e.getAttribute("default"))

            if e.hasAttribute("doc"):
                args["doc"] = e.getAttribute("doc")
            if e.hasAttribute("min"):
                args["min"] = float(e.getAttribute("min"))
            if e.hasAttribute("max"):
                args["max"] = float(e.getAttribute("max"))

            props.append(StkFloatProperty(**args))

        elif e.localName == "LabelProp":
            args = dict()
            args["id"] = e.getAttribute("id")
            args["fullid"] = idprefix + '_' + e.getAttribute("id")
            args["name"] = e.getAttribute("name")
            args["default"] = None

            if e.hasAttribute("doc"):
                args["doc"] = e.getAttribute("doc")

            props.append(StkLabelPseudoProperty(**args))

        elif e.localName == "ColorProp":
            if e.hasAttribute("doc"):
                props.append(StkColorProperty(id=e.getAttribute("id"), fullid=idprefix + '_' + e.getAttribute("id"),
                                              name=e.getAttribute("name"), default=e.getAttribute("default"),
                                              doc=e.getAttribute("doc"), contextLevel=contextLevel))
            else:
                props.append(StkColorProperty(id=e.getAttribute("id"), fullid=idprefix + '_' + e.getAttribute("id"),
                                              name=e.getAttribute("name"), default=e.getAttribute("default"),
                                              contextLevel=contextLevel))

        elif e.localName == "PropGroup":

            args = dict()
            args["id"] = e.getAttribute("id")
            args["fullid"] = idprefix + '_' + e.getAttribute("id")
            args["name"] = e.getAttribute("name")
            args["subproperties"] = parseProperties(e, contextLevel, args["fullid"])
            args["contextLevel"] = contextLevel
            p = StkPropertyGroup(**args)
            props.append(p)

        elif e.localName == "BoolProp":

            args = dict()
            args["id"] = e.getAttribute("id")
            args["fullid"] = idprefix + '_' + e.getAttribute("id")
            args["name"] = e.getAttribute("name")
            args["default"] = e.getAttribute("default")
            args["subproperties"] = parseProperties(e, contextLevel, args["fullid"])
            args["contextLevel"] = contextLevel

            if e.hasAttribute("doc"):
                args["doc"] = e.getAttribute("doc")

            if e.hasAttribute("box"):
                args["box"] = bool(e.getAttribute("box"))

            props.append(StkBoolProperty(**args))

        elif e.localName == "ObjRefProp":
            args = dict()
            args["id"] = e.getAttribute("id")
            args["fullid"] = idprefix + '_' + e.getAttribute("id")
            args["name"] = e.getAttribute("name")
            args["default"] = e.getAttribute("default")
            args["contextLevel"] = contextLevel

            global_env = {}
            local_env = {}
            exec("filterFn = " + e.getAttribute("filter"), global_env, local_env)
            args["filter"] = local_env["filterFn"]

            if e.hasAttribute("static_objects"):
                exec("static_objects_fn = " + e.getAttribute("static_objects"), global_env, local_env)
                args["static_objects"] = local_env["static_objects_fn"]

            if e.hasAttribute("doc"):
                args["doc"] = e.getAttribute("doc")

            #if e.hasAttribute("unique_id_suffix"):
            #    args["unique_id_suffix"] = e.getAttribute("unique_id_suffix")

            if e.hasAttribute("obj_identifier"):
                exec("obj_identifier_fn = " + e.getAttribute("obj_identifier"), global_env, local_env)
                args["obj_identifier"] = local_env["obj_identifier_fn"]

            if e.hasAttribute("obj_text"):
                exec("obj_text_fn = " + e.getAttribute("obj_text"), global_env, local_env)
                args["obj_text"] = local_env["obj_text_fn"]

            props.append(StkObjectReferenceProperty(**args))

    return props

def getPropertiesFromXML(filename, contextLevel):
    import os
    idprefix = os.path.splitext(os.path.basename(filename))[0]
    node = xml.dom.minidom.parse(filename)
    for curr in node.childNodes:
        if curr.localName == "Properties":
            return [curr.getAttribute("bl-label"), parseProperties(curr, contextLevel, idprefix)]
    raise RuntimeError("No <Properties> node in " + filename)

def getDataPath(start):
    return os.path.join(start, "stkdata")
