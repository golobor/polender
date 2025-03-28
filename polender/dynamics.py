import bpy
from mathutils import Vector


def get_obj_loc(obj, frame):
    # Store current frame
    original_frame = bpy.context.scene.frame_current
    
    # Set frame where we want to evaluate
    bpy.context.scene.frame_set(frame)
    
    obj_loc = obj.location.copy()  # Local space position
    
    # Restore original frame
    bpy.context.scene.frame_set(original_frame)
    
    return obj_loc  # or local_pos


def animate_linear_shift(
        objects, 
        shift_vector, 
        time_span, 
        shift_existing_keyframes=True,
        extend=False):
    """
    Animate objects shifting their positions over time.
    """
    t_lo, t_hi = time_span
    shift_vector = Vector(shift_vector)
    
    for obj in objects:
        # Record start position and insert keyframe
        bpy.context.scene.frame_set(int(t_lo))
        obj.keyframe_insert(data_path="location", frame=t_lo)
        
        # Set end position and insert keyframe
        bpy.context.scene.frame_set(int(t_hi))
        obj.location += shift_vector
        obj.keyframe_insert(data_path="location", frame=t_hi)

        if not shift_existing_keyframes:
            continue
        
        # If object has keyframes between start and end, adjust them
        if obj.animation_data and obj.animation_data.action:
            for fc in obj.animation_data.action.fcurves:
                if fc.data_path == "location":
                    for kp in fc.keyframe_points:
                        if t_lo < kp.co[0] < t_hi:
                            t = (kp.co[0] - t_lo) / (t_hi - t_lo)
                            kp.co[1] += shift_vector[fc.array_index] * t
                        elif extend and (kp.co[0] > t_hi):
                            kp.co[1] += shift_vector[fc.array_index]
                    fc.update()


def insert_pause(t, duration):
    """
    Introduces a pause into the animation at time t for a given duration.
    Operates on location only.

    Parameters:
    t (int): The time at which to introduce the pause.
    duration (int): The duration of the pause.
    """
    t = int(t)
    duration = int(duration)

    # Go to time t
    bpy.context.scene.frame_set(t)
    
    for obj in bpy.context.scene.objects:
        # Insert a keyframe at time t
        loc = obj.location.copy()
        obj.keyframe_insert(data_path="location", frame=t)
    
        # Shift all keyframes after time t by duration
        for obj in bpy.context.scene.objects:
            for fcurve in obj.animation_data.action.fcurves:
                for keyframe in fcurve.keyframe_points:
                    if keyframe.co.x > t:
                        keyframe.co.x += duration
        
        # Insert a second keyframe at time t + duration
        bpy.context.scene.frame_set(t + duration)
        obj.location = loc
        obj.keyframe_insert(data_path="location", frame=t + duration)
 
    
def clear_animation(objs):
    if objs is None:
        objs = bpy.context.scene.objects
        
    # Remove animation from all objects
    for obj in objs:
        obj.animation_data_clear()

    # # Optional: also remove unused actions
    # for action in bpy.data.actions:
    #     bpy.data.actions.remove(action)



def smooth_animation(objs):
    """
    Smoothes the animation of objects by setting keyframe interpolation to BEZIER.
    """

    for obj in objs:
        if obj.animation_data and obj.animation_data.action:
            for fcurve in obj.animation_data.action.fcurves:
                for keyframe in fcurve.keyframe_points:
                    keyframe.interpolation = 'BEZIER'
                    keyframe.easing = 'AUTO'


def add_fcurve_noise(objs, strength=10.0, scale=20.0):
    for obj in objs:
        # Ensure the object has animation data
        if obj.animation_data is None:
            obj.animation_data_create()
        # Ensure an action is assigned
        if obj.animation_data.action is None:
            action = bpy.data.actions.new(name=f"{obj.name}_Action")
            obj.animation_data.action = action


        # Make sure location fcurves exist for X, Y, Z.
        for axis in range(3):
            found = any(fc.data_path == "location" and fc.array_index == axis 
                        for fc in obj.animation_data.action.fcurves)
            if not found:
                obj.keyframe_insert(data_path="location", frame=1)
                
        for fcurve in obj.animation_data.action.fcurves:
            noise = fcurve.modifiers.new('NOISE')
            noise.strength = strength
            noise.scale = scale
            noise.phase = hash(obj.name + str(fcurve.array_index)) % 1000  # Random phase per axis per object
            noise.use_restricted_range = False


def remove_fcurve_noise(objs):
    for obj in objs:
        if obj.animation_data and obj.animation_data.action:
            for fcurve in obj.animation_data.action.fcurves:
                for modifier in fcurve.modifiers:
                    if modifier.type == 'NOISE':
                        fcurve.modifiers.remove(modifier)