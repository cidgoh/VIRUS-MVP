"""Functions for obtaining data used in Plotly visualizations.

Entry point is ``get_data``.
"""

from copy import deepcopy
import csv
import json
import os


# TODO update docstrings


def map_pos_to_gene(pos):
    """Map a nucleotide position to a SARS-CoV-2 gene.

    See https://www.ncbi.nlm.nih.gov/nuccore/MN908947.

    :param pos: Nucleotide position
    :type pos: int
    :return: SARS-CoV-2 gene at nucleotide position ``pos``
    :rtype: str
    """
    with open("gene_positions.json") as fp:
        gene_positions_dict = json.load(fp)
    for gene in gene_positions_dict:
        start = gene_positions_dict[gene]["start"]
        end = gene_positions_dict[gene]["end"]
        if start <= pos <= end:
            return gene
    # Intergenic region
    return "n/a"


def parse_gvf_dir(dir_, file_order=None):
    """TODO"""
    if file_order is None:
        file_order = []

    ret = {}
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
            if ext != "gvf":
                continue
            ret[strain] = {}
            with open(entry.path) as fp:
                reader = csv.DictReader(fp, delimiter="\t")
                for row in reader:
                    attrs_first_split = row["#attributes"].split(";")[:-1]
                    attrs_second_split = \
                        [x.split("=", 1) for x in attrs_first_split]
                    attrs = {k: v for k, v in attrs_second_split}

                    pos = row["#start"]
                    if pos not in ret[strain]:
                        ret[strain][pos] = {}
                        ret[strain][pos]["ref"] = attrs["Reference_seq"]
                        ret[strain][pos]["alt"] = attrs["Variant_seq"]
                        ret[strain][pos]["gene"] = attrs["gene"]

                        ao = float(attrs["ao"].split(",")[0])
                        dp = float(attrs["dp"])
                        ret[strain][pos]["alt_freq"] = str(ao / dp)

                        ret[strain][pos]["clade_defining"] = \
                            attrs["clade_defining"]

                        ret[strain][pos]["hidden_cell"] = False

                        if attrs["Name"]:
                            ret[strain][pos]["mutation_name"] = attrs["Name"]
                        else:
                            ret[strain][pos]["mutation_name"] = "n/a"

                        ref_len = len(attrs["Reference_seq"])
                        alt_len = len(attrs["Variant_seq"])
                        if ref_len < alt_len:
                            ret[strain][pos]["mutation_type"] = "insertion"
                        elif ref_len > alt_len:
                            ret[strain][pos]["mutation_type"] = "deletion"
                        else:
                            ret[strain][pos]["mutation_type"] = "snp"

                        ret[strain][pos]["functions"] = []

                    if attrs["function_category"]:
                        function = attrs["function_category"]
                        ret[strain][pos]["functions"] += [function]
    return ret


def filter_parsed_gvf_dirs_by_clade_defining(parsed_gvf_dirs):
    """TODO"""
    ret = deepcopy(parsed_gvf_dirs)
    for strain in parsed_gvf_dirs:
        for pos in parsed_gvf_dirs[strain]:
            if not parsed_gvf_dirs[strain][pos]["clade_defining"]:
                ret[strain][pos]["hidden_cell"] = True
    return ret


def filter_parsed_gvf_dirs_by_freq(parsed_gvf_dirs, min_mutation_freq,
                                   max_mutation_freq):
    """TODO"""
    ret = deepcopy(parsed_gvf_dirs)
    for strain in parsed_gvf_dirs:
        for pos in parsed_gvf_dirs[strain]:
            alt_freq = float(ret[strain][pos]["alt_freq"])
            if alt_freq < min_mutation_freq or alt_freq > max_mutation_freq:
                ret[strain][pos]["hidden_cell"] = True
    return ret


