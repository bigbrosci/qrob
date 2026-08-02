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

dict_metals           = {    # Lattice Parameter from vdw_D3
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

### Convert CH3OH to 1412
dict_l = {
    '1312': 'HOCH2', '1300': 'CH3', '1212': 'HOCH', '1211': 'OCH2',
    '1200': 'CH2', '1112': 'HOC', '1111': 'OCH', '1100': 'CH',
    '1011': 'OC', '1000': 'C', '0000': '0000',
}
dict_r = {
    '1312': 'CH2OH', '1300': 'CH3', '1212': 'CHOH', '1211': 'CH2O',
    '1200': 'CH2', '1112': 'COH', '1111': 'CHO', '1100': 'CH',
    '1011': 'CO', '1000': 'C', '0000': '0000',
}


## The user need to modify it by him/herself  <<<  VERT IMPORTTANT!!! 
### DFT + U 
u_value = {
    'Ag': 5.0, 'Cu': 5.0, 'Fe': 5.0, 'Ir': 5.0, 'Ni': 5.0, 'Pd': 5.0,
    'Pt': 5.0, 'Rh': 5.0, 'Co': 5.0, 'Ru': 5.0, 'Os': 5.0, 'Au': 5.0,
    'Ti': 5.1, 'Zn': 5.0, 'Sn': 5.0
}

j_value = {
    'Ag': 1.0, 'Cu': 1.0, 'Fe': 1.0, 'Ir': 1.0, 'Ni': 1.0, 'Pd': 1.0,
    'Pt': 1.0, 'Rh': 1.0, 'Co': 1.0, 'Ru': 1.0, 'Os': 1.0, 'Au': 1.0,
    'Ti': 1.0, 'Zn': 1.0, 'Sn': 1.0
}

### SPIN & MAG
mag_value = {
    'H': 0.0, 'He': 0.0,
    'Li': 0.0, 'Be': 0.0, 'B': 0.0, 'C': 0.0, 'N': 0.0, 'O': 0.0, 'F': 0.0, 'Ne': 0.0,
    'Na': 0.0, 'Mg': 0.0, 'Al': 0.0, 'Si': 0.0, 'P': 0.0, 'S': 0.0, 'Cl': 0.0, 'Ar': 0.0,
    'K': 0.0, 'Ca': 0.0,
    'Sc': 0.0, 'Ti': 0.0, 'V': 1.0, 'Cr': 1.0, 'Mn': 4.0, 'Fe': 3.0, 'Co': 2.0, 'Ni': 1.0,
    'Cu': 0.0, 'Zn': 0.0, 'Ga': 0.0, 'Ge': 0.0, 'As': 0.0, 'Se': 0.0, 'Br': 0.0, 'Kr': 0.0,
    'Rb': 0.0, 'Sr': 0.0,
    'Y': 0.0, 'Zr': 0.0, 'Nb': 0.0, 'Mo': 0.0, 'Tc': 1.0, 'Ru': 1.0, 'Rh': 1.0, 'Pd': 0.0,
    'Ag': 0.0, 'Cd': 0.0, 'In': 0.0, 'Sn': 0.0, 'Sb': 0.0, 'Te': 0.0, 'I': 0.0, 'Xe': 0.0,
    'Cs': 0.0, 'Ba': 0.0,
    'La': 0.0, 'Ce': 1.0, 'Pr': 2.0, 'Nd': 3.0, 'Pm': 4.0, 'Sm': 5.0, 'Eu': 7.0, 'Gd': 7.0,
    'Tb': 6.0, 'Dy': 5.0, 'Ho': 4.0, 'Er': 3.0, 'Tm': 2.0, 'Yb': 1.0, 'Lu': 0.0,
    'Hf': 0.0, 'Ta': 0.0, 'W': 0.0, 'Re': 0.0, 'Os': 1.0, 'Ir': 1.0, 'Pt': 0.0, 'Au': 0.0,
    'Hg': 0.0, 'Tl': 0.0, 'Pb': 0.0, 'Bi': 0.0, 'Po': 0.0, 'At': 0.0, 'Rn': 0.0,
    'Fr': 0.0, 'Ra': 0.0,
    'Ac': 0.0, 'Th': 0.0, 'Pa': 1.0, 'U': 2.0, 'Np': 3.0, 'Pu': 4.0, 'Am': 5.0, 'Cm': 6.0,
    'Bk': 5.0, 'Cf': 4.0, 'Es': 3.0, 'Fm': 2.0, 'Md': 1.0, 'No': 0.0, 'Lr': 0.0,
    'Rf': 0.0, 'Db': 0.0, 'Sg': 0.0, 'Bh': 0.0, 'Hs': 0.0, 'Mt': 0.0, 'Ds': 0.0, 'Rg': 0.0,
    'Cn': 0.0, 'Nh': 0.0, 'Fl': 0.0, 'Mc': 0.0, 'Lv': 0.0, 'Ts': 0.0, 'Og': 0.0,
} 

#### Information about the potcar databse 

def save_dict_csv(dict_in, name):
    import csv
    out_name = name + '.csv'
    with open(out_name, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        for key, val in dict_in.items():
            writer.writerow([key, val])

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
    with open(file_in) as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        for row in reader:
            dict_csv.update({row[0]: row[1:]})
    return dict_csv

def eval_dict_json(file_in):
    import json
    with open(file_in) as f:
      dict_json = json.load(f)
    return dict_json



#### Cohesive Energy (eV/atom) - from http://www.knowledgedoor.com/2/elements_handbook/cohesive_energy.html
cohesive_energy = {
    'Actinium': 4.25, 'Aluminum': 3.39, 'Americium': 2.73, 'Antimony': 2.75, 'Argon': 0.08,
    'Arsenic': 2.96, 'Barium': 1.9, 'Beryllium': 3.32, 'Bismuth': 2.18, 'Boron': 5.81,
    'Bromine': 1.22, 'Cadmium': 1.16, 'Calcium': 1.84, 'Carbon': 7.37, 'Cerium': 4.32,
    'Cesium': 0.804, 'Chlorine': 1.4, 'Chromium': 4.1, 'Cobalt': 4.39, 'Copper': 3.49,
    'Curium': 3.99, 'Dysprosium': 3.04, 'Erbium': 3.29, 'Europium': 1.86, 'Fluorine': 0.84,
    'Gadolinium': 4.14, 'Gallium': 2.81, 'Germanium': 3.85, 'Gold': 3.81, 'Hafnium': 6.44,
    'Holmium': 3.14, 'Indium': 2.52, 'Iodine': 1.11, 'Iridium': 6.94, 'Iron': 4.28,
    'Krypton': 0.116, 'Lanthanum': 4.47, 'Lead': 2.03, 'Lithium': 1.63, 'Lutetium': 4.43,
    'Magnesium': 1.51, 'Manganese': 2.92, 'Mercury': 0.67, 'Molybdenum': 6.82, 'Neodymium': 3.4,
    'Neon': 0.02, 'Neptunium': 4.73, 'Nickel': 4.44, 'Niobium': 7.57, 'Nitrogen': 4.92,
    'Osmium': 8.17, 'Oxygen': 2.6, 'Palladium': 3.89, 'Phosphorus': 3.43, 'Platinum': 5.84,
    'Plutonium': 3.6, 'Polonium': 1.5, 'Potassium': 0.934, 'Praseodymium': 3.7, 'Radium': 1.66,
    'Radon': 0.202, 'Rhenium': 8.03, 'Rhodium': 5.75, 'Rubidium': 0.852, 'Ruthenium': 6.74,
    'Samarium': 2.14, 'Scandium': 3.9, 'Selenium': 2.46, 'Silicon': 4.63, 'Silver': 2.95,
    'Sodium': 1.113, 'Strontium': 1.72, 'Sulfur': 2.85, 'Tantalum': 8.1, 'Technetium': 6.85,
    'Tellurium': 2.19, 'Terbium': 4.05, 'Thallium': 1.88, 'Thorium': 6.2, 'Thulium': 2.42,
    'Tin': 3.14, 'Titanium': 4.85, 'Tungsten': 8.9, 'Uranium': 5.55, 'Vanadium': 5.31,
    'Xenon': 0.16, 'Ytterbium': 1.6, 'Yttrium': 4.37, 'Zinc': 1.35, 'Zirconium': 6.25,
}

#### Electronegativity (CRC values) - Pauling scale
electronegativity = {
    'Ac': 1.1, 'Ag': 1.93, 'Al': 1.61, 'Am': 1.3, 'As': 2.18, 'At': 2.2, 'Au': 2.4,
    'B': 2.04, 'Ba': 0.89, 'Be': 1.57, 'Bi': 1.9, 'Bk': 1.3, 'Br': 2.96,
    'C': 2.55, 'Ca': 1.0, 'Cd': 1.69, 'Ce': 1.12, 'Cf': 1.3, 'Cl': 3.16, 'Cm': 1.3,
    'Co': 1.88, 'Cr': 1.66, 'Cs': 0.79, 'Cu': 1.9,
    'Dy': 1.22,
    'Er': 1.24, 'Es': 1.3,
    'F': 3.98, 'Fe': 1.83, 'Fm': 1.3, 'Fr': 0.7,
    'Ga': 1.81, 'Gd': 1.2, 'Ge': 2.01,
    'H': 2.2, 'Hf': 1.3, 'Hg': 1.9, 'Ho': 1.23,
    'I': 2.66, 'In': 1.78, 'Ir': 2.2,
    'K': 0.82, 'Kr': 3.0,
    'La': 1.1, 'Li': 0.98, 'Lu': 1.27,
    'Md': 1.3, 'Mg': 1.31, 'Mn': 1.55, 'Mo': 2.16,
    'N': 3.04, 'Na': 0.93, 'Nb': 1.6, 'Nd': 1.14, 'Ni': 1.91, 'No': 1.3, 'Np': 1.3,
    'O': 3.44, 'Os': 2.2,
    'P': 2.19, 'Pa': 1.5, 'Pb': 1.8, 'Pd': 2.2, 'Po': 2.0, 'Pr': 1.13, 'Pt': 2.2, 'Pu': 1.3,
    'Ra': 0.9, 'Rb': 0.82, 'Re': 1.9, 'Rh': 2.28, 'Ru': 2.2,
    'S': 2.58, 'Sb': 2.05, 'Sc': 1.36, 'Se': 2.55, 'Si': 1.9, 'Sm': 1.17, 'Sn': 1.96, 'Sr': 0.95,
    'Ta': 1.5, 'Tc': 1.9, 'Te': 2.1, 'Th': 1.3, 'Ti': 1.54, 'Tl': 1.8, 'Tm': 1.25,
    'U': 1.7,
    'V': 1.63,
    'W': 1.7,
    'Xe': 2.6,
    'Y': 1.22,
    'Zn': 1.65, 'Zr': 1.33,
}

dict_id_nl_bsc = {
    'Qiang_Li': 'iciq72010',
}

list_id_nl_tekla = ['qli']
