"""Functions for obtaining data used in Plotly visualizations.

Entry point is ``get_data``.
"""

from copy import deepcopy
import csv
from itertools import islice
import os


from definitions import GENE_POSITIONS_DICT


def map_pos_to_gene(pos):
    """Map a nucleotide position to a SARS-CoV-2 gene.

    See https://www.ncbi.nlm.nih.gov/nuccore/MN908947.

    :param pos: Nucleotide position
    :type pos: int
    :return: SARS-CoV-2 gene at nucleotide position ``pos``
    :rtype: str
    """
    for gene in GENE_POSITIONS_DICT:
        start = GENE_POSITIONS_DICT[gene]["start"]
        end = GENE_POSITIONS_DICT[gene]["end"]
        if start <= pos <= end:
            return gene
    return "INTERGENIC"


def parse_gvf_dir(dir_):
    """Parse a directory with gvf files for relevant data.

    This supplies ``get_data`` with the relevant information it needs
    from gvf files to generate the data used in visualizations.

    :param dir_: Path to directory to parse
    :type dir_: str
    :return: Relevant strain data from gvf files used by ``get_data``
    :rtype: dict
    """
    ret = {}
    for entry in os.scandir(dir_):
        filename, ext = entry.name.rsplit(".", 1)
        if ext != "gvf":
            continue
        with open(entry.path, encoding="utf-8") as fp:
            # Skip gvf header rows
            reader = csv.DictReader(islice(fp, 3, None), delimiter="\t")

            parsing_first_row = True

            for row in reader:
                attrs_first_split = row["#attributes"].split(";")[:-1]
                attrs_second_split = \
                    [x.split("=", 1) for x in attrs_first_split]
                attrs = {k: v for k, v in attrs_second_split}

                if parsing_first_row:
                    # Default values
                    strain = filename
                    who_variant = None
                    status = None

                    if "viral_lineage" in attrs:
                        strain = attrs["viral_lineage"]
                    if "who_variant" in attrs:
                        strain += " (" + attrs["who_variant"] + ")"
                        who_variant = attrs["who_variant"]
                    if "status" in attrs:
                        status = attrs["status"]

                    ret[strain] = {
                        "mutations": {},
                        "who_variant": who_variant,
                        "status": status
                    }

                    parsing_first_row = False

                pos = row["#start"]
                if pos not in ret[strain]["mutations"]:
                    ret[strain]["mutations"][pos] = []
                    mutation_types = row["#type"].split(",")
                    num_of_mutations = len(mutation_types)
                    for i in range(num_of_mutations):
                        mutation_dict = {
                            "ref": attrs["Reference_seq"],
                            "alt": attrs["Variant_seq"].split(",")[i],
                            "gene": attrs["vcf_gene"],
                            "ao": float(attrs["ao"].split(",")[i]),
                            "dp": float(attrs["dp"]),
                            "clade_defining":
                                attrs["clade_defining"] == "True",
                            "hidden_cell": False,
                            "mutation_name": attrs["Name"],
                            "functions": {}
                        }
                        alt_freq = mutation_dict["ao"]/mutation_dict["dp"]
                        mutation_dict["alt_freq"] = str(round(alt_freq, 4))
                        type = mutation_types[i]
                        if type == "ins":
                            mutation_dict["mutation_type"] = "insertion"
                        elif type == "del":
                            mutation_dict["mutation_type"] = "deletion"
                        else:
                            mutation_dict["mutation_type"] = "snp"
                        ret[strain]["mutations"][pos].append(mutation_dict)

                fn_category = attrs["function_category"].strip('"')
                fn_desc = attrs["function_description"].strip('"')
                fn_source = attrs["source"].strip('"')
                fn_citation = attrs["citation"].strip('"')
                fn_dict = {}
                if fn_category:
                    if fn_category not in fn_dict:
                        fn_dict[fn_category] = {}
                    fn_dict[fn_category][fn_desc] = \
                        {"source": fn_source, "citation": fn_citation}
                for i in range(len(ret[strain]["mutations"][pos])):
                    parsed_mutation = ret[strain]["mutations"][pos]
                    parsed_mutation[i]["functions"].update(fn_dict)

    return ret


