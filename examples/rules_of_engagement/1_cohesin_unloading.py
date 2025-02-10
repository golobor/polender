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



N_NODES = 300
STEP = 8
CHAIN_BOND_INFLUENCE = 0.5


chain, hooks = ae.make_hooked_chain(N_NODES, STEP)


ae.chain_hooks(hooks, max_dist=STEP+1, min_dist=STEP-1, influence=CHAIN_BOND_INFLUENCE)


ae.add_fiber_softbody(chain)
ae.add_smooth_skin(chain, skin_radius=2.0)


cam_loc = Vector((-10, 50, 300))
cam = polender.objects.add_camera(
    loc = cam_loc,
    direction=('Z', 'Y'),
    focal_length=45
)




# two initial cohesin loops
ae.animate_looparray_extrusion(
    hooks,
    [
    {50: None,
     100: (80, 110),},
     {75: None,
      125: (160, 190)}
     ],
    bridge_width = 2.5,
    step = STEP,
    n_intermediate_keyframes = 1,
    )


# initial condensin loop
ae.animate_looparray_extrusion(
    hooks,
    [   
    {200: (145, 146),
     250: (130, 159),
    }
    ],
    bridge_width = 2.5,
    step = STEP,
    n_intermediate_keyframes = 1,
    )


# swallowing cohesin 2
ae.animate_looparray_extrusion(
    hooks,
    [
    # cohesin 1
    {300: (130, 159),
     450: (130, 192),
     475: (130, 192),
     525: (111, 192),
    }
     ],
    bridge_width = 2.5,
    step = STEP,
    n_intermediate_keyframes= 1,
    )



# swallowing cohesin 1

ae.animate_looparray_extrusion(
    hooks,
    [
    {550: (111, 192),
     650: (80, 192),
    }
     ],
    bridge_width = 2.5,
    step = STEP,
    n_intermediate_keyframes = 1,
    )


# extra codes 

# detecting hooks and the chain
# hooks = list(polender.utils.discover_objects(
#     'hook_{}_empty', obj_type='EMPTY').values())
# chain = bpy.data.objects['chain']
# print(chain)

# changing radius of the chain
# ae.set_skin_radius(chain, 3.0)


# adding noise

# ae.disable_constraints(hooks)
# polender.dynamics.add_fcurve_noise(hooks, strength=10.0, scale=10.0)


# removing noise (useful for editing)
# polender.dynamics.remove_fcurve_noise(hooks)


# adding noise to condensins and cohesins
# condensin = bpy.data.objects['Condensin']
# cohesin1 = bpy.data.objects['Cohesin 1']
# cohesin2 = bpy.data.objects['Cohesin 2']

# polender.dynamics.add_fcurve_noise([condensin, cohesin1, cohesin2], strength=3.0, scale=10.0)
# polender.dynamics.remove_fcurve_noise([condensin, cohesin1, cohesin2])


