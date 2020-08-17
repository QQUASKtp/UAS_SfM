#!/usr/bin/env python3

from sys import exit
from sys import stderr

from CGAL.CGAL_Kernel import Point_3
from CGAL.CGAL_Polyhedron_3 import Polyhedron_3
from CGAL.CGAL_Point_set_3 import Point_set_3
from CGAL.CGAL_Advancing_front_surface_reconstruction import *

import argparse

# Get input parameters
parser = argparse.ArgumentParser()
parser.add_argument("-i", "--inCloud", type=str, required=True, help="Input shapefile")

parser.add_argument("-o", "--outMesh", type=str, required=True, help="Output mesh ply file")

args = parser.parse_args() 

print("reading points")
points = Point_set_3(args.inCloud)

P = Polyhedron_3()

print("constructing mesh using advancing front technique")
advancing_front_surface_reconstruction(points, P)

print("ply file writtne to "+args.outMesh)
P.write_to_file(args.outMesh)
