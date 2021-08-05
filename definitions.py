import json
import os

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
REFERENCE_DATA_DIR = os.path.join(ROOT_DIR, "reference_data")
USER_DATA_DIR = os.path.join(ROOT_DIR, "user_data")
GENE_COLORS_PATH = os.path.join(ROOT_DIR, "assets/gene_colors.json")
GENE_POSITIONS_PATH = os.path.join(ROOT_DIR, "assets/gene_positions.json")

with open(GENE_COLORS_PATH) as fp:
    GENE_COLORS_DICT = json.load(fp)

with open(GENE_POSITIONS_PATH) as fp:
    GENE_POSITIONS_DICT = json.load(fp)