def filter_parsed_mutations_by_clade_defining(parsed_mutations):
    """Hide non-clade defining mutations from parsed gvf mutations.

    :param parsed_mutations: ``parse_gvf_dir`` return "mutations" value
    :type parsed_mutations: dict
    :return: ``parsed_gvf_dirs`` with non-clade defining mutations
        labeled as hidden.
    :rtype: dict
    """
    ret = deepcopy(parsed_mutations)
    for strain in parsed_mutations:
        for pos in parsed_mutations[strain]:
            for i, mutation in enumerate(parsed_mutations[strain][pos]):
                if not mutation["clade_defining"]:
                    ret[strain][pos][i]["hidden_cell"] = True
    return ret


def filter_parsed_mutations_by_freq(parsed_mutations, min_mutation_freq,
                                    max_mutation_freq):
    """Hide mutations of specific frequencies from parsed gvf file.

    :param parsed_mutations: ``parse_gvf_dir`` return "mutations" value
    :type parsed_mutations: dict
    :param min_mutation_freq: Minimum mutation frequency required to
        not hide mutations.
    :type min_mutation_freq: float
    :param max_mutation_freq: Maximum mutation frequency required to
        not hide mutations.
    :type max_mutation_freq: float
    :return: ``parsed_gvf_dirs`` with mutations of specified
        frequencies labeled as hidden.
    :rtype: dict
    """
    ret = deepcopy(parsed_mutations)
    for strain in parsed_mutations:
        for pos in parsed_mutations[strain]:
            for i, mutation in enumerate(parsed_mutations[strain][pos]):
                alt_freq = float(mutation["alt_freq"])
                cond1 = alt_freq < min_mutation_freq
                cond2 = alt_freq > max_mutation_freq
                if cond1 or cond2:
                    ret[strain][pos][i]["hidden_cell"] = True
    return ret


