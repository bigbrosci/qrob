#!/usr/bin/env python3
import os
dict_element = {'1':'H','2':'He','3':'Li','4':'Be','5':'B','6':'C','7':'N','8':'O','9':'F','10':'Ne','11':'Na','12':'Mg','13':'Al','14':'Si','15':'P','16':'S','17':'Cl','18':'Ar','19':'K','20':'Ca','21':'Sc','22':'Ti','23':'V','24':'Cr','25':'Mn','26':'Fe','27':'Co','28':'Ni','29':'Cu','30':'Zn','31':'Ga','32':'Ge','33':'As','34':'Se','35':'Br','36':'Kr','37':'Rb','38':'Sr','39':'Y','40':'Zr','41':'Nb','42':'Mo','43':'Tc','44':'Ru','45':'Rh','46':'Pd','47':'Ag','48':'Cd','49':'In','50':'Sn','51':'Sb','52':'Te','53':'I','54':'Xe','55':'Cs','56':'Ba','57':'La','58':'Ce','59':'Pr','60':'Nd','61':'Pm','62':'Sm','63':'Eu','64':'Gd','65':'Tb','66':'Dy','67':'Ho','68':'Er','69':'Tm','70':'Yb','71':'Lu','72':'Hf','73':'Ta','74':'W','75':'Re','76':'Os','77':'Ir','78':'Pt','79':'Au','80':'Hg','81':'Tl','82':'Pb','83':'Bi','84':'Po','85':'At','86':'Rn','87':'Fr','88':'Ra','89':'Ac','90':'Th','91':'Pa','92':'U','93':'Np','94':'Pu','95':'Am','96':'Cm','97':'Bk','98':'Cf','99':'Es','100':'Fm','101':'Md','102':'No','103':'Lr','104':'Rf','105':'Db','106':'Sg','107':'Bh','108':'Hs','109':'Mt',}

#### Part-0 Dictionaries
atomic_mass = dict(H=1.01, He=4.00, Li=6.94, Be=9.01, B=10.81, C=12.01,
                   N=14.01, O=16.00, F=19.00, Ne=20.18, Na=22.99, Mg=24.31,
                   Al=26.98, Si=28.09, P=30.97, S=32.07, Cl=35.45, Ar=39.95,
                   K=39.10, Ca=40.08, Sc=44.96, Ti=47.87, V=50.94, Cr=52.00,
                   Mn=54.94, Fe=55.85, Co=58.93, Ni=58.69, Cu=63.55, Zn=65.39,
                   Ga=69.72, Ge=72.61, As=74.92, Se=78.96, Br=79.90, Kr=83.80,
                   Rb=85.47, Sr=87.62, Y=88.91, Zr=91.22, Nb=92.91, Mo=95.94,
                   Tc=98.00, Ru=101.07, Rh=102.91, Pd=106.42, Ag=107.87,
                   Cd=112.41, In=114.82, Sn=118.71, Sb=121.76, Te=127.60,
                   I=126.90, Xe=131.29, Cs=132.91, Ba=137.33, La=138.91,
                   Ce=140.12, Pr=140.91, Nd=144.24, Pm=145.00, Sm=150.36,
                   Eu=151.96, Gd=157.25, Tb=158.93, Dy=162.50, Ho=164.93,
                   Er=167.26, Tm=168.93, Yb=173.04, Lu=174.97, Hf=178.49,
                   Ta=180.95, W=183.84, Re=186.21, Os=190.23, Ir=192.22,
                   Pt=195.08, Au=196.97, Hg=200.59, Tl=204.38, Pb=207.2,
                   Bi=208.98, Po=209.00, At=210.00, Rn=222.00, Fr=223.00,
                   Ra=226.00, Ac=227.00, Th=232.04, Pa=231.04, U=238.03,
                   Np=237.00, Pu=244.00, Am=243.00, Cm=247.00, Bk=247.00,
                   Cf=251.00, Es=252.00, Fm=257.00, Md=258.00, No=259.00,
                   Lr=262.00, Rf=261.00, Db=262.00, Sg=266.00, Bh=264.00,
                   Hs=269.00, Mt=268.00)

