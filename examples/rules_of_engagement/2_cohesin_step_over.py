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




N_NODES = 200
STEP = 8
INIT_CONF_SCALE = 55.0
CHAIN_BOND_INFLUENCE = 0.25
COHESIN_INFLUENCE = 0.75



import numpy as np
from scipy.integrate import quad
import math


def init_conf_wave(
        N,
        step=8.0,
        amplitude=30.0, 
        wavelength=30.0,
        phase0=0):

    def sine_arclength_integrand(t, A, w, phase0=0):
        """Integrand for sine wave arc length: sqrt(1 + (dy/dx)^2)"""
        return np.sqrt(1 + (A*w*np.cos(w*t+phase0))**2)


    def find_x_for_arclength(target_length, start_x, A, w, phase0, tolerance=1e-6):
        """Find x coordinate that gives desired arc length from start_x"""
        def length_difference(x):
            length, _ = quad(sine_arclength_integrand, start_x, x, args=(A, w, phase0))
            return length - target_length
        
        # Binary search for x that gives desired length
        x_min = start_x
        x_max = start_x + 2*target_length  # Conservative upper bound
        
        while (x_max - x_min) > tolerance:
            x_mid = (x_min + x_max) / 2
            diff = length_difference(x_mid)
            
            if abs(diff) < tolerance:
                return x_mid
            elif diff < 0:
                x_min = x_mid
            else:
                x_max = x_mid
                
        return (x_min + x_max) / 2


    out = np.zeros((N, 3))    
    w = 2 * np.pi / wavelength

    
    # Find x coordinates for all points
    for i in range(1, N):
        x = find_x_for_arclength(
            step, 
            out[i-1][0], 
            amplitude, 
            w,
            phase0)
        y = amplitude * (
            np.sin(w * x + phase0) 
            - np.sin(phase0))
        out[i] = [x, y, 0]
        
    return out



def recalculate_empty_chain(empties, frame):
    bpy.context.scene.frame_set(frame)
    
    # Small displacement to force constraint solving
    for empty in empties:
        orig_loc = empty.location.copy()
        empty.location.x += 0.0001  # Tiny displacement
        empty.location = orig_loc   # Restore position
        
        # Alternative method if needed:
        # empty.update_tag(refresh={'OBJECT'})
    
    # Force multiple updates to resolve constraints
    for _ in range(3):  # Multiple iterations help with complex chains
        bpy.context.view_layer.update()
        depsgraph = bpy.context.evaluated_depsgraph_get()
        depsgraph.update()
    
chain1, hooks1 = ae.make_hooked_chain(N_NODES, STEP, root_loc = (0, 0, 0), name='hooked_chain_1', subobj_suffix='1')
chain2, hooks2 = ae.make_hooked_chain(N_NODES, STEP, root_loc = (0, 120,  0), name='hooked_chain_2', subobj_suffix='2')


for chain in [chain1, chain2]:
    ae.add_fiber_softbody(chain)
    ae.add_smooth_skin(chain, skin_radius=0.75)


init_conf = np.zeros((N_NODES, 3))
wave_lo = N_NODES//4
wave_hi = N_NODES//4 + N_NODES//2
init_conf[wave_lo: wave_hi] = init_conf_wave(
    N_NODES//2, 
    step=STEP,
    amplitude=INIT_CONF_SCALE*0.8, 
    wavelength=INIT_CONF_SCALE*6.2, 
    phase0=3*np.pi/2)


init_conf[:wave_lo] = init_conf[wave_lo][np.newaxis, :]
init_conf[:wave_lo][:, 0] -= np.arange(1, wave_lo+1)[::-1] * STEP
init_conf[wave_hi:] = init_conf[wave_hi-1][np.newaxis, :]
init_conf[wave_hi:][:, 0] += np.arange(1, N_NODES-wave_hi+1) * STEP




for hook, pos in zip(hooks1, init_conf):
    hook.location = pos

