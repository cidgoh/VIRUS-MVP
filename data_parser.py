"""TODO..."""
import csv
import os


def parse_data_files(dir_):
    """TODO..."""
    ret = {}
    with os.scandir(dir_) as it:
        for entry in it:
            strain = entry.name.split("_")[0]
            ret[strain] = {}
            with open(entry.path) as fp:
                reader = csv.DictReader(fp, delimiter="\t")
                for row in reader:
                    pos = int(row["POS"])
                    ret[strain][pos] = {}
                    ret[strain][pos]["ref"] = row["REF"]
                    ret[strain][pos]["alt"] = row["ALT"]
                    ret[strain][pos]["alt_freq"] = row["ALT_FREQ"]
                    ret[strain][pos]["ref_codon"] = row["REF_CODON"]
                    ret[strain][pos]["alt_codon"] = row["ALT_CODON"]
                    ret[strain][pos]["ref_aa"] = row["REF_AA"]
                    ret[strain][pos]["alt_aa"] = row["ALT_AA"]
                    if row["ALT"][0] == "+":
                        ret[strain][pos]["mutation_type"] = "insertion"
                    elif row["ALT"][0] == "-":
                        ret[strain][pos]["mutation_type"] = "deletion"
                    else:
                        ret[strain][pos]["mutation_type"] = "snp"
    return ret


def get_data(dir_):
    """TODO..."""
    parsed_files = parse_data_files(dir_)
    data = {
        "heatmap_x": get_heatmap_x(parsed_files),
        "heatmap_y": get_heatmap_y(parsed_files),
        "insertions_x": get_insertions_x(parsed_files),
        "insertions_y": get_insertions_y(parsed_files),
        "deletions_x": get_deletions_x(parsed_files),
        "deletions_y": get_deletions_y(parsed_files),
        "tables": get_tables(parsed_files)
    }
    data["heatmap_z"] = get_heatmap_z(parsed_files, data["heatmap_x"])
    data["heatmap_cell_text"] = \
        get_heatmap_cell_text(parsed_files, data["heatmap_x"])
    return data


def get_heatmap_x(parsed_files):
    """TODO..."""
    seen = set()
    ret = []
    for strain in parsed_files:
        for pos in parsed_files[strain]:
            if pos not in seen:
                seen.add(pos)
                ret.append(pos)
    ret.sort()
    return ret


def get_heatmap_y(parsed_files):
    """TODO..."""
    ret = []
    for strain in parsed_files:
        ret.append(strain)
    return ret


def get_heatmap_z(parsed_files, heatmap_x):
    """TODO..."""
    ret = []
    for strain in parsed_files:
        row = []
        for pos in heatmap_x:
            if pos in parsed_files[strain]:
                row.append(parsed_files[strain][pos]["alt_freq"])
            else:
                row.append(None)
        ret.append(row)
    return ret


def get_heatmap_cell_text(parsed_files, heatmap_x):
    """TODO..."""
    ret = []
    for strain in parsed_files:
        row = []
        for pos in heatmap_x:
            if pos in parsed_files[strain]:
                cell_data = parsed_files[strain][pos]
                cell_text_str = "<b>Position:</b> %s<br>" \
                                "<b>Mutation type:</b> %s<br>" \
                                "<br>" \
                                "<b>Reference:</b> %s<br>" \
                                "<b>Alternate:</b> %s<br>" \
                                "<b>Alternate frequency:</b> %s<br>" \
                                "<br>" \
                                "<b>Reference codon:</b> %s<br>" \
                                "<b>Alternate codon:</b> %s<br>" \
                                "<b>Reference amino acid:</b> %s<br>" \
                                "<b>Alternate amino acid:</b> %s"
                cell_text_params = (pos,
                                    cell_data["mutation_type"],
                                    cell_data["ref"],
                                    cell_data["alt"],
                                    cell_data["alt_freq"],
                                    cell_data["ref_codon"],
                                    cell_data["alt_codon"],
                                    cell_data["ref_aa"],
                                    cell_data["alt_aa"])
                row.append(cell_text_str % cell_text_params)
            else:
                row.append(None)
        ret.append(row)
    return ret


def get_insertions_x(parsed_files):
    """TODO..."""
    ret = []
    for strain in parsed_files:
        for pos in parsed_files[strain]:
            if parsed_files[strain][pos]["mutation_type"] == "insertion":
                ret.append(pos)
    return ret


def get_insertions_y(parsed_files):
    """TODO..."""
    ret = []
    for strain in parsed_files:
        for pos in parsed_files[strain]:
            if parsed_files[strain][pos]["mutation_type"] == "insertion":
                ret.append(strain)
    return ret


def get_deletions_x(parsed_files):
    """TODO..."""
    ret = []
    for strain in parsed_files:
        for pos in parsed_files[strain]:
            if parsed_files[strain][pos]["mutation_type"] == "deletion":
                ret.append(pos)
    return ret


def get_deletions_y(parsed_files):
    """TODO..."""
    ret = []
    for strain in parsed_files:
        for pos in parsed_files[strain]:
            if parsed_files[strain][pos]["mutation_type"] == "deletion":
                ret.append(strain)
    return ret


def get_tables(parsed_files):
    """TODO..."""
    ret = {}
    for strain in parsed_files:
        pos_col = []
        mutation_type_col = []
        ref_col = []
        alt_col = []
        alt_freq_col = []
        ref_codon_col = []
        alt_codon_col = []
        ref_aa_col = []
        alt_aa_col = []
        for pos in parsed_files[strain]:
            pos_col.append(pos)
            cell_data = parsed_files[strain][pos]
            mutation_type_col.append(cell_data["mutation_type"])
            ref_col.append(cell_data["ref"])
            alt_col.append(cell_data["alt"])
            alt_freq_col.append(cell_data["alt_freq"])
            ref_codon_col.append(cell_data["ref_codon"])
            alt_codon_col.append(cell_data["alt_codon"])
            ref_aa_col.append(cell_data["ref_aa"])
            alt_aa_col.append(cell_data["alt_aa"])
        ret[strain] = [
            pos_col, mutation_type_col, ref_col, alt_col, alt_freq_col,
            ref_codon_col, alt_codon_col, ref_aa_col, alt_aa_col
        ]
    return ret
