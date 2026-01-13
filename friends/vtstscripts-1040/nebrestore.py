#!/usr/bin/env python3

# usage: nebrestore.py rundirectory imgstart imgend
# example:   nebrestore.py run1 00 06 
# this will overwrite the current directory 00 to 06 POSCAR with POSCAR from run1/00 to run1/06

import sys,os,shutil

if len(sys.argv) != 4:
  print("Incorrect number of arguments given! usage: nebrestore.py rundirectory imgstart imgend")
  exit()

rundir = sys.argv[1]
startimg = sys.argv[2]
endimg = sys.argv[3]

if not os.path.isdir(rundir) :
  print(rundir + " does not exist! exiting")
  exit()

if isinstance(startimg,int) :
  print("starting image must be an integer!") 
  exit()

if isinstance(endimg,int) :
  print("ending image must be an integer!")
  exit()

if len(startimg) == 1:
  startimg = startimg.zfill(2)

if len(endimg) == 1: 
  endimg = endimg.zfill(2)

if not os.path.isdir(rundir + "/"+startimg):
  print("Error! " + rundir + "/" + str(startimg) + " does not exist!")
  exit()

if not os.path.isdir(rundir + "/"+endimg):
  print("Error! " + rundir + "/" + str(endimg) + " does not exist!")
  exit()

if not os.path.isdir(startimg):
  print("Error! " + str(startimg) + " does not exist!")
  exit()

if not os.path.isdir(endimg):
  print("Error! " + str(endimg) + " does not exist!")
  exit()

print("restoring the NEB band to using POSCAR from " + rundir + " " + startimg + " to " + endimg)

for img in range(int(startimg),int(endimg)+1):
  img = str(img)
  img = img.zfill(2)
  shutil.copy(rundir+"/"+img+"/"+"POSCAR",img) 
  
 