def get_data(dirs, clade_defining=False, hidden_strains=None,
             strain_order=None, min_mutation_freq=None,
             max_mutation_freq=None):
    """Get relevant data for Plotly visualizations in this application.

    This will include table and histogram data, which is straight
    forward. But this will also include various information related to
    the main heatmap, including heatmap x y coordinates for mutations,
    insertions, deletions, and hover text. This will also include
    information for rendering the mutation frequency slider.

    Basically, this function gives us data to plug into the
    visualization functions of Plotly.

    This relevant data is parsed from gvf files across one or more
    folders, with each gvf file in the form of the files found in
    ``reference_data/``.

    :param dirs: List of paths to folders to obtain data from
    :type dirs: list[str]
    :param clade_defining: Set non-clade defining mutations as hidden
    :type clade_defining: bool
    :param hidden_strains: List of strains from the dirs that the user
        does not want to display in the heatmap and table.
    :type hidden_strains: list[str]
    :param strain_order: Order of strains from the dirs that the user
        wants to display in the heatmap.
    :type strain_order: list[str]
    :param min_mutation_freq: Set mutations with a lower frequency than
        this as hidden.
    :type min_mutation_freq: int|float
    :param max_mutation_freq: Set mutations with a higher frequency
        than this as hidden.
    :type max_mutation_freq: int|float
    :return: Information on relevant columns in gvf files stored in
        folders listed in dirs.
    :rtype: dict
    """
    if hidden_strains is None:
        hidden_strains = []
    if strain_order is None:
        strain_order = []

    # Faster sort with this obj
    strain_order_dict = {s: i for i, s in enumerate(strain_order)}

    dir_strains = {}
    parsed_gvf_dirs = {}
    for dir_ in dirs:
        unsorted_parsed_gvf_dir = parse_gvf_dir(dir_)

        unsorted_items = unsorted_parsed_gvf_dir.items()
        if strain_order_dict:
            sorted_items = sorted(unsorted_items,
                                  key=lambda item: strain_order_dict[item[0]])
        else:
            sorted_items = sorted(unsorted_items,
                                  key=lambda item: item[0])
        parsed_gvf_dir = {k: v for k, v in sorted_items}

        parsed_gvf_dirs = {**parsed_gvf_dirs, **parsed_gvf_dir}
        dir_strains[dir_] = list(parsed_gvf_dir.keys())

    parsed_mutations = \
        {k: v["mutations"] for k, v in parsed_gvf_dirs.items()}

    visible_parsed_mutations = \
        {k: v for k, v in parsed_mutations.items() if k not in hidden_strains}

    if clade_defining:
        visible_parsed_mutations = \
            filter_parsed_mutations_by_clade_defining(visible_parsed_mutations)

    mutation_freq_slider_vals = \
        get_mutation_freq_slider_vals(visible_parsed_mutations)
    if min_mutation_freq is not None and max_mutation_freq is not None:
        visible_parsed_mutations = \
            filter_parsed_mutations_by_freq(visible_parsed_mutations,
                                            min_mutation_freq,
                                            max_mutation_freq)

    max_mutations_per_pos_dict = get_max_mutations_per_pos(parsed_mutations)
    ret = {
        "heatmap_cells_tickvals":
            get_heatmap_cells_tickvals(max_mutations_per_pos_dict),
        "heatmap_x_nt_pos":
            get_heatmap_x_nt_pos(max_mutations_per_pos_dict),
        "heatmap_y":
            get_heatmap_y(visible_parsed_mutations),
        "tables":
            get_tables(visible_parsed_mutations),
        "histogram_x":
            get_histogram_x(visible_parsed_mutations),
        "dir_strains":
            dir_strains,
        "hidden_strains":
            hidden_strains,
        "all_strains":
            get_heatmap_y(parsed_gvf_dirs),
        "mutation_freq_slider_vals":
            mutation_freq_slider_vals,
        "insertions_x":
            get_insertions_x(visible_parsed_mutations,
                             max_mutations_per_pos_dict),
        "insertions_y":
            get_insertions_y(visible_parsed_mutations),
        "deletions_x":
            get_deletions_x(visible_parsed_mutations,
                            max_mutations_per_pos_dict),
        "deletions_y":
            get_deletions_y(visible_parsed_mutations),
        "heatmap_z":
            get_heatmap_z(visible_parsed_mutations,
                          max_mutations_per_pos_dict),
        "heatmap_hover_text":
            get_heatmap_hover_text(visible_parsed_mutations,
                                   max_mutations_per_pos_dict),
        "heatmap_mutation_names":
            get_heatmap_mutation_names(visible_parsed_mutations,
                                       max_mutations_per_pos_dict),
        "heatmap_mutation_fns":
            get_heatmap_mutation_fns(visible_parsed_mutations,
                                     max_mutations_per_pos_dict),
        "heatmap_x_genes":
            get_heatmap_x_genes(max_mutations_per_pos_dict)
    }
    ret["heatmap_x_tickvals"] = \
        get_heatmap_x_tickvals(ret["heatmap_cells_tickvals"])
    ret["heatmap_x_aa_pos"] = \
        get_heatmap_x_aa_pos(ret["heatmap_x_nt_pos"], ret["heatmap_x_genes"])
    ret["heatmap_cells_fig_height"] = len(ret["heatmap_y"]) * 40
    ret["heatmap_cells_container_height"] = \
        min(10*40, ret["heatmap_cells_fig_height"])
    ret["heatmap_cells_fig_width"] = len(ret["heatmap_x_nt_pos"]) * 36

    return ret


def get_mutation_freq_slider_vals(parsed_mutations):
    """Get the mutation freq slider vals from ``parsed_gvf_dirs``.

    This value is ultimately used when rendering the mutation frequency
    slider. This is really just a sorted list of unique mutation
    frequencies from visible cells in ``parsed_gvf_dirs``.

    :param parsed_mutations: A dictionary containing multiple merged
        ``get_parsed_gvf_dir`` return "mutations" values.
    :type parsed_mutations: dict
    :return: Lowest to highest sorted list of unique mutation
        frequencies from visible cells in ``parsed_gvf_dirs``.
    :rtype: list[str]
    """
    alt_freq_set = set()
    for strain in parsed_mutations:
        for pos in parsed_mutations[strain]:
            for mutation in parsed_mutations[strain][pos]:
                if not mutation["hidden_cell"]:
                    alt_freq_set.add(mutation["alt_freq"])
    ret = sorted(list(alt_freq_set), key=float)
    return ret


