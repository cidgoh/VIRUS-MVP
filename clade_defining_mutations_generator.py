"""TODO..."""

import csv
import os


def get_clade_defining_mutations():
    """"TODO..."""
    ret = {}
    with open("VOC clade-defining mutations - Catalog.tsv") as fp:
        reader = csv.DictReader(fp, delimiter="\t")
        for row in reader:
            strain = row["lineage"]
            if strain not in ret:
                ret[strain] = set()
            ret[strain].add(row["nucleotide_position"])
    return ret


def main():
    """TODO..."""
    clade_defining_mutations = get_clade_defining_mutations()
    with os.scandir("clade_defining_mutations_data") as it:
        for entry in it:
            strain = entry.name.split("_")[0]
            fieldnames = []
            filtered_rows = []
            with open(entry.path, "r") as fp:
                reader = csv.DictReader(fp, delimiter="\t")
                fieldnames = reader.fieldnames
                for row in reader:
                    if row["POS"] in clade_defining_mutations[strain]:
                        filtered_rows.append(row)
            with open(entry.path, "w") as fp:
                writer =\
                    csv.DictWriter(fp, fieldnames=fieldnames, delimiter="\t")
                writer.writeheader()
                for filtered_row in filtered_rows:
                    writer.writerow(filtered_row)
    return


if __name__ == "__main__":
    main()
