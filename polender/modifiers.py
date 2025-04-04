import numpy as np

import bpy


def merge_meshes(objects, operation='UNION', result_name=None, keep_originals=True, solver='FAST', remove_doubles_threshold=0):
    """
    Merges multiple mesh objects using boolean operations.
    
    Parameters:
        objects: List of Blender mesh objects to merge
        operation: Boolean operation type ('UNION', 'DIFFERENCE', 'INTERSECT')
        result_name: Name for the resulting merged object
        keep_originals: Whether to keep the original objects
        
    Returns:
        The new merged object
    """
    if not objects or len(objects) < 2:
        raise ValueError("At least two objects must be provided to merge")
    
    # Make a copy of the first object as our base
    base_obj = objects[0].copy()
    base_obj.data = objects[0].data.copy()
    if result_name:
        base_obj.name = result_name
    else:
        base_obj.name = f"{objects[0].name}_merged"
    bpy.context.collection.objects.link(base_obj)
    
    # Apply boolean modifiers for each additional object
    for i, obj in enumerate(objects[1:]):
        if obj.type != 'MESH':
            raise ValueError(f"Object {obj.name} is not a mesh")
            
        # Create boolean modifier
        bool_mod = base_obj.modifiers.new(name=f"Boolean_{i}", type='BOOLEAN')
        bool_mod.operation = operation
        bool_mod.object = obj
        bool_mod.solver = solver
        bool_mod.use_hole_tolerant = True
        bool_mod.use_self = True

        # Apply the modifier
        bpy.context.view_layer.objects.active = base_obj
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)
    
    # Remove original objects if not keeping them
    if not keep_originals:
        for obj in objects:
            if obj != base_obj :
                bpy.data.objects.remove(obj)
    
    # Optional: Remove duplicate vertices
    bpy.context.view_layer.objects.active = base_obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    if remove_doubles_threshold > 0:
        bpy.ops.mesh.remove_doubles(threshold=remove_doubles_threshold)

    bpy.ops.object.mode_set(mode='OBJECT')
    
    return base_obj


def remesh(obj, voxel_size = 0.003, adaptivity=0.001, convert_to_mesh=True):
    # Apply a remesh modifier
    remesh_mod = obj.modifiers.new(name="Remesh", type='REMESH')
    remesh_mod.mode = 'VOXEL'
    remesh_mod.voxel_size = voxel_size  # Adjust the voxel size as needed
    remesh_mod.use_smooth_shade = True
    remesh_mod.adaptivity = adaptivity  
    remesh_mod.use_remove_disconnected = True

    bpy.ops.object.modifier_apply(modifier=remesh_mod.name)

    if convert_to_mesh:
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        bpy.ops.object.convert(target='MESH')

    return obj

