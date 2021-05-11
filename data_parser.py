"""Functions for obtaining data used in Plotly visualizations.

Entry point is ``get_data``.
"""

from copy import deepcopy
import csv
import json
import os


def parse_gff3_file(path):
    """Parses relevant visualization data from gff3 file.

    The return type is like:
    ``{strain1: {pos1: [gff3_attributes_dicts], pos2:
    [gff3_attributes_dicts], strain2: ...}``, where
    ``gff3_attributes_dicts`` are dictionaries containing attribute
    information for >1 mutations that may be at a nuceleotide position.

    :param path: Path to gff3 file
    :type path: str
    :return: Dictionary containing information parsed from gff3 file
    :rtype: dict
    """
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
            else:
                attributes_dict["functions"] = ""

            annotations_dict[strain][pos].append(attributes_dict)

    return annotations_dict


def parse_data_dir(dir_, file_order=None):
    """Parses relevant visualization data from ``dir_``.

    This function assists ``get_data``, which is a function that
    prepares data in a format suitable for Plotly functions. However,
    ``parse_data_dir`` does not care about Plotly. It simply parses
    tsv files that are in the format of tsv files found in data/, and
    puts them into an easy to iterate Dictionary for ``get_data`` to
    manipulate for Plotly. The filename of these tsv files is
    interpreted to be the strain name.

    The files are parsed in order of modification date. However, this
    can be overridden by listing the files you want parsed first in
    ``file_order``. Any files not found in ``file_order`` will still be
    parsed by modification date.

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
                    pos = row["POS"]
                    ret[strain][pos] = {}
                    ret[strain][pos]["ref"] = row["REF"]
                    ret[strain][pos]["alt"] = row["ALT"]
                    ret[strain][pos]["alt_freq"] = row["ALT_FREQ"]
                    ret[strain][pos]["ref_codon"] = row["REF_CODON"]
                    ret[strain][pos]["alt_codon"] = row["ALT_CODON"]
                    ret[strain][pos]["ref_aa"] = row["REF_AA"]
                    ret[strain][pos]["alt_aa"] = row["ALT_AA"]
                    # We may update this in ``get_annotated_data_dir``
                    ret[strain][pos]["clade_defining"] = False

                    gff_feature = row["GFF_FEATURE"]
                    if gff_feature in cds_gene_map:
                        ret[strain][pos]["gene"] = cds_gene_map[gff_feature]
                    else:
                        ret[strain][pos]["gene"] = "n/a"

                    # We may update these in ``get_annotated_data_dir``
                    ret[strain][pos]["mutation_name"] = "n/a"
                    ret[strain][pos]["functions"] = "n/a"

                    if row["ALT"][0] == "+":
                        ret[strain][pos]["mutation_type"] = "insertion"
                    elif row["ALT"][0] == "-":
                        ret[strain][pos]["mutation_type"] = "deletion"
                    else:
                        ret[strain][pos]["mutation_type"] = "snp"
    return ret


def get_annotated_data_dir(parsed_data_dir, gff3_annotations):
    """Annotate ``parse_data_dir`` val with ``parse_gff3_file`` val.

    Although ``parse_data_dir`` provides the information needed for a
    barebones visualization, such as mutation positions and frequency,
    there is information returned by ``parse_gff3_file`` that is also
    valuable for visualization purposes, such as clade defining
    mutations and mutation functions.

    :param parsed_data_dir: ``parse_data_dir`` return value
    :type parsed_data_dir: dict
    :param gff3_annotations: ``parse_gff3_file`` return value
    :type gff3_annotations: dict
    :return: ``parsed_data_dir`` with additional information added from
        ``gff3_annotations``.
    :rtype: dict
    """
    annotated_data_dir = deepcopy(parsed_data_dir)
    for strain in parsed_data_dir:
        if strain not in gff3_annotations:
            continue
        for pos in parsed_data_dir[strain]:
            if pos not in gff3_annotations[strain]:
                continue
            parsed_data_dir_mutation = parsed_data_dir[strain][pos]
            # There is some syntax differences between the gff3 and
            # data files, so we need to modify the ref to alt mutation
            # from the data file we are looking for to match the format
            # expected by the gff3 file.
            matching_gff3_del = parsed_data_dir_mutation["ref"]
            matching_gff3_ins = parsed_data_dir_mutation["alt"]
            if len(matching_gff3_ins) and matching_gff3_ins[0] in ["-", "+"]:
                matching_gff3_ins = matching_gff3_ins[1:]

            gff3_annotations_mutation = None
            for mutation in gff3_annotations[strain][pos]:
                if mutation["del"] == matching_gff3_del \
                        and mutation["ins"] == matching_gff3_ins:
                    gff3_annotations_mutation = mutation
                    break
            # We found a mutation in the gff3 file that corresponds to
            # the mutation in the data dir we are currently visiting in
            # the for loop.
            if gff3_annotations_mutation:
                if gff3_annotations_mutation["clade_defining"] == "true":
                    annotated_data_dir[strain][pos]["clade_defining"] = True
                if gff3_annotations_mutation["Name"]:
                    annotated_data_dir[strain][pos]["mutation_name"] = \
                        gff3_annotations_mutation["Name"]
                if gff3_annotations_mutation["functions"]:
                    annotated_data_dir[strain][pos]["functions"] = \
                        gff3_annotations_mutation["functions"]
    return annotated_data_dir


def filter_clade_defining_mutations(annotated_data_dirs, weak_filter):
    """Filter ``annotated_data_dirs`` for clade defining mutations.

    Returns a copy of ``annotated_data_dirs``, with the only the clade
    defining mutations. You can specify strains in
    ``annotated_data_dirs`` to apply a weak filter to. Strains that are
    filtered weakly will not be filtered by the clade defining
    attribute, but will instead have their mutations filtered based on
    whether their mutations share a position with clade defining
    mutations from non-weakly filtered strains. This is useful for user
    uploaded strains.

    :param annotated_data_dirs: A dictionary containing multiple merged
        ``get_annotated_data_dir`` return values.
    :type annotated_data_dirs: dict
    :param weak_filter: List of strains to filter based on whether they
        share a nucleotide position with clade defining mutations from
        other strains, instead of the clade defining attribute of the
        mutations themselves.
    :type weak_filter: list[str]
    :return: Filtered copy of ``annotated_data_dirs``, containing clade
        defining mutations only.
    :rtype: dict
    """
    seen_pos_set = set()
    ret = deepcopy(annotated_data_dirs)
    for strain in annotated_data_dirs:
        if strain in weak_filter:
            continue
        for pos in annotated_data_dirs[strain]:
            if annotated_data_dirs[strain][pos]["clade_defining"]:
                seen_pos_set.add(pos)
            else:
                ret[strain].pop(pos)
    for strain in weak_filter:
        for pos in annotated_data_dirs[strain]:
            if pos not in seen_pos_set:
                ret[strain].pop(pos)
    return ret


def get_data(dirs, gff3_annotations, clade_defining=False, hidden_strains=None,
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
    ``data/``, and from annotations parsed from a gff3 file, in the
    form of ``gff3_annotations.tsv``.

    We will also keep track of the directory each strain came from,
    because it becomes useful when distinguishing user uploaded strains
    from other strains. We will also keep track of strains the user has
    chosen to hide.

    :param dirs: List of paths to folders to obtain data from
    :type dirs: list[str]
    :param gff3_annotations: ``parse_gff3_file`` return value
    :type gff3_annotations: dict
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

    annotated_data_dirs = {}
    dir_strains = {}
    file_order = [strain + ".tsv" for strain in strain_order]
    for dir_ in dirs:
        parsed_data_dir = parse_data_dir(dir_, file_order)
        annotated_data_dir = \
            get_annotated_data_dir(parsed_data_dir, gff3_annotations)
        annotated_data_dirs = {**annotated_data_dirs, **annotated_data_dir}
        dir_strains[dir_] = list(parsed_data_dir.keys())

    if clade_defining:
        weak_filter = dir_strains["user_data"]
        annotated_data_dirs = \
            filter_clade_defining_mutations(annotated_data_dirs,
                                            weak_filter=weak_filter)

    all_strain_data = annotated_data_dirs
    visible_strain_data = \
        {k: v for k, v in all_strain_data.items() if k not in hidden_strains}

    data = {
        "heatmap_x": get_heatmap_x(visible_strain_data),
        "heatmap_y": get_heatmap_y(visible_strain_data),
        "insertions_x": get_insertions_x(visible_strain_data),
        "insertions_y": get_insertions_y(visible_strain_data),
        "deletions_x": get_deletions_x(visible_strain_data),
        "deletions_y": get_deletions_y(visible_strain_data),
        "tables": get_tables(visible_strain_data),
        "dir_strains": dir_strains,
        "hidden_strains": hidden_strains,
        "all_strains": get_heatmap_y(all_strain_data)
    }
    data["heatmap_z"] = \
        get_heatmap_z(visible_strain_data, data["heatmap_x"])
    data["heatmap_cell_text"] = \
        get_heatmap_cell_text(visible_strain_data, data["heatmap_x"])
    data["heatmap_x_genes"] =\
        get_heatmap_x_genes(visible_strain_data, data["heatmap_x"])
    return data


def get_heatmap_x(annotated_data_dirs):
    """Get x axis values of heatmap cells.

    These are the nucleotide position of mutations.

    :param annotated_data_dirs: A dictionary containing multiple merged
        ``get_annotated_data_dir`` return values.
    :type annotated_data_dirs: dict
    :return: List of x axis values
    :rtype: list[str]
    """
    seen = set()
    ret = []
    for strain in annotated_data_dirs:
        for pos in annotated_data_dirs[strain]:
            if pos not in seen:
                seen.add(pos)
                ret.append(pos)
    ret.sort(key=int)
    return ret


def get_heatmap_x_genes(annotated_data_dirs, heatmap_x):
    """Get gene values corresponding to x axis values in heatmap.

    :param annotated_data_dirs: A dictionary containing multiple merged
        ``get_annotated_data_dir`` return values.
    :type annotated_data_dirs: dict
    :param heatmap_x: ``get_heatmap_x`` return value
    :type heatmap_x: list[str]
    :return: List of genes for each x in ``heatmap_x``
    :rtype: list[str]
    """
    ret = []
    for pos in heatmap_x:
        for strain in annotated_data_dirs:
            if pos in annotated_data_dirs[strain]:
                gene = annotated_data_dirs[strain][pos]["gene"]
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


def get_heatmap_y(annotated_data_dirs):
    """Get y axis values of heatmap cells.

    These are the VOC strains.

    :param annotated_data_dirs: A dictionary containing multiple merged
        ``get_annotated_data_dir`` return values.
    :type annotated_data_dirs: dict
    :return: List of y axis values
    :rtype: list[str]
    """
    ret = []
    for strain in annotated_data_dirs:
        ret.append(strain)
    return ret


def get_heatmap_z(annotated_data_dirs, heatmap_x):
    """Get z values of heatmap cells.

    These are the mutation frequencies, and the z values dictate the
    colours of the heatmap cells.

    :param annotated_data_dirs: A dictionary containing multiple merged
        ``get_annotated_data_dir`` return values.
    :type annotated_data_dirs: dict
    :param heatmap_x: ``get_heatmap_x`` return value
    :type heatmap_x: list[int]
    :return: List of z values
    :rtype: list[str]
    """
    ret = []
    for strain in annotated_data_dirs:
        row = []
        for pos in heatmap_x:
            if pos in annotated_data_dirs[strain]:
                row.append(annotated_data_dirs[strain][pos]["alt_freq"])
            else:
                row.append(None)
        ret.append(row)
    return ret


def get_heatmap_cell_text(annotated_data_dirs, heatmap_x):
    """Get hover text of heatmap cells.

    :param annotated_data_dirs: A dictionary containing multiple merged
        ``get_annotated_data_dir`` return values.
    :type annotated_data_dirs: dict
    :param heatmap_x: ``get_heatmap_x`` return value
    :type heatmap_x: list[int]
    :return: List of D3 formatted text values for each x y coordinate
        in ``heatmap_x``.
    :rtype: list[str]
    """
    ret = []
    for strain in annotated_data_dirs:
        row = []
        for pos in heatmap_x:
            if pos in annotated_data_dirs[strain]:
                cell_data = annotated_data_dirs[strain][pos]
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


def get_insertions_x(annotated_data_dirs):
    """Get x coordinates of insertion markers to overlay in heatmap.

    :param annotated_data_dirs: A dictionary containing multiple merged
        ``get_annotated_data_dir`` return values.
    :type annotated_data_dirs: dict
    :return: List of x coordinate values to display insertion markers
    :rtype: list[int]
    """
    ret = []
    for strain in annotated_data_dirs:
        for pos in annotated_data_dirs[strain]:
            mutation_type = annotated_data_dirs[strain][pos]["mutation_type"]
            if mutation_type == "insertion":
                ret.append(pos)
    return ret


def get_insertions_y(annotated_data_dirs):
    """Get y coordinates of insertion markers to overlay in heatmap.

    :param annotated_data_dirs: A dictionary containing multiple merged
        ``get_annotated_data_dir`` return values.
    :type annotated_data_dirs: dict
    :return: List of y coordinate values to display insertion markers
    :rtype: list[str]
    """
    ret = []
    for strain in annotated_data_dirs:
        for pos in annotated_data_dirs[strain]:
            if annotated_data_dirs[strain][pos]["mutation_type"] == "insertion":
                ret.append(strain)
    return ret


def get_deletions_x(annotated_data_dirs):
    """Get x coordinates of deletion markers to overlay in heatmap.

    :param annotated_data_dirs: A dictionary containing multiple merged
        ``get_annotated_data_dir`` return values.
    :type annotated_data_dirs: dict
    :return: List of x coordinate values to display insertion markers
    :rtype: list[int]
    """
    ret = []
    for strain in annotated_data_dirs:
        for pos in annotated_data_dirs[strain]:
            if annotated_data_dirs[strain][pos]["mutation_type"] == "deletion":
                ret.append(pos)
    return ret


def get_deletions_y(annotated_data_dirs):
    """Get y coordinates of deletion markers to overlay in heatmap.

    :param annotated_data_dirs: A dictionary containing multiple merged
        ``get_annotated_data_dir`` return values.
    :type annotated_data_dirs: dict
    :return: List of y coordinate values to display deletion markers
    :rtype: list[str]
    """
    ret = []
    for strain in annotated_data_dirs:
        for pos in annotated_data_dirs[strain]:
            if annotated_data_dirs[strain][pos]["mutation_type"] == "deletion":
                ret.append(strain)
    return ret


def get_tables(annotated_data_dirs):
    """Get table column data for each y axis value or strain.

    The columns are represented as lists.

    :param annotated_data_dirs: A dictionary containing multiple merged
        ``get_annotated_data_dir`` return values.
    :type annotated_data_dirs: dict
    :return: Dictionary with keys for each strain, and a list of lists
        values representing columns for each strain.
    :rtype: dict[str, list[list]]
    """
    ret = {}
    for strain in annotated_data_dirs:
        pos_col = []
        mutation_name_col = []
        ref_col = []
        alt_col = []
        alt_freq_col = []
        functions_col = []
        for pos in annotated_data_dirs[strain]:
            pos_col.append(pos)
            cell_data = annotated_data_dirs[strain][pos]
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