def get_max_mutations_per_pos(parsed_mutations):
    """Get max number of mutations at each nt pos in parsed_gvf_dirs.

    The returned value is sorted by nt pos to make things easier in
    other functions.

    :param parsed_mutations: A dictionary containing multiple merged
        ``get_parsed_gvf_dir`` return "mutations" values.
    :type parsed_mutations: dict
    :return: Dict with nt pos as key, and  max num of mutations across
        all strains in parsed_gvf_dirs as val.
    :rtype: dict
    """
    pos_dict = {}
    for strain in parsed_mutations:
        for pos in parsed_mutations[strain]:
            num_of_mutations = len(parsed_mutations[strain][pos])
            if pos not in pos_dict:
                pos_dict[pos] = num_of_mutations
            else:
                pos_dict[pos] = max(num_of_mutations, pos_dict[pos])

    def sort_by_key(items): return int(items[0])
    sorted_dict = dict(sorted(pos_dict.items(), key=sort_by_key))
    return sorted_dict


def get_heatmap_cells_tickvals(max_mutations_per_pos_dict):
    """Get tickvals for the heatmap cells fig.

    :param max_mutations_per_pos_dict: See
        ``get_max_mutations_per_pos`` return value.
    :type max_mutations_per_pos_dict: dict
    :return: List of numerically indexed tickvals for heatmap cells fig
    :rtype: list[int]
    """
    ret = [-0.5]
    for _, num_of_mutations in max_mutations_per_pos_dict.items():
        # Need extra space for heterozygous mutations
        ret.append(ret[-1] + num_of_mutations)
    return ret


def get_heatmap_x_tickvals(heatmap_cells_tickvals):
    """Get tickvals for the heatmap x-axis figs.

    :param heatmap_cells_tickvals: See ``get_heatmap_cells_tickvals``
        return value.
    :type heatmap_cells_tickvals: list
    :return: List of numerically indexed tickvals for heatmap x-axis
        figs.
    :rtype: list[int]
    """
    ret = []
    for i in range(0, len(heatmap_cells_tickvals)-1):
        # Place it in the middle of the heatmap cell gridlines
        avg = (heatmap_cells_tickvals[i] + heatmap_cells_tickvals[i+1]) / 2
        ret.append(avg)
    return ret


def get_heatmap_x_nt_pos(max_mutations_per_pos_dict):
    """Get heatmap nt pos x-axis vals.

    :param max_mutations_per_pos_dict: See
        ``get_max_mutations_per_pos`` return value.
    :type max_mutations_per_pos_dict: dict
    :return: List of nt pos x-axis vals
    :rtype: list[str]
    """
    ret = []
    for pos in max_mutations_per_pos_dict:
        for _ in range(max_mutations_per_pos_dict[pos]):
            ret.append(pos)
    return ret


def get_heatmap_x_genes(max_mutations_per_pos_dict):
    """Get gene values corresponding to x-axis values in heatmap.

    :param max_mutations_per_pos_dict: See
        ``get_max_mutations_per_pos`` return value.
    :type max_mutations_per_pos_dict: dict
    :return: List of genes for each x in ``heatmap_x``
    :rtype: list[str]
    """
    ret = []
    for pos in max_mutations_per_pos_dict:
        gene = map_pos_to_gene(int(pos))
        for _ in range(max_mutations_per_pos_dict[pos]):
            ret.append(gene)
    return ret


def get_heatmap_x_aa_pos(heatmap_x_nt_pos, heatmap_x_genes):
    """Get aa positions corresponding to x axis values in heatmap.

    These are in the form of {gene}.{aa position in gene}, or if they
    are intergenic, in the form of
    {downstream gene}.1-{number of nt upstream}.

    :param heatmap_x_nt_pos: ``get_heatmap_x_nt_pos`` return value
    :type heatmap_x_nt_pos: list[str]
    :param heatmap_x_genes: ``get_heatmap_x_genes`` return value
    :type heatmap_x_genes: list[str]
    :return: List of amino acid positions relative to their gene for
        each x in ``heatmap_x``, of the form
        {gene}.{aa position in gene} or
        {downstream gene}.1-{number of nt upstream}.
    :rtype: list[str]
    """
    gene_start_positions = \
        {k: GENE_POSITIONS_DICT[k]["start"] for k in GENE_POSITIONS_DICT}
    last_gene_seen = "3' UTR"
    ret = ["" for _ in heatmap_x_nt_pos]
    # Iterate through nt pos in reverse
    for i, pos in enumerate(reversed(heatmap_x_nt_pos)):
        # Negative index
        _i = -1 - i
        gene = heatmap_x_genes[_i]
        if gene in {"5' UTR", "3' UTR"}:
            ret[_i] = gene
            continue
        if gene == "INTERGENIC":
            last_gene_start_pos = gene_start_positions[last_gene_seen]
            downstream_diff = last_gene_start_pos - int(pos)
            ret[_i] = "<b>%s.1 - %s</b>" % (last_gene_seen, downstream_diff)
            continue
        last_gene_seen = gene
        gene_start_pos = gene_start_positions[gene]
        ret[_i] = gene + "." + str(int((int(pos) - gene_start_pos) / 3) + 1)
    return ret


