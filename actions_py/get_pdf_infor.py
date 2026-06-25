#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent
brain_root = repo_root / "brain"
for candidate in (repo_root, brain_root):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from actions_py.bootstrap import ensure_repo_root

ensure_repo_root()

"""
Created on Wed Apr 17 21:53:43 2019
@author: qli
"""
import sys, re
import pdftotext

# Step1: Get the DOI from PDF file 
pdf_in = sys.argv[1]

def get_doi(page):
    doi_re = re.compile(r'10\.(\d)+/([^\s><"]+?)')
    doi = doi_re.search(page).group(0)
    return doi
#doi = get_doi(pdf[0])

with open(pdf_in, "rb") as f:
    pdf = pdftotext.PDF(f)
print(pdf[0])

