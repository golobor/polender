import sys
import pathlib
import importlib

import bpy
from mathutils import Vector, Matrix
import polender.utils

libpath = pathlib.Path(__file__).parent.parent.parent.absolute().as_posix()
sys.path.append(libpath)

import polender
import polender.dynamics
import polender.objects
import polender.geoutils
import polender.animate_extrusion as ae

importlib.reload(polender)
importlib.reload(polender.dynamics)
importlib.reload(polender.objects)
importlib.reload(polender.geoutils)
importlib.reload(ae)



N_NODES = 200
STEP = 8


chain, hooks = ae.make_hooked_chain(N_NODES, STEP)

ae.add_fiber_softbody(chain)
ae.add_smooth_skin(chain, skin_radius=0.75)

condensin_1st_loop = (55, 75)
condensin_2nd_loop = (55, 88)
condensin_3rd_loop = (55, 102)
cohesin_loop = (90, 102)

left_coh_anchor_loc, right_coh_anchor_loc = ae.animate_loop_extrusion(
    hooks,
    loop_span = cohesin_loop,
    time_span = (0, 20),
    loop_base_width = 2.5,
    step = STEP,
    )

bpy.context.scene.frame_set(20)
polender.dynamics.clear_animation(None)

bpy.context.scene.frame_set(0)
        
left_anchor_loc, right_anchor_loc = ae.animate_loop_extrusion(
    hooks,
    loop_span = (condensin_1st_loop),
    time_span = (100, 300),
    loop_base_width = 2.5,
    step = STEP,
    )


ae.animate_resume_extrusion(
    hooks,
    prev_loop=condensin_1st_loop,
    new_loop=condensin_2nd_loop,
    time_span=(475, 600),
    step = STEP,
    delay_extrusion=30,
)


ae.animate_resume_extrusion(
    hooks,
    prev_loop=condensin_2nd_loop,
    new_loop=condensin_3rd_loop,
    time_span=(675, 800),
    step = STEP,
    delay_extrusion=30,
)



cam_loc = left_anchor_loc + Vector((-10, 50, 300))
cam = polender.objects.add_camera(
    loc = cam_loc,
    direction=('Z', 'Y'),
    focal_length=45
)



# hooks = list(polender.utils.discover_objects(
#     'Hook_{}_empty', obj_type='EMPTY').values())

# polender.dynamics.remove_fcurve_noise(hooks)
# polender.dynamics.add_fcurve_noise(hooks, strength=3.0, scale=10.0)

# # condensin = bpy.data.objects['Condensin']
# # polender.dynamics.remove_fcurve_noise([condensin])
# # polender.dynamics.add_fcurve_noise([condensin], strength=3.0, scale=10.0)

# # 

# # remove_fcurve_noise(hooks)

# polender.dynamics.smooth_animation(hooks)#+[condensin])



# ae.animate_looparray_extrusion(
#    hooks,
#    [(50, 60), (20, 80)],
#    [(0, 20), (20, 80)],
#    loop_base_width = 2.5,
#    step = 4,
#    )