def get_heatmap_y(parsed_mutations):
    """Get y axis values of heatmap cells.

    These are the VOC strains.

    :param parsed_mutations: A dictionary containing multiple merged
        ``get_parsed_gvf_dir`` return "mutations" values.
    :type parsed_mutations: dict
    :return: List of y axis values
    :rtype: list[str]
    """
    ret = []
    for strain in parsed_mutations:
        ret.append(strain)
    return ret


def get_heatmap_z(parsed_mutations, max_mutations_per_pos_dict):
    """Get z values of heatmap cells.

    These are the mutation frequencies, and the z values dictate the
    colours of the heatmap cells.

    :param parsed_mutations: A dictionary containing multiple merged
        ``get_parsed_gvf_dir`` return "mutations" values.
    :type parsed_mutations: dict
    :param max_mutations_per_pos_dict: See
        ``get_max_mutations_per_pos`` return value.
    :type max_mutations_per_pos_dict: dict
    :return: List of z values
    :rtype: list[list[str]]
    """
    ret = []
    for strain in parsed_mutations:
        row = []
        for pos, num_of_mutations in max_mutations_per_pos_dict.items():
            cols = [None for _ in range(num_of_mutations)]
            if pos in parsed_mutations[strain]:
                for i, mutation in enumerate(parsed_mutations[strain][pos]):
                    if not mutation["hidden_cell"]:
                        # Set to 0 if sample size == 1, which allows it
                        # to be displayed as white with our colorscale.
                        if mutation["dp"] == 1:
                            cols[i] = 0
                        else:
                            cols[i] = mutation["alt_freq"]
            row.extend(cols)
        ret.append(row)
    return ret


def get_heatmap_hover_text(parsed_mutations, max_mutations_per_pos_dict):
    """Get hover text of heatmap cells.

    :param parsed_mutations: A dictionary containing multiple merged
        ``get_parsed_gvf_dir`` return "mutations" values.
    :type parsed_mutations: dict
    :param max_mutations_per_pos_dict: See
        ``get_max_mutations_per_pos`` return value.
    :type max_mutations_per_pos_dict: dict
    :return: List of D3 formatted text values for each x y coordinate
        in ``heatmap_x_nt_pos``.
    :rtype: list[list[str]]
    """
    ret = []
    for strain in parsed_mutations:
        row = []
        for pos, num_of_mutations in max_mutations_per_pos_dict.items():
            cols = [None for _ in range(num_of_mutations)]
            if pos in parsed_mutations[strain]:
                for i, mutation in enumerate(parsed_mutations[strain][pos]):
                    mutation_name = mutation["mutation_name"]
                    if not mutation_name:
                        mutation_name = "No recorded name"

                    functions_str = ""
                    for j, fn_category in enumerate(mutation["functions"]):
                        if j == 7:
                            functions_str += "...click for more<br>"
                            break
                        functions_str += fn_category + "<br>"
                    if not functions_str:
                        functions_str = "None recorded so far"

                    cell_text_str = "<b>Mutation name: %s</b><br>" \
                                    "<br>" \
                                    "Reference: %s<br>" \
                                    "Alternate: %s<br>" \
                                    "Alternate frequency: %s<br>" \
                                    "<br>" \
                                    "<b>Functions:</b> <br>%s"
                    cell_text_params = (mutation_name,
                                        mutation["ref"],
                                        mutation["alt"],
                                        mutation["alt_freq"],
                                        functions_str)
                    cols[i] = cell_text_str % cell_text_params
            row.extend(cols)
        ret.append(row)
    return ret


