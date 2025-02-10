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



N_NODES = 600
STEP = 8
CHAIN_BOND_INFLUENCE = 0.5

MID = N_NODES//2



chain, hooks = ae.make_hooked_chain(N_NODES, STEP)

ae.chain_hooks(hooks, max_dist=STEP+1, min_dist=STEP-1, influence=CHAIN_BOND_INFLUENCE)

ae.add_fiber_softbody(chain)
ae.add_smooth_skin(chain, skin_radius=2.0)


ae.animate_looparray_extrusion(
    hooks,
    [
    
    {100: None,
     200: (MID - 72, MID - 25),},
     {100: None,
     200: (MID - 22, MID + 25),},
     {100: None,
     200: (MID + 28, MID + 75),},
     
     ],
    bridge_width = 2.5,
    vertical_orientations=[1, -1, 1],
    step = STEP,
    n_intermediate_keyframes = 1,
    )



ae.animate_looparray_extrusion(
    hooks,
    [
    
    {300: None,
     400: (MID - 122, MID - 75),},
    {300: None,
     400: (MID + 78, MID + 125),},
    
    {325: None,
     425: (MID - 172, MID - 125),},
     {325: None,
     425: (MID + 128, MID + 175),},


    {350: None,
     450: (MID - 222, MID - 175),},
    {350: None,
     450: (MID + 178, MID + 225),},

    {360: None,
     460: (MID - 272, MID - 225),},    
    {360: None,
     460: (MID + 228, MID + 275),},
     ],
    bridge_width = 2.5,
    vertical_orientations=[-1, -1, 1, 1, -1, -1, 1, 1],
    step = STEP,
    n_intermediate_keyframes = 1,
    )


cam_loc = Vector((2400, 50, 600))
cam = polender.objects.add_camera(
    loc = cam_loc,
    direction=('Z', 'Y'),
    focal_length=45
)



hooks = list(polender.utils.discover_objects(
    'hook_{}_empty', obj_type='EMPTY').values())

print(hooks)

condensins = [o for o in bpy.data.objects.values() if 'Condensin' in o.name]
print(condensins)

ae.disable_constraints(hooks)
polender.dynamics.add_fcurve_noise(hooks, strength=10.0, scale=10.0)
polender.dynamics.add_fcurve_noise(condensins, strength=3.0, scale=10.0)


# polender.dynamics.remove_fcurve_noise(hooks)
# polender.dynamics.remove_fcurve_noise(condensins)

condensin = bpy.data.objects['Condensin']
cohesin1 = bpy.data.objects['Cohesin 1']
cohesin2 = bpy.data.objects['Cohesin 2']

polender.dynamics.add_fcurve_noise([condensin, cohesin1, cohesin2], strength=3.0, scale=10.0)
polender.dynamics.remove_fcurve_noise([condensin, cohesin1, cohesin2])


