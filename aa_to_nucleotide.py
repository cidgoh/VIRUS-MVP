#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 21 12:17:15 2021

@author: madeline
"""

'''Given a SARS-CoV-2 nucleotide position, outputs the corresponding gene, amino acid code, and amino acid number.  Note that this will only work for nucleotides found inside a coding region of the SARS-CoV-2 genome as described in https://www.ncbi.nlm.nih.gov/nuccore/1798174254'''

from Bio import SeqIO
import numpy as np

record_dict = SeqIO.to_dict(SeqIO.parse("genefeatures.txt", "fasta"), key_function = lambda rec : rec.description.split()[1])
genes = {"5'UTR": (1, 265), 'ORF1ab': (266, 21555), 'S': (21563, 25384), 'ORF3a': (25393, 26220), 'E': (26245, 26472), 'M': (26523, 27191),'ORF6': (27202, 27387), 'ORF7a': (27394, 27759), 'ORF8': (27894, 28259), 'N': (28274, 29533), 'ORF10': (29558, 29674), "3'UTR": (29675, 29903)}
mydict = {y:x for x,y in genes.items()} #reversed dictionary
    
def get_aa_code(nucleotide_position): 
# get gene names, amino acid positions and aa codes (relative to gene start)
#note that gene boundaries are inclusive

    for gene_range in mydict.keys():

        if (nucleotide_position >= gene_range[0]) & (nucleotide_position <= gene_range[1]):
            aa_position = np.ceil((nucleotide_position - gene_range[0] + 1)/3).astype(int)
            print("aa_position: ", aa_position)
            gene = mydict.get(gene_range)
            print("gene: ", gene)
            seq_dict_key = "[gene=" + str(gene) + "]"
            coding_dna = record_dict.get(seq_dict_key).seq
            messenger_rna = coding_dna.transcribe()
            aa = messenger_rna.translate()
            amino_acid_code = aa[aa_position - 1]
            print("aa: ", amino_acid_code)
            
    return aa_position, gene, str(amino_acid_code)