def get_heatmap_mutation_names(parsed_mutations, max_mutations_per_pos_dict):
    """Get mutation names associated with heatmap cells.

    This is useful when allowing users to click on heatmap cells for
    mutation details.

    :param parsed_mutations: A dictionary containing multiple merged
        ``get_parsed_gvf_dir`` return "mutations" values.
    :type parsed_mutations: dict
    :param max_mutations_per_pos_dict: See
        ``get_max_mutations_per_pos`` return value.
    :type max_mutations_per_pos_dict: dict
    :return: Mutation names for each x y coordinate in heatmap.
    :rtype: list[list[str]]
    """
    ret = []
    for strain in parsed_mutations:
        row = []
        for pos, num_of_mutations in max_mutations_per_pos_dict.items():
            cols = [None for _ in range(num_of_mutations)]
            if pos in parsed_mutations[strain]:
                for i, mutation in enumerate(parsed_mutations[strain][pos]):
                    if mutation["mutation_name"]:
                        cols[i] = mutation["mutation_name"]
            row.extend(cols)
        ret.append(row)
    return ret


def get_heatmap_mutation_fns(parsed_mutations, max_mutations_per_pos_dict):
    """Get mutation fns associated with heatmap cells.

    This is useful when allowing users to click on heatmap cells for
    mutation details.

    :param parsed_mutations: A dictionary containing multiple merged
        ``get_parsed_gvf_dir`` return "mutations" values.
    :type parsed_mutations: dict
    :param max_mutations_per_pos_dict: See
        ``get_max_mutations_per_pos`` return value.
    :type max_mutations_per_pos_dict: dict
    :return: Mutation functions for each x y coordinate in heatmap, as
        structured in dict format used by ``parsed_gvf_dirs``.
    :rtype: list[list[dict]]
    """
    ret = []
    for strain in parsed_mutations:
        row = []
        for pos, num_of_mutations in max_mutations_per_pos_dict.items():
            cols = [None for _ in range(num_of_mutations)]
            if pos in parsed_mutations[strain]:
                for i, mutation in enumerate(parsed_mutations[strain][pos]):
                    if mutation["functions"]:
                        cols[i] = mutation["functions"]
            row.extend(cols)
        ret.append(row)
    return ret


def get_insertions_x(parsed_mutations, max_mutations_per_pos_dict):
    """Get x coordinates of insertion markers to overlay in heatmap.

    These are the linear x coordinates used in the Plotly graph object.
    i.e., the indices of data["heatmap_x_nt_pos"]

    :param parsed_mutations: A dictionary containing multiple merged
        ``get_parsed_gvf_dir`` return "mutations" values.
    :type parsed_mutations: dict
    :param max_mutations_per_pos_dict: See
        ``get_max_mutations_per_pos`` return value.
    :type max_mutations_per_pos_dict: dict
    :return: List of x coordinate values to display insertion markers
    :rtype: list[int]
    """
    ret = []
    for strain in parsed_mutations:
        # How far markers need to be pushed right due to earlier
        # heterozygous mutations.
        x_offset = 0

        for i, pos in enumerate(max_mutations_per_pos_dict):
            num_of_mutations = max_mutations_per_pos_dict[pos]
            if pos in parsed_mutations[strain]:
                for j, mutation in enumerate(parsed_mutations[strain][pos]):
                    insertion = mutation["mutation_type"] == "insertion"
                    hidden = mutation["hidden_cell"]
                    if insertion and not hidden:
                        ret.append(i + j + x_offset)
            x_offset += num_of_mutations - 1
    return ret


def get_insertions_y(parsed_mutations):
    """Get y coordinates of insertion markers to overlay in heatmap.

    These are the linear y coordinates used in the Plotly graph object.
    i.e., the indices of data["heatmap_y"]

    :param parsed_mutations: A dictionary containing multiple merged
        ``get_parsed_gvf_dir`` return "mutations" values.
    :type parsed_mutations: dict
    :return: List of y coordinate values to display insertion markers
    :rtype: list[str]
    """
    ret = []
    for y, strain in enumerate(parsed_mutations):
        for pos in parsed_mutations[strain]:
            for mutation in parsed_mutations[strain][pos]:
                insertion = mutation["mutation_type"] == "insertion"
                hidden = mutation["hidden_cell"]
                if insertion and not hidden:
                    ret.append(y)
    return ret


