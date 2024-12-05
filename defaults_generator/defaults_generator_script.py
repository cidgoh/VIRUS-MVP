"""Write hidden strains and strain order assets.

The subset of visible strains should be an intersection of:
  * Strains in `reference_data_/`
  * Canadian strains from `GrowingLineages.tsv`
  * Strains from `Last 120 days.tsv`

The order of strains should match the order in `GrowingLineages.tsv`.

Ultimately, we are generating a subset of strains to display by
default, in a specific order. This script is run manually whenever we
update the data. This script should not be run by users.
"""

import json
from csv import DictReader
from io import TextIOWrapper
from os import scandir
from urllib.request import urlopen

from definitions import (REFERENCE_DATA_DIR,
                         DEFAULT_REFERENCE_HIDDEN_STRAINS_PATH,
                         DEFAULT_REFERENCE_STRAIN_ORDER_PATH)

GROWING_LINEAGES_PATH = \
    "https://covarr-net.github.io/duotang/downloads/GrowingLineages.tsv"
LAST_120_DAYS_PATH = \
    "https://covarr-net.github.io/duotang/downloads/Last%20120%20days.tsv"

def parse_gvf_sample_name(path):
    """Parse sample group name from gvf file header.

    :param path: Path to gvf file to parse
    :type path: str
    :return: Gvf file sample group
    :rtype: str
    """
    with open(path, encoding="utf-8") as fp:
        # Skip first two lines
        next(fp)
        next(fp)
        # "##sample-description sample_desc=x;sample_group=y;"
        sample_desc = fp.readline()
        # "sample_desc=x;sample_group=y"
        sample_desc_vals_str = sample_desc.split()[1].strip(";")
        # [["sample_desc", "x"], ["sample_group", "y"]]
        sample_desc_vals_list = \
            [e.split("=") for e in sample_desc_vals_str.split(";")]
        # {"sample_desc": "x", "sample_group": "y"}
        return dict(sample_desc_vals_list)["sample_group"]

def main():
    reference_strains_table = sorted(
        {parse_gvf_sample_name(e.path): 0 for e in scandir(REFERENCE_DATA_DIR)}
    )
    default_strains_table = {}

    with TextIOWrapper(urlopen(GROWING_LINEAGES_PATH)) as fp:
        for lineage_dict in DictReader(fp, delimiter="\t"):
            if lineage_dict["region"] != "Canada":
                continue
            lineage_name = lineage_dict["lineage"]
            if lineage_name.endswith("*"):
                prefix_cond = lineage_name[:-1]
            else:
                prefix_cond = lineage_name
            for strain in reference_strains_table:
                if strain.startswith(prefix_cond):
                    if strain not in default_strains_table:
                        default_strains_table[strain] = 0

    with TextIOWrapper(urlopen(LAST_120_DAYS_PATH)) as fp:
        for lineage_dict in DictReader(fp, delimiter="\t"):
            lineage_name = lineage_dict["Lineage"]
            for strain in reference_strains_table:
                if strain.startswith(lineage_name):
                    if strain not in default_strains_table:
                        default_strains_table[strain] = 0

    default_hidden_strains = [e for e in reference_strains_table
                              if e not in default_strains_table]
    with open(DEFAULT_REFERENCE_HIDDEN_STRAINS_PATH, "w") as fp:
        json.dump(default_hidden_strains, fp, indent=2)

    default_strain_order = \
        [e for e in default_strains_table] + default_hidden_strains
    with open(DEFAULT_REFERENCE_STRAIN_ORDER_PATH, "w") as fp:
        json.dump(default_strain_order, fp, indent=2)


if __name__ == "__main__":
    main()
