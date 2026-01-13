#!/usr/bin/env python
import subprocess
import os 
import numpy
import sys
from kdb_remote_client import run as remote_run
from kdb_local_client import run as local_run
from kdb.aselite import read_vasp
from kdb.aselite import Atoms  # def get_distance(self, a0, a1, mic=False):
#Should find the reactant,saddle,product,compute the forward and reverse barriers, and submit it in the the correct format

#CODE :
#Get numbers of images in system
# for each image: append its energy to array, find max of array ->saddle energy, submit process to kdb

def get_saddle_image_number_and_barriers(path):
    #num_img = ( 'grep "IMAGES" INCAR | tail -n 1|cut -c 8-106')
    num_img = ( 'grep "IMAGES" INCAR | tail -n 1')
    eng_img = ('grep -a "energy  without" OUTCAR | tail -n 1|cut -c 67-78')
    temp_NI = (subprocess.check_output(num_img, shell=True).decode("utf-8"))
    temp_NI  = temp_NI.strip()
    temp_NI = temp_NI.split('=')
    NI = int(temp_NI[-1])
    Energy_All = []#Array to store energy of each image including reactant and product
    for i in range(0,NI+2):
        if i < 10:
            s = "/0"+str(i)
        else:
            s = "/"+str(i)
        os.chdir(path+s)
        try:
          if "OUTCAR.gz" in os.listdir():
            os.system("gunzip OUTCAR.gz")
          if "OUTCAR" in os.listdir():
            pass
        except:
          print ("No OUTCAR or OUTCAR.gz in directory")
        energy_image = float(subprocess.check_output(eng_img, shell=True))
        Energy_All.append(energy_image)
        Sadd_Img = numpy.where(Energy_All==numpy.amax(Energy_All))[0][0]#get index of max of images
    forward_barrier = (numpy.amax(Energy_All)-Energy_All[0])
    reverse_barrier = (numpy.amax(Energy_All)-Energy_All[NI+1])
    print ("forward_barrier: ",forward_barrier)
    print ("reverse_barrier: ",reverse_barrier)
    print ("The saddle is image "+ str( Sadd_Img))
    return Sadd_Img, NI, forward_barrier, reverse_barrier

#state_i = (read_vasp('MIN_1'))	
#state_j = (read_vasp('MIN_2'))

def get_mode(before_saddle,after_saddle):
    #print ("Entered get_mode function")
    mode = []
    before_saddle = (read_vasp(before_saddle))
    a_saddle = (read_vasp(after_saddle))
    #print ("State I Cell: ",before_saddle.get_cell())
    #print ("State I Cell[0]: ",before_saddle.get_cell()[0])
    #print ("State J: ",saddle.get_positions())
    Saddle_Half_Cell = numpy.linalg.norm(a_saddle.get_cell())/2
    movement = a_saddle.get_positions()-before_saddle.get_positions()
    #print ("Movement: ",movement)
    # NEED TO FINISH THIS CODE, How exactly to account for PBC?
    for i in range(len(movement)):
        Dr = numpy.linalg.solve(a_saddle.get_cell().T, movement[i])
        D = numpy.dot(Dr - numpy.round(Dr) * a_saddle.get_pbc(), a_saddle.get_cell())
        movement[i] = D
    mode = movement
    #print ("Mode: ",mode)
    return mode

#allows users to add -l in arguments in case they wish to create a local kdb
def get_options():
    local_insert = False
    for i in sys.argv:
        if i =="-l":
            local_insert = True
    print("Local Insert: ", local_insert)
    return local_insert

path = os.getcwd()#Get the path from where the script is run

def main():
    Saddle_Image, NI, b_f, b_r = get_saddle_image_number_and_barriers(path)
    reactant = path+"/00/POSCAR"
    if Saddle_Image < 10:
        saddle = path+"/0"+str(Saddle_Image)+"/CONTCAR"
    else:
        saddle = path+"/"+str(Saddle_Image)+"/CONTCAR"
    if NI < 9:
        product = path+"/0"+str(NI+1)+"/POSCAR"
    else:
        product = path+"/"+str(NI+1)+"/POSCAR"
    #print (reactant)
    #print (saddle)
    #print (product)
    if Saddle_Image > NI: #Product is the highest energy image
        if NI < 10:
            mode = get_mode(path+"/0"+str(NI)+"/CONTCAR",product)
        else:
            mode = get_mode(path+"/"+str(NI)+"/CONTCAR",product)
    elif Saddle_Image == NI:  # highest energy image is 2nd to the last
        if Saddle_Image < 11:
            mode = get_mode(path+"/0"+str(Saddle_Image-1)+"/CONTCAR",product)
        else:
            mode = get_mode(path+"/"+str(Saddle_Image-1)+"/CONTCAR",product)
    elif Saddle_Image == 1:
        after_saddle = path+"/02/CONTCAR"
        mode = get_mode(reactant,after_saddle)
    # not considering the case where Saddle_Image == 0
    else: #Case that a middle image is the highest energy image
        if Saddle_Image < 9:
            after_saddle = path+"/0"+str(Saddle_Image+1)+"/CONTCAR"
        else:
            after_saddle = path+"/"+str(Saddle_Image+1)+"/CONTCAR"
        if Saddle_Image < 11:
            mode = get_mode(path+"/0"+str(Saddle_Image-1)+"/CONTCAR",after_saddle)
        else:
            mode = get_mode(path+"/"+str(Saddle_Image-1)+"/CONTCAR",after_saddle)
    #print ("Mode: ",mode)
    os.chdir(path)#Ensure Back at original path
    f = open("MODE.dat", "w")
    for i in range (len(mode)):
       for j in range (3):
        f.write(str(mode[i][j])+"\t")
        if j ==2:
           f.write("\n")
    path_mode = path+"/MODE.dat"
    f.close()
    local_insert = get_options()
    if local_insert:
        insert_kdb = (local_run(["insert", reactant, saddle, product, path_mode, b_f, b_r]))
        #insert_kdb = (local_run(["insert",reactant,saddle,product]))
    else:
        #insert_kdb = (remote_run(["insert",reactant,saddle,product,mode])) 
        insert_kdb = (remote_run(["insert", reactant, saddle, product, path_mode, b_f, b_r])) 
    return 0

main()

