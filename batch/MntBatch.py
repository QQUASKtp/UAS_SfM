#!/home/ciaran/anaconda3/bin/python
# -*- coding: utf-8 -*-
"""
Created on Tue May 29 16:20:58 2018

@author: Ciaran Robb

https://github.com/Ciaran1981/Sfm

This scripts calls the MicMac PIMs2MNT function in chunks for large datasets

This assumes you have done PIMs first on the whole dataset and simply wish to tile the Ortho photos - which is the storage heavy operation

This tiles the datset into a grid then processes in sequence.
As Micmac produces a lot of ancillary data - it is often best with 1000s of images to tile the datset
to avoid filling your hard disk.

Usage: 
    
MntBatch.py -folder $PWD -algo Forest -num 3,3 -zr 0.02 -zoom 4 

"""

#import pandas as pd
import argparse
from subprocess import call
from glob2 import glob
from os import path, mkdir, remove
from shutil import rmtree, move, copyfile
from joblib import Parallel, delayed
parser = argparse.ArgumentParser()

parser.add_argument("-folder", "--fld", type=str, required=True, 
                    help="path to wrkspace")

parser.add_argument("-algo", "--algotype", type=str, required=False, default="BigMac",
                    help="Micmac algo type eg Forest, BigMac, MicMac, QuickMac")

parser.add_argument("-num", "--noCh", type=str, required=False, default='2,2',
                    help="number of tiles in grid form eg 2,2 which is x,y")

parser.add_argument("-zoom", "--zmF", type=str, required=False, default='2', 
                    help="Zoom level - eg 1=1 point per pixel, 2 = 1 point per  4 pixels")

parser.add_argument("-zr", "--zrg", type=str, required=False, default='0.02',
                    help="z reg term context dependent")

parser.add_argument("-ori", "--oRI", type=str, required=False, default="Ground_UTM", 
                    help="ori folder if not the default name of Ground_UTM")

parser.add_argument("-eq", "--egal", type=str, required=False, default='0', 
                    help="Radiometric equalisation either 0 (default) or 1 - entirely context dependent")

#parser.add_argument("-g", "--gp", type=bool, required=False, default=False, 
#                    help="gpu use true or false")

parser.add_argument("-nt", "--noT", type=int, required=False, 
                    help="no of tiles at a time")

parser.add_argument("-max", "--mx", type=int, required=False, 
                    help="max no of chunks to do - this is for testing with a smaller subset")

args = parser.parse_args() 


# These are just vars for convenience and testing

gOri = args.oRI

algo = args.algotype

numChunks = args.noCh

zregu = 'ZReg='+args.zrg
    
zoomF = 'ZoomF='+args.zmF
 
# This will likely become redundant   
if args.gp is None:
    mmgpu = 'mm3d'
else:
    mmgpu = '/home/ciaran/MicMacGPU/micmac/bin/mm3d'
    
#if args.noT is None:
#    mp = 4 
#else:
#    mp = args.noT

                        
#maxIm = args.noIm2

fld = args.fld

imList = glob(path.join(fld, '*.JPG'))

imList.sort()

#sections = chunkIt(imList, numChunks)
#subList = imList[minIm:maxIm]

DMatch = path.join(args.fld, 'DMatch')
bFolder = path.join(args.fld, 'PIMsBatch')
distMatch = path.join(args.fld, 'DistributedMatching.xml')

binList = [DMatch, bFolder]

for crap in binList:
    try:       
        rmtree(crap)
        
    except OSError:
        pass

try:
    remove(distMatch)
except OSError:
        pass

mkdir(bFolder)
# run tiling
tileIt = ['tile.py', '-i', 'Ori-'+gOri, '-e',
            'JPG', '-f', 'DMatch', '-n',
            numChunks]

call(tileIt)


pishList = [path.join(fld, 'PIMs-TmpBasc'),
            path.join(fld, 'PIMs-ORTHO'),
            path.join(fld, 'PIMs-TmpMnt'),
            path.join(fld, 'PIMs-TmpMntOrtho')]


txtList = glob(path.join(DMatch,'*.list'))
nameList = [path.split(i)[1] for i in txtList]
txtList.sort()
nameList.sort()
finalList = list(zip(txtList, nameList))

# Some very ugly stuff going on in here

#if gpu is true
for subList in txtList:
#def procPims(subList, bFolder):
    flStr = open(subList).read()
    flStr.replace("\n", "|")
    flStr = open(subList).read()
    # first we need the box terrain line
    box = flStr.split('\n', 1)[0]
    # then the images
    imgs = flStr.split("\n", 1)[1]

    imgs.replace("\n", "|")
    sub = imgs.replace("\n", "|")
    print('the img subset is \n'+sub+'\n\n')                 

    
    hd, tl = path.split(subList)
    subDir = path.join(bFolder, tl)
    mkdir(subDir)
    
    
    mnt = ['mm3d', 'PIMs2MNT', algo, 'Pat='+'."'+sub+'"', 'DoOrtho=1', zregu]
    call(mnt)
  
    tawny = ['mm3d', 'Tawny', 'PIMs-ORTHO/', 'RadiomEgal='+args.egal,# 'DegRap=4',
             'Out=Orthophotomosaic.tif']
    call(tawny)
    
    conIm = ['mm3d', 'ConvertIm', 'PIMs-ORTHO/Orthophotomosaic.tif', 'Out=PIMs-ORTHO/OrthFinal.tif']
    call(conIm)
    
    
    copyfile(path.join(args.fld, 'PIMs-ORTHO',  'Orthophotomosaic.tfw'),
             path.join(args.fld, subDir,  'OrthFinal.tfw'))
    copyfile(path.join(args.fld, 'PIMs-ORTHO',  'OrthFinal.tif'),
             path.join(args.fld, subDir,  'OrthFinal.tif'))

    newOrtho = path.join(subDir, 'OrthFinal.tif')

    
    Parallel(n_jobs=-1, verbose=5)(delayed(rmtree)(pish) for pish in pishList)
    # mm3d does not remove it's leftovers in forest mode.....
   
        
    

    


#if args.mx is None:
#    todoList = Parallel(n_jobs=mp,verbose=5)(delayed(proc_malt)(i[0], 
#         i[1], bFolder, bbox=args.bb) for i in finalList) 
#else:
#    subFinal = finalList[0:args.mx]
    
#if args.mx is None:
#    [procPims(f, bFolder) for f in txtList]
##    todoList = Parallel(n_jobs=mp,verbose=5)(delayed(procPims)(i,
##                        bFolder) for i in txtList)
#
#else:
#    subFinal = txtList[0:args.mx]
#    [procPims(f, bFolder) for f in subFinal]
#    todoList = Parallel(n_jobs=mp,verbose=5)(delayed(procPims)( 
#             i, bFolder) for i in subFinal) 

