import re

import bpy


def hide_obj(obj, t):
    bpy.context.scene.frame_set(t)
    obj.hide = True
    obj.keyframe_insert('hide')      
    obj.hide_render = True
    obj.keyframe_insert('hide_render')


def unhide_obj(obj, t):
    bpy.context.scene.frame_set(t)
    obj.hide = False
    obj.keyframe_insert('hide')      
    obj.hide_render = False
    obj.keyframe_insert('hide_render')


def clone_obj(obj):
    bpy.context.scene.objects.active = obj
    bpy.ops.object.select_all(action='DESELECT')
    obj.select = True
    bpy.ops.object.duplicate(linked=True)
    return bpy.context.scene.objects.active


def matches_template(template, string, pattern_type='any'):
    # Convert format template to regex pattern
    pattern = re.escape(template) 
    if pattern_type == 'numbers':
        replacement = r'(\\d+)'  # Capture group added
    elif pattern_type == 'any':
        replacement = r'(.*?)'   # Capture group added
    elif pattern_type == 'word':
        replacement = r'(\\w+)'  # Capture group added
    else:
        raise ValueError("Invalid pattern_type. Use 'numbers', 'any', or 'word'")
    pattern = str.format(template, replacement)
    pattern = '^' + pattern + '$'
    match = re.match(pattern, string)
    if match:
        # Return all captured groups
        if len(match.groups()) == 1:
            return match.group(1)  # Return single value if only one group
        return match.groups()      # Return tuple of all matches if multiple groups
    return None


def discover_objects(
        obj_name_template,
        obj_type='EMPTY',
):
    objs = {int(idx):obj
            for obj in bpy.data.objects 
            if (idx:=matches_template(obj_name_template, obj.name)) is not None
            and ((obj_type is None) or (obj.type == obj_type))
            }      
    objs = dict(sorted(list(objs.items()), key=lambda x:x[0]))
    return objs
