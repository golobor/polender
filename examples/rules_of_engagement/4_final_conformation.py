import sys
import pathlib
import importlib

import bpy
from mathutils import Vector, Matrix


libpath = pathlib.Path(__file__).parent.parent.parent.absolute().as_posix()
sys.path.append(libpath)


import polender
import polender.dynamics
import polender.objects
import polender.geoutils
import polender.utils
import polender.animate_extrusion as ae

importlib.reload(polender)
importlib.reload(polender.dynamics)
importlib.reload(polender.objects)
importlib.reload(polender.geoutils)
importlib.reload(polender.utils)
importlib.reload(ae)


import bpy
import mathutils
from mathutils import Vector


def make_hooked_chain_along_curve(curve_obj, spacing, name='hooked_chain', subobj_suffix=''):
    """
    Creates a chain of vertices (with connected edges) and corresponding empties
    distributed evenly along the evaluated Bezier curve from the given curve object.
    The spacing between points is determined by `spacing`.

    Parameters:
      curve_obj: The Blender curve object (must be a Bezier curve).
      spacing: The desired spacing between points along the curve.
      name: Name for the new collection.
      subobj_suffix: Suffix for naming the generated objects.

    Returns:
      A tuple (chain_obj, sample_positions) where chain_obj is the mesh object
      created for the chain and sample_positions is a list of Vector positions.
    """
    # Create a new collection for the chain objects
    hooked_chain_collection = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(hooked_chain_collection)

    # Evaluate the curve to get a mesh approximation.
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated_obj = curve_obj.evaluated_get(depsgraph)
    mesh_from_curve = bpy.data.meshes.new_from_object(evaluated_obj, preserve_all_data_layers=True, depsgraph=depsgraph)

    # Extract the ordered vertex positions as a polyline.
    points = [Vector(v.co) for v in mesh_from_curve.vertices]
    if len(points) < 2:
        print("Not enough points in the curve.")
        return None, None

    # Compute cumulative distances along the polyline.
    distances = [0.0]
    for i in range(1, len(points)):
        seg_length = (points[i] - points[i-1]).length
        distances.append(distances[-1] + seg_length)
    total_length = distances[-1]

    # Sample positions along the curve at intervals of `spacing`.
    sample_positions = []
    current_distance = 0.0
    while current_distance <= total_length:
        # Find the segment that contains the current target distance.
        for i in range(1, len(distances)):
            if distances[i] >= current_distance:
                seg_start = points[i-1]
                seg_end = points[i]
                seg_length = distances[i] - distances[i-1]
                t = 0 if seg_length == 0 else (current_distance - distances[i-1]) / seg_length
                pos = seg_start.lerp(seg_end, t)
                sample_positions.append(pos)
                break
        current_distance += spacing

    # Create a new mesh object for the chain.
    mesh = bpy.data.meshes.new('chain' + subobj_suffix)
    chain_obj = bpy.data.objects.new('chain' + subobj_suffix, mesh)
    hooked_chain_collection.objects.link(chain_obj)

    # Create vertices and connect them with edges.
    n_nodes = len(sample_positions)
    vertices = [p.to_tuple() for p in sample_positions]
    if len(vertices) >= 2:
        edges = [(i, i+1) for i in range(len(vertices)-1)]
    else:
        edges = []
    mesh.from_pydata(vertices, edges, [])
    mesh.update()

    hooks_collection = bpy.data.collections.new('hooks' + subobj_suffix)
    hooked_chain_collection.children.link(hooks_collection)

    hook_empties = []
    bpy.context.view_layer.objects.active = chain_obj
    chain_obj.select_set(True)

    for i in range(n_nodes):        
        # Create empty at the correct position
        hook = bpy.data.objects.new(f'hook_{i}_empty'+subobj_suffix, None)
        
        hook.location = vertices[i]
        
        #bpy.context.scene.collection.objects.link(hook)
        hooks_collection.objects.link(hook)  # Link to hooks collection instead of scene collection

        
        # Add hook modifier
        hook_mod = chain_obj.modifiers.new(name=f'hook_{i}_mod'+subobj_suffix, type='HOOK')
        hook_mod.object = hook
        hook_mod.falloff_type = 'NONE'
        hook_mod.strength = 1.0
        
        # Create vertex group
        vg = chain_obj.vertex_groups.new(name=f'hook_{i}_vg'+subobj_suffix)
        
        vg.add([i], 1.0, 'REPLACE')
        
        # Select vertices for this hook
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        
        # Select vertices in vertex group
        bpy.context.active_object.vertex_groups.active_index = vg.index
        bpy.ops.object.vertex_group_select()
        
        # Assign vertices to hook

        bpy.ops.object.hook_assign(modifier=hook_mod.name)
        bpy.ops.object.hook_reset(modifier=hook_mod.name)
        bpy.ops.object.mode_set(mode='OBJECT')

        hook_empties.append(hook)

    return chain_obj,  hook_empties 





# cam_loc = Vector((400, 70, 300))
# cam = polender.objects.add_camera(
#     loc = cam_loc,
#     direction=('Z', 'Y'),
#     focal_length=30
# )

# chain1, hooks1 = make_hooked_chain_along_curve(
#     bpy.data.objects['chromatid_1'],
#     spacing=1.0,
#     subobj_suffix='_1'
# )


# ae.add_fiber_softbody(chain1)
# ae.add_smooth_skin(chain1, skin_radius=0.3)


# chain2, hooks2 = make_hooked_chain_along_curve(
#     bpy.data.objects['chromatid_2'],
#     spacing=1.0,
#     subobj_suffix='_2'
# )


# ae.add_fiber_softbody(chain2)
# ae.add_smooth_skin(chain2, skin_radius=0.3)


hooks1 = list(polender.utils.discover_objects(
    'hook_{}_empty_1', obj_type='EMPTY').values())
hooks2 = list(polender.utils.discover_objects(
    'hook_{}_empty_2', obj_type='EMPTY').values())

NOISE_SCALE = 20.0
SMC_NOISE_STRENGTH = 0.5
CHROMATIN_NOISE_STRENGTH = 0.5


polender.dynamics.remove_fcurve_noise(hooks1)
polender.dynamics.remove_fcurve_noise(hooks2)

polender.dynamics.add_fcurve_noise(hooks1, strength=CHROMATIN_NOISE_STRENGTH, scale=NOISE_SCALE)
polender.dynamics.add_fcurve_noise(hooks2, strength=CHROMATIN_NOISE_STRENGTH, scale=NOISE_SCALE)


condensins = [o for name, o in bpy.data.objects.items() if 'Condensin' in name]
cohesins = [o for name, o in bpy.data.objects.items() if 'Cohesin' in name]

polender.dynamics.remove_fcurve_noise(cohesins+condensins)
polender.dynamics.add_fcurve_noise(cohesins+condensins, strength=SMC_NOISE_STRENGTH, 
                                   scale=NOISE_SCALE)