for hook, pos in zip(hooks2, init_conf):
    pos = [pos[0], 180 - pos[1], pos[2]]
    hook.location = pos




COHESION_BONDS = [
    (75, 75),
    (123, 123),
]

for i, j in COHESION_BONDS:
    ae.add_distance_constraint(
        hooks1[i], hooks2[j], distance=STEP/2, influence=COHESIN_INFLUENCE)
    ae.add_distance_constraint(
        hooks2[j], hooks1[i], distance=STEP/2, influence=COHESIN_INFLUENCE)



ae.chain_hooks(hooks1, max_dist=STEP+1, influence=CHAIN_BOND_INFLUENCE)
ae.chain_hooks(hooks2, max_dist=STEP+1, influence=CHAIN_BOND_INFLUENCE)



cam_loc = Vector((400, 70, 300))
cam = polender.objects.add_camera(
    loc = cam_loc,
    direction=('Z', 'Y'),
    focal_length=30
)


ae.animate_looparray_extrusion(
    hooks1,
    [{100: (112, 113),
     200: (112, 133),},
     ],
    bridge_width = 2.5,
    step = STEP,
    n_intermediate_keyframes= 0,
    add_constraints_with_influence=COHESIN_INFLUENCE,
    #shift_backbone=False
    )

ae.animate_looparray_extrusion(
    hooks2,
    [{250: (132, 133),
     350: (112, 133),},
     ],
    bridge_width = 2.5,
    step = STEP,
    n_intermediate_keyframes =0,
    vertical_orientations=[-1],
    add_constraints_with_influence=COHESIN_INFLUENCE,
    #shift_backbone=False
    )

polender.dynamics.animate_linear_shift(
    hooks2,
    polender.dynamics.get_obj_loc(hooks2[112], 250)-polender.dynamics.get_obj_loc(hooks2[112], 350),
    time_span=(250,350),
    extend=True
)



hooks1 = list(polender.utils.discover_objects(
    'hook_{}_empty1', obj_type='EMPTY').values())

hooks2 = list(polender.utils.discover_objects(
    'hook_{}_empty2', obj_type='EMPTY').values())


chain1 = bpy.data.objects['chain1']
chain2 = bpy.data.objects['chain2']
print(chain1, chain2)

ae.set_skin_radius(chain1, 3.0)
ae.set_skin_radius(chain2, 3.0)


smcs = [o for o in bpy.data.objects.values() if 'Sphere' in o.name]
print(smcs)

ae.disable_constraints(hooks1)
ae.disable_constraints(hooks2)
polender.dynamics.add_fcurve_noise(hooks1, strength=10.0, scale=10.0)
polender.dynamics.add_fcurve_noise(hooks2, strength=10.0, scale=10.0)
polender.dynamics.add_fcurve_noise(smcs, strength=3.0, scale=10.0)


# polender.dynamics.remove_fcurve_noise(hooks1)
# polender.dynamics.remove_fcurve_noise(hooks2)
# polender.dynamics.remove_fcurve_noise(smcs)



# ae.remove_constraints(
#     hooks1, 
#     'LIMIT_DISTANCE', 
#     #cond_f=lambda x: x.distance == 2.5, 
# )

# ae.remove_constraints(
#     hooks2, 
#     'LIMIT_DISTANCE', 
#     #cond_f=lambda x: x.distance == 2.5, 
# )


# polender.dynamics.add_fcurve_noise(hooks1, strength=3.0, scale=10.0)
# polender.dynamics.add_fcurve_noise(hooks2, strength=3.0, scale=10.0)


# polender.objects.add_backdrop(s=1000)


# ae.change_constraints(
#     hooks1, 
#     'LIMIT_DISTANCE', 
#     cond_f=lambda x: x.distance == 10, 
#     distance=20)

# ae.change_constraints(
#     hooks2, 
#     'LIMIT_DISTANCE', 
#     cond_f=lambda x: x.distance == 10, 
#     distance=20)


