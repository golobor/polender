import warnings

import bpy
from mathutils import Vector


def clear_animation(objects=None, properties=None, new_values=None):
    """
    Clear animation keyframes for specific properties from Blender objects.
    
    Args:
        objects: A single object, list of objects, or None to use selected objects
        properties: List of property data paths to clear
        new_values: Dictionary of {property: value} to set after clearing animation.
                   If None, properties won't be changed
    """
    
    # Handle different input types for objects
    obj_list = []
    if objects is None:
        obj_list = list(bpy.context.selected_objects)
    elif isinstance(objects, list):
        obj_list = objects
    else:
        obj_list = [objects]
    
    # Process each object
    for obj in obj_list:
        # Check if the object has animation data
        if obj.animation_data and obj.animation_data.action:
            action = obj.animation_data.action
            
            # Clear specified properties (or all if None)
            props_to_clear = properties or [fc.data_path for fc in action.fcurves]
            
            for prop in props_to_clear:
                # Find the fcurve directly by name
                fcurve = action.fcurves.find(prop)
                if fcurve:
                    action.fcurves.remove(fcurve)
                else:
                    warnings.warn(f"Property '{prop}' not found in action '{action.name}' for object '{obj.name}'") 
        
        # Set new values if provided
        if new_values:
            for prop, value in new_values.items():
                if hasattr(obj, prop):
                    setattr(obj, prop, value)


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
 
    
# def clear_animation(objs):
#     if objs is None:
#         objs = bpy.context.scene.objects
        
#     # Remove animation from all objects
#     for obj in objs:
#         obj.animation_data_clear()

#     # # Optional: also remove unused actions
#     # for action in bpy.data.actions:
#     #     bpy.data.actions.remove(action)



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


def animate_curve_point_radius(curve_obj, start_frame=1, end_frame=50, radius=1.0):
    curve = curve_obj.data
    spline = curve.splines[0]  # Assuming first spline
    
    # Get total points for calculation
    if spline.type == 'BEZIER':
        total_points = len(spline.bezier_points)
        
        # Calculate the frame spacing between points
        frame_step = (end_frame - start_frame) / total_points
        
        # For each point, set just two keyframes
        for i, point in enumerate(spline.bezier_points):
            if i % 10000 == 0:
                print(f"Animating point {i} of {total_points}")
            # Calculate the frame when this point should appear
            appear_frame = start_frame + int(i * frame_step)
            
            # Set radius 0 at start frame (hidden)
            #bpy.context.scene.frame_set(start_frame)
            point.radius = 0.0
            point.keyframe_insert("radius", frame=start_frame)
            
            # Set radius 1 at appearance frame (visible)
            #bpy.context.scene.frame_set(appear_frame)
            point.keyframe_insert("radius", frame=appear_frame-1)
            point.radius = radius
            point.keyframe_insert("radius", frame=appear_frame)



def _create_taper_curve(name):
    """Create a new taper curve object"""
    # Remove existing curve/object if present
    if name in bpy.data.curves:
        if name in bpy.data.objects:
            bpy.data.objects.remove(bpy.data.objects[name])
        bpy.data.curves.remove(bpy.data.curves[name])
        
    # Create a new curve and object
    curve = bpy.data.curves.new(name, 'CURVE')
    curve.dimensions = '2D'
    
    obj = bpy.data.objects.new(name, curve)
    bpy.context.scene.collection.objects.link(obj)
    
    # Hide the taper object
    obj.hide_viewport = True
    obj.hide_render = True
    
    return curve, obj

def _setup_growth_taper(curve_obj, start_frame, end_frame, step_width=0.02):
    """Set up a clean growing effect taper curve"""
    # Create the taper object
    taper_name = f"{curve_obj.name}_taper"
    taper_curve, taper_obj = _create_taper_object(taper_name)
    
    # Create a spline with 3 points (minimal configuration)
    spline = taper_curve.splines.new('BEZIER')
    ps = spline.bezier_points
    ps.add(3) 
    
    # Set all handles to vector type for sharp transitions
    for point in ps:
        point.handle_left_type = 'VECTOR'
        point.handle_right_type = 'VECTOR'
    
    # Initial state: completely invisible
    ps[0].co = (0, 0, 0)
    ps[1].co = (0, 0, 0)
    ps[2].co = (0, 0, 0)
    ps[3].co = (1, 0, 0)
    
    # Keyframe initial state
    for p in ps:
        p.keyframe_insert("co", frame=start_frame)
    
    velocity = (1+step_width) / (end_frame - start_frame)

    ps[0].co = (0, 1, 0)
    ps[1].co = (0, 1, 0)
    ps[2].co = (step_width, 0, 0)

    for p in ps:
        p.keyframe_insert("co", frame=start_frame+max(1,int(step_width/velocity)))
    
    ps[1].co = (1 - step_width, 1, 0)
    ps[2].co = (1, 0, 0)

    for p in ps[1:]:
        p.keyframe_insert("co", frame=start_frame+int(1.0/velocity))

    ps[1].co = (1, 1, 0)
    ps[2].co = (1, 1, 0)
    ps[3].co = (1, 1, 0)

    for p in ps[1:]:
        p.keyframe_insert("co", frame=end_frame)
        
    # Make animation linear
    if taper_curve.animation_data and taper_curve.animation_data.action:
        for fcurve in taper_curve.animation_data.action.fcurves:
            for kf in fcurve.keyframe_points:
                kf.interpolation = 'LINEAR'
    
    # Assign taper to curve
    curve_obj.data.taper_object = taper_obj
    
    return taper_obj


def animate_curve_growth(curve_obj, start_frame=1, end_frame=50, step_width=0.02, thickness=0.01):
    """Apply growing animation to a curve using taper"""
    # Make sure it's a curve
    if curve_obj.type != 'CURVE':
        print(f"Object {curve_obj.name} is not a curve, skipping.")
        return None
    
    # Set up curve properties
    curve_data = curve_obj.data
    curve_data.use_fill_caps = True
    curve_data.bevel_depth = thickness  # Set your desired thickness
    
    # Create and set up taper
    taper_obj = _setup_growth_taper(curve_obj, start_frame, end_frame, step_width)
    
    print(f"Applied growth animation to {curve_obj.name}")
    return taper_obj



def hide_obj(obj, t, unhide=False):
    bpy.context.scene.frame_set(t)
    obj.hide_viewport = not unhide
    obj.hide_render = not unhide

    obj.keyframe_insert('hide_viewport', frame=t)
    obj.keyframe_insert('hide_render', frame=t)