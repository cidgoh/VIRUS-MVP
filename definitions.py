from csv import DictReader
import json
import os

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
REFERENCE_DATA_DIR = os.path.join(ROOT_DIR, "reference_data")
USER_DATA_DIR = os.path.join(ROOT_DIR, "user_data")
ASSETS_DIR = os.path.join(ROOT_DIR, "assets")
NF_NCOV_VOC_DIR = os.path.join(ROOT_DIR, "nf-ncov-voc")
GENE_COLORS_PATH = os.path.join(ASSETS_DIR, "gene_colors.json")
GENE_POSITIONS_PATH = os.path.join(ASSETS_DIR, "gene_positions.json")
NSP_POSITIONS_PATH = os.path.join(ASSETS_DIR, "nsp_positions.json")
DEFAULT_REFERENCE_HIDDEN_STRAINS_PATH = \
    os.path.join(ASSETS_DIR, "default_reference_hidden_strains.json")
DEFAULT_REFERENCE_STRAIN_ORDER_PATH = \
    os.path.join(ASSETS_DIR, "default_reference_strain_order.json")
REFERENCE_SURVEILLANCE_REPORTS_DIR = \
    os.path.join(ROOT_DIR, "reference_surveillance_reports")
USER_SURVEILLANCE_REPORTS_DIR = \
    os.path.join(ROOT_DIR, "user_surveillance_reports")

with open(GENE_COLORS_PATH) as fp:
    GENE_COLORS_DICT = json.load(fp)

with open(GENE_POSITIONS_PATH) as fp:
    GENE_POSITIONS_DICT = json.load(fp)

with open(NSP_POSITIONS_PATH) as fp:
    NSP_POSITIONS_DICT = json.load(fp)

with open(DEFAULT_REFERENCE_HIDDEN_STRAINS_PATH) as fp:
    DEFAULT_REFERENCE_HIDDEN_STRAINS = json.load(fp)

with open(DEFAULT_REFERENCE_STRAIN_ORDER_PATH) as fp:
    DEFAULT_REFERENCE_STRAIN_ORDER = json.load(fp)