# this did not work for some reason:

# def extend_hooked_chain(
#     chain_obj,
#     n_additional_nodes,
#     step,
#     subobj_suffix='',
# ):
#     # Get the existing hooks collection
#     hooks_collection = None
#     for collection in chain_obj.users_collection[0].children:
#         if collection.name == 'hooks' + subobj_suffix:
#             hooks_collection = collection
#             break
    
#     if not hooks_collection:
#         raise ValueError("Hooks collection not found")

#     # Get existing hooks
#     existing_hooks = list(polender.utils.discover_objects(
#         'hook_{}_empty'+subobj_suffix, obj_type='EMPTY', root=hooks_collection).values())
#     last_hook = existing_hooks[-1]
    
#     # Get the mesh
#     mesh = chain_obj.data

#     # Store current vertex count
#     start_idx = len(mesh.vertices)
    
#     # Create new vertices starting from last position
#     step = (Vector(step) 
#             if isinstance(step, (list, tuple, Vector, np.ndarray)) 
#             else Vector((step, 0, 0)))
    
#     new_vertices = []
#     for i in range(n_additional_nodes):
#         new_pos = last_hook.location + (i + 1) * step
#         new_vertices.append(new_pos)

#     # Add new vertices to mesh
#     mesh.vertices.add(len(new_vertices))
#     for i, v in enumerate(new_vertices):
#         mesh.vertices[start_idx + i].co = v

#     # Add new edges
#     mesh.edges.add(len(new_vertices))
#     for i in range(len(new_vertices)):
#         mesh.edges[start_idx + i - 1].vertices = (start_idx + i - 1, start_idx + i)

#     mesh.update()

#     # ADDED: Store current active object and selection
#     current_active = bpy.context.active_object
#     current_selected = bpy.context.selected_objects[:]
    
#     # ADDED: Deselect all and make chain_obj active
#     bpy.ops.object.select_all(action='DESELECT')
#     chain_obj.select_set(True)
#     bpy.context.view_layer.objects.active = chain_obj

#     # Create new hooks
#     new_hooks = []
#     for i in range(n_additional_nodes):
#         idx = start_idx + i
        
#         # Create empty at the correct position
#         hook = bpy.data.objects.new(f'hook_{idx}_empty'+subobj_suffix, None)
#         hook.location = new_vertices[i]
#         hooks_collection.objects.link(hook)
        
#         # Add hook modifier
#         hook_mod = chain_obj.modifiers.new(name=f'hook_{idx}_mod'+subobj_suffix, type='HOOK')
#         hook_mod.object = hook
#         hook_mod.falloff_type = 'NONE'
#         hook_mod.strength = 1.0
        
#         # Create vertex group
#         vg = chain_obj.vertex_groups.new(name=f'hook_{idx}_vg'+subobj_suffix)
#         vg.add([idx], 1.0, 'REPLACE')
        
#         # Select vertices for this hook
#         bpy.ops.object.mode_set(mode='EDIT')
#         bpy.ops.mesh.select_all(action='DESELECT')
        
#         # Select vertices in vertex group
#         chain_obj.vertex_groups.active_index = vg.index
#         bpy.ops.object.vertex_group_select()
        
#         # Assign vertices to hook
#         bpy.ops.object.hook_assign(modifier=hook_mod.name)
#         bpy.ops.object.hook_reset(modifier=hook_mod.name)
#         bpy.ops.object.mode_set(mode='OBJECT')
        
#         new_hooks.append(hook)
    
    
#     # ADDED: Restore previous selection and active object
#     bpy.ops.object.select_all(action='DESELECT')
#     for obj in current_selected:
#         obj.select_set(True)
#     bpy.context.view_layer.objects.active = current_active

#     # Add constraints to new hooks
#     step_magnitude = step.length
#     ae.chain_hooks([existing_hooks[-1]] + new_hooks, step=step_magnitude)
    
#     return new_hooks
