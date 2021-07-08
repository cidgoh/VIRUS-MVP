#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jul  8 10:58:54 2021

@author: madeline
"""

'''
Merges the functional annotation .tsv with the gvf file produced by vcftogvf.py.  
Assigns a unique ID of the form ID_n to each unique set of mutations that share a functional effect.

TO-DO:
-change clade_defining attribute to correct True/False values
-tidy up code
'''

import pandas as pd
import re
import glob
import os
import numpy as np


def convertfile(gvf_file, annotation_file):

    df = pd.read_csv(annotation_file, sep='\t', header=0) #load functional annotations spreadsheet
    gvf = pd.read_csv(gvf_file, sep='\t', header=0) #load entire GVF file for modification

    attributes = gvf["#attributes"].str.split(pat=';').apply(pd.Series)

    hgvs_protein = attributes[0].str.split(pat='=').apply(pd.Series)[1]
    hgvs_nucleotide = attributes[1].str.split(pat='=').apply(pd.Series)[1]
    gvf["mutation"] = hgvs_protein.str[2:] #drop the prefix


    #merge annotated vcf and functional annotation files by 'mutation' column in the gvf
    for column in df.columns:
        df[column] = df[column].str.lstrip()
    merged_df = pd.merge(df, gvf, on=['mutation'], how='right')


    #collect all mutation groups (including reference mutation) in a column, sorted alphabetically
    merged_df["mutation_group"] = merged_df["comb_mutation"].astype(str) + ", '" + merged_df["mutation"].astype(str) + "'"
    merged_df["mutation_group"] = merged_df["mutation_group"].str.replace("'| ",'')
    mutation_groups = merged_df["mutation_group"].str.split(pat=',').apply(pd.Series)
    print(mutation_groups)
    mutation_groups = mutation_groups.transpose() 
    sorted_df = mutation_groups
    for column in mutation_groups.columns:
        sorted_df[column] = mutation_groups.sort_values(by=column, ignore_index=True)[column]
    sorted_df = sorted_df.transpose()
    
    #since they're sorted, put everything back into a single cell, don't care about dropna
    df3 = sorted_df.apply(lambda x :','.join(x.astype(str)),axis=1)
    unique_groups = df3.drop_duplicates() #92 unique groups
    unique_groups_multicol = sorted_df.drop_duplicates() #92 unique groups, not all members of which might be present in the gvf file
    merged_df["mutation_group_labeller"] = df3 #for sanity checking

    #make a unique id for mutation groups that have all members represented in the vcf
    #for groups with missing members, delete those functional annotations
    merged_df["id"] = 'NaN'
    id_num = 0
    for row in range(unique_groups.shape[0]):
        group_mutation_set = set(unique_groups_multicol.iloc[row])
        group_mutation_set = {x for x in group_mutation_set if (x==x and x!='nan')} #remove nan and 'nan' from set
        gvf_all_mutations = set(gvf['mutation'].unique())
        indices = merged_df[merged_df.mutation_group_labeller == unique_groups.iloc[row]].index.tolist()
        if group_mutation_set.issubset(gvf_all_mutations): #if all mutations in the group are in the vcf file, include those rows and give them an id
            merged_df.loc[merged_df.mutation_group_labeller == unique_groups.iloc[row], "id"] = "ID_" + str(id_num)
            id_num += 1
        else:
            merged_df = merged_df.drop(indices) #if not, drop group rows, leaving the remaining indices unchanged

    #change semicolons in function descriptions to colons
    merged_df['function_description'] = merged_df['function_description'].str.replace(';',':')
    #add key-value pairs to attributes column
    for column in ['function_category', 'source', 'citation', 'comb_mutation', 'function_description']:
        key = column.lower()
        merged_df[column] = merged_df[column].fillna('') #replace NaNs with empty string
        if column in ['function_category', 'citation', 'function_description']:
            merged_df["#attributes"] = merged_df["#attributes"].astype(str) + key + '=' + '"' + merged_df[column].astype(str) + '"' + ';'
        else:
            merged_df["#attributes"] = merged_df["#attributes"].astype(str) + key + '=' + merged_df[column].astype(str) + ';'

    merged_df["#attributes"] = merged_df["#attributes"].astype(str) + "clade_defining=True;" #placeholder for now
    merged_df["#attributes"] = 'ID=' + merged_df['id'].astype(str) + ';' + merged_df["#attributes"].astype(str)
    
    return merged_df
    

#process all gvf files in the data folder and save them inside merged_gvf_files
folderpath = "reference_data_/08_07_2021" #folder containing annotated VCFs
new_folder = folderpath + "/merged_gvf_files" #gvf files from this script will be stored in here
if not os.path.exists(new_folder):
    os.makedirs(new_folder)
os.chdir(folderpath)

gvf_columns = ['#seqid','#source','#type','#start','#end','#score','#strand','#phase','#attributes']

parent_directory = os.path.dirname(os.path.dirname(os.getcwd())) #path to voc_prototype main folder
annotation_file = parent_directory + '/functional_annotation_V.0.2.tsv'

print("Merged files saved as:")
for file in glob.glob('./gvf_files/*.gvf'): #process all .gvf files
    result = convertfile(file, annotation_file)
    filepath = "./merged_gvf_files/" + file.rsplit('/', 1)[-1][:-3] + "merged.gvf"
    result.to_csv(filepath, sep='\t', index=False, columns=gvf_columns)
    print(filepath)