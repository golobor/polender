import re

import bpy


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
        name_filter='{}',
        obj_type='MESH',
        root=bpy.data,
):
    objs = {}
    
    if isinstance(name_filter, str):
        if '{}' in name_filter:
            name_filter_func = lambda name: matches_template(name_filter, name)
    elif hasattr(name_filter, '__call__'):
        name_filter_func = name_filter
    else:
        raise ValueError("name_filter must be a string or a callable function")
    
    for obj in root.objects:
        idx = name_filter_func(obj.name)
        if not (idx is False or idx is None):
            if obj_type is None or obj.type == obj_type:
                objs[idx] = obj
        
    objs = dict(sorted(list(objs.items()), key=lambda x:x[0]))
    return objs
