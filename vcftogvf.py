#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu May 13 14:59:11 2021

@author: madeline
"""

'''
This script converts VCF files that have been annotated by snpEFF into GVF files,
ignoring pragmas as this is an intermediate step to the final GVF that will contain functional annotations.
'''

import pandas as pd
import re
import glob
import os
import numpy as np


gvf_columns = ['#seqid','#source','#type','#start','#end','#score','#strand','#phase','#attributes']

def convertfile(var_data):
    
    df = pd.read_csv(var_data, sep='\t', header=1)
    df['strain'] = re.search('/(.+?)_ids', var_data).group(1)
    
    new_df = pd.DataFrame(index=range(0,len(df)),columns=gvf_columns)
    
    #parse EFF column
    eff_info = df['EFF'].str.findall('\((.*?)\)') #series: extract everything between parentheses as elements of a list
    eff_info = eff_info.apply(pd.Series)[0] #take first element of list
    eff_info = eff_info.str.split(pat='|').apply(pd.Series) #split at pipe, form dataframe

    #hgvs names
    hgvs = eff_info[3].str.rsplit(pat='c.').apply(pd.Series)
    hgvs_protein = hgvs[0].str[:-1]
    hgvs_protein.replace(r'^\s+$', np.nan, regex=True)
    hgvs_nucleotide = 'c.' + hgvs[1]
    new_df['#attributes'] = new_df['#attributes'].astype(str) + 'Name=' + hgvs_protein + ';'
    new_df['#attributes'] = new_df['#attributes'].astype(str) + 'nt_name=' + hgvs_nucleotide + ';'
    
    #gene names
    new_df['#attributes'] = new_df['#attributes'].astype(str) + 'gene=' + eff_info[5] + ';'

    #mutation type: looks like MISSENSE or SILENT from Zohaib's file
    new_df['#attributes'] = new_df['#attributes'].astype(str) + 'mutation_type=' + eff_info[1] + ';'    
    
    #columns copied straight from Zohaib's file
    for column in ['REF','ALT','AO', 'DP', 'RO']:
        key = column.lower()
        if key=='ref':
            key = 'Reference_seq'
        elif key=='alt':
            key = 'Variant_seq'
        new_df['#attributes'] = new_df['#attributes'].astype(str) + key + '=' + df[column].astype(str) + ';'
    
    #add strain name
    new_df['#attributes'] = new_df['#attributes'] + 'viral_lineage=' + df['strain'] + ';'
    
    #add WHO strain name
    alt_strain_names = {'B.1.1.7': 'Alpha', 'B.1.351': 'Beta', 'P.1': 'Gamma', 'B.1.617.2': 'Delta', 'B.1.427': 'Epsilon', 'B.1.429': 'Epsilon', 'P.2': 'Zeta', 'B.1.525': 'Eta', 'P.3': 'Theta', 'B.1.526': 'Iota', 'B.1.617.1': 'Kappa'}
    mapped_alt_strains = df['strain'].map(alt_strain_names)
    new_df['#attributes'] = new_df['#attributes'] + 'who_label=' + mapped_alt_strains + ';'

    #add VOC/VOI designation
    if mapped_alt_strains.all() in {'Alpha', 'Beta', 'Gamma', 'Delta'}:
        new_df['#attributes'] = new_df['#attributes'] + 'status=VOC;'
    else:
        new_df['#attributes'] = new_df['#attributes'] + 'status=VOI;'
    
    #remove starting NaN; leave trailing ';'
    new_df['#attributes'] = new_df['#attributes'].str[3:]
    
    #fill in other GVF columns
    new_df['#seqid'] = df['CHROM']
    new_df['#source'] = '.'
    new_df['#type'] = df['TYPE']
    new_df['#start'] = df['POS']
    new_df['#end'] = (df['POS'] + df['ALT'].str.len() - 1).astype(str)  #this needs fixing
    new_df['#score'] = '.'
    new_df['#strand'] = '+'
    new_df['#phase'] = '.'
    
    return new_df


#process all VCF files in the data folder
folderpath = "reference_data_/31_05_2021" #folder containing annotated VCFs
new_folder = folderpath + "/gvf_files" #gvf files from this script will be stored in here
if not os.path.exists(new_folder):
    os.makedirs(new_folder)
os.chdir(folderpath)

for file in glob.glob('./*_ids_GISAID_reformatted.sorted.annotated.tsv'):
    result = convertfile(file)
    filepath = "./gvf_files" + file[1:-4] + ".gvf"
    print(filepath)
    result.to_csv(filepath, sep='\t', index=False, columns=gvf_columns)