def get_data(dirs, clade_defining=False, hidden_strains=None,
             strain_order=None, min_mutation_freq=None,
             max_mutation_freq=None):
    """TODO"""
    if hidden_strains is None:
        hidden_strains = []
    if strain_order is None:
        strain_order = []

    dir_strains = {}
    file_order = [strain + ".gvf" for strain in strain_order]
    parsed_gvf_dirs = {}
    for dir_ in dirs:
        parsed_gvf_dir = parse_gvf_dir(dir_, file_order)
        parsed_gvf_dirs = {**parsed_gvf_dirs, **parsed_gvf_dir}
        dir_strains[dir_] = list(parsed_gvf_dir.keys())

    visible_parsed_gvf_dirs = \
        {k: v for k, v in parsed_gvf_dirs.items() if k not in hidden_strains}

    if clade_defining:
        visible_parsed_gvf_dirs = \
            filter_parsed_gvf_dirs_by_clade_defining(visible_parsed_gvf_dirs)

    mutation_freq_slider_vals = \
        get_mutation_freq_slider_vals(visible_parsed_gvf_dirs)
    if min_mutation_freq and max_mutation_freq:
        visible_parsed_gvf_dirs = \
            filter_parsed_gvf_dirs_by_freq(visible_parsed_gvf_dirs,
                                           min_mutation_freq,
                                           max_mutation_freq)

    ret = {
        "heatmap_x": get_heatmap_x(parsed_gvf_dirs),
        "heatmap_y": get_heatmap_y(visible_parsed_gvf_dirs),
        "tables": get_tables(visible_parsed_gvf_dirs),
        "histogram_x": get_histogram_x(visible_parsed_gvf_dirs),
        "dir_strains": dir_strains,
        "hidden_strains": hidden_strains,
        "all_strains": get_heatmap_y(parsed_gvf_dirs),
        "mutation_freq_slider_vals": mutation_freq_slider_vals
    }
    ret["insertions_x"] = get_insertions_x(visible_parsed_gvf_dirs,
                                           ret["heatmap_x"],
                                           ret["heatmap_y"])
    ret["insertions_y"] = get_insertions_y(visible_parsed_gvf_dirs,
                                           ret["heatmap_x"],
                                           ret["heatmap_y"])
    ret["deletions_x"] = get_deletions_x(visible_parsed_gvf_dirs,
                                         ret["heatmap_x"],
                                         ret["heatmap_y"])
    ret["deletions_y"] = get_deletions_y(visible_parsed_gvf_dirs,
                                         ret["heatmap_x"],
                                         ret["heatmap_y"])
    ret["heatmap_z"] = \
        get_heatmap_z(visible_parsed_gvf_dirs, ret["heatmap_x"])
    ret["heatmap_cell_text"] = \
        get_heatmap_cell_text(visible_parsed_gvf_dirs, ret["heatmap_x"])
    ret["heatmap_x_genes"] = \
        get_heatmap_x_genes(ret["heatmap_x"])

    return ret


def get_mutation_freq_slider_vals(annotated_data_dirs):
    """Get the mutation freq slider vals from ``annotated_data_dirs``.

    This value is ultimately used when rendering the mutation frequency
    slider. This is really just a sorted list of unique mutation
    frequencies from visible cells in ``annotated_data_dirs``.

    :param annotated_data_dirs: A dictionary containing multiple merged
        ``get_annotated_data_dir`` return values.
    :type annotated_data_dirs: dict
    :return: Lowest to highest sorted list of unique mutation
        frequencies from visible cells in ``annotated_data_dirs``.
    :rtype: list[str]
    """
    alt_freq_set = set()
    for strain in annotated_data_dirs:
        for pos in annotated_data_dirs[strain]:
            if not annotated_data_dirs[strain][pos]["hidden_cell"]:
                alt_freq_set.add(annotated_data_dirs[strain][pos]["alt_freq"])
    ret = sorted(list(alt_freq_set), key=float)
    return ret


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


def get_heatmap_x_genes(heatmap_x):
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
        ret.append(map_pos_to_gene(int(pos)))
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
            cond = pos in annotated_data_dirs[strain] \
                   and not annotated_data_dirs[strain][pos]["hidden_cell"]
            if cond:
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

                functions_set = set(cell_data["functions"])
                functions_str = ""
                for i, fn in enumerate(functions_set):
                    if i == 8:
                        functions_str += "...click for more<br>"
                        break
                    functions_str += fn + "<br>"

                cell_text_str = "<b>Mutation name: %s</b><br>" \
                                "<br>" \
                                "<b>Position:</b> %s<br>" \
                                "<b>Gene:</b> %s<br>" \
                                "<br>" \
                                "<b>Reference:</b> %s<br>" \
                                "<b>Alternate:</b> %s<br>" \
                                "<b>Alternate frequency:</b> %s<br>" \
                                "<br>" \
                                "<b>Functions:</b> <br>%s"
                cell_text_params = (cell_data["mutation_name"],
                                    pos,
                                    cell_data["gene"],
                                    cell_data["ref"],
                                    cell_data["alt"],
                                    cell_data["alt_freq"],
                                    functions_str)
                row.append(cell_text_str % cell_text_params)
            else:
                row.append(None)
        ret.append(row)
    return ret


