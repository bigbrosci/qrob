#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re
from pathlib import Path

try:
    from .data import ja as BUILTIN_JA
except ImportError:
    from data import ja as BUILTIN_JA

###### To get the abbriveation of the Journals ###############
def rule_one(journal_name):
    '''Delete the preposition words'''
    journal_name = journal_name.strip().lower()
    ele_list = journal_name.split()
    delete_list = ['the', 'of', 'and', 'in', 'for', 'on', 'to', 'with', '&'] # , 'I', 'Y', 'la', 'de', 'des', 'der', 'et', 'los', 'und']
    # if  'a' is not the last one , delete it
    for i in delete_list:
        if i in ele_list :
            ele_list.remove(i)
    journal_name = ' '.join(ele_list)
    return journal_name

def load_ja():
    '''Load journal abbreviations from a local dictionary file or fall back to built-ins.'''
    candidates = [
        Path('/home/robot/bin/Q_robot/books/books_have_read/my_ja_dict.txt'),
        Path(__file__).resolve().parent / 'my_ja_dict.txt',
    ]
    for dict_file in candidates:
        if dict_file.exists():
            return eval(dict_file.read_text())
    return BUILTIN_JA

def get_abb(journal):
    '''Get the abbreviation from the dictionary ja'''
    ja = load_ja()
    journal_ruled = rule_one(journal)
    abbreviation = 'None'
    for key, value in ja.items():
        journal_dict = rule_one(key)
        if journal_ruled == journal_dict:
            abbreviation = value
    if abbreviation == 'None': 
        print('Can not find the abbreviation for: %s' %(journal))
    return abbreviation

###########Bib References##########################

dict_filed_articles = {
#http://bib-it.sourceforge.net
'article' : ['title', 'author', 'journal', 'volume', 'number', 'pages', 'year', 'publisher', 'doi', 'abstract'],
'book' :    ['title', 'author', 'editor', 'volume', 'year', 'publisher', 'issn', 'edition']
}

def locate_bib(bib_file):
    '''To know where (the line numbers) the bib infor starts and ends ''' 
    file_in = open(bib_file, 'r')
    bib_lines = file_in.readlines()
    file_in.close()
    bib_start = []
    bib_end   = []
    for num, line in enumerate(bib_lines):
        list_start = ['@', '{', ',']
        if all(ele in line for ele in list_start):
            if line.strip()[0] == '@':
                bib_start.append(num)
        elif line.strip() == '}' :
                bib_end.append(num)
    return bib_start, bib_end, bib_lines
#bib_start, bib_end, bib_lines = locate_bib('hhdma.bib')
#print(bib_start, bib_end)
#print(len(bib_start))
#print(len(bib_end))

def readbib(one_bib):
    '''Analyze the input bib lines
    1) analyze the Entry
    2) analyze the filelds
    3) return the dictionary for a single bib file
    '''
    lines = one_bib 
    dict_bib = {}
    for line in lines:
        line = line.strip()
        if '@' and '{' and ',' in line and '}' not in line:
            infor = line.split('{')
            entry = infor[0][1:].lower()
            label = infor[1][:-1].lower()
            dict_bib.update({'entry' : entry})
            dict_bib.update({'label' : label})
        elif '=' in line: 
            key, value_raw = line.split('=')[0:2]
            key = key.strip().lower()
            value_raw = value_raw.strip()
            if value_raw[-1] == ',' :  ## sometime the last but one line are not ended with ','
                value = value_raw[1:-2]
            else: 
                value = value_raw[1:-1]
            dict_bib.update({key:value})
    return dict_bib

def add_field(dict_bib, field, field_infor):
    ''' Add field information to current bib_dict. '''
    if field.lower() not in dict_bib.keys():
        dict_bib.update({field:field_infor})
    return dict_bib

def change_field(dict_bib, field, field_infor):
    ''' Change the field information in the current bib_dict. '''
    dict_bib.update({field:field_infor})
    return dict_bib

def journal_analyzer(dict_bib):
    '''Check the Abbreviation of the Journal in the bib dictionary'''
    ja = load_ja()
    journal = dict_bib.get('journal')
    if not journal:
        return dict_bib
    journal = journal.replace('&', 'and')
    journal = ' '.join(re.findall(r"[\w']+", journal)).lower()
        
    for key, value in ja.items():
        key = ' '.join(re.findall(r"[\w']+", key)).lower()
        print(key)
        if journal == key: 
            dict_bib.update({'journal': value})
    return dict_bib    

