#!/usr/bin/env python3
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from actions_py.bootstrap import ensure_repo_root

ensure_repo_root()
#Writen By Qiang 
# Get the dband center using the XXX.dat from dos_extract.py script
import numpy as np
import sys
if len(sys.argv) not in (2, 4):
    print('Command Usage: dcenter.py file [start end]')
    sys.exit(1)
file_in = sys.argv[1]
data = np.loadtxt(file_in, ndmin=2)
if data.shape[1] not in (2, 3):
    raise ValueError("Expected energy and one or two DOS columns")
start, end = (data[0, 0], data[-1, 0]) if len(sys.argv) == 2 else map(float, sys.argv[2:])

def integer_ele(x,y):
    interval = x[1] - x[0]
    sum_y = y[1] + y[0]
    sum_xy = x[1] * y[1] + x[0] * y[0] 
    ele_lower = 0.5 * interval * sum_y 
    ele_upper = 0.5 * interval * sum_xy 
    return ele_lower, ele_upper 

def integer_array(x,y):
    intervals = np.diff(x)
    sum_lower = np.sum(0.5 * intervals * (y[1:] + y[:-1]))
    weighted = x * y
    sum_upper = np.sum(0.5 * intervals * (weighted[1:] + weighted[:-1]))
    return sum_upper / sum_lower, sum_lower


def get_dat_range(x, start, end):
    l_start = [] 
    l_end = []
    for i, value  in enumerate(x):
        if value >= start:
            l_start.append(i)  # abbriviation for index_start 
        if value >= end:
            l_end.append(i)  # abbriviation for index_start 
    index_s = l_start[0]
    index_e = l_end[0]
    return index_s, index_e   

ISPIN = data.shape[1] - 1
x_in = data[:, 0]
index_s, index_e = get_dat_range(x_in, start, end)
x = x_in[index_s:index_e]

if ISPIN == 1: 
    y_in = data[:, 1]
    y = y_in[index_s: index_e]
    d_center, num_elec = integer_array(x, y)
    print( 'd-band center is %s' %(d_center)  )
    print( 'electron counting %s' %(num_elec) )
elif ISPIN == 2 : 
    y1_in, y2_in = data[:, 1], data[:, 2]
    y1 = y1_in[index_s: index_e]
    y2 = y2_in[index_s: index_e]
    d_center1, num_elec1 = integer_array(x, y1)
    d_center2, num_elec2 = integer_array(x, y2)
    print(  'd-band center for SPIN-1 is %10.6f ' %(d_center1) )
    print(  'd-band center for SPIN-2 is %10.6f ' %(d_center2) )
    print(  'd-band_average is %10.6f'            %((d_center1 + d_center2) / 2) )
 
    print(  'Electron counting for ISPIN-1 is %10.6f ' %(num_elec1) )
    print(  'Electron counting for ISPIN-2 is %10.6f ' %(num_elec2) )
    print(  'Total Electron is %10.6f ' %((num_elec1 + num_elec2))  )
