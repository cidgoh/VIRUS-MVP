"""Functions for obtaining data used in Plotly visualizations.

Entry point is ``get_data``.
"""

from copy import deepcopy
import csv
from itertools import compress, islice
import os

from definitions import (GENE_POSITIONS_DICT, NSP_POSITIONS_DICT,
                         DEFAULT_REFERENCE_HIDDEN_STRAINS,
                         DEFAULT_REFERENCE_STRAIN_ORDER,
                         FIRST_REGION, LAST_REGION)


def map_pos_to_gene(pos):
    """Map a nucleotide position to a gene.

    :param pos: Nucleotide position
    :type pos: int
    :return: Gene at nucleotide position ``pos``
    :rtype: str
    """
    for gene in GENE_POSITIONS_DICT:
        start = GENE_POSITIONS_DICT[gene]["start"]
        end = GENE_POSITIONS_DICT[gene]["end"]
        if start <= pos <= end:
            return gene
    return "INTERGENIC"


def map_pos_to_nsp(pos):
    """Map a nucleotide position to a NSP.

    NSP == non-structural protein

    :param pos: Nucleotide position
    :type pos: int
    :return: NSP at nucleotide position ``pos``
    :rtype: str
    """
    for nsp in NSP_POSITIONS_DICT:
        start = NSP_POSITIONS_DICT[nsp]["start"]
        end = NSP_POSITIONS_DICT[nsp]["end"]
        if start <= pos <= end:
            return nsp
    return "n/a"


def parse_gvf_sample_name(path):
    """Parse sample group name from gvf file header.

    :param path: Path to gvf file to parse
    :type path: str
    :return: Gvf file sample group
    :rtype: str
    """
    with open(path, encoding="utf-8") as fp:
        # Skip first two lines
        next(fp)
        next(fp)
        # "##sample-description sample_desc=x;sample_group=y;"
        sample_desc = fp.readline()
        # "sample_desc=x;sample_group=y"
        sample_desc_vals_str = sample_desc.split()[1].strip(";")
        # [["sample_desc", "x"], ["sample_group", "y"]]
        sample_desc_vals_list = \
            [e.split("=") for e in sample_desc_vals_str.split(";")]
        # {"sample_desc": "x", "sample_group": "y"}
        return dict(sample_desc_vals_list)["sample_group"]


def parse_gvf_sample_variants(path):
    """Parse gvf file variant data relevant to viz.

    :param path: Path to gvf file to parse
    :type path: str
    :return: Relevant variant data from gvf files used by viz
    :rtype: dict
    """
    with open(path, encoding="utf-8") as fp:
        # Skip gvf header rows
        reader = csv.DictReader(islice(fp, 4, None), delimiter="\t")

        parsing_first_row = True

        for row in reader:
            attrs_first_split = row["#attributes"].split(";")[:-1]
            attrs_second_split = \
                [x.split("=", 1) for x in attrs_first_split]
            attrs = {k: v for k, v in attrs_second_split}

            if parsing_first_row:
                # Default values
                variant = None
                variant_type = None
                status = None
                sample_size = attrs["sample_size"]

                if "variant" in attrs:
                    variant = attrs["variant"]

                if "variant_type" in attrs:
                    variant_type = attrs["variant_type"]
                if "status" in attrs:
                    status = attrs["status"]

                ret = {
                    "mutations": {},
                    "variant": variant,
                    "variant_type": variant_type,
                    "status": status,
                    "sample_size": sample_size
                }

                parsing_first_row = False

            pos = row["#start"]
            if pos not in ret["mutations"]:
                ret["mutations"][pos] = []

            mutation_name = attrs["Name"]
            cond = attrs["alias"] not in {"n/a", mutation_name}
            mutation_alias = attrs["alias"] if cond else ""
            alt = attrs["Variant_seq"]

            mutation_dict = {}
            for existing_dict in ret["mutations"][pos]:
                cond1 = existing_dict["mutation_name"] == mutation_name
                cond2 = existing_dict["alt"] == alt
                if cond1 and cond2:
                    mutation_dict = existing_dict
                    break

            if not mutation_dict:
                mutation_dict = {
                    "ref": attrs["Reference_seq"],
                    "alt": alt,
                    "gene": attrs["vcf_gene"],
                    "ao": float(attrs["ao"]),
                    "dp": float(attrs["dp"]),
                    "multi_aa_name": attrs["multi_aa_name"],
                    "clade_defining":
                        attrs["clade_defining"] == "True",
                    "hidden_cell": False,
                    "mutation_name": mutation_name,
                    "mutation_alias": mutation_alias,
                    "functions": {}
                }

                alt_freq = mutation_dict["ao"] / mutation_dict["dp"]
                mutation_dict["alt_freq"] = str(round(alt_freq, 4))

                mutation_type = row["#type"]
                if mutation_type == "ins":
                    mutation_dict["mutation_type"] = "insertion"
                elif mutation_type == "del":
                    mutation_dict["mutation_type"] = "deletion"
                else:
                    mutation_dict["mutation_type"] = mutation_type

                ret["mutations"][pos].append(mutation_dict)

            fn_dict = mutation_dict["functions"]
            fn_category = attrs["function_category"].strip('"')
            if not fn_category:
                continue
            if fn_category not in fn_dict:
                fn_dict[fn_category] = {}

            fn_desc = attrs["function_description"].strip('"')
            fn_source = attrs["source"].strip('"')
            fn_citation = attrs["citation"].strip('"')
            fn_dict[fn_category][fn_desc] = \
                {"source": fn_source, "citation": fn_citation}
    return ret