## Crystal structure of elements: from https://en.wikipedia.org/wiki/Periodic_table_(crystal_structure)
bcc = ['V',  'Cr', 'Mn', 'Fe', 'Nb', 'Pb']
hcp = ['Mg', 'Sc', 'Ti', 'Co', 'Zn', 'Y', 'Zr', 'Tc', 'Ru', 'Cd', 'Hf', 'Re', 'Os']
fcc = ['Al', 'Ca', 'Ni', 'Cu', 'Rh', 'Pd', 'Ag', 'Ir', 'Pt', 'Au']

### Metal  Bulk structures from DFT_D2 
dict_metals_vdWD3zero           = {
'Ag':(-12.83721745,4,4.0711,4.0711),
'Co':(-14.76776158,2,2.4729,3.9814),
'Cu':(-16.95007138,4,3.5683,3.5683),
'Fe':(-17.09658076,2,2.8068,2.8068),
'Ir':(-38.24513552,4,3.8377,3.8377),
'Ni':(-23.4791717,4,3.4744,3.4744),
'Os':(-23.64822617,2,2.7331,4.3278),
'Pd':(-23.17971002,4,3.8822,3.8822),
'Pt':(-27.46886041,4,3.9171,3.9171),
'Rh':(-31.41993461,4,3.7845,3.7845),
'Ru':(-19.62094079,2,2.6903,4.2535),
} 

## The user need to modify it by him/herself  <<<  VERT IMPORTTANT!!! 
u_value = {
'Ag': 5.0,
'Cu': 5.0,
'Fe': 5.0,
'Ir': 5.0,
'Ni': 5.0,
'Pd': 5.0,
'Pt': 5.0,
'Rh': 5.0,
'Co': 5.0,
'Ru': 5.0,
'Os': 5.0,        
'Au': 5.0,        
'Ti': 5.1,
'Zn': 5.0,
'Sn': 5.0,
}

j_value = {
'Ag': 1.0,
'Cu': 1.0,
'Fe': 1.0,
'Ir': 1.0,
'Ni': 1.0,
'Pd': 1.0,
'Pt': 1.0,
'Rh': 1.0,
'Co': 1.0,
'Ru': 1.0,
'Os': 1.0,
'Au': 1.0,
'Ti': 1.0,        
'Zn': 1.0,        
'Sn': 1.0,        
}

#### Information about the potcar databse 
def get_potcar_data():
    home = os.path.expanduser('~')
    data_potcars_file = home + '/bin/q-robot/books/potpaw_PBE.52/data_potcars'
    file_in = open(data_potcars_file, 'r')
    data = file_in.read()
    file_in.close()
    return eval(data)    


def save_dict_csv(dict_in, name):
    import csv
    out_name = name + '.csv'
    w = csv.writer(open(out_name, 'w'))
    for key, val in dict.items():
        w.writerow([key,val]) 

def save_dict_json(dict_in, name):
    import json 
    out_name = name + '.json'
    json = json.dumps(dict_in)
    f = open(out_name, 'w')
    f.write(json)
    f.close()

def save_dict_txt(dict_in, name):
    out_name = name + '.txt'
    f = open(out_name, 'w')
    f.write(str(dict_in))
    f.close()


def eval_dict_txt(file_in):
    dict_txt  = eval(open(file_in).read())
    return dict_txt

def eval_dict_csv(file_in):
    import csv
    dict_csv = {}
    with open('example.csv') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        for row in reader:
            dict_csv.update({row[0]:row[1:]})
    return dict_csv

def eval_dict_json(file_in):
    import json
    with open(file_in) as f:
      dict_json = json.load(f)
    return dict_json