def format_one_bib(one_bib):
    '''format the bib file in a good manner '''
    dict_bib = readbib(one_bib)
    if dict_bib.get('entry') == 'article':      
        dict_bib = journal_analyzer(dict_bib)
    
    def field_line(field):
        filed_value = dict_bib.get(field)
        if filed_value == None: 
            line_f = '  %s={%s},\n' %(field, 'None')
        else:     
            line_f = '  %s={%s},\n' %(field, filed_value)
        return line_f
    
    bib_lines = []    
    if dict_bib.get('entry') == 'article':       
        bib_lines.append('@article{%s,\n'     %(dict_bib.get('label')))
        for field in ['title', 'author', 'journal', 'year', 'volume', 'pages', 'doi', 'publisher', 'file']:
            bib_lines.append(field_line(field))
    elif dict_bib.get('entry') == 'book':
        bib_lines.append('@book{%s,\n'        %(dict_bib.get('label')))
        for field in ['title', 'author', 'year', 'edition', 'isbn', 'publisher']:
            bib_lines.append(field_line(field))
    else:
        bib_lines.append('@%s{%s,\n'   %(dict_bib.get('entry'), dict_bib.get('label')))
        for field in ['title', 'author', 'year']:
            bib_lines.append(field_line(field))
    bib_lines.append('}\n')        
    return bib_lines 


def Author_analyzer():
    '''
    1) Given Name
    2) Middle Name
    3) Family Name
    4) Abbreviations such as Qiang --> Q. 
    4) The sequence of Given and Family names. Q. Li or Li Q. 
     '''

