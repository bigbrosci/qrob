#!/usr/bin/env python3
import os
import re
import sys
from ase import Atoms
from ase.io import read,Trajectory
from ase.visualize import view

#usage: agnebmovie.py 0 or 1 
# 0 for visualizing POSCARs, 1 for visualizing CONTCARs

def main():
  mode = int(sys.argv[1])
  # List 2-digit directories in CWD
  pat = re.compile(r"^\d\d$")
  dirs = [d for d in os.listdir(".") if os.path.isdir(d) and pat.match(d)]
  if not dirs:
      die("No 2-digit image directories (00–99) found in current directory.")

  # Sort numerically ascending (00, 01, 02, ...)
  dirs = sorted(dirs, key=lambda s: int(s))
  imgmax = max(dirs, key=lambda s: int(s))

  with Trajectory("neb.traj",'w') as traj:
    for i in range(0,int(imgmax)+1):
      if i == 0:
        atoms = read(f"{int(i):02d}"+"/POSCAR")
      elif i == int(imgmax):
        atoms = read(f"{int(i):02d}"+"/POSCAR")
      else:
        if mode == 0:
          atoms = read(f"{int(i):02d}"+"/POSCAR")
        elif mode == 1:
          atoms = read(f"{int(i):02d}"+"/CONTCAR")
      traj.write(atoms)
  traj.close()
  images = read("neb.traj",":")
  view(images)  

if __name__ == "__main__":
    main()

