"""Functions for obtaining data used in Plotly visualizations.

Entry point is ``get_data``.
"""

import csv
import json
import os


def parse_gff3_file(path):
    """TODO"""
    # TODO eventually the functions will be included in the gff3 file
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
            # TODO: This gets formatted in Plotly hover text. In the
            #  spirit of this function, we should make this a list, and
            #  format it in ``get_data``.
            functions = "<br>".join(functions)
            if strain not in functional_annotations_dict:
                functional_annotations_dict[strain] = {}
            functional_annotations_dict[strain][mutation_name] = functions

    annotations_dict = {}
    with open(path) as fp:
        reader = csv.DictReader(fp, delimiter="\t")
        for row in reader:
            if row["#start"] == "":
                continue

            attributes_list = row["#attributes"].split(";")
            attributes_nested_list = [x.split("=") for x in attributes_list]
            attributes_dict = {}
            for nested_list in attributes_nested_list:
                if len(nested_list) >= 2:
                    key = nested_list[0]
                    val = nested_list[1]
                    attributes_dict[key] = val

            strain = attributes_dict["voc_name"]
            pos = int(row["#start"])
            if strain not in annotations_dict:
                annotations_dict[strain] = {}
            if pos not in annotations_dict[strain]:
                annotations_dict[strain][pos] = []

            mutation_name = attributes_dict["Alias"]
            if strain in functional_annotations_dict \
                    and mutation_name in functional_annotations_dict[strain]:
                attributes_dict["functions"] = \
                    functional_annotations_dict[strain][mutation_name]

            annotations_dict[strain][pos].append(attributes_dict)

    return annotations_dict


def parse_data_files(dir_, file_order=None):
    """Parses relevant visualization data from ``dir_``.

    This function assists ``get_data``, which is a function that
    prepares data in a format suitable for Plotly functions. However,
    ``parse_data_files`` does not care about Plotly. It simply parses
    tsv files that are in the format of tsv files found in data/, and
    puts them into an easy to iterate Dictionary for ``get_data`` to
    manipulate for Plotly. The filename of these tsv files is
    interpreted to be the strain name.

    The files are parsed in order of modification date. However, this
    can be overridden by listing the files you want parsed first in
    ``file_order``. Any files not found in ``file_order`` will still be
    parsed by modification date.

    TODO: there is also some data being parsed from some other files.
        We should obtain that data upstream when the files are
        generated, so this function can just focus on parsing a folder.

    :param dir_: Path to folder to parse tsv files from
    :type dir_: str
    :param file_order: List of filenames corresponding to files to
        parse first, if they exist in ``dir_``.
    :type file_order: list[str]
    :return: Select column data parsed from tsv files in ``dir_``
    :rtype: dict
    """
    if file_order is None:
        file_order = []

    ret = {}
    with open("cds_gene_map.json") as fp:
        # Maps cds info in tsv files to actual genes
        cds_gene_map = json.load(fp)
    with os.scandir(dir_) as it:
        # Iterate through tsv files in dir_ sorted by ``file_order``
        # first, and then modification time.
        def key(e):
            if e.name in file_order:
                return file_order.index(e.name)
            else:
                return os.path.getmtime(e)
        for entry in sorted(it, key=key):
            strain, ext = entry.name.rsplit(".", 1)
            if ext != "tsv":
                continue
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
                    # We update this later
                    ret[strain][pos]["clade_defining"] = False

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

    # TODO: we should add functionality to vcf files upstream of this
    #  codebase.
    # TODO: how do we do clade defining mutations for user uploaded
    #  files?
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
            # TODO: This gets formatted in Plotly hover text. In the
            #  spirit of this function, we should make this a list, and
            #  format it in ``get_data``.
            functions = "<br>".join(functions)
            if strain not in functional_annotations_dict:
                functional_annotations_dict[strain] = {}
            functional_annotations_dict[strain][mutation_name] = functions

    # TODO: we should add clade defining key to vcf files upstream of
    #  this codebase.
    with open("VOC clade-defining mutations - gff3.tsv") as fp:
        reader = csv.DictReader(fp, delimiter="\t")
        for row in reader:
            attributes_list = row["#attributes"].split(";")
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
                ret[strain][pos]["clade_defining"] = True
                if mutation_name != "":
                    ret[strain][pos]["mutation_name"] = mutation_name
                if mutation_name in functional_annotations_dict[strain]:
                    ret[strain][pos]["functions"] = \
                        functional_annotations_dict[strain][mutation_name]

    return ret


