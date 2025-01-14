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
