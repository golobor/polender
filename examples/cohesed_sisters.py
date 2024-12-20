    # context.area: CONSOLE
import sys
import types
import importlib

import numpy as np

import bpy
from mathutils import *

import pip
# pip.main('install --upgrade pip'.split())
# pip.main('install numpy gsd'.split())
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
THICKNESS = 0.5

bpy.P = types.SimpleNamespace()
bpy.P.polender = polender

path = './trajectory.gsd'

bpy.P.snap = polykit.io.fetch_hoomd.fetch_snaphot(
    path,
    frame_idx=-1
)


bpy.P.d, bpy.P.chains = polykit.io.fetch_hoomd.unwrap_chains(bpy.P.snap, bond_types=['polymer'])

bpy.P.d *= SCALE_FACTOR

for ch in bpy.P.chains:
    d_chain = bpy.P.d[slice(*ch)]
    d, curve = bpy.P.polender.add_curve(d_chain, smooth_bezier=True, thickness=THICKNESS*SCALE_FACTOR)

bpy.P.d = bpy.P.d - bpy.P.d.mean(axis=0)

d = bpy.P.d[:bpy.P.d.shape[0] // 2]
d, curve = polender.add_curve(d , smooth_bezier=True)

d = bpy.P.d[bpy.P.d.shape[0] // 2:]
d, curve = polender.add_curve(d , smooth_bezier=True)

bpy.P.polender.add_backdrop(s=10)