def filter_parsed_mutations_by_clade_defining(parsed_mutations):
    """Hide non-clade defining mutations from parsed gvf mutations.

    :param parsed_mutations: ``parse_gvf_sample_variants`` ret "mutations" vals
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


def filter_parsed_mutations_by_fns(parsed_mutations, filtered_fns):
    """TODO"""
    ret = deepcopy(parsed_mutations)
    filtered_fns_set = set(filtered_fns)
    for strain in parsed_mutations:
        for pos in parsed_mutations[strain]:
            for i, mutation in enumerate(parsed_mutations[strain][pos]):
                if not set(mutation["functions"]) & filtered_fns_set:
                    ret[strain][pos][i]["hidden_cell"] = True
    return ret


def filter_parsed_mutations_by_freq(parsed_mutations, min_mutation_freq,
                                    max_mutation_freq):
    """Hide mutations of specific frequencies from parsed gvf file.

    :param parsed_mutations: ``parse_gvf_sample_variants`` ret "mutations" vals
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


def get_data(dirs, show_clade_defining=False, hidden_strains=None,
             strain_order=None, filtered_fns=None, min_mutation_freq=None,
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
    :param show_clade_defining: Set non-clade defining mutations as
        hidden.
    :type show_clade_defining: bool
    :param hidden_strains: List of strains from the dirs that the user
        does not want to display in the heatmap and table.
    :type hidden_strains: None | list[str]
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
    # Default view
    if not strain_order:
        strain_order = DEFAULT_REFERENCE_STRAIN_ORDER
    if hidden_strains is None:
        hidden_strains = DEFAULT_REFERENCE_HIDDEN_STRAINS
        # Only display top 100 strains
        more_hidden_strains = \
            [e for i, e in enumerate(strain_order) if e not in hidden_strains]
        more_hidden_strains = \
            [e for i, e in enumerate(more_hidden_strains) if i > 100]
        hidden_strains += more_hidden_strains

    # Faster obj to work with
    hidden_strains_set = set(hidden_strains)

    # Faster sort with this obj
    strain_order_dict = {s: i for i, s in enumerate(strain_order)}

    def strain_path_sort_key(strain_path):
        strain = strain_path[0]
        if strain in strain_order_dict:
            return strain_order_dict[strain], strain
        else:
            return len(strain_order_dict), strain

    dir_strains_dict = {}
    parsed_gvf_dirs = {}
    for dir_ in dirs:
        dir_entry_paths = \
            [e.path for e in os.scandir(dir_) if e.path.endswith(".gvf")]
        dir_entry_strains = \
            [parse_gvf_sample_name(e) for e in dir_entry_paths]
        strain_paths_dict = dict(zip(dir_entry_strains, dir_entry_paths))
        sorted_strain_paths_dict = \
            dict(sorted(strain_paths_dict.items(), key=strain_path_sort_key))
        dir_strains_dict[dir_] = list(sorted_strain_paths_dict.keys())
        visible_sorted_strain_paths_dict = \
            {k: v for k, v in sorted_strain_paths_dict.items()
             if k not in hidden_strains_set}
        # Heatmap displays rows in reverse
        reversed_items = reversed(visible_sorted_strain_paths_dict.items())
        parsed_gvf_dir = \
            {s: parse_gvf_sample_variants(p) for s, p in reversed_items}
        parsed_gvf_dirs = {**parsed_gvf_dirs, **parsed_gvf_dir}

    parsed_mutations = \
        {k: v["mutations"] for k, v in parsed_gvf_dirs.items()}
    sample_sizes = {k: v["sample_size"] for k, v in parsed_gvf_dirs.items()}

    # These are dictionary because they are in the return val, which
    # needs to be json compatible (how Dash moves content across
    # network).
    voc_strains = {k: None for k in parsed_gvf_dirs
                   if parsed_gvf_dirs[k]["variant_type"] == "VOC"}
    voi_strains = {k: None for k in parsed_gvf_dirs
                   if parsed_gvf_dirs[k]["variant_type"] == "VOI"}
    circulating_strains = \
        {k: None for k in parsed_gvf_dirs
         if parsed_gvf_dirs[k]["status"] == "actively_circulating"}
    variants_dict = {k: v["variant"] for k, v in parsed_gvf_dirs.items()}

    visible_parsed_mutations = parsed_mutations
    if show_clade_defining:
        visible_parsed_mutations = \
            filter_parsed_mutations_by_clade_defining(visible_parsed_mutations)

    if filtered_fns:
        visible_parsed_mutations = \
            filter_parsed_mutations_by_fns(visible_parsed_mutations,
                                           filtered_fns)

    mutation_freq_slider_vals = \
        get_mutation_freq_slider_vals(visible_parsed_mutations)
    if min_mutation_freq is not None and max_mutation_freq is not None:
        visible_parsed_mutations = \
            filter_parsed_mutations_by_freq(visible_parsed_mutations,
                                            min_mutation_freq,
                                            max_mutation_freq)

    intra_col_mutation_pos_dict = \
        get_intra_col_mutation_pos_dict(parsed_mutations)
    ret = {
        "heatmap_cells_tickvals":
            get_heatmap_cells_tickvals(intra_col_mutation_pos_dict),
        "heatmap_x_nt_pos":
            get_heatmap_x_nt_pos(intra_col_mutation_pos_dict),
        "heatmap_y_strains":
            get_heatmap_y_strains(visible_parsed_mutations),
        "heatmap_y_sample_sizes":
            get_heatmap_y_sample_sizes(visible_parsed_mutations, sample_sizes),
        "tables":
            get_tables(visible_parsed_mutations),
        "histogram_x":
            get_histogram_x(visible_parsed_mutations),
        "dir_strains_dict":
            dir_strains_dict,
        "hidden_strains":
            hidden_strains,
        "voc_strains":
            voc_strains,
        "voi_strains":
            voi_strains,
        "circulating_strains":
            circulating_strains,
        "variants_dict":
            variants_dict,
        "all_strains":
            [i for v in dir_strains_dict.values() for i in v],
        "mutation_freq_slider_vals":
            mutation_freq_slider_vals,
        "insertions_x":
            get_insertions_x(visible_parsed_mutations,
                             intra_col_mutation_pos_dict),
        "insertions_y":
            get_insertions_y(visible_parsed_mutations),
        "deletions_x":
            get_deletions_x(visible_parsed_mutations,
                            intra_col_mutation_pos_dict),
        "deletions_y":
            get_deletions_y(visible_parsed_mutations),
        "heatmap_z":
            get_heatmap_z(visible_parsed_mutations,
                          intra_col_mutation_pos_dict,
                          sample_sizes),
        "heatmap_hover_text":
            get_heatmap_hover_text(visible_parsed_mutations,
                                   intra_col_mutation_pos_dict),
        "heatmap_mutation_names":
            get_heatmap_mutation_names(visible_parsed_mutations,
                                       intra_col_mutation_pos_dict),
        "heatmap_mutation_fns":
            get_heatmap_mutation_fns(visible_parsed_mutations,
                                     intra_col_mutation_pos_dict),
        "heatmap_x_genes":
            get_heatmap_x_genes(intra_col_mutation_pos_dict),
        "heatmap_x_nsps":
            get_heatmap_x_nsps(intra_col_mutation_pos_dict),
        "jump_to_info_dict":
            get_jump_to_info_dict(visible_parsed_mutations)
    }
    ret["heatmap_x_tickvals"] = \
        get_heatmap_x_tickvals(ret["heatmap_cells_tickvals"])
    ret["heatmap_x_aa_pos"] = \
        get_heatmap_x_aa_pos(ret["heatmap_x_nt_pos"], ret["heatmap_x_genes"])
    ret["heatmap_cells_fig_height"] = \
        max(10*40, len(ret["heatmap_y_strains"]) * 40)
    ret["heatmap_cells_container_height"] = \
        min(10*40, ret["heatmap_cells_fig_height"])
    ret["heatmap_cells_fig_width"] = len(ret["heatmap_x_nt_pos"]) * 36
    ret["jump_to_dropdown_search_options"] = \
        get_jump_to_dropdown_search_options(ret["jump_to_info_dict"])

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


def get_intra_col_mutation_pos_dict(parsed_mutations):
    """Get dict sorting mutations into intra-position indices.

    The keys of the returned value are nt positions, and the values are
    dicts sorting n unique mutations at that position into indices
    0, ..., n.

    The returned value is sorted by nt pos to make things easier in
    other functions.

    :param parsed_mutations: A dictionary containing multiple merged
        ``get_parsed_gvf_dir`` return "mutations" values.
    :type parsed_mutations: dict
    :return: Dict with nt pos as key, and nested dicts as values
        assigning mutations to intra-position indices.
    :rtype: dict
    """
    intra_col_mutation_pos_dict = {}

    # In the first pass, we assign sets of mutation names as dict vals
    for strain in parsed_mutations:
        for pos in parsed_mutations[strain]:
            mutation_names_set = \
                {e["mutation_name"] for e in parsed_mutations[strain][pos]}
            if pos not in intra_col_mutation_pos_dict:
                intra_col_mutation_pos_dict[pos] = mutation_names_set
            else:
                intra_col_mutation_pos_dict[pos] |= mutation_names_set

    # In the second pass, we assign col indices to the mutation names
    for pos in intra_col_mutation_pos_dict:
        intra_col_mutation_pos_dict[pos] = \
            {e: i for i, e in enumerate(intra_col_mutation_pos_dict[pos])}

    def sort_by_key(items): return int(items[0])
    sorted_dict = \
        dict(sorted(intra_col_mutation_pos_dict.items(), key=sort_by_key))

    return sorted_dict


def get_heatmap_cells_tickvals(intra_col_mutation_pos_dict):
    """Get tickvals for the heatmap cells fig.

    :param intra_col_mutation_pos_dict: See
        ``get_intra_col_mutation_pos_dict`` return value.
    :type intra_col_mutation_pos_dict: dict
    :return: List of numerically indexed tickvals for heatmap cells fig
    :rtype: list[int]
    """
    ret = [-0.5]
    for pos in intra_col_mutation_pos_dict:
        # Need extra space for heterozygous mutations
        ret.append(ret[-1] + len(intra_col_mutation_pos_dict[pos]))
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


def get_heatmap_x_nt_pos(intra_col_mutation_pos_dict):
    """Get heatmap nt pos x-axis vals.

    :param intra_col_mutation_pos_dict: See
        ``get_intra_col_mutation_pos_dict`` return value.
    :type intra_col_mutation_pos_dict: dict
    :return: List of nt pos x-axis vals
    :rtype: list[str]
    """
    ret = []
    for pos in intra_col_mutation_pos_dict:
        for _ in range(len(intra_col_mutation_pos_dict[pos])):
            ret.append(pos)
    return ret


def get_heatmap_x_genes(intra_col_mutation_pos_dict):
    """Get gene values corresponding to x-axis values in heatmap.

    :param intra_col_mutation_pos_dict: See
        ``get_intra_col_mutation_pos_dict`` return value.
    :type intra_col_mutation_pos_dict: dict
    :return: List of genes for each x in ``heatmap_x``
    :rtype: list[str]
    """
    ret = []
    for pos in intra_col_mutation_pos_dict:
        gene = map_pos_to_gene(int(pos))
        for _ in range(len(intra_col_mutation_pos_dict[pos])):
            ret.append(gene)
    return ret


def get_heatmap_x_nsps(intra_col_mutation_pos_dict):
    """Get NSP values corresponding to x-axis values in heatmap.

    :param intra_col_mutation_pos_dict: See
        ``get_intra_col_mutation_pos_dict`` return value.
    :type intra_col_mutation_pos_dict: dict
    :return: List of NSPs for each x in ``heatmap_x``
    :rtype: list[str]
    """
    ret = []
    for pos in intra_col_mutation_pos_dict:
        nsp = map_pos_to_nsp(int(pos))
        for _ in range(len(intra_col_mutation_pos_dict[pos])):
            ret.append(nsp)
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
    last_gene_seen = "3'UTR"
    ret = ["" for _ in heatmap_x_nt_pos]
    # Iterate through nt pos in reverse
    for i, pos in enumerate(reversed(heatmap_x_nt_pos)):
        # Negative index
        _i = -1 - i
        gene = heatmap_x_genes[_i]
        if gene in {FIRST_REGION, LAST_REGION}:
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


def get_heatmap_y_strains(parsed_mutations):
    """Get strain y axis values of heatmap cells.

    :param parsed_mutations: A dictionary containing multiple merged
        ``get_parsed_gvf_dir`` return "mutations" values.
    :type parsed_mutations: dict
    :return: List of strain y axis values
    :rtype: list[str]
    """
    ret = []
    for strain in parsed_mutations:
        ret.append(strain)
    return ret


def get_heatmap_y_sample_sizes(parsed_mutations, sample_sizes):
    """Get sample size y axis values of heatmap cells.

    :param parsed_mutations: A dictionary containing multiple merged
        ``get_parsed_gvf_dir`` return "mutations" values.
    :type parsed_mutations: dict
    :param sample_sizes: A dictionary containing multiple merged
        ``get_parsed_gvf_dir`` return "sample_size" values.
    :type sample_sizes: dict
    :return: List of sample size y axis values
    :rtype: list[str]
    """
    ret = []
    for strain in parsed_mutations:
        ret.append(sample_sizes[strain])
    return ret


def get_heatmap_z(parsed_mutations, intra_col_mutation_pos_dict, sample_sizes):
    """Get z values of heatmap cells.

    These are the mutation frequencies, and the z values dictate the
    colours of the heatmap cells.

    :param parsed_mutations: A dictionary containing multiple merged
        ``get_parsed_gvf_dir`` return "mutations" values.
    :type parsed_mutations: dict
    :param intra_col_mutation_pos_dict: See
        ``get_intra_col_mutation_pos_dict`` return value.
    :type intra_col_mutation_pos_dict: dict
    :param sample_sizes: A dictionary containing multiple merged
        ``get_parsed_gvf_dir`` return "sample_size" values.
    :type sample_sizes: dict
    :return: List of z values
    :rtype: list[list[str]]
    """
    ret = []
    for strain in parsed_mutations:
        row = []
        for pos in intra_col_mutation_pos_dict:
            cols = [None for _ in range(len(intra_col_mutation_pos_dict[pos]))]
            if pos in parsed_mutations[strain]:
                for mutation in parsed_mutations[strain][pos]:
                    if not mutation["hidden_cell"]:
                        mutation_name = mutation["mutation_name"]
                        col = intra_col_mutation_pos_dict[pos][mutation_name]
                        # Set to 0 if sample size == 1, which allows it
                        # to be displayed as white with our colorscale.
                        if sample_sizes[strain] == "1":
                            cols[col] = 0
                        else:
                            cols[col] = mutation["alt_freq"]
            row.extend(cols)
        ret.append(row)
    return ret


def get_heatmap_hover_text(parsed_mutations, intra_col_mutation_pos_dict):
    """Get hover text of heatmap cells.

    :param parsed_mutations: A dictionary containing multiple merged
        ``get_parsed_gvf_dir`` return "mutations" values.
    :type parsed_mutations: dict
    :param intra_col_mutation_pos_dict: See
        ``get_intra_col_mutation_pos_dict`` return value.
    :type intra_col_mutation_pos_dict: dict
    :return: List of D3 formatted text values for each x y coordinate
        in ``heatmap_x_nt_pos``.
    :rtype: list[list[str]]
    """
    ret = []
    for strain in parsed_mutations:
        row = []
        for pos in intra_col_mutation_pos_dict:
            cols = [None for _ in range(len(intra_col_mutation_pos_dict[pos]))]
            if pos in parsed_mutations[strain]:
                for mutation in parsed_mutations[strain][pos]:
                    mutation_name = mutation["mutation_name"]
                    col = intra_col_mutation_pos_dict[pos][mutation_name]
                    if not mutation_name:
                        mutation_name = "No recorded name"

                    multi_aa_name = mutation["multi_aa_name"]
                    if not multi_aa_name:
                        multi_aa_name = "False"

                    functions_str = ""
                    for j, fn_category in enumerate(mutation["functions"]):
                        if j == 7:
                            functions_str += "...click for more<br>"
                            break
                        functions_str += fn_category + "<br>"
                    if not functions_str:
                        functions_str = "None recorded so far"

                    cell_text_str = "<b>Mutation name:</b> %s<br>" \
                                    "Multiple AA mutations?: %s<br>" \
                                    "<br>" \
                                    "Reference: %s<br>" \
                                    "Alternate: %s<br>" \
                                    "Alternate frequency: %s<br>" \
                                    "<br>" \
                                    "<b>Functions:</b> <br>%s"
                    cell_text_params = (mutation_name,
                                        multi_aa_name,
                                        mutation["ref"],
                                        mutation["alt"],
                                        mutation["alt_freq"],
                                        functions_str)
                    cols[col] = cell_text_str % cell_text_params
            row.extend(cols)
        ret.append(row)
    return ret


def get_jump_to_info_dict(parsed_mutations):
    """Get dict containing info needed for "jump to" modal fns.

    The keys in this dict are mutation names. The values are:
      * mutation alias
      * top-left most strain seen in heatmap with mutation
      * top-right most strain seen in heatmap with mutation

    :param parsed_mutations: A dictionary containing multiple merged
        ``get_parsed_gvf_dir`` return "mutations" values.
    :type parsed_mutations: dict
    :return: Dict with info needed for "jump to" modal fns
    :type: dict
    """
    ret = {}
    for strain in reversed(parsed_mutations):
        for nt_pos in parsed_mutations[strain]:
            for mutation in parsed_mutations[strain][nt_pos]:
                mutation_name = mutation["mutation_name"]
                mutation_alias = mutation["mutation_alias"]
                hidden = mutation["hidden_cell"]
                if mutation_name and not hidden and mutation_name not in ret:
                    ret[mutation_name] = {"strain": strain,
                                          "nt_pos": nt_pos,
                                          "mutation_alias": mutation_alias}
    return ret


def get_jump_to_dropdown_search_options(jump_to_info_dict):
    """List of dash bootstrap opts for "jump to" modal.

    @param jump_to_info_dict: ``get_jump_to_info_dict`` ret val
    @type jump_to_info_dict: dict
    @return: List of dicts with a label and val key
    @rtype: list
    """
    ret = []
    for mutation_name in jump_to_info_dict:
        alias = jump_to_info_dict[mutation_name]["mutation_alias"]
        alias_suffix = " (%s)" % alias if alias else ""
        ret.append({"label": mutation_name + alias_suffix,
                    "value": mutation_name})
    return ret


def get_heatmap_mutation_names(parsed_mutations, intra_col_mutation_pos_dict):
    """Get mutation names associated with heatmap cells.

    This is useful when allowing users to click on heatmap cells for
    mutation details.

    :param parsed_mutations: A dictionary containing multiple merged
        ``get_parsed_gvf_dir`` return "mutations" values.
    :type parsed_mutations: dict
    :param intra_col_mutation_pos_dict: See
        ``get_intra_col_mutation_pos_dict`` return value.
    :type intra_col_mutation_pos_dict: dict
    :return: Mutation names for each x y coordinate in heatmap.
    :rtype: list[list[str]]
    """
    ret = []
    for strain in parsed_mutations:
        row = []
        for pos in intra_col_mutation_pos_dict:
            cols = [None for _ in range(len(intra_col_mutation_pos_dict[pos]))]
            if pos in parsed_mutations[strain]:
                for mutation in parsed_mutations[strain][pos]:
                    mutation_name = mutation["mutation_name"]
                    if mutation_name:
                        col = intra_col_mutation_pos_dict[pos][mutation_name]
                        cols[col] = mutation_name
            row.extend(cols)
        ret.append(row)
    return ret


def get_heatmap_mutation_fns(parsed_mutations, intra_col_mutation_pos_dict):
    """Get mutation fns associated with heatmap cells.

    This is useful when allowing users to click on heatmap cells for
    mutation details.

    :param parsed_mutations: A dictionary containing multiple merged
        ``get_parsed_gvf_dir`` return "mutations" values.
    :type parsed_mutations: dict
    :param intra_col_mutation_pos_dict: See
        ``get_intra_col_mutation_pos_dict`` return value.
    :type intra_col_mutation_pos_dict: dict
    :return: Mutation functions for each x y coordinate in heatmap, as
        structured in dict format used by ``parsed_gvf_dirs``.
    :rtype: list[list[dict]]
    """
    ret = []
    for strain in parsed_mutations:
        row = []
        for pos in intra_col_mutation_pos_dict:
            cols = [None for _ in range(len(intra_col_mutation_pos_dict[pos]))]
            if pos in parsed_mutations[strain]:
                for mutation in parsed_mutations[strain][pos]:
                    if mutation["functions"]:
                        mutation_name = mutation["mutation_name"]
                        col = intra_col_mutation_pos_dict[pos][mutation_name]
                        cols[col] = mutation["functions"]
            row.extend(cols)
        ret.append(row)
    return ret


def get_insertions_x(parsed_mutations, intra_col_mutation_pos_dict):
    """Get x coordinates of insertion markers to overlay in heatmap.

    These are the linear x coordinates used in the Plotly graph object.
    i.e., the indices of data["heatmap_x_nt_pos"]

    :param parsed_mutations: A dictionary containing multiple merged
        ``get_parsed_gvf_dir`` return "mutations" values.
    :type parsed_mutations: dict
    :param intra_col_mutation_pos_dict: See
        ``get_intra_col_mutation_pos_dict`` return value.
    :type intra_col_mutation_pos_dict: dict
    :return: List of x coordinate values to display insertion markers
    :rtype: list[int]
    """
    ret = []
    for strain in parsed_mutations:
        # How far markers need to be pushed right due to earlier
        # heterozygous mutations.
        x_offset = 0

        for i, pos in enumerate(intra_col_mutation_pos_dict):
            num_of_mutations = len(intra_col_mutation_pos_dict[pos])
            if pos in parsed_mutations[strain]:
                for mutation in parsed_mutations[strain][pos]:
                    insertion = mutation["mutation_type"] == "insertion"
                    hidden = mutation["hidden_cell"]
                    if insertion and not hidden:
                        mutation_name = mutation["mutation_name"]
                        col_index = \
                            intra_col_mutation_pos_dict[pos][mutation_name]
                        ret.append(i + col_index + x_offset)
            x_offset += num_of_mutations - 1
    return ret


def get_insertions_y(parsed_mutations):
    """Get y coordinates of insertion markers to overlay in heatmap.

    These are the linear y coordinates used in the Plotly graph object.
    i.e., the indices of data["heatmap_y_strains"]

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


def get_deletions_x(parsed_mutations, intra_col_mutation_pos_dict):
    """Get x coordinates of deletion markers to overlay in heatmap.

    These are the linear x coordinates used in the Plotly graph object.
    i.e., the indices of data["heatmap_x_nt_pos"]

    :param parsed_mutations: A dictionary containing multiple merged
        ``get_parsed_gvf_dir`` return "mutations" values.
    :type parsed_mutations: dict
    :param intra_col_mutation_pos_dict: See
        ``get_intra_col_mutation_pos_dict`` return value.
    :type intra_col_mutation_pos_dict: dict
    :return: List of x coordinate values to display insertion markers
    :rtype: list[int]
    """
    ret = []
    for strain in parsed_mutations:
        # How far markers need to be pushed right due to earlier
        # heterozygous mutations.
        x_offset = 0

        for i, pos in enumerate(intra_col_mutation_pos_dict):
            num_of_mutations = len(intra_col_mutation_pos_dict[pos])
            if pos in parsed_mutations[strain]:
                for mutation in parsed_mutations[strain][pos]:
                    deletion = mutation["mutation_type"] == "deletion"
                    hidden = mutation["hidden_cell"]
                    if deletion and not hidden:
                        mutation_name = mutation["mutation_name"]
                        col_index = \
                            intra_col_mutation_pos_dict[pos][mutation_name]
                        ret.append(i + col_index + x_offset)
            x_offset += num_of_mutations - 1
    return ret


def get_deletions_y(parsed_mutations):
    """Get y coordinates of deletion markers to overlay in heatmap.

    These are the linear y coordinates used in the Plotly graph object.
    i.e., the indices of data["heatmap_y_strains"]

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
