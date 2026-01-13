#!/usr/bin/env python3

# usage: neb_apply_constraintemplate.py POSCAR startimg endimg
# mode_a can be constrain or unconstrain
# mode can be inclusive or exclusive
# example:   nebconstrain.py inclusive 00 06 14 58 99 
# this will edit the POSCARs from 00 to 06 and add constrain to atom 14 58 99
# note that the atomic index starts at 0 !

# note, exclusive and unconstrain is not implemented yet

import sys,os
import ase, ase.io, ase.constraints

#if len(sys.argv) < 6:
#  print("Incorrect number of arguments given! usage: nebconstrain.py constrain/unconstrain inclusive/exclusive imgstart imgend atomic_indexes")

#isconstrain = sys.argv[1]=='constrain'
#isinclusive = sys.argv[2]=='inclusive'
poscar = sys.argv[1]
startimg = sys.argv[2]
endimg = sys.argv[3]



if len(startimg) == 1:
  startimg = startimg.zfill(2)

if len(endimg) == 1: 
  endimg = endimg.zfill(2)

#with open("nebconstrain_memo","w") as memo:
#  memo.writelines("Newly added constraints are ")
#  memo.write(" ".join(str(x) for x in indexes))
#  memo.writelines("Existing constraints are")
#  atoms = ase.io.read(startimg+"/POSCAR",format='vasp')
#  cons = atoms.constraints
#  memo.write(" ".join(str(x) for x in cons))

atoms = ase.io.read(poscar,format="vasp")
cons = atoms.constraints
cons_list = list(cons) if isinstance(cons, (list, tuple)) else ([cons] if cons else [])

for img in range(int(startimg),int(endimg)+1):
  img = str(img)
  img = img.zfill(2)
  atoms = ase.io.read(img+"/POSCAR",format='vasp')
  atoms.set_constraint(cons_list)  
  ase.io.write(img+"/POSCAR",atoms,format="vasp") 
 