def get_data(dirs, clade_defining=False, hidden_strains=None,
             strain_order=None):
    """Get relevant data for Plotly visualizations in this application.

    This will include table data, which is straight forward. But this
    will also include various information related to the main heatmap,
    including heatmap x y coordinates for mutations, insertions,
    deletions, and hover text.

    Basically, this function gives us data to plug into the
    visualization functions of Plotly.

    This relevant data is parsed from tsv files across one or more
    folders, with each tsv file in the form of the tsv files found in
    ``data/``.

    We will also keep track of the directory each strain came from,
    because it becomes useful when distinguishing user uploaded strains
    from other strains. We will also keep track of strains the user has
    chosen to hide.

    :param dirs: List of paths to folders to obtain data from
    :type dirs: list[str]
    :param clade_defining: Get data for clade defining mutations only
    :type clade_defining: bool
    :param hidden_strains: List of strains from the dirs that the user
        does not want to display in the heatmap and table.
    :type hidden_strains: list[str]
    :param strain_order: Order of strains from the dirs that the user
        wants to display in the heatmap and table.
    :type strain_order: list[str]
    :return: Information on relevant columns in tsv files stored in
        folders listed in dirs.
    :rtype: dict
    """
    if hidden_strains is None:
        hidden_strains = []
    if strain_order is None:
        strain_order = []

    parsed_files = {}
    dir_strains = {}
    file_order = [strain + ".tsv" for strain in strain_order]
    for dir_ in dirs:
        this_parsed_files = parse_data_files(dir_, file_order)
        dir_strains[dir_] = list(this_parsed_files.keys())
        parsed_files = {**parsed_files, **this_parsed_files}

    if clade_defining:
        for strain in parsed_files:
            kv_pairs = parsed_files[strain].items()
            parsed_files[strain] = \
                {k: v for k, v in kv_pairs if v["clade_defining"]}

    unfiltered_parsed_files = parsed_files
    parsed_files =\
        {k: v for k, v in parsed_files.items() if k not in hidden_strains}

    data = {
        "heatmap_x": get_heatmap_x(parsed_files),
        "heatmap_y": get_heatmap_y(parsed_files),
        "insertions_x": get_insertions_x(parsed_files),
        "insertions_y": get_insertions_y(parsed_files),
        "deletions_x": get_deletions_x(parsed_files),
        "deletions_y": get_deletions_y(parsed_files),
        "tables": get_tables(parsed_files),
        "dir_strains": dir_strains,
        "hidden_strains": hidden_strains,
        "all_strains": get_heatmap_y(unfiltered_parsed_files)
    }
    data["heatmap_z"] = get_heatmap_z(parsed_files, data["heatmap_x"])
    data["heatmap_cell_text"] = \
        get_heatmap_cell_text(parsed_files, data["heatmap_x"])
    data["heatmap_x_genes"] =\
        get_heatmap_x_genes(parsed_files, data["heatmap_x"])
    return data


