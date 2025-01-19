import numpy as np

import bpy
import re
import math
import functools

from mathutils import Vector

from .dynamics import animate_linear_shift, get_obj_loc


def make_hooked_chain(
    n_nodes,
    step,
    root_loc = (0, 0, 0),
    name='hooked_chain',
    subobj_suffix='',
):
    # Create a new collection for hooks
    hooked_chain_collection = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(hooked_chain_collection)

    # Create a new mesh for the chain
    mesh = bpy.data.meshes.new('chain' + subobj_suffix)
    obj = bpy.data.objects.new('chain' + subobj_suffix, mesh)
    hooked_chain_collection.objects.link(obj)
    
    # Create vertices in a line
    root_loc = Vector(root_loc)
    step = (Vector(step) 
            if isinstance(step, (list, tuple, Vector, np.ndarray)) 
            else Vector((step, 0, 0)))
    vertices = []
    for i in range(n_nodes):
        vertices.append(i * step + root_loc)

    # Create edges connecting vertices
    edges = []
    for i in range(len(vertices) - 1):
        edges.append((i, i + 1))

    # Create the mesh
    mesh.from_pydata(vertices, edges, [])
    mesh.update()

    # Make the chain object active
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)

    hook_empties = []
    hooks_collection = bpy.data.collections.new('hooks' + subobj_suffix)
    hooked_chain_collection.children.link(hooks_collection)


    # Create hooks and assign them
    for i in range(n_nodes):        
        # Create empty at the correct position
        hook = bpy.data.objects.new(f'hook_{i}_empty'+subobj_suffix, None)
        
        hook.location = vertices[i].copy()
        
        #bpy.context.scene.collection.objects.link(hook)
        hooks_collection.objects.link(hook)  # Link to hooks collection instead of scene collection

        
        # Add hook modifier
        hook_mod = obj.modifiers.new(name=f'hook_{i}_mod'+subobj_suffix, type='HOOK')
        hook_mod.object = hook
        hook_mod.falloff_type = 'NONE'
        hook_mod.strength = 1.0
        
        # Create vertex group
        vg = obj.vertex_groups.new(name=f'hook_{i}_vg'+subobj_suffix)
        
        # Add exactly 5 vertices starting from start_idx
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
    
    return obj, hook_empties


def change_hook_strength(hooked_objs, new_strength=1.0):
    # For all objects in scene
    for obj in hooked_objs:
    # Check modifiers
        for mod in obj.modifiers:
            # If modifier is a hook
            if mod.type == 'HOOK':
                mod.strength = new_strength # Change this value (0.0 to 1.0)


def add_fiber_softbody(obj):
    # Add soft body modifier first
    soft_body = obj.modifiers.new(name="Softbody", type='SOFT_BODY')
    soft_body.settings.use_goal = True
    soft_body.settings.use_self_collision = True
    
    # Self-collision settings
    soft_body.settings.ball_size = 0.5  # Collision ball size
    #soft_body.ball_stiff = 0.95  # Collision ball stiffness
    soft_body.settings.ball_damp = 0.5  # Collision ball dampening
    
    # Goal settings
    soft_body.settings.goal_default = 0.7  # Goal strength
    #soft_body.goal_spring = 0.5  # Goal stiffness
    soft_body.settings.goal_friction = 20.0  # Goal dampening
    soft_body.settings.speed = 3.0  # Goal dampening

    soft_body.settings.pull = 0.7  # Edge pull force
    soft_body.settings.push = 0.7  # Edge push force
    #soft_body.settings.bend = 0.5  # Bend stiffness

    soft_body.point_cache.frame_end = 1000


def add_smooth_skin(obj, skin_radius=0.5):
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)

    subsurf_mod = obj.modifiers.new(name="Subdivision", type='SUBSURF')
    subsurf_mod.levels = 2  # Viewport subdivisions
    subsurf_mod.render_levels = 2  # Render subdivisions
    subsurf_mod.quality = 3  # Subdivision qualitys

    # Add Skin modifier
    skin_mod = obj.modifiers.new(name="Skin", type='SKIN')
    
    skin_data = obj.data.skin_vertices[0].data
    for skin_vert in skin_data:
        skin_vert.radius = (skin_radius, skin_radius)  # (X, Y) radius for each vertex