def get_deletions_x(parsed_mutations, max_mutations_per_pos_dict):
    """Get x coordinates of deletion markers to overlay in heatmap.

    These are the linear x coordinates used in the Plotly graph object.
    i.e., the indices of data["heatmap_x_nt_pos"]

    :param parsed_mutations: A dictionary containing multiple merged
        ``get_parsed_gvf_dir`` return "mutations" values.
    :type parsed_mutations: dict
    :param max_mutations_per_pos_dict: See
        ``get_max_mutations_per_pos`` return value.
    :type max_mutations_per_pos_dict: dict
    :return: List of x coordinate values to display insertion markers
    :rtype: list[int]
    """
    ret = []
    for strain in parsed_mutations:
        # How far markers need to be pushed right due to earlier
        # heterozygous mutations.
        x_offset = 0

        for i, pos in enumerate(max_mutations_per_pos_dict):
            num_of_mutations = max_mutations_per_pos_dict[pos]
            if pos in parsed_mutations[strain]:
                for j, mutation in enumerate(parsed_mutations[strain][pos]):
                    deletion = mutation["mutation_type"] == "deletion"
                    hidden = mutation["hidden_cell"]
                    if deletion and not hidden:
                        ret.append(i+j+x_offset)
            x_offset += num_of_mutations - 1
    return ret


def get_deletions_y(parsed_mutations):
    """Get y coordinates of deletion markers to overlay in heatmap.

    These are the linear y coordinates used in the Plotly graph object.
    i.e., the indices of data["heatmap_y"]

    :param parsed_mutations: A dictionary containing multiple merged
        ``get_parsed_gvf_dir`` return "mutations" values.
    :type parsed_mutations: dict
    :return: List of y coordinate values to display deletion markers
    :rtype: list[str]
    """
    ret = []
    for y, strain in enumerate(parsed_mutations):
        for pos in parsed_mutations[strain]:
            for mutation in parsed_mutations[strain][pos]:
                deletion = mutation["mutation_type"] == "deletion"
                hidden = mutation["hidden_cell"]
                if deletion and not hidden:
                    ret.append(y)
    return ret


def get_tables(parsed_mutations):
    """Get table column data for each y axis value or strain.

    The columns are represented as lists.

    :param parsed_mutations: A dictionary containing multiple merged
        ``get_parsed_gvf_dir`` return "mutations" values.
    :type parsed_mutations: dict
    :return: Dictionary with keys for each strain, and a list of lists
        values representing columns for each strain.
    :rtype: dict[str, list[list]]
    """
    ret = {}
    for strain in parsed_mutations:
        pos_col = []
        mutation_name_col = []
        ref_col = []
        alt_col = []
        alt_freq_col = []
        functions_col = []
        for pos in parsed_mutations[strain]:
            for mutation in parsed_mutations[strain][pos]:
                pos_col.append(pos)
                mutation_name_col.append(mutation["mutation_name"])
                ref_col.append(mutation["ref"])
                alt_col.append(mutation["alt"])
                alt_freq_col.append(mutation["alt_freq"])
                functions_col.append([fn for fn in mutation["functions"]])
        ret[strain] = [
            pos_col, mutation_name_col, ref_col, alt_col, alt_freq_col,
            functions_col
        ]
    return ret


def get_histogram_x(parsed_mutations):
    """Get x data values binned by Plotly when producing the histogram.

    This is just the positions containing mutations, with duplicates
    permitted for mutations shared by strains.

    :param parsed_mutations: A dictionary containing multiple merged
        ``get_parsed_gvf_dir`` return "mutations" values.
    :type parsed_mutations: dict
    :return: List of x data values used in histogram view
    :rtype: list[str]
    """
    ret = []
    for strain in parsed_mutations:
        for pos in parsed_mutations[strain]:
            for mutation in parsed_mutations[strain][pos]:
                hidden_cell = mutation["hidden_cell"]
                if not hidden_cell:
                    ret.append(pos)
    return ret