ja = {
    'Accounts of Chemical Research': 'Acc. Chem. Res.',
    'ACS Applied Materials and Interfaces': 'ACS Appl. Mater. Interfaces',
    'Advances in Catalysis': 'Adv. Catal.',
    'AIP Conference Proceedings': 'AIP Conf. Proc.',
    'Angewandte Chemie International Edition': 'Angew. Chem. Int. Ed.',
    'Annual Review of Plant Biology': 'Annu. Rev. Plant Biol.',
    'Applied Surface Science': 'Appl. Surf. Sci.',
    'Catalysis Communications': 'Catal. Commun.',
    'Catalysis Letters': 'Catal. Lett.',
    'Catalysis Today': 'Catal. Today',
    'Chemical Communications': 'Chem. Commun.',
    'Chemical Engineering and Technology': 'Chem. Eng. Technol.',
    'Chemical Engineering Science': 'Chem. Eng. Sci.',
    'Chemical Physics Letters': 'Chem. Phys. Lett.',
    'Chemical Reviews': 'Chem. Rev.',
    'Chemical Science': 'Chem. Sci.',
    'Chemical Society Reviews': 'Chem. Soc. Rev.',
    'ChemPhysChem': 'ChemPhysChem',
    'ChemSusChem': 'ChemSusChem',
    'Computational Materials Science': 'Comput. Mater. Sci.',
    'Dalton Transactions': 'Dalton Trans.',
    'Energy and Environmental Science': 'Energy Environ. Sci.',
    'Energy and Fuels': 'Energy Fuels',
    'Faraday Discussions': 'Faraday Discuss.',
    'Green Chemistry': 'Green Chem.',
    'Industrial and Engineering Chemistry Research': 'Ind. Eng. Chem. Res.',
    'International Journal of Hydrogen Energy': 'Int. J. Hydrogen Energy',
    'Journal of physics. Condensed matter : an Institute of Physics journal': 'J. Phys. Condens. Matter',
    'Journal of Alloys and Compounds': 'J. Alloys Compd.',
    'Journal of Applied Polymer Science': 'J. Appl. Polym. Sci.',
    'Journal of Catalysis': 'J. Catal.',
    'Journal of Chemical Information and Modeling': 'J. Chem. Inf. Model.',
    'Journal of Chemical Physics': 'J. Chem. Phys.',
    'Journal of Chemical Theory and Computation': 'J. Chem. Theory Comput.',
    'Journal of Computational Chemistry': 'J. Comput. Chem.',
    'Journal of electroanalytical chemistry and interfacial electrochemistry': 'J. Electroanal. Chem.',
    'Journal of Electroanalytical Chemistry': 'J. Electroanal. Chem.',
    'Journal of Molecular Catalysis A: Chemical': 'J. Mol. Catal. A: Chem.',
    'Journal of Physical Chemistry A': 'J. Phys. Chem. A',
    'Journal of Physical Chemistry B': 'J. Phys. Chem. B',
    'Journal of Physical Chemistry C': 'J. Phys. Chem. C',
    'Journal of Physical Chemistry': 'J. Phys. Chem.',
    'The Journal of Physical Chemistry': 'J. Phys. Chem.',
    'Journal of Physical Chemistry. A': 'J. Phys. Chem. A',
    'Journal of Physical Chemistry. B': 'J. Phys. Chem. B',
    'Journal of Physics and Chemistry of Solids': 'J. Phys. Chem. Solids',
    'Journal of Power Sources': 'J. Power Sources',
    'Journal of the American Chemical Society': 'J. Am. Chem. Soc.',
    'Journal of Molecular Modeling': 'J. Mol. Model.',
    'Langmuir': 'Langmuir',
    'Nanotechnology': 'Nanotechnology',
    'Nature Communications': 'Nat. Commun.',
    'Nature Materials': 'Nat. Mater.',
    'Nature': 'Nature',
    'Nature Catalysis': 'Nat. Catal.',
    'Organic and Biomolecular Chemistry': 'Org. Biomol. Chem.',
    'Physical Chemistry Chemical Physics': 'Phys. Chem. Chem. Phys.',
    'Physical Review B': 'Phys. Rev. B',
    'Physical Review Letters': 'Phys. Rev. Lett.',
    'RSC Advances': 'RSC Adv.',
    'Science': 'Science',
    'Surface Science Reports': 'Surf. Sci. Rep.',
    'Surface Science': 'Surf. Sci.',
    'Tetrahedron': 'Tetrahedron',
    'The Journal of Chemical Physics': 'J. Chem. Phys.',
    'The Journal of Physical Chemistry B': 'J. Phys. Chem. B',
    'The Journal of Physical Chemistry C': 'J. Phys. Chem. C',
    'THEOCHEM': 'THEOCHEM',
    'Topics in Catalysis': 'Top. Catal.',
    'Zeitschrift fuer Anorganische und Allgemeine Chemie': 'Z. Anorg. Allg. Chem.',
    'Platinum Metals Review': 'Platin. Met. Rev.',
    'Theochem': 'Theochem',
    'ACS Central Science': 'ACS Cent. Sci.',
    'Physical Review': 'Phys. Rev.',
    'Applied catalysis B Environmental': 'Appl. Catal. B',
    '{Applied Catalysis A: General': 'Appl. Catal. A',
    'Science Advances': 'Sci. Adv.',
    'Sensors and Actuators B: Chemical': 'Sens. Actuator B-Chem.',
    'Catalysis Science and Technology': 'Catal. Sci. Tech.',
    'Zeitschrift für Physikalische Chemie': 'Z. Phys. Chem.-Stoch. Ve.',
    'Journal of Industrial and Engineering Chemistry': 'J. Ind. Eng. Chem.',
    'Renewable and Sustainable Energy Reviews': 'Rev. Mod. Phys.',
    'Journal of Physics F: Metal Physics': 'J. Phys. F: Metal Phys.',
    'Transactions of the Faraday Society': 'Trans. Faraday Soc.',
    'The Chemical Educator': 'Chem. Educator',
    'Biofuels, Bioproducts and Biorefining': 'Biofuel. Bioprod. Bioref.',
    'ACS Catalysis': 'ACS Catal.',
    'Proceedings of the Royal Society of London. Series A, Mathematical and physical sciences': 'Proc. R. Soc. Lond. Math. Phys. Sci.',
    'Industrial crops and products': 'Ind. Crops Prod.',
    'Catalysts': 'Catalysts',
    'Nature Chemistry': 'Nat. Chem.',
    'ChemCatChem': 'ChemCatChem',
    'Applied catalysis. A General': 'Appl. Catal. A Gen.',
    'Chemistry: A European Journal': 'Chem.: Eur. J.',
}