def get_insertions_x(annotated_data_dirs, heatmap_x, heatmap_y):
    """Get x coordinates of insertion markers to overlay in heatmap.

    Since the underlying structure of the heatmap does not usual
    categorical values for the x-axis, for performance reasons, and
    instead uses the indices of ``heatmap_x``, we must specify the
    indices here--not actual nucleotide positions.

    :param annotated_data_dirs: A dictionary containing multiple merged
        ``get_annotated_data_dir`` return values.
    :type annotated_data_dirs: dict
    :return: List of x coordinate values to display insertion markers
    :rtype: list[int]
    """
    ret = []
    for i, pos in enumerate(heatmap_x):
        for j, strain in enumerate(heatmap_y):
            if pos not in annotated_data_dirs[strain]:
                continue
            mutation_type = annotated_data_dirs[strain][pos]["mutation_type"]
            hidden_cell = annotated_data_dirs[strain][pos]["hidden_cell"]
            if mutation_type == "insertion" and not hidden_cell:
                ret.append(i)
    return ret


def get_insertions_y(annotated_data_dirs, heatmap_x, heatmap_y):
    """Get y coordinates of insertion markers to overlay in heatmap.

    Since the underlying structure of the heatmap does not usual
    categorical values for the y-axis, for performance reasons, and
    instead uses the indices of ``heatmap_y``, we must specify the
    indices here--not actual nucleotide positions.

    :param annotated_data_dirs: A dictionary containing multiple merged
        ``get_annotated_data_dir`` return values.
    :type annotated_data_dirs: dict
    :return: List of y coordinate values to display insertion markers
    :rtype: list[str]
    """
    ret = []
    for i, pos in enumerate(heatmap_x):
        for j, strain in enumerate(heatmap_y):
            if pos not in annotated_data_dirs[strain]:
                continue
            mutation_type = annotated_data_dirs[strain][pos]["mutation_type"]
            hidden_cell = annotated_data_dirs[strain][pos]["hidden_cell"]
            if mutation_type == "insertion" and not hidden_cell:
                ret.append(j)
    return ret


def get_deletions_x(annotated_data_dirs, heatmap_x, heatmap_y):
    """Get x coordinates of deletion markers to overlay in heatmap.

    Since the underlying structure of the heatmap does not usual
    categorical values for the x-axis, for performance reasons, and
    instead uses the indices of ``heatmap_x``, we must specify the
    indices here--not actual nucleotide positions.

    :param annotated_data_dirs: A dictionary containing multiple merged
        ``get_annotated_data_dir`` return values.
    :type annotated_data_dirs: dict
    :return: List of x coordinate values to display insertion markers
    :rtype: list[int]
    """
    ret = []
    for i, pos in enumerate(heatmap_x):
        for j, strain in enumerate(heatmap_y):
            if pos not in annotated_data_dirs[strain]:
                continue
            mutation_type = annotated_data_dirs[strain][pos]["mutation_type"]
            hidden_cell = annotated_data_dirs[strain][pos]["hidden_cell"]
            if mutation_type == "deletion" and not hidden_cell:
                ret.append(i)
    return ret


def get_deletions_y(annotated_data_dirs, heatmap_x, heatmap_y):
    """Get y coordinates of deletion markers to overlay in heatmap.

    Since the underlying structure of the heatmap does not usual
    categorical values for the y-axis, for performance reasons, and
    instead uses the indices of ``heatmap_y``, we must specify the
    indices here--not actual nucleotide positions.

    :param annotated_data_dirs: A dictionary containing multiple merged
        ``get_annotated_data_dir`` return values.
    :type annotated_data_dirs: dict
    :return: List of y coordinate values to display deletion markers
    :rtype: list[str]
    """
    ret = []
    for i, pos in enumerate(heatmap_x):
        for j, strain in enumerate(heatmap_y):
            if pos not in annotated_data_dirs[strain]:
                continue
            mutation_type = annotated_data_dirs[strain][pos]["mutation_type"]
            hidden_cell = annotated_data_dirs[strain][pos]["hidden_cell"]
            if mutation_type == "deletion" and not hidden_cell:
                ret.append(j)
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


def get_histogram_x(annotated_data_dirs):
    """Get x data values binned by Plotly when producing the histogram.

    This is just the positions containing mutations, with duplicates
    permitted for mutations shared by strains.

    :param annotated_data_dirs: A dictionary containing multiple merged
        ``get_annotated_data_dir`` return values.
    :type annotated_data_dirs: dict
    :return: List of x data values used in histogram view
    :rtype: list[str]
    """
    ret = []
    for strain in annotated_data_dirs:
        for pos in annotated_data_dirs[strain]:
            hidden_cell = annotated_data_dirs[strain][pos]["hidden_cell"]
            if not hidden_cell:
                ret.append(pos)
    return ret
