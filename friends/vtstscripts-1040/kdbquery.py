#!/usr/bin/env python
import os, subprocess
import shutil
import sys
from kdb_remote_client import run as remote_run
from kdb_local_client import run as local_run
from ase.io import read, write

#Get the users specified flags
def get_options():
    local_query = False
    setup = False
    movie = False
    user_config = False
    structure = None
    for i in sys.argv:
        if i == sys.argv[0]:
            continue
        else:
            if i =="-l":
                local_query = True
            elif i=="-s":
                setup =  True
            elif i =="-m":
                movie = True
            elif i =="-c":
                user_config = True
            else:
                if structure is None:
                    structure = i
                else:
                    sys.exit("WARNING: multiple query structures provided")

    #print("Local Query: ", local_query)
    #print("Set Up: ",setup)
    #print("Movie: ",movie)
    #print("User Config: ",user_config)
    if structure is None:
        sys.exit("FAILED: please provide a structure to query")
    return local_query,setup,movie,user_config,structure

#Query the Database (optional -l) #NK pass query structure since its not global anymore
def query_db(local_query,user_config,query_structure):
    if local_query: #additional check 
        query_kdb = (local_run(["query",query_structure]))
        #print(query_kdb)
    else:
        if user_config:
            query_kdb = ( remote_run(["query",query_structure,"-c"]))
        else:
            query_kdb = ( remote_run(["query",query_structure]))
    #print ("Local Query: ",local_query)
    #os.system(query_kdb)


def edit_INCAR_for_dimer(total_path,flag,value):
    with open(total_path, "r") as f:
        lines = f.readlines()
    change_line = 0
    with open(total_path, "w") as f:
        for line in lines:
            if line.startswith(flag):
                f.write(flag+ " = "+value+"\n")
                change_line = 1
            else:
                f.write(line)
        if change_line == 0:
            f.write(flag+ " = "+value+"\n")
        f.close()
    return 0

#Set Up Flag (-s)
def set_up_calculation():
    num_kdb_processes = 0
    for file in os.listdir(path_initial+"/kdbmatches"):
        if (file[0] == 'P'):
            num_kdb_processes +=1
    print("Suggested KDB Processes: ",num_kdb_processes)
    os.chdir(path_initial+"/kdbmatches")
    for i in range(num_kdb_processes):
        sug_dir = ("KDB"+str(i))
        prod_dir = ("PRODUCT"+str(i))
        sad_dir = ("SADDLE"+str(i))
        os.mkdir(sug_dir)
        os.chdir(sug_dir)
        os.mkdir(sad_dir)
        os.mkdir(prod_dir)
        shutil.copyfile(path_initial+"/INCAR","./"+prod_dir+"/INCAR")
        shutil.copyfile(path_initial+"/KPOINTS","./"+prod_dir+"/KPOINTS")
        shutil.copyfile(path_initial+"/POTCAR","./"+prod_dir+"/POTCAR")
        shutil.copyfile(path_initial+"/kdbmatches/PRODUCT_"+str(i),"./"+prod_dir+"/POSCAR")
        shutil.copyfile(path_initial+"/INCAR","./"+sad_dir+"/INCAR")
        shutil.copyfile(path_initial+"/KPOINTS","./"+sad_dir+"/KPOINTS")
        shutil.copyfile(path_initial+"/POTCAR","./"+sad_dir+"/POTCAR")
        shutil.copyfile(path_initial+"/kdbmatches/SADDLE_"+str(i),"./"+sad_dir+"/POSCAR")
        if (os.path.exists(path_initial+"/kdbmatches/MODE_"+str(i))):
            shutil.copyfile(path_initial+"/kdbmatches/MODE_"+str(i),"./"+sad_dir+"/MODE")
        else:
            print("MODE not given")
        os.chdir(sad_dir) # Now go into the SADDLE_i directory to edit INCAR with DIMER FLAGS
        edit_INCAR_for_dimer("INCAR","IBRION","3")
        edit_INCAR_for_dimer("INCAR","POTIM","0.0")
        edit_INCAR_for_dimer("INCAR","ICHAIN","2")
        edit_INCAR_for_dimer("INCAR","EDIFF","1E-7")
        edit_INCAR_for_dimer("INCAR","IOPT","2")#2 is recommended 
        os.chdir(path_initial+"/kdbmatches")
    os.chdir(path_initial) # Not taking any risk, at /home/calculation directory
    return 0

# create a movie of each predicted mechanism
def movie_of_reaction():
    num_kdb_processes = 0
    for file in os.listdir(path_initial+"/kdbmatches"):
        if (file[0] == 'P'):
            num_kdb_processes +=1
    reactant=read(query_structure,format='vasp')
    os.chdir(path_initial+"/kdbmatches")
    for i in range(num_kdb_processes):
        filename = "PROCESS_"+str(i)
        temp_saddle=read("SADDLE_"+str(i), format='vasp')
        temp_product=read("PRODUCT_"+str(i), format='vasp')
        write(filename,reactant,format='vasp')
        write(filename,temp_saddle,append=True,format='vasp')
        write(filename,temp_product,append=True,format='vasp')
    return 0

#query_structure = sys.argv[1] #NK do not need this anymore
path_initial = os.getcwd() # path of directory from where it is run
this_script_path = os.path.dirname(os.path.abspath(__file__)) # vtstscripts path


def main():
    query, user_set_up_calculation, user_movie_setup, user_config, query_structure = get_options() 
    #NI = get_saddle_image_number_and_barriers(path_initial)
    query_db(query,user_config,query_structure)
    if user_set_up_calculation:
        set_up_calculation()    
    if user_movie_setup:
        movie_of_reaction()
    #print ("END")
    return 0

main()