BibEntries = [
    'article', 'book', 'booklet', 'inbook', 'incollection', 'inproceedings',
    'manual', 'mastersthesis', 'misc', 'phdthesis', 'proceedings',
    'techreport', 'unpublished',
]

BibFields = [
    'address', 'annote', 'author', 'booktitle', 'chapter', 'crossref',
    'edition', 'editor', 'howpublished', 'institution', 'journal', 'key',
    'month', 'note', 'number', 'organization', 'pages', 'publisher',
    'school', 'series', 'title', 'type', 'volume', 'year', 'doi',
]


### Old_versions############
#
#def readbib(one_bib):
#    '''Analyze the input bib lines
#    1) analyze the Entry
#    2) analyze the filelds
#    3) return the dictionary for a single bib file
#    '''
#    lines = one_bib 
#    dict_bib = {}
#    for line in lines:
#        line = line.strip()
#        if '@' and '{' and ',' in line and '}' not in line:
#            infor = line.split('{')
#            entry = infor[0][1:].lower()
#            label = infor[1][:-1].lower()
#            dict_bib.update({'entry' : entry})
#            dict_bib.update({'label' : label})
#        elif '=' in line: 
#            key, value_raw = line.split('=')[0:2]
#            key = key.strip().lower()
#            value_raw = value_raw.strip()
#            if value_raw[-1] == ',' :  ## sometime the last but one line are not ended with ','
#                value = value_raw[1:-2]
#            else: 
#                value = value_raw[1:-1]
#            dict_bib.update({key:value})
#    return dict_bib
#
#def add_field(dict_bib, field, field_infor):
#    ''' Add field information to current bib_dict. '''
#    if field.lower() not in dict_bib.keys():
#        dict_bib.update({field:field_infor})
#    return dict_bib
#
#def change_field(dict_bib, field, field_infor):
#    ''' Change the field information in the current bib_dict. '''
#    dict_bib.update({field:field_infor})
#    return dict_bib
#
#def journal_analyzer(dict_bib):
#    '''Check the Abbreviation of the Journal in the bib dictionary'''
#    journal = dict_bib.get('journal')
#    journal = journal.replace('&', 'and')
#    journal = ' '.join(re.findall(r"[\w']+", journal)).lower()
#        
#    for key, value in ja.items():
#        key = ' '.join(re.findall(r"[\w']+", key)).lower()
#        print(key)
#        if journal == key: 
#            dict_bib.update({'journal': value})
#    return dict_bib    
#
#def format_one_bib(one_bib):
#    
#    dict_bib = readbib(one_bib)
#    if dict_bib.get('entry') == 'article':      
#        dict_bib = journal_analyzer(dict_bib)
#    
#    def field_line(field):
#        filed_value = dict_bib.get(field)
#        if filed_value == None: 
#            line_f = '  %s={%s},\n' %(field, 'None')
#        else:     
#            line_f = '  %s={%s},\n' %(field, filed_value)
#        return line_f
#    
#    bib_lines = []    
#    if dict_bib.get('entry') == 'article':       
#        bib_lines.append('@article{%s,\n'     %(dict_bib.get('label')))
#        for field in ['title', 'author', 'journal', 'year', 'volume', 'pages', 'doi', 'publisher', 'file']:
#            bib_lines.append(field_line(field))
#    elif dict_bib.get('entry') == 'book':
#        bib_lines.append('@book{%s,\n'        %(dict_bib.get('label')))
#        for field in ['title', 'author', 'year', 'edition', 'isbn', 'publisher']:
#            bib_lines.append(field_line(field))
#    else:
#        bib_lines.append('@%s{%s,\n'   %(dict_bib.get('entry'), dict_bib.get('label')))
#        for field in ['title', 'author', 'year']:
#            bib_lines.append(field_line(field))
#    bib_lines.append('}\n')        
#    return bib_lines 
#
#def Author_analyzer():
#    '''
#    1) Given Name
#    2) Middle Name
#    3) Family Name
#    4) Abbreviations such as Qiang --> Q. 
#    4) The sequence of Given and Family names. Q. Li or Li Q. 
#     '''
#
#def rich_one_bib(bib_lines):
#    '''add the missing information automatically '''    
