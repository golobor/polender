import bpy
import mathutils
import numpy as np


def hide_obj(obj, t):
    bpy.context.scene.frame_set(t)
    obj.hide = True
    obj.keyframe_insert('hide')      
    obj.hide_render = True
    obj.keyframe_insert('hide_render')


def unhide_obj(obj, t):
    bpy.context.scene.frame_set(t)
    obj.hide = False
    obj.keyframe_insert('hide')      
    obj.hide_render = False
    obj.keyframe_insert('hide_render')


def clone_obj(obj):
    bpy.context.scene.objects.active = obj
    bpy.ops.object.select_all(action='DESELECT')
    obj.select = True
    bpy.ops.object.duplicate(linked=True)
    return bpy.context.scene.objects.active


# def add_curve(
#         coords,
#         thickness = 0.2,
#         name='polymer', 
#         resolution=4,
#         kind='BEZIER'):
#     # create the Curve Datablock
#     curveData = bpy.data.curves.new(name+'_curve', type='CURVE')
#     curveData.dimensions = '3D'
#     curveData.resolution_u = resolution

#     # map coords to spline
#     if kind == 'NURBS':
#         polyline = curveData.splines.new('NURBS')
#         polyline.points.add(len(coords)-1)
#         for i, coord in enumerate(coords):
#             x,y,z = coord
#             polyline.points[i].co = (x, y, z, 1)
#     elif kind == 'BEZIER':
#         polyline = curveData.splines.new('BEZIER')
#         polyline.bezier_points.add(len(coords)-1)
#         for i, coord in enumerate(coords):
#             polyline.bezier_points[i].co = coord

#         for point in polyline.bezier_points:
#             point.handle_left_type="AUTO"
#             point.handle_right_type="AUTO"

#     # create Object
#     curveOB = bpy.data.objects.new(name+'_obj', curveData)

#     # attach to scene and validate context
#     bpy.context.scene.collection.objects.link(curveOB)
#     bpy.context.view_layer.objects.active = curveOB
#     curveOB.select_set(True)

#     curveOB.data.resolution_u     = resolution     # Preview U
#     curveOB.data.fill_mode        = 'FULL' # Fill Mode ==> Full
#     curveOB.data.bevel_depth      = thickness   # Bevel Depth
#     curveOB.data.bevel_resolution = resolution      # Bevel Resolution

#     return curveData, curveOB


def add_curve(
        coords, 
        thickness = 0.5,
        name='polymer', 
        resolution=4,
        kind='BEZIER',
        smooth_bezier=False):
    # create the Curve Datablock
    curveData = bpy.data.curves.new(name+'_curve', type='CURVE')
    curveData.dimensions = '3D'
    curveData.resolution_u = resolution

    # map coords to spline

    if kind == 'BEZIER':
        polyline = curveData.splines.new('BEZIER')
        polyline.bezier_points.add(len(coords)-1)
        polyline.bezier_points.foreach_set('co', coords.flatten())
        polyline.bezier_points.foreach_set('handle_left', coords.flatten())
        polyline.bezier_points.foreach_set('handle_right', coords.flatten())

    elif kind == 'NURBS':
        polyline = curveData.splines.new('NURBS')
        polyline.points.add(len(coords)-1)
        polyline.points.foreach_set('co', np.hstack([coords, np.ones((len(coords), 1))]).flatten())
    elif kind == 'POLY':
        polyline = curveData.splines.new('POLY')
        polyline.points.add(len(coords)-1)
        polyline.points.foreach_set('co', np.hstack([coords, np.ones((len(coords), 1))]).flatten())
    else:
        raise ValueError('Unknown curve type')
            
    curveOB = bpy.data.objects.new(name+'_obj', curveData)

    # attach to scene and validate context
    bpy.context.scene.collection.objects.link(curveOB)
    bpy.context.view_layer.objects.active = curveOB
    curveOB.select_set(True)

    curveOB.data.resolution_u     = resolution     # Preview U
    curveOB.data.fill_mode        = 'FULL' # Fill Mode ==> Full
    curveOB.data.bevel_depth      = thickness   # Bevel Depth
    curveOB.data.bevel_resolution = resolution      # Bevel Resolution
    
    if kind == 'BEZIER' and smooth_bezier:
        smooth_bezier_curve(curveOB)

    # if kind == 'BEZIER' and smooth_bezier:
    #     for point in polyline.bezier_points:
    #         point.handle_left_type='AUTO'
    #         point.handle_right_type='AUTO'
    # else:
    #     # this doesn't change the handle, but i'll try to anyway...
    #     left_type_enum = (
    #         bpy.types.BezierSplinePoint
    #         .bl_rna.properties['handle_left_type']
    #         .enum_items['AUTO'].value)
    #     right_type_enum = (
    #         bpy.types.BezierSplinePoint
    #         .bl_rna.properties['handle_right_type']
    #         .enum_items['AUTO'].value)
    #     polyline.bezier_points.foreach_set('handle_left_type', [left_type_enum]*len(coords)) # 'AUTO'?..
    #     polyline.bezier_points.foreach_set('handle_right_type', [right_type_enum]*len(coords)) # 'AUTO'?..

    

    return curveData, curveOB


# def smooth_curve_expensive(curve):
#     for point in curve.splines[0].bezier_points:        
#         point.handle_left_type='AUTO'
#         point.handle_right_type='AUTO'


