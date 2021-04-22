"""TODO..."""
import csv
import json
import os


def parse_data_files(dir_):
    """Parses relevant visualization data from ``dir_``.

    This function assists ``get_data``, which is a function that
    prepares data in a format suitable for Plotly functions. However,
    ``parse_data_files`` does not care about Plotly. It simply parses
    tsv files that are in the format of tsv files found in data/, and
    puts them into an easy to iterate Dictionary for ``get_data`` to
    manipulate for Plotly.

    TODO: there is also some data being parsed from some other files.
        We should obtain that data upstream when the files are
        generated, so this function can just focus on parsing a folder.

    :param dir_: Path to folder to parse tsv files from
    :type dir_: String
    :return: Select column data parsed from tsv files in ``dir_``
    :rtype: Dict
    """
    ret = {}
    with open("cds_gene_map.json") as fp:
        # Maps cds info in tsv files to actual genes
        cds_gene_map = json.load(fp)
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

                    gff_feature = row["GFF_FEATURE"]
                    if gff_feature in cds_gene_map:
                        ret[strain][pos]["gene"] = cds_gene_map[gff_feature]
                    else:
                        ret[strain][pos]["gene"] = "n/a"

                    ret[strain][pos]["mutation_name"] = "n/a"
                    ret[strain][pos]["functions"] = "n/a"
                    if row["ALT"][0] == "+":
                        ret[strain][pos]["mutation_type"] = "insertion"
                    elif row["ALT"][0] == "-":
                        ret[strain][pos]["mutation_type"] = "deletion"
                    else:
                        ret[strain][pos]["mutation_type"] = "snp"

    functional_annotations_dict = {}
    functional_annotations_tsv_path = \
        "VOC clade-defining mutations - functional_annotation.tsv"
    with open(functional_annotations_tsv_path) as fp:
        reader = csv.DictReader(fp, delimiter="\t")
        for row in reader:
            strain = row["lineage"]
            mutation_name = row["aa_name"]
            functions = row["function_category"]
            if functions == "":
                continue
            functions = functions.split("|")
            functions = [x.strip() for x in functions]
            functions = "<br>".join(functions)
            if strain not in functional_annotations_dict:
                functional_annotations_dict[strain] = {}
            functional_annotations_dict[strain][mutation_name] = functions

    with open("VOC clade-defining mutations - gff3.tsv") as fp:
        reader = csv.DictReader(fp, delimiter="\t")
        for row in reader:
            attributes_list = row['#attributes'].split(";")
            attributes_nested_list = [x.split("=") for x in attributes_list]
            attributes_dict = {}
            for attribute_list in attributes_nested_list:
                if len(attribute_list) >= 2:
                    attributes_dict[attribute_list[0]] = attribute_list[1]

            if row["#start"] == "":
                continue

            strain = attributes_dict["voc_name"]
            pos = int(row["#start"])
            mutation_name = attributes_dict["Alias"]
            if strain in ret and pos in ret[strain]:
                if mutation_name != "":
                    ret[strain][pos]["mutation_name"] = mutation_name
                if mutation_name in functional_annotations_dict[strain]:
                    ret[strain][pos]["functions"] = \
                        functional_annotations_dict[strain][mutation_name]

    return ret


def get_data(dir_):
    """Get relevant data for Plotly visualizations in this application.

    This will include table data, which is straight forward. But this
    will also include various information related to the main heatmap,
    including heatmap x y coordinates for mutations, insertions,
    deletions, and hover text.

    Basically, this function gives us data to plug into the
    visualization functions of Plotly.

    This relevant data is parsed from tsv files in the form of the tsv
    files found in data/. Other folders with similar formats can be
    parsed too.

    :param dir_: Path to folder to obtain data from
    :type dir_: String
    :return: Information on relevant columns in tsv files stored in
        dir_.
    :rtype: Dict
    """
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
    data["heatmap_x_genes"] =\
        get_heatmap_x_genes(parsed_files, data["heatmap_x"])
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


def get_heatmap_x_genes(parsed_files, heatmap_x):
    """TODO..."""
    ret = []
    with open("cds_gene_map.json") as fp:
        cds_gene_map = json.load(fp)
    for pos in heatmap_x:
        for strain in parsed_files:
            if pos in parsed_files[strain]:
                gene = parsed_files[strain][pos]["gene"]
                if gene != "n/a":
                    ret.append(gene)
                else:
                    ret.append("")
                break

    # We need to fill in intergenic gaps with last gene seen until vcf
    # is more accurate.
    end_3_utr_index = None
    for i in range(0, len(ret)):
        if ret[i] != "":
            if i != 0:
                end_3_utr_index = i
            break
    start_5_utr_index = None
    for i in range(len(ret) - 1, -1, -1):
        if ret[i] != "":
            if i != (len(ret) - 1):
                start_5_utr_index = i
            break
    for i in range(len(ret)):
        if not end_3_utr_index or i < end_3_utr_index:
            continue
        if not start_5_utr_index or i > start_5_utr_index:
            continue
        if ret[i] == "":
            ret[i] = ret[i-1]

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
                cell_text_str = "<b>Mutation name: %s</b><br>" \
                                "<br>" \
                                "<b>Position:</b> %s<br>" \
                                "<b>Gene:</b> %s<br>" \
                                "<br>" \
                                "<b>Reference:</b> %s<br>" \
                                "<b>Alternate:</b> %s<br>" \
                                "<b>Alternate frequency:</b> %s<br>" \
                                "<br>" \
                                "<b>Functions:</b> <br>%s<br>"
                cell_text_params = (cell_data["mutation_name"],
                                    pos,
                                    cell_data["gene"],
                                    cell_data["ref"],
                                    cell_data["alt"],
                                    cell_data["alt_freq"],
                                    cell_data["functions"])
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
        mutation_name_col = []
        ref_col = []
        alt_col = []
        alt_freq_col = []
        functions_col = []
        for pos in parsed_files[strain]:
            pos_col.append(pos)
            cell_data = parsed_files[strain][pos]
            mutation_name_col.append(cell_data["mutation_name"])
            ref_col.append(cell_data["ref"])
            alt_col.append(cell_data["alt"])
            alt_freq_col.append(cell_data["alt_freq"])
            functions_col.append(cell_data["functions"])
        ret[strain] = [
            pos_col, mutation_name_col, ref_col, alt_col, alt_freq_col,
            functions_col
        ]
    return ret
