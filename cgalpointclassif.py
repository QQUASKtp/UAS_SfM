#!/usr/bin/env python3

from CGAL.CGAL_Kernel import Point_3
from CGAL.CGAL_Kernel import Vector_3
from CGAL.CGAL_Point_set_3 import Point_set_3
from CGAL.CGAL_Classification import *

import sys
import os
import numpy as np
from plyfile import PlyProperty, PlyListProperty, PlyData

import argparse

# Get input parameters
parser = argparse.ArgumentParser()
parser.add_argument("-i", "--inCloud", type=str, required=True, help="Input shapefile")
parser.add_argument('-l','--classes', nargs='+', help='<Required> Set flag', required=True)
parser.add_argument('-f','--fixply',  type=str, 
                    help='fix cc-generated fields - enter the field name, typically scalar_label',
                    required=False, default=None)
parser.add_argument('-m','--meth',  help='method', required=False, default=None)
parser.add_argument("-o", "--outCloud", type=str, required=False,default=None, 
                    help="Output ply file - if different from input")
args = parser.parse_args() 

incloud = args.inCloud
outcloud = args.outCloud

fields = args.classes
reg = args.meth

 


def fixply(incloud, outcloud, field='scalar_label'): 
    
    # The labels should be contiguous ie -1,0,1,2,3 - counting from zero
    
    pf = PlyData.read(incloud)
    
    ar = np.array(pf.elements[0].data[field])

    # after cloud compare thee are often spurious vales like -2564
    
    # do the nan to num in place 
    ar = np.nan_to_num(ar, nan=-1)
    

    ar[ar<-1]=-1
    
    ar = np.int32(ar)
    
#    ar[ar==1]=0
#
#    ar[ar==2]=1
#
#    ar[ar==3]=2
#
#    ar[ar==4]=3
    
    # All this modifies the original data
    new = pf['vertex']
    new.properties = ()
    new.data.dtype.names = ['x', 'y', 'z', 
                            'red', 'green', 'blue',
                            'nx', 'ny', 'nz',  'label']
    new.properties = (PlyProperty('x', 'double'),
                       PlyProperty('y', 'double'), 
                       PlyProperty('z', 'double'), 
                       PlyProperty('red', 'uchar'), 
                       PlyProperty('green', 'uchar'), 
                       PlyProperty('blue', 'uchar'), 
                       PlyProperty('nx', 'double'), 
                       PlyProperty('ny', 'double'), 
                       PlyProperty('nz', 'double'), 
                       PlyProperty('label', 'int'))
    
    pf.elements[0].data['label']=ar
    
    
    
    
    pf.write(outcloud)

def cgalclassify(incloud, outcloud, rgb=True, training="training",
                 method='graphcut', 
                 outmodel="random_forest.gz", k=12,
                 classes = ["ground", "veg", "building"]):

    
    # here we can find out the class names....
    # points.properties() will give label/training names & other props
    pf = PlyData.read(incloud)
    clList = pf.comments
    if clList[0] == "Generated by the CGAL library":
        clss = clList[2:len(clList)]
        classes = [c.split()[2] for c in clss]
        classes.pop(0)
        del clss, clList
    

    print("Reading input...")
    points = Point_set_3(incloud)
    print(points.size(), "points read")
    
    labels = Label_set()
    for c in classes:
        labels.add(c)
    print("Computing feature...")
    
  

    
    
    features = Feature_set()
    generator = Point_set_feature_generator(points, 5)
    # for a mesh
    #generator.generate_face_based_features
    # 5 is the number of levels (pyramids)
    
    features.begin_parallel_additions()
    generator.generate_point_based_features(features)
    if points.has_normal_map():
        generator.generate_normal_based_features(features, points.normal_map())
    
    if rgb is True:
        if points.has_int_map("red") and points.has_int_map("green") and points.has_int_map("blue"):
            generator.generate_color_based_features(features,
                                                    points.int_map("red"),
                                                    points.int_map("green"),
                                                    points.int_map("blue"))
    
    features.end_parallel_additions()
    
    print("features computed")

    classification = points.int_map("label")
    if not classification.is_valid():
        print("No ground truth found. Exiting.")
        exit()
    
    # Copy classification in training map for later evaluating
    training = points.add_int_map("training")
    for idx in points.indices():
        training.set(idx, classification.get(idx))
    
    print("Training random forest classifier...")
    classifier = ETHZ_Random_forest_classifier(labels, features)
#   TODO - this is in the C++ api and may be useful     
#   https://doc.cgal.org/latest/Classification/index.html
#    classifier.set_weight (distance_to_plane, 6.75e-2f)
#    classifier.set_weight (dispersion, 5.45e-1f)
#    classifier.set_weight (elevation, 1.47e1f)
#  
#  
#    classifier.set_effect (ground, distance_to_plane, Classifier::NEUTRAL)
#    classifier.set_effect (ground, dispersion, Classifier::NEUTRAL)
#    classifier.set_effect (ground, elevation, Classifier::PENALIZING)
#  
#    classifier.set_effect (vegetation, distance_to_plane,  Classifier::FAVORING)
#    classifier.set_effect (vegetation, dispersion, Classifier::FAVORING)
#    classifier.set_effect (vegetation, elevation, Classifier::NEUTRAL)
#    classifier.set_effect (roof, distance_to_plane,  Classifier::NEUTRAL)
#    classifier.set_effect (roof, dispersion, Classifier::NEUTRAL)
#    classifier.set_effect (roof, elevation, Classifier::FAVORING)
    
    
    
    classifier.train(points.range(training), num_trees=50, max_depth=10)
    
    print("Saving classifier's trained configuration...")
    classifier.save_configuration(outmodel)
    
    # classification map will be overwritten

    if method == 'graphcut':
        print("Classifying with graphcut...")
        classify_with_graphcut(points, labels, classifier,
                               generator.neighborhood().k_neighbor_query(6),
                               0.5,  # strength of graphcut
                               12,   # nb subdivisions (speed up)
                               classification)
    elif method == "smoothing":
        print("Classifying with local smoothing...")
        classify_with_local_smoothing(points, labels, classifier,
                                      generator.neighborhood().k_neighbor_query(6),
                                      classification)
    else:
        print("Classifying with standard algo")
        classify(points, labels, classifier, classification)
    
    
    print("Writing output...")
    
    if args.outCloud == None:
        outcloud = incloud
    points.write(outcloud)
    
    print("Evaluation:")
    evaluation = Evaluation(labels, points.range(training), points.range(classification))

    print(" * Accuracy =", evaluation.accuracy())
    print(" * Mean F1 score =", evaluation.mean_f1_score())
    print(" * Mean IoU =", evaluation.mean_intersection_over_union())
    


# Main routine
    
if args.fixply != None:
    # If this is not generated via cgal....
    fixply(incloud, incloud, args.fixply)
    
outmodel = outcloud[:-3]+"cgalRF.gz"

cgalclassify(incloud, outcloud, rgb=True, method=reg, 
                 outmodel=outmodel, k=12,
                 classes = fields)




