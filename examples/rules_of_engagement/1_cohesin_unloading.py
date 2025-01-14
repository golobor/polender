import sys
import pathlib
import importlib

import bpy
from mathutils import Vector, Matrix


libpath = pathlib.Path(__file__).parent.parent.parent.absolute()
sys.path.append(libpath)
import polender.animate_extrusion as ae
importlib.reload(ae)


# N_NODES = 200
# STEP = 8


# chain, hooks = ae.make_hooked_chain(N_NODES, STEP)

# ae.add_fiber_softbody(chain)
# ae.add_smooth_skin(chain, skin_radius=0.75)

# condensin_1st_loop = (55, 75)
# condensin_2nd_loop = (55, 85)
# condensin_3rd_loop = (55, 102)
# cohesin_loop = (90, 102)

# ae.animate_loop_extrusion(
#     hooks,
#     loop_span = cohesin_loop,
#     time_span = (0, 20),
#     loop_base_width = 2.5,
#     step = STEP,
#     )

# bpy.context.scene.frame_set(20)
# ae.clear_animation(None)

# bpy.context.scene.frame_set(0)
        
# left_anchor_loc, right_anchor_loc = ae.animate_loop_extrusion(
#     hooks,
#     loop_span = (condensin_1st_loop),
#     time_span = (100, 300),
#     loop_base_width = 2.5,
#     step = STEP,
#     )

# ae.animate_resume_extrusion(
#     hooks,
#     prev_loop=condensin_1st_loop,
#     new_loop=condensin_2nd_loop,
#     time_span=(475, 600),
#     delay_extrusion=30,
# )

# ae.animate_resume_extrusion(
#     hooks,
#     prev_loop=condensin_2nd_loop,
#     new_loop=condensin_3rd_loop,
#     time_span=(675, 800),
#     delay_extrusion=30,
# )



#ae.animate_extrusion.add_fcurve_noise(hooks, strength=10.0)




def setup_camera(loc=(0, 0, 100), 
                 focal_length=10,
                 direction=('Z', 'Y'),
                 name='MainCamera',):
    # Create camera
    cam_data = bpy.data.cameras.new('MainCamera')
    cam_obj = bpy.data.objects.new('MainCamera', cam_data)
    bpy.context.scene.collection.objects.link(cam_obj)

    # Set camera position along z-axis
    cam_obj.location = loc
    
    # Point camera at origin
    rot_quat = cam_obj.location.to_track_quat(*direction)
    cam_obj.rotation_euler = rot_quat.to_euler()

    # Set camera properties
    cam_data.lens = focal_length  # Long focal length
    cam_data.clip_start = 0.1
    cam_data.clip_end = 1000

    # Make this the active camera
    bpy.context.scene.camera = cam_obj
    
    return cam_obj

# Call after your animation code
cam = setup_camera()



#animate_looparray_extrusion(
#    hooks,
#    [(50, 60), (20, 80)],
#    [(0, 20), (20, 80)],
#    loop_base_width = 2.5,
#    step = 4,
#    )



# hooks = discover_objects('Hook_{}_empty', obj_type='EMPTY')

# remove_fcurve_noise(hooks)