def smooth_bezier_curve(curve_obj):
    bpy.ops.object.select_all(action='DESELECT')
    curve_obj.select_set(True)
    bpy.context.view_layer.objects.active = curve_obj
    bpy.ops.object.mode_set(mode = 'EDIT')
    bpy.ops.curve.select_all(action='SELECT')
    bpy.ops.curve.handle_type_set()
    bpy.ops.curve.normals_make_consistent(False)
    bpy.ops.curve.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode = 'OBJECT')


def add_keyframe_curve(
        name, 
        coords,
        t
        ):
    
    curve = bpy.data.curves[name].splines[0]
    kind = curve.type

    # map coords to spline
    if kind == 'NURBS':
        for point, coord in zip(curve.points, coords):
            x,y,z = coord
            point.co = (x, y, z, 1)
            point.keyframe_insert(data_path="co", frame = t)
    elif kind == 'BEZIER':
        for point, coord in zip(curve.bezier_points, coords):
            point.co = coord
            point.keyframe_insert(data_path="co", frame = t)

        for point, coord in zip(curve.bezier_points, coords):
            point.keyframe_insert(data_path="handle_left", frame = t)
            point.keyframe_insert(data_path="handle_right", frame = t)


def create_animated_curve(
    ds,
    ts,
    thickness = 0.2,
    name='polymer', 
    resolution=4,
    kind='BEZIER'):


    curve, obj = add_curve(
        ds[0],
        thickness=thickness,
        name=name, 
        resolution=resolution,
        kind=kind)

    name = curve.name

    ts = ts if hasattr(ts, "__iter__") else np.arange(len(ds)) * ts

    for d, t in zip(ds,ts):
        add_keyframe_curve(name, d, t)





#def get_rot_from_vec(p1, p2):
#    dx = p2[0] - p1[0]
#    dy = p2[1] - p1[1]
#    dz = p2[2] - p1[2]
#    dist = np.sqrt(dx*dx + dy*dy + dz*dz)
#    phi = np.arctan2(dy, dx) 
#    theta = np.arccos(dz/dist) 
#    return np.array([0, theta, phi])

def get_rot_from_vec(vec, axes=('Y','X')):
    return mathutils.Vector(vec).to_track_quat(*axes).to_euler()

def align_four_points(p1, p2, p3, p4):
    p1 = np.array(p1)
    p2 = np.array(p2)
    p3 = np.array(p3)
    p4 = np.array(p4)
    loc = (p1 + p2 + p3 + p4)/4
    rot = get_rot_from_vec( (p3+p4) / 2 - loc )
    return loc, rot


def set_loc_rot(obj, loc, rot, keyframe_t=None):
    obj.location = loc
    obj.rotation_euler = rot

    if keyframe_t is not None:
        obj.keyframe_insert(data_path="location", frame = keyframe_t)
        obj.keyframe_insert(data_path="rotation_euler", frame = keyframe_t)

    
def add_torus(
    major_radius,
    minor_radius,
    name=None
    ):

           
    bpy.ops.mesh.primitive_torus_add(
        view_align=False, 
        major_segments=48, 
        minor_segments=12,
        mode='MAJOR_MINOR',
        major_radius=major_radius, 
        minor_radius=minor_radius, 
        #abso_major_rad=1.25, 
        #abso_minor_rad=0.75,
        #generate_uvs=False
        )

    bpy.ops.object.shade_smooth()

    obj = bpy.context.active_object

    if name:
        obj.name = name
    
    return obj



def add_spheres(positions, radius=0.015, collection=""):
    """
    Creates spheres at given positions with the specified radius and adds them to a new collection.
    
    Args:
    - positions (list): List of tuples specifying the 3D coordinates for the spheres.
    - radius (float, optional): Radius of the spheres. Defaults to 1.0.
    - collection_name (str, optional): Name of the collection to add the spheres to. If the collection
      doesn't exist, it will be created. Defaults to "NewCollection".
    """
    
    # Check if the collection already exists. If not, create it.
    if collection:
        if collection not in bpy.data.collections:
            new_collection = bpy.data.collections.new(collection)
            bpy.context.scene.collection.children.link(new_collection)
        else:
            new_collection = bpy.data.collections[collection]
    else:
        new_collection = bpy.context.collection
    
    for position in positions:
        bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, location=position)
        sphere = bpy.context.active_object
        
        # Link the sphere to the new collection and unlink from the default collection
        new_collection.objects.link(sphere)
        bpy.context.collection.objects.unlink(sphere)

    return new_collection




def add_backdrop(s=100, 
                 name='Backdrop', 
                 bevel_width_frac=0.15, 
                 bevel_segments=10,
                 mat=(1,1,1,1)):
    from bpy_extras.object_utils import object_data_add
    from mathutils import Vector

    hs = s/2
    verts = [
        Vector(( hs,-hs,  0)),
        Vector(( hs, hs,  0)),
        Vector((-hs, hs,  0)),
        Vector((-hs,-hs,  0)),
        Vector((-hs, hs, s)),
        Vector(( hs, hs, s)),
    ]
    faces = [[2,3,0,1], [5,4,2,1]]

    mesh = bpy.data.meshes.new(name=name)
    mesh.from_pydata(verts, [], faces)
    object_data_add(bpy.context, mesh)
    backdrop_obj = bpy.context.object
    bpy.ops.object.shade_smooth()

    bev_mod = backdrop_obj.modifiers.new('bevel', 'BEVEL')
    bev_mod.width = s * bevel_width_frac
    bev_mod.segments = bevel_segments

    if issubclass(type(mat), tuple):
        mat_obj = bpy.data.materials.new('back_mat')
        mat_obj.diffuse_color = list(mat)
        backdrop_obj.active_material = mat_obj
    
    return backdrop_obj