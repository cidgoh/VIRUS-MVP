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
from os import scandir
from os.path import join

from definitions import (ROOT_DIR, REFERENCE_DATA_DIR,
                         DEFAULT_REFERENCE_HIDDEN_STRAINS_PATH,
                         DEFAULT_REFERENCE_STRAIN_ORDER_PATH)

GROWING_LINEAGES_PATH = \
    join(ROOT_DIR, "defaults_generator", "GrowingLineages.tsv")
LAST_120_DAYS_PATH = \
    join(ROOT_DIR, "defaults_generator", "Last 120 days.tsv")


def main():
    reference_file_names_table = \
        sorted({e.name: 0 for e in scandir(REFERENCE_DATA_DIR)})
    default_file_names_table = {}

    with open(GROWING_LINEAGES_PATH) as fp:
        for lineage_dict in DictReader(fp, delimiter="\t"):
            if lineage_dict["region"] != "Canada":
                continue
            lineage_name = lineage_dict["lineage"]
            if lineage_name.endswith("*"):
                prefix_cond = lineage_name[:-1]
            else:
                prefix_cond = lineage_name + "_"
            for file_name in reference_file_names_table:
                if file_name.startswith(prefix_cond):
                    if file_name not in default_file_names_table:
                        default_file_names_table[file_name] = 0

    with open(LAST_120_DAYS_PATH) as fp:
        for lineage_dict in DictReader(fp, delimiter="\t"):
            lineage_name = lineage_dict["Lineage"]
            for file_name in reference_file_names_table:
                if file_name.startswith(lineage_name + "_"):
                    if file_name not in default_file_names_table:
                        default_file_names_table[file_name] = 0

    default_hidden_file_names = [e for e in reference_file_names_table
                                 if e not in default_file_names_table]
    # Super hackey; could break if naming format changes
    default_hidden_strains = \
        [e.split("_")[0] for e in default_hidden_file_names]
    with open(DEFAULT_REFERENCE_HIDDEN_STRAINS_PATH, "w") as fp:
        json.dump(default_hidden_strains, fp, indent=2)

    default_file_names_order = \
        [e for e in default_file_names_table] + default_hidden_strains
    # Super hackey; could break if naming format changes
    default_strain_order = [e.split("_")[0] for e in default_file_names_order]
    with open(DEFAULT_REFERENCE_STRAIN_ORDER_PATH, "w") as fp:
        json.dump(default_strain_order, fp, indent=2)


if __name__ == "__main__":
    main()
