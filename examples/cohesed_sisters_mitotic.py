# context.area: CONSOLE
import sys
import types
import importlib

import numpy as np

import bpy
from mathutils import *

import pip
# pip.main('install --upgrade pip'.split())
# pip.main('install numpy gsd'.split()
# pip.main('install scikit-learn'.split())
# pip.main('uninstall polykit'.split())
# pip.main('install /Users/anton.goloborodko/src/polykit/ -U'.split())

import polykit
import polykit.io
import polykit.io.fetch_hoomd
importlib.reload(polykit.io.fetch_hoomd)

sys.path.append('./')
import polender
importlib.reload(polender)

SCALE_FACTOR = 0.01
THICKNESS = 1.0

bpy.P = types.SimpleNamespace()
bpy.P.polender = polender


path = './traj.gsd'

bpy.P.snap = polykit.io.fetch_hoomd.fetch_snaphot(
    path,
    #frame_idx=-1
    frame_idx=41,
)


bpy.P.d, bpy.P.chains = polykit.io.fetch_hoomd.unwrap_chains(bpy.P.snap, bond_types=['chain_bond'])
bpy.P.d = bpy.P.d - bpy.P.d.mean(axis=0)


def pca_align(d):
    # Center the data by subtracting the mean
    d_centered = d - np.mean(d, axis=0)

    # Perform SVD
    U, S, Vt = np.linalg.svd(d_centered, full_matrices=False)

    # Project the data onto the first 3 principal components
    d_pcad = np.dot(d_centered, Vt.T[:, :3])

    return d_pcad

bpy.P.d = pca_align(bpy.P.d)
bpy.P.d = bpy.P.d[:, [2,1,0]]

bpy.P.d *= SCALE_FACTOR

for ch in bpy.P.chains:
    d_chain = bpy.P.d[slice(*ch)]
    d, curve = bpy.P.polender.add_curve(d_chain, smooth_bezier=True, thickness=THICKNESS*SCALE_FACTOR)

# bpy.P.polender.add_backdrop(s=10)

bonds = bpy.P.snap.bonds.group.astype(np.int32)
root_loop_type = 'root_loop'
loops = bonds[
    bpy.P.snap.bonds.typeid==bpy.P.snap.bonds.types.index(root_loop_type)
]

bridges = bonds[
    bpy.P.snap.bonds.typeid==bpy.P.snap.bonds.types.index('bridge')
]

cond_coords = (bpy.P.d[loops[:,0]] + bpy.P.d[loops[:,1]])/2
bridges_coords = (bpy.P.d[bridges[:,0]] + bpy.P.d[bridges[:,1]])/2

bpy.P.polender.add_spheres(
    cond_coords,
    radius=2.5 * SCALE_FACTOR,
    collection='condensin_highcoh'
)


bpy.P.polender.add_spheres(
    bridges_coords,
    radius=4.0 * SCALE_FACTOR,
    collection='cohesin_highcoh'
)