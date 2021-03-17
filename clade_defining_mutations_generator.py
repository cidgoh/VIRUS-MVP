"""TODO..."""

import csv
import os


def get_clade_defining_mutations():
    """"TODO..."""
    ret = {}
    with open("VOC clade-defining mutations - gff3.tsv") as fp:
        fieldnames = [
            "#seqid", "#source", "#type", "#start", "#end", "#score",
            "#strand", "#phase", "#attributes"
        ]
        reader = csv.DictReader(fp, delimiter="\t", fieldnames=fieldnames)
        for _ in range(0, 5):
            next(reader)
        for row in reader:
            attributes =\
                get_clade_defining_mutation_attributes(row["#attributes"])
            strain = attributes["ID"].split("-")[0]
            if strain not in ret:
                ret[strain] = set()
            ret[strain].add(row["#start"])
    return ret


def get_clade_defining_mutation_attributes(gff3_attributes_str):
    gff3_single_attribute_str_list = gff3_attributes_str.split(";")
    ret = {}
    for gff3_single_attribute_str in gff3_single_attribute_str_list:
        if "=" in gff3_single_attribute_str:
            [key, val] = gff3_single_attribute_str.split("=")
            ret[key] = val
    return ret


def main():
    """TODO..."""
    clade_defining_mutations = get_clade_defining_mutations()
    with os.scandir("clade_defining_mutations_data") as it:
        for entry in it:
            strain = entry.name.split("_")[0]
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
