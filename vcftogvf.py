#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu May 13 14:59:11 2021

@author: madeline
"""

'''
This script converts VCF files that have been annotated by snpEFF into GVF files,
ignoring pragmas as this is an intermediate step to the final GVF that will contain functional annotations.

TO-DO:
-correct end points
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
    for column in ['REF','ALT','ALT_DP', 'DP', 'REF_DP']:
        key = column.lower()
        if key=='ref':
            key = 'Reference_seq'
        elif key=='alt':
            key = 'Variant_seq'
        elif key=='ref_dp':
            key = 'ro'
        elif key=='alt_dp':
            key = 'ao'
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
    new_df['#type'] = '.' #df['TYPE']
    new_df['#start'] = df['POS']
    new_df['#end'] = (df['POS'] + df['ALT'].str.len() - 1).astype(str)  #this needs fixing
    new_df['#score'] = '.'
    new_df['#strand'] = '+'
    new_df['#phase'] = '.'
    
    return new_df

#process all annotated VCF files in the data folder
def convertfolder(folderpath):
    print("Converted files saved as:")
    new_folder = folderpath + "/gvf_files" #gvf files from this script will be stored in here
    if not os.path.exists(new_folder):
        os.makedirs(new_folder)
    os.chdir(folderpath)
    
    pragmas = pd.DataFrame([['##gff-version 3'], ['##gvf-version 1.10'], ['##species NCBI_Taxonomy_URI=http://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?id=2697049']]) #pragmas are in column 0

    for file in glob.glob('./*.tsv'): #get all .tsv files
        result = convertfile(file)
        #add pragmas to df, then save to .tsv
        result = result[gvf_columns]
        result = pd.DataFrame(np.vstack([result.columns, result])) #columns are now 0, 1, ...
        fin = pragmas.append(result)
        filepath = "./gvf_files" + file[1:-4] + ".gvf"
        print(filepath)
        fin.to_csv(filepath, sep='\t', index=False, header=False)
        

folder = "reference_data_/08_07_2021" #folder containing annotated VCFs
convertfolder(folder)