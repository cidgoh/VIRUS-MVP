import json
import os

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
REFERENCE_DATA_DIR = os.path.join(ROOT_DIR, "reference_data")
USER_DATA_DIR = os.path.join(ROOT_DIR, "user_data")
ASSETS_DIR = os.path.join(ROOT_DIR, "assets")
NF_NCOV_VOC_DIR = os.path.join(ROOT_DIR, "nf-ncov-voc")
GENOME_CONFIG_PATH = os.path.join(ASSETS_DIR, "genome_config.json")
DEFAULT_REFERENCE_HIDDEN_STRAINS_PATH = \
    os.path.join(ASSETS_DIR, "default_reference_hidden_strains.json")
DEFAULT_REFERENCE_STRAIN_ORDER_PATH = \
    os.path.join(ASSETS_DIR, "default_reference_strain_order.json")
REFERENCE_SURVEILLANCE_REPORTS_DIR = \
    os.path.join(ROOT_DIR, "reference_surveillance_reports")
USER_SURVEILLANCE_REPORTS_DIR = \
    os.path.join(ROOT_DIR, "user_surveillance_reports")

with open(GENOME_CONFIG_PATH) as fp:
    GENOME_CONFIG_DICT = json.load(fp)

GENOME_LEN = GENOME_CONFIG_DICT["Src"]["end"]

gene_bar_components = \
    [e for e in GENOME_CONFIG_DICT if GENOME_CONFIG_DICT[e]["type"]
     in ["CDS", "five_prime_UTR", "three_prime_UTR", "INTERGENIC"]]
GENE_COLORS_DICT = \
    {k: GENOME_CONFIG_DICT[k]["color"] for k in gene_bar_components}
GENE_POSITIONS_DICT = \
    {k: {x: GENOME_CONFIG_DICT[k][x] for x in ["start", "end"]}
     for k in gene_bar_components[:-1]}

nsp_bar_components = \
    [e for e in GENOME_CONFIG_DICT
     if GENOME_CONFIG_DICT[e]["type"] == "mature_protein_region_of_CDS"]
NSP_POSITIONS_DICT = \
    {k: {x: GENOME_CONFIG_DICT[k][x] for x in ["start", "end"]}
     for k in nsp_bar_components}

with open(DEFAULT_REFERENCE_HIDDEN_STRAINS_PATH) as fp:
    DEFAULT_REFERENCE_HIDDEN_STRAINS = json.load(fp)

with open(DEFAULT_REFERENCE_STRAIN_ORDER_PATH) as fp:
    DEFAULT_REFERENCE_STRAIN_ORDER = json.load(fp)