def get_heatmap_x(parsed_files):
    """Get x axis values of heatmap cells.

    These are the nucleotide position of mutations.

    :param parsed_files: ``parse_data_files`` return value
    :type parsed_files: dict
    :return: List of x axis values
    :rtype: list[int]
    """
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
    """Get gene values corresponding to x axis values in heatmap.

    :param parsed_files: ``parse_data_files`` return value
    :type parsed_files: dict
    :param heatmap_x: ``get_heatmap_x`` return value
    :type heatmap_x: list[int]
    :return: List of genes for each x in ``heatmap_x``
    :rtype: list[str]
    """
    ret = []
    for pos in heatmap_x:
        for strain in parsed_files:
            if pos in parsed_files[strain]:
                gene = parsed_files[strain][pos]["gene"]
                if gene != "n/a":
                    ret.append(gene)
                else:
                    ret.append("")
                break

    # TODO: We need to fill in intergenic gaps with last gene seen
    #  until vcf is more accurate.
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
    """Get y axis values of heatmap cells.

    These are the VOC strains.

    :param parsed_files: ``parse_data_files`` return value
    :type parsed_files: dict
    :return: List of y axis values
    :rtype: list[str]
    """
    ret = []
    for strain in parsed_files:
        ret.append(strain)
    return ret


def get_heatmap_z(parsed_files, heatmap_x):
    """Get z values of heatmap cells.

    These are the mutation frequencies, and the z values dictate the
    colours of the heatmap cells.

    :param parsed_files: ``parse_data_files`` return value
    :type parsed_files: dict
    :param heatmap_x: ``get_heatmap_x`` return value
    :type heatmap_x: list[int]
    :return: List of z values
    :rtype: list[str]
    """
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
    """Get hover text of heatmap cells.

    :param parsed_files: ``parse_data_files`` return value
    :type parsed_files: dict
    :param heatmap_x: ``get_heatmap_x`` return value
    :type heatmap_x: list[int]
    :return: List of D3 formatted text values for each x y coordinate
        in ``heatmap_x``.
    :rtype: list[str]
    """
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
    """Get x coordinates of insertion markers to overlay in heatmap.

    :param parsed_files: ``parse_data_files`` return value
    :type parsed_files: dict
    :return: List of x coordinate values to display insertion markers
    :rtype: list[int]
    """
    ret = []
    for strain in parsed_files:
        for pos in parsed_files[strain]:
            if parsed_files[strain][pos]["mutation_type"] == "insertion":
                ret.append(pos)
    return ret


def get_insertions_y(parsed_files):
    """Get y coordinates of insertion markers to overlay in heatmap.

    :param parsed_files: ``parse_data_files`` return value
    :type parsed_files: dict
    :return: List of y coordinate values to display insertion markers
    :rtype: list[str]
    """
    ret = []
    for strain in parsed_files:
        for pos in parsed_files[strain]:
            if parsed_files[strain][pos]["mutation_type"] == "insertion":
                ret.append(strain)
    return ret


def get_deletions_x(parsed_files):
    """Get x coordinates of deletion markers to overlay in heatmap.

    :param parsed_files: ``parse_data_files`` return value
    :type parsed_files: dict
    :return: List of x coordinate values to display insertion markers
    :rtype: list[int]
    """
    ret = []
    for strain in parsed_files:
        for pos in parsed_files[strain]:
            if parsed_files[strain][pos]["mutation_type"] == "deletion":
                ret.append(pos)
    return ret


def get_deletions_y(parsed_files):
    """Get y coordinates of deletion markers to overlay in heatmap.

    :param parsed_files: ``parse_data_files`` return value
    :type parsed_files: dict
    :return: List of y coordinate values to display deletion markers
    :rtype: list[str]
    """
    ret = []
    for strain in parsed_files:
        for pos in parsed_files[strain]:
            if parsed_files[strain][pos]["mutation_type"] == "deletion":
                ret.append(strain)
    return ret


def get_tables(parsed_files):
    """Get table column data for each y axis value or strain.

    The columns are represented as lists.

    :param parsed_files: ``parse_data_files`` return value
    :type parsed_files: dict
    :return: Dictionary with keys for each strain, and a list of lists
        values representing columns for each strain.
    :rtype: dict[str, list[list]]
    """
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
