import numpy as np
from mathutils import Vector

def set_loc_rot(obj, loc, rot, keyframe_t=None):
    obj.location = loc
    obj.rotation_euler = rot

    if keyframe_t is not None:
        obj.keyframe_insert(data_path="location", frame = keyframe_t)
        obj.keyframe_insert(data_path="rotation_euler", frame = keyframe_t)


def get_rot_from_vec(vec, axes=('Y','X')):
    return Vector(vec).to_track_quat(*axes).to_euler()


def align_four_points(p1, p2, p3, p4):
    p1 = np.array(p1)
    p2 = np.array(p2)
    p3 = np.array(p3)
    p4 = np.array(p4)
    loc = (p1 + p2 + p3 + p4)/4
    rot = get_rot_from_vec( (p3+p4) / 2 - loc )
    return loc, rot


def alignment_quaternion(axes_obj_vs_world1 = ('Z', 'Y'), axes_obj_vs_world2 = ('Z', 'Y')):
    """
    Create a quaternion rotation to align two object's axis with two given world axes
    
    Args:
        axis_obj_vs_world1 (tuple): Tuple of strings indicating the axis of the object and the world axis to align it to
        axis_obj_vs_world2 (tuple): Tuple of strings indicating the axis of the object and the world axis to align it to
    
    Returns:
        Quaternion: Rotation to achieve desired alignment
    """
    # Convert axis strings to vectors
    axes = {'X': Vector((1,0,0)), 
            'Y': Vector((0,1,0)), 
            'Z': Vector((0,0,1)),
            '-X': Vector((-1,0,0)),
            '-Y': Vector((0,-1,0)), 
            '-Z': Vector((0,0,-1))}
    
    # Get direction vectors
    align_vec = axes[axes_obj_vs_world1[0]]
    target_align_vec = axes[axes_obj_vs_world1[1]]

    up_vec = axes[axes_obj_vs_world2[0]]    
    target_up_vec = axes[axes_obj_vs_world2[1]]
    
    # Create rotation quaternion
    rot = align_vec.rotation_difference(target_align_vec)
    
    # Rotate up vector by first rotation
    rotated_up = up_vec.copy()
    rotated_up.rotate(rot)
    
    # Find rotation to align up vector while maintaining align axis
    up_rot = rotated_up.rotation_difference(target_up_vec)
    
    # Combine rotations
    final_rot = up_rot @ rot
    
    return final_rot
