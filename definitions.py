import json
import os
import re

from flask import session

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
REFERENCE_DATA_DIR = os.path.join(ROOT_DIR, "reference_data")
USER_DATA_DIR = os.path.join(ROOT_DIR, "user_data")
ASSETS_DIR = os.path.join(ROOT_DIR, "assets")
NF_NCOV_VOC_DIR = os.path.join(ROOT_DIR, "nf-ncov-voc")
VIRUS_REFERENCE_SEGMENT_PATH = \
    os.path.join(ASSETS_DIR, "virus_reference_segment.json")
GENOME_CONFIG_PATH = os.path.join(ASSETS_DIR, "genome_config.json")
RUN_INFO_PATH = os.path.join(ASSETS_DIR, "run_info.json")
DEFAULT_REFERENCE_HIDDEN_STRAINS_PATH = \
    os.path.join(ASSETS_DIR, "default_reference_hidden_strains.json")
DEFAULT_REFERENCE_STRAIN_ORDER_PATH = \
    os.path.join(ASSETS_DIR, "default_reference_strain_order.json")
REFERENCE_SURVEILLANCE_REPORTS_DIR = \
    os.path.join(ROOT_DIR, "reference_surveillance_reports")
USER_SURVEILLANCE_REPORTS_DIR = \
    os.path.join(ROOT_DIR, "user_surveillance_reports")
README_PATH = os.path.join(ROOT_DIR, "README.md")

with open(VIRUS_REFERENCE_SEGMENT_PATH) as fp:
    VIRUS_REFERENCE_SEGMENT_DICT = json.load(fp)

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

first_component = min(GENE_POSITIONS_DICT,
                   key=lambda k: GENE_POSITIONS_DICT[k]["start"])
if GENE_POSITIONS_DICT[first_component]["start"] == 1:
    FIRST_REGION = [1, GENE_POSITIONS_DICT[first_component]["end"]]
else:
    FIRST_REGION = [1, GENE_POSITIONS_DICT[first_component]["start"]-1]

last_component = max(GENE_POSITIONS_DICT,
                  key=lambda k: GENE_POSITIONS_DICT[k]["end"])
if GENE_POSITIONS_DICT[last_component]["end"] == GENOME_LEN:
    LAST_REGION = [GENE_POSITIONS_DICT[last_component]["start"], GENOME_LEN]
else:
    LAST_REGION = [GENE_POSITIONS_DICT[last_component]["end"]+1, GENOME_LEN]

nsp_bar_components = \
    [e for e in GENOME_CONFIG_DICT
     if GENOME_CONFIG_DICT[e]["type"] == "mature_protein_region_of_CDS"]
NSP_POSITIONS_DICT = \
    {k: {x: GENOME_CONFIG_DICT[k][x] for x in ["start", "end"]}
     for k in nsp_bar_components}

with open(RUN_INFO_PATH) as fp:
    RUN_INFO_DICT = json.load(fp)

with open(DEFAULT_REFERENCE_HIDDEN_STRAINS_PATH) as fp:
    DEFAULT_REFERENCE_HIDDEN_STRAINS = json.load(fp)

with open(DEFAULT_REFERENCE_STRAIN_ORDER_PATH) as fp:
    DEFAULT_REFERENCE_STRAIN_ORDER = json.load(fp)

def safe_path_segment_name(s):
    s = re.sub(r"[\\/]+", "_", s)
    s = re.sub(r"\.\.+", "_", s)
    s = re.sub(r"[^a-zA-Z0-9._-]", "_", s)
    return s.strip("_")

def get_nested_dir(root, fail_if_empty=False):
    """TODO"""
    virus = safe_path_segment_name(session.get("virus"))
    reference = safe_path_segment_name(session.get("reference"))
    segment = session.get("segment")
    if segment:
        ret_path = os.path.join(root, virus, reference,
                                safe_path_segment_name(str(segment)))
    else:
        ret_path = os.path.join(root, virus, reference)
    os.makedirs(ret_path, exist_ok=True)
    if fail_if_empty and not os.listdir(ret_path):
        raise RuntimeError(ret_path + " is empty")
    return ret_path

def get_reference_data_dir():
    """TODO"""
    return get_nested_dir(REFERENCE_DATA_DIR, True)

def get_user_data_dir():
    """TODO"""
    return get_nested_dir(USER_DATA_DIR)

def get_reference_surveillance_reports_dir():
    """TODO"""
    return get_nested_dir(REFERENCE_SURVEILLANCE_REPORTS_DIR)

def get_user_surveillance_reports_dir():
    """TODO"""
    return get_nested_dir(USER_SURVEILLANCE_REPORTS_DIR)