def _arrange_hooks_into_loop(
        hooks_loop,
        step,
        root_loc, 
        bridge_width,
        stem_length=2, 
        stem_only=False,
        vertical_orientation=1):
    
    l_loop = len(hooks_loop)
    vo = vertical_orientation

    real_stem_length = min(stem_length, int(round(l_loop / 2)))
    # arange hooks of the stem
    for i in range(real_stem_length):
        hook = hooks_loop[i]
        hook.location = root_loc + Vector((-bridge_width/2, i * step * vo, 0))

        hook = hooks_loop[-i-1]
        hook.location = root_loc + Vector((bridge_width/2, i * step * vo, 0))



    if stem_only or l_loop <= 2 * stem_length:
        return

    n_hooks_circle = l_loop - 2 * stem_length 
    l_circle = n_hooks_circle * step
    r_circle = l_circle / math.pi / 2

    stem_angle = np.arcsin(bridge_width / 2 / r_circle)
    loop_total_angle = 2 * math.pi - stem_angle * 2

    angle_per_hook = loop_total_angle / (n_hooks_circle + 1 )

    center_circle = root_loc + Vector((0, step * (stem_length - 1) * vo, 0)) + Vector((0, r_circle * vo, 0))

    for i, hook in enumerate(hooks_loop[stem_length:-stem_length]):
        hook_angle = 1.5 * math.pi - angle_per_hook * (i + 1) - stem_angle
        hook_position = center_circle.copy()
        hook_position[0] += r_circle * math.cos(hook_angle)
        hook_position[1] += (r_circle * math.sin(hook_angle)) * vo
        hook.location = hook_position.copy()
        

def keyframe_hook_loop(
    t,
    hooks_loop, 
    step,
    root_loc, 
    bridge_width,
    stem_length=2, 
    stem_only=False,
    vertical_orientation=1
    ):

    bpy.context.scene.frame_set(int(t))

    _arrange_hooks_into_loop(
        hooks_loop,
        step,
        root_loc,
        bridge_width,
        stem_length,
        stem_only,
        vertical_orientation=vertical_orientation)
    
    hooks_to_keyframe = hooks_loop[:stem_length] + hooks_loop[-stem_length:] if stem_only else hooks_loop

    for hook in hooks_to_keyframe:    
        hook.keyframe_insert(data_path="location", frame=int(t))



