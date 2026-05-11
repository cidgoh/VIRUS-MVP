from warnings import warn
import json
import os
import re

from flask import session
from pydantic import RootModel, conlist
from typing import Dict, List, Union

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
REFERENCE_DATA_DIR = os.path.join(ROOT_DIR, "reference_data")
USER_DATA_DIR = os.path.join(ROOT_DIR, "user_data")
ASSETS_DIR = os.path.join(ROOT_DIR, "assets")
NF_NCOV_VOC_DIR = os.path.join(ROOT_DIR, "nf-ncov-voc")
VIRUS_SEGMENT_REFERENCE_PATH = \
    os.path.join(ASSETS_DIR, "virus_segment_reference.json")
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

referencesList = conlist(str, min_length=1)
VirusSegmentReference = RootModel[
    Dict[
        str,
        Union[
            referencesList,
            Dict[str, referencesList]
        ]
    ]
]

with open(VIRUS_SEGMENT_REFERENCE_PATH) as fp:
    VIRUS_SEGMENT_REFERENCE_DICT = json.load(fp)
    VirusSegmentReference.model_validate(VIRUS_SEGMENT_REFERENCE_DICT)

with open(RUN_INFO_PATH) as fp:
    RUN_INFO_DICT = json.load(fp)

with open(DEFAULT_REFERENCE_HIDDEN_STRAINS_PATH) as fp:
    DEFAULT_REFERENCE_HIDDEN_STRAINS = json.load(fp)

with open(DEFAULT_REFERENCE_STRAIN_ORDER_PATH) as fp:
    DEFAULT_REFERENCE_STRAIN_ORDER = json.load(fp)


def is_segmented(virus):
    """TODO"""
    return isinstance(VIRUS_SEGMENT_REFERENCE_DICT[virus], dict)


def safe_path_segment_name(s):
    s = re.sub(r"[\\/]+", "_", s)
    s = re.sub(r"\.\.+", "_", s)
    s = re.sub(r"[^a-zA-Z0-9._-]", "_", s)
    return s.strip("_")


def get_nested_dir(root, virus, segment, reference, fail_if_empty=False):
    """TODO"""
    virus = safe_path_segment_name(virus)
    reference = safe_path_segment_name(reference)
    if segment:
        ret_path = os.path.join(root,
                                virus,
                                safe_path_segment_name(str(segment)),
                                reference)
    else:
        ret_path = os.path.join(root,
                                virus,
                                reference)
    os.makedirs(ret_path, exist_ok=True)
    if fail_if_empty and not os.listdir(ret_path):
        raise RuntimeError(ret_path + " is empty")
    return ret_path


def get_nested_dir_with_session_vars(root, fail_if_empty=False):
    """TODO"""
    virus = session.get("virus")
    segment = session.get("segment")
    reference = session.get("reference")
    return get_nested_dir(root, virus, segment, reference, fail_if_empty)


def get_reference_data_dir():
    """TODO"""
    return get_nested_dir_with_session_vars(REFERENCE_DATA_DIR, True)


def get_user_data_dir():
    """TODO"""
    return get_nested_dir_with_session_vars(USER_DATA_DIR)


def get_reference_surveillance_reports_dir():
    """TODO"""
    return get_nested_dir_with_session_vars(REFERENCE_SURVEILLANCE_REPORTS_DIR)


def get_user_surveillance_reports_dir():
    """TODO"""
    return get_nested_dir_with_session_vars(USER_SURVEILLANCE_REPORTS_DIR)


def populate_nested_asset_dict(virus, reference, segment=None):
    """TODO"""
    ret_dict = {}

    nested_asset_dir = \
        get_nested_dir(ASSETS_DIR, virus, segment, reference)
    genome_config_path = os.path.join(nested_asset_dir, "genome_config.json")
    if not os.path.exists(genome_config_path):
        warn("Genome config file missing for:%s\n%s\n%s)" % (virus,
                                                             segment,
                                                             reference))
        return {}
    with open(genome_config_path) as fp:
        genome_config_dict = json.load(fp)

    genome_len = genome_config_dict["Src"]["end"]
    ret_dict["genome_len"] = genome_len

    gene_bar_components = \
        [e for e in genome_config_dict if genome_config_dict[e]["type"]
         in ["CDS", "five_prime_UTR", "three_prime_UTR", "INTERGENIC"]]
    ret_dict["gene_colors_dict"] = \
        {k: genome_config_dict[k]["color"] for k in gene_bar_components}
    gene_positions_dict = \
        {k: {x: genome_config_dict[k][x] for x in ["start", "end"]}
         for k in gene_bar_components[:-1]}
    ret_dict["gene_positions_dict"] = gene_positions_dict

    first_component = min(gene_positions_dict,
                          key=lambda k: gene_positions_dict[k]["start"])
    if gene_positions_dict[first_component]["start"] == 1:
        ret_dict["first_region"] = [
            1,
            gene_positions_dict[first_component]["end"]
        ]
    else:
        ret_dict["first_region"] = [
            1,
            gene_positions_dict[first_component]["start"] - 1
        ]

    last_component = max(gene_positions_dict,
                         key=lambda k: gene_positions_dict[k]["end"])
    if gene_positions_dict[last_component]["end"] == genome_len:
        ret_dict["last_region"] = [
            gene_positions_dict[last_component]["start"],
            genome_len
        ]
    else:
        ret_dict["last_region"] = [
            gene_positions_dict[last_component]["end"] + 1,
            genome_len
        ]

    nsp_bar_components = \
        [e for e in genome_config_dict
         if genome_config_dict[e]["type"] == "mature_protein_region_of_CDS"]
    ret_dict["nsp_positions_dict"] = \
        {k: {x: genome_config_dict[k][x] for x in ["start", "end"]}
         for k in nsp_bar_components}

    return ret_dict

NESTED_ASSET_DICT = {}
for virus_ in VIRUS_SEGMENT_REFERENCE_DICT:
    NESTED_ASSET_DICT[virus_] = {}
    if is_segmented(virus_):
        for segment_ in VIRUS_SEGMENT_REFERENCE_DICT[virus_]:
            NESTED_ASSET_DICT[virus_][segment_] = {}
            for reference_ in VIRUS_SEGMENT_REFERENCE_DICT[virus_][segment_]:
                NESTED_ASSET_DICT[virus_][segment_][reference_] = \
                    populate_nested_asset_dict(virus_, segment_, reference_)
    else:
        for reference_ in VIRUS_SEGMENT_REFERENCE_DICT[virus_]:
            NESTED_ASSET_DICT[virus_][reference_] = \
                populate_nested_asset_dict(virus_, reference_)


def get_asset_dict(virus=None, segment=None, reference=None):
    """TODO"""
    if virus is None:
        virus = session.get("virus")
    if segment is None:
        segment = session.get("segment")
    if reference is None:
        reference = session.get("reference")
    if segment:
        return NESTED_ASSET_DICT[virus][segment][reference]
    else:
        return NESTED_ASSET_DICT[virus][reference]
