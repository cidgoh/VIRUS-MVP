"""TODO..."""
import csv
import os


def parse_data_files():
    """TODO..."""
    ret = {}
    with os.scandir("data") as it:
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
                    if row["ALT"][0] == "+":
                        ret[strain][pos]["mutation_type"] = "insertion"
                    elif row["ALT"][0] == "-":
                        ret[strain][pos]["mutation_type"] = "deletion"
                    else:
                        ret[strain][pos]["mutation_type"] = "snp"
            continue
    return ret


def get_data():
    """TODO..."""
    parsed_files = parse_data_files()
    data = {
        "heatmap_x": get_heatmap_x(parsed_files),
        "heatmap_y": get_heatmap_y(parsed_files),
        "heatmap_z": get_heatmap_z(parsed_files),
        "heatmap_cell_text": get_heatmap_cell_text(parsed_files),
        "insertions_x": get_insertions_x(parsed_files),
        "insertions_y": get_insertions_y(parsed_files),
        "deletions_x": get_deletions_x(parsed_files),
        "deletions_y": get_deletions_y(parsed_files),
        "tables": get_tables(parsed_files)
    }
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


def get_heatmap_z(parsed_files):
    """TODO..."""
    ret = []
    heatmap_x = get_heatmap_x(parsed_files)
    for strain in parsed_files:
        row = []
        for pos in heatmap_x:
            if pos in parsed_files[strain]:
                row.append(parsed_files[strain][pos]["alt_freq"])
            else:
                row.append(None)
        ret.append(row)
    return ret


def get_heatmap_cell_text(parsed_files):
    """TODO..."""
    ret = []
    heatmap_x = get_heatmap_x(parsed_files)
    for strain in parsed_files:
        row = []
        for pos in heatmap_x:
            if pos in parsed_files[strain]:
                cell_data = parsed_files[strain][pos]
                cell_text_str = "Pos %s; %s to %s; Freq %s"
                cell_text_params = (pos,
                                    cell_data["ref"],
                                    cell_data["alt"],
                                    cell_data["alt_freq"])
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
        ref_col = []
        alt_col = []
        alt_freq_col = []
        for pos in parsed_files[strain]:
            pos_col.append(pos)
            cell_data = parsed_files[strain][pos]
            ref_col.append(cell_data["ref"])
            alt_col.append(cell_data["alt"])
            alt_freq_col.append(cell_data["alt_freq"])
        ret[strain] = [pos_col, ref_col, alt_col, alt_freq_col]
    return ret