def _animate_extrusion_no_tails(
        hooks,        
        time_span,
        step,
        bridge_width,
        stem_length=2,
        root_loc = None,
        init_loop_idxs = None,
        n_intermediate_keyframes = 0,
        vertical_orientation=1
):

    if init_loop_idxs is None:
        init_loop_idxs = (len(hooks) // 2, len(hooks) // 2 + 1)

    bpy.context.scene.frame_set(int(time_span[0]))
    
    if root_loc is None:
        root_loc = ( hooks[init_loop_idxs[0]].location.copy() 
                   + hooks[init_loop_idxs[1]-1].location.copy()) / 2

    n_steps = max(init_loop_idxs[0], len(hooks) - init_loop_idxs[1]) + 1

    t_lo, t_hi = time_span
    frames_per_hook = (t_hi - t_lo) / n_steps

    full_loop_steps = np.unique(
        np.linspace(0, n_steps-1, int(n_intermediate_keyframes)+2, dtype=int)[1:])

    for i in range(n_steps):
        t = t_lo + i * frames_per_hook
        if i == 0:
            bpy.context.scene.frame_set(int(t_lo))
            for hook in hooks:
                hook.keyframe_insert(data_path="location", frame=int(t_lo))
        else:
            hooks_to_keyframe_span = (
                max(0, init_loop_idxs[0] - i),
                min(len(hooks), init_loop_idxs[1] + i))

            hooks_to_keyframe = hooks[slice(*hooks_to_keyframe_span)]
            keyframe_full_loop = i in full_loop_steps
            keyframe_hook_loop(
                t,
                hooks_to_keyframe, 
                step,
                root_loc, 
                bridge_width,
                stem_length=stem_length, 
                stem_only=not keyframe_full_loop,
                vertical_orientation=vertical_orientation
                )


def normalize_loop_traj(loop_traj):
    if not isinstance(loop_traj, dict):
        raise ValueError("loop_traj must be a dictionary {time: (start_loop, end_loop)}")
    loop_traj = dict(sorted(loop_traj.items(), key=lambda x: x[0]))

    # infer loading position assuming two-sided extrusion
    if list(loop_traj.values())[0] is None:
        next_loop = list(loop_traj.values())[1]
        mid_next_loop = (next_loop[0] + next_loop[1]) // 2
        loop_traj[list(loop_traj.keys())[0]] = (mid_next_loop, mid_next_loop + 1)
    return loop_traj


def animate_looparray_extrusion(
    hooks,
    loops_traj,
    vertical_orientations=None,
    bridge_width = 2.5,
    step = 4,
    n_intermediate_keyframes = None,
    ):

    if isinstance(loops_traj, dict):
        loops_traj = [loops_traj]

    loops_traj = [normalize_loop_traj(lt) for lt in loops_traj]

    linear_shifts = []
    if vertical_orientations is None:
        vertical_orientations = [1] * len(loops_traj)

    for loop_traj, vo in zip(loops_traj, vertical_orientations):
        last_t = max(loop_traj.keys())
        final_loop = loop_traj[last_t]

        for (t_lo, prev_loop), (t_hi, next_loop) in zip(
                list(loop_traj.items())[:-1],
                list(loop_traj.items())[1:]):

            rel_init_loop_idxs = (prev_loop[0] - next_loop[0], prev_loop[1] - next_loop[0])

            _animate_extrusion_no_tails(
                hooks[slice(*next_loop)],
                time_span = (t_lo, t_hi),
                step=step,
                bridge_width=bridge_width,
                stem_length=2,
                root_loc = None,
                init_loop_idxs = rel_init_loop_idxs,
                n_intermediate_keyframes=n_intermediate_keyframes,
                vertical_orientation=vo
                )
            

            delta_left = (
                get_obj_loc(hooks[next_loop[0]], t_hi) 
                - get_obj_loc(hooks[next_loop[0]], t_lo) )
            
            delta_right = (
                get_obj_loc(hooks[next_loop[1]-1], t_hi) 
                - get_obj_loc(hooks[next_loop[1]-1], t_lo) )

            # delta_left = (prev_loop[0] - next_loop[0]) * Vector((step, 0, 0))
            # delta_right = (prev_loop[1] - next_loop[1]) * Vector((step, 0, 0))


            linear_shifts.append(
                functools.partial(
                    animate_linear_shift,
                    hooks[0:final_loop[0]], 
                    shift_vector=delta_left,
                    time_span=(t_lo, t_hi),
                    shift_existing_keyframes=True,
                    extend=True
                )
            )

            linear_shifts.append(
                functools.partial(
                    animate_linear_shift,
                    hooks[final_loop[0]:next_loop[0]], 
                    shift_vector=delta_left,
                    time_span=(t_lo, t_hi),
                    shift_existing_keyframes=True,
                    extend=False
                    )
            )

            linear_shifts.append(
                functools.partial(
                    animate_linear_shift,
                    hooks[next_loop[1]:final_loop[1]], 
                    shift_vector=delta_right,
                    time_span=(t_lo, t_hi),
                    shift_existing_keyframes=True,
                    extend=False
                    )
            )

        
            linear_shifts.append(
                functools.partial(
                    animate_linear_shift,
                    hooks[final_loop[1]:], 
                    shift_vector=delta_right,
                    time_span=(t_lo, t_hi),
                    shift_existing_keyframes=True,
                    extend=True
                )
            )
            
               
    for linear_shift in linear_shifts:
        linear_shift()

# def animate_resume_extrusion(
#     hooks,
#     prev_loop,
#     new_loop,
#     time_span,
#     step,
#     delay_extrusion=0,
# ):
#     # only right-sided extrusion is implemented
    
#     bpy.context.scene.frame_set(time_span[0])
#     prev_loop_locs = (
#         hooks[prev_loop[0]].location.copy(),
#         hooks[prev_loop[1]-1].location.copy()
#         )
#     prev_loop_mid_loc = (prev_loop_locs[0] + prev_loop_locs[1]) / 2

#     delta = hooks[prev_loop[1] - 1].location - hooks[new_loop[1] - 1].location

#     extrusion_time_span = (time_span[0] + delay_extrusion, time_span[1])

#     _animate_extrusion_threading(
#             hooks[prev_loop[1]:new_loop[1]],
#             time_span = extrusion_time_span,
#             loop_stem_base_loc = prev_loop_locs[1],
#             loop_stem_tip_loc = prev_loop_locs[1] + Vector((0, step, 0)),
#             last_stays_at_stem_base=True,
#     )

#     animate_linear_shift(
#         hooks[new_loop[1]:], 
#         delta,
#         time_span= extrusion_time_span)
        
#     _animate_loop_final_conformation(
#         hooks_loop=hooks[slice(*prev_loop)],
#         t=time_span[0],
#         step=step,
#         stem_tip_loc=(prev_loop_mid_loc + Vector((0, step, 0))),
#         skip_stem=True
#     )

#     _animate_loop_final_conformation(
#         hooks_loop=hooks[slice(*new_loop)],
#         t=time_span[1],
#         step=step,
#         stem_tip_loc=(prev_loop_mid_loc + Vector((0, step, 0))),
#         skip_stem=True
#     )

# def _animate_extrusion_no_tails(
#     hooks_loop,
#     time_span = (20, 80),
#     loop_base_width = 2.5,
#     step = 4):

#     mid_loop_idx = len(hooks_loop) // 2

#     mid_loop_loc = ( hooks_loop[mid_loop_idx].location 
#                    + hooks_loop[mid_loop_idx+1].location) / 2
                   
#     left_anchor_loc =  mid_loop_loc + Vector((- loop_base_width / 2, 0, 0))
#     right_anchor_loc = mid_loop_loc + Vector((  loop_base_width / 2, 0, 0))

    
#     _animate_extrusion_threading(
#         hooks_loop[0:mid_loop_idx+1][::-1],
#         time_span,
#         left_anchor_loc,
#         left_anchor_loc + Vector((0, step, 0)),
#     )

#     _animate_extrusion_threading(
#         hooks_loop[mid_loop_idx+1:],
#         time_span,
#         right_anchor_loc,
#         right_anchor_loc + Vector((0, step, 0)),
#     )
    
#     _animate_loop_final_conformation(
#         hooks_loop,
#         time_span[1],
#         step,
#         mid_loop_loc + Vector((0, step, 0)),
#         skip_stem=True
#     )

#     return left_anchor_loc, right_anchor_loc


# def animate_loop_extrusion(
#     hooks,
#     loop_span = (30, 60),
#     time_span = (20, 80),
#     step = 4,
#     bridge_width = 2.5,
#     init_loop_idxs = None,
#     n_full_loop_keyframes = None,
#     ):

#     rel_init_loop_idxs = (
#         None 
#         if init_loop_idxs is None 
#         else (init_loop_idxs[0] - loop_span[0], init_loop_idxs[1] - loop_span[0])
#         )
    
#     assert (init_loop_idxs[0] > 0)
#     assert (0 < init_loop_idxs[1] < len(hooks))


#     _animate_extrusion_no_tails(
#             hooks[slice(*loop_span)],        
#             time_span=time_span,
#             step=step,
#             bridge_width=bridge_width,
#             stem_length=2,
#             root_loc = None,
#             init_loop_idxs = rel_init_loop_idxs,
#             n_full_loop_keyframes=n_full_loop_keyframes
#     )

#     bpy.context.scene.frame_set(int(time_span[0]))
#     left_anchor_init_loc = hooks[loop_span[0]].location.copy()
#     right_anchor_init_loc = hooks[loop_span[1]-1].location.copy()

#     bpy.context.scene.frame_set(int(time_span[1]))
#     left_anchor_final_loc = hooks[loop_span[0]].location.copy()
#     right_anchor_final_loc = hooks[loop_span[1]-1].location.copy()

#     left_delta = left_anchor_final_loc - left_anchor_init_loc
#     right_delta = right_anchor_final_loc - right_anchor_init_loc

#     animate_linear_shift(
#         hooks[:loop_span[0]], 
#         left_delta,
#         time_span)
        
#     bpy.context.scene.frame_set(int(time_span[0]))
#     animate_linear_shift(
#         hooks[loop_span[1]:], 
#         right_delta,
#         time_span)
    

# def animate_looparray_extrusion(
#     hooks,
#     loop_traj,
#     bridge_width = 2.5,
#     step = 4,
#     n_full_loop_keyframes = None,

#     ):


#     # Get all empties with the given prefix, sorted by name
#     deltas = []

#     loop_traj = sorted(loop_traj, key=lambda x: x[2][0])

#     for init_loop, final_loop, time_span in loop_traj:
#         rel_init_loop_idxs = (
#             None 
#             if init_loop is None 
#             else (init_loop[0] - final_loop[0], init_loop[1] - final_loop[0])
#         )

#         _animate_extrusion_no_tails(
#             hooks[slice(*final_loop)],
#             time_span = time_span,
#             step=step,
#             bridge_width=bridge_width,
#             stem_length=2,
#             root_loc = None,
#             init_loop_idxs = rel_init_loop_idxs,
#             n_full_loop_keyframes=n_full_loop_keyframes
#             )
        
#         bpy.context.scene.frame_set(int(time_span[0]))
#         left_anchor_init_loc = hooks[final_loop[0]].location.copy()
#         right_anchor_init_loc = hooks[final_loop[1]-1].location.copy()

#         bpy.context.scene.frame_set(int(time_span[1]))
#         left_anchor_final_loc = hooks[final_loop[0]].location.copy()
#         right_anchor_final_loc = hooks[final_loop[1]-1].location.copy()

#         deltas.append(
#             (left_anchor_final_loc - left_anchor_init_loc, 
#              right_anchor_final_loc - right_anchor_init_loc),
#         )
        
        
#     for (init_loop, final_loop, time_span), (left_delta, right_delta) in zip(
#             loop_traj, deltas):

#         animate_linear_shift(
#             hooks[:final_loop[0]], 
#             left_delta,
#             time_span)
            
#         animate_linear_shift(
#             hooks[final_loop[1]:], 
#             right_delta,
#             time_span)
