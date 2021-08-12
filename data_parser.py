"""Functions for obtaining data used in Plotly visualizations.

Entry point is ``get_data``.
"""

from copy import deepcopy
import csv
from io import StringIO
from itertools import islice
import json
import os

import numpy as np
import pandas as pd

from definitions import GENE_POSITIONS_DICT


def vcf_str_to_gvf_str(vcf_str, strain):
    """Convert VCF str to gvf str.

    This is inspired by a script Madeline wrote:
    https://bit.ly/2Vgv1WO. A lot of the code is directly lifted.

    This is meant to rudimentarily convert VCF files to GVF files until
    we connect the modules together, at which point the visualization
    will not be responsible for converting VCF to GVF, because the
    functional annotations module will do it.

    :param vcf_str: String representation of VCF file uploaded by user
    :type vcf_str: str
    :param strain: Name of strain to assign uploaded file
    :type strain: str
    :return: String representation of GVF file converted from vcf_str
    :rtype: str
    """
    vcf_fp = StringIO(vcf_str)
    df = pd.read_csv(vcf_fp, sep="\t", header=65)

    gvf_columns = ["#seqid", "#source", "#type", "#start", "#end", "#score",
                   "#strand", "#phase", "#attributes"]
    new_df = pd.DataFrame(index=range(0, len(df)), columns=gvf_columns)

    # parse EFF column
    eff_info = df["INFO"].str.findall("\((.*?)\)")
    eff_info = eff_info.apply(pd.Series)[0]
    eff_info = eff_info.str.split(pat="|").apply(pd.Series)

    # hgvs names
    hgvs = eff_info[3].str.rsplit(pat="c.").apply(pd.Series)
    hgvs_protein = hgvs[0].str[:-1]
    hgvs_protein.replace(r"^\s+$", np.nan, regex=True)
    hgvs_nucleotide = "c." + hgvs[1]
    new_df["#attributes"] = \
        new_df["#attributes"].astype(str) + "Name=" + hgvs_protein + ";"
    new_df["#attributes"] = \
        new_df["#attributes"].astype(str) + "nt_name=" + hgvs_nucleotide + ";"
    new_df["#attributes"] = \
        new_df["#attributes"].astype(str) + "gene=" + eff_info[5] + ";"
    new_df["#attributes"] = (new_df["#attributes"].astype(str)
                             + "mutation_type=" + eff_info[1] + ";")

    # columns copied straight from Zohaib"s file
    for column in ["REF", "ALT"]:
        key = column.lower()
        if key == "ref":
            key = "Reference_seq"
        elif key == "alt":
            key = "Variant_seq"
        new_df["#attributes"] = (new_df["#attributes"].astype(str) + key
                                 + "=" + df[column].astype(str) + ";")

    # add ao, dp, ro
    info = df["INFO"].str.split(pat=";").apply(pd.Series)
    new_df["#attributes"] = new_df["#attributes"] + info[5].str.lower() + ";"
    new_df["#attributes"] = new_df["#attributes"] + info[7].str.lower() + ";"
    new_df["#attributes"] = new_df["#attributes"] + info[28].str.lower() + ";"

    # add strain name
    new_df["#attributes"] = \
        new_df["#attributes"] + "viral_lineage=" + strain + ";"

    new_df["#attributes"] = (new_df["#attributes"] + "who_label=;")
    new_df["#attributes"] = new_df["#attributes"] + "status=;"

    # Other attributes not in Madeline's script
    new_df["#attributes"] += "clade_defining=False;"
    new_df["#attributes"] += 'function_category="";'
    new_df["#attributes"] += 'function_description="";'
    new_df["#attributes"] += 'source="";'
    new_df["#attributes"] += 'citation="";'

    # remove starting NaN; leave trailing ";"
    new_df["#attributes"] = new_df["#attributes"].str[3:]

    # fill in other GVF columns
    new_df["#seqid"] = df["#CHROM"]
    new_df["#source"] = "."
    new_df["#type"] = info[40].str.split(pat="=").apply(pd.Series)[1]
    new_df["#start"] = df["POS"]
    new_df["#end"] = (df["POS"] + df["ALT"].str.len() - 1).astype(str)
    new_df["#score"] = "."
    new_df["#strand"] = "+"
    new_df["#phase"] = "."

    # only keep the columns needed for a gvf file
    new_df = new_df[gvf_columns]

    ret = new_df.to_csv(sep="\t", index=False)
    return ret


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


def parse_gvf_dir(dir_, file_order=None):
    """Parse a directory with gvf files for relevant data.

    This supplies ``get_data`` with the relevant information it needs
    from gvf files to generate the data used in visualizations.

    :param dir_: Path to directory to parse
    :type dir_: str
    :param file_order: List of files you want parsed first in order,
        otherwise files are parsed in order of modification time.
    :type file_order: list[str]
    :return: Relevant strain data from gvf files used by ``get_data``
    :rtype: dict
    """
    if file_order is None:
        file_order = []

    ret = {}
    with os.scandir(dir_) as it:
        # Iterate through gvf files in dir_ sorted by ``file_order``
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
                # Skip gvf header rows
                reader = csv.DictReader(islice(fp, 3, None), delimiter="\t")

                for row in reader:
                    attrs_first_split = row["#attributes"].split(";")[:-1]
                    attrs_second_split = \
                        [x.split("=", 1) for x in attrs_first_split]
                    attrs = {k: v for k, v in attrs_second_split}

                    pos = row["#start"]
                    if pos not in ret[strain]:
                        ret[strain][pos] = {}
                        ret[strain][pos]["ref"] = attrs["Reference_seq"]
                        ret[strain][pos]["alt"] = \
                            attrs["Variant_seq"].split(",")[0]
                        ret[strain][pos]["gene"] = attrs["gene"]

                        ao = float(attrs["ao"].split(",")[0])
                        dp = float(attrs["dp"])
                        ret[strain][pos]["alt_freq"] = str(ao / dp)

                        ret[strain][pos]["clade_defining"] = \
                            attrs["clade_defining"] == "True"

                        ret[strain][pos]["hidden_cell"] = False

                        ret[strain][pos]["mutation_name"] = attrs["Name"]

                        ref_len = len(ret[strain][pos]["ref"])
                        alt_len = len(ret[strain][pos]["alt"])
                        if ref_len < alt_len:
                            ret[strain][pos]["mutation_type"] = "insertion"
                        elif ref_len > alt_len:
                            ret[strain][pos]["mutation_type"] = "deletion"
                        else:
                            ret[strain][pos]["mutation_type"] = "snp"

                        ret[strain][pos]["functions"] = {}

                    fn_category = attrs["function_category"].strip('"')
                    fn_desc = attrs["function_description"].strip('"')
                    fn_source = attrs["source"].strip('"')
                    fn_citation = attrs["citation"].strip('"')
                    if fn_category:
                        if fn_category not in ret[strain][pos]["functions"]:
                            ret[strain][pos]["functions"][fn_category] = {}
                        ret[strain][pos]["functions"][fn_category][fn_desc] = \
                            {"source": fn_source, "citation": fn_citation}
    return ret


def filter_parsed_gvf_dirs_by_clade_defining(parsed_gvf_dirs):
    """Hide non-clade defining mutations from parsed gvf file.

    :param parsed_gvf_dirs: ``parse_gvf_dir`` return value
    :type parsed_gvf_dirs: dict
    :return: ``parsed_gvf_dirs`` with non-clade defining mutations
        labeled as hidden.
    :rtype: dict
    """
    ret = deepcopy(parsed_gvf_dirs)
    for strain in parsed_gvf_dirs:
        for pos in parsed_gvf_dirs[strain]:
            if not parsed_gvf_dirs[strain][pos]["clade_defining"]:
                ret[strain][pos]["hidden_cell"] = True
    return ret


def filter_parsed_gvf_dirs_by_freq(parsed_gvf_dirs, min_mutation_freq,
                                   max_mutation_freq):
    """Hide mutations of specific frequencies from parsed gvf file.

    :param parsed_gvf_dirs: ``parse_gvf_dir`` return value
    :type parsed_gvf_dirs: dict
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
        "heatmap_x_nt_pos": get_heatmap_x_nt_pos(parsed_gvf_dirs),
        "heatmap_y": get_heatmap_y(visible_parsed_gvf_dirs),
        "tables": get_tables(visible_parsed_gvf_dirs),
        "histogram_x": get_histogram_x(visible_parsed_gvf_dirs),
        "dir_strains": dir_strains,
        "hidden_strains": hidden_strains,
        "all_strains": get_heatmap_y(parsed_gvf_dirs),
        "mutation_freq_slider_vals": mutation_freq_slider_vals
    }
    heatmap_y, heatmap_x_nt_pos = ret["heatmap_y"], ret["heatmap_x_nt_pos"]
    ret["insertions_x"] = get_insertions_x(visible_parsed_gvf_dirs,
                                           heatmap_x_nt_pos,
                                           heatmap_y)
    ret["insertions_y"] = get_insertions_y(visible_parsed_gvf_dirs,
                                           heatmap_x_nt_pos,
                                           heatmap_y)
    ret["deletions_x"] = get_deletions_x(visible_parsed_gvf_dirs,
                                         heatmap_x_nt_pos,
                                         heatmap_y)
    ret["deletions_y"] = get_deletions_y(visible_parsed_gvf_dirs,
                                         heatmap_x_nt_pos,
                                         heatmap_y)
    ret["heatmap_z"] = \
        get_heatmap_z(visible_parsed_gvf_dirs, heatmap_x_nt_pos)
    ret["heatmap_hover_text"] = \
        get_heatmap_hover_text(visible_parsed_gvf_dirs, heatmap_x_nt_pos)
    ret["heatmap_mutation_names"] = \
        get_heatmap_mutation_names(visible_parsed_gvf_dirs, heatmap_x_nt_pos)
    ret["heatmap_mutation_fns"] = \
        get_heatmap_mutation_fns(visible_parsed_gvf_dirs, heatmap_x_nt_pos)
    ret["heatmap_x_genes"] = \
        get_heatmap_x_genes(heatmap_x_nt_pos)
    ret["heatmap_x_aa_pos"] = \
        get_heatmap_x_aa_pos(heatmap_x_nt_pos, ret["heatmap_x_genes"])
    ret["heatmap_cells_fig_height"] = len(heatmap_y) * 40
    ret["heatmap_cells_fig_width"] = len(heatmap_x_nt_pos) * 36

    return ret


def get_mutation_freq_slider_vals(parsed_gvf_dirs):
    """Get the mutation freq slider vals from ``parsed_gvf_dirs``.

    This value is ultimately used when rendering the mutation frequency
    slider. This is really just a sorted list of unique mutation
    frequencies from visible cells in ``parsed_gvf_dirs``.

    :param parsed_gvf_dirs: A dictionary containing multiple merged
        ``parsed_gvf_dir`` return values.
    :type parsed_gvf_dirs: dict
    :return: Lowest to highest sorted list of unique mutation
        frequencies from visible cells in ``parsed_gvf_dirs``.
    :rtype: list[str]
    """
    alt_freq_set = set()
    for strain in parsed_gvf_dirs:
        for pos in parsed_gvf_dirs[strain]:
            if not parsed_gvf_dirs[strain][pos]["hidden_cell"]:
                alt_freq_set.add(parsed_gvf_dirs[strain][pos]["alt_freq"])
    ret = sorted(list(alt_freq_set), key=float)
    return ret


def get_heatmap_x_nt_pos(parsed_gvf_dirs):
    """Get x axis values of heatmap cells.

    These are the nucleotide position of mutations.

    :param parsed_gvf_dirs: A dictionary containing multiple merged
        ``get_parsed_gvf_dir`` return values.
    :type parsed_gvf_dirs: dict
    :return: List of x axis values
    :rtype: list[str]
    """
    seen = set()
    ret = []
    for strain in parsed_gvf_dirs:
        for pos in parsed_gvf_dirs[strain]:
            if pos not in seen:
                seen.add(pos)
                ret.append(pos)
    ret.sort(key=int)
    return ret


def get_heatmap_x_genes(heatmap_x_nt_pos):
    """Get gene values corresponding to x axis values in heatmap.

    :param heatmap_x_nt_pos: ``get_heatmap_x_nt_pos`` return value
    :type heatmap_x_nt_pos: list[str]
    :return: List of genes for each x in ``heatmap_x``
    :rtype: list[str]
    """
    ret = []
    for pos in heatmap_x_nt_pos:
        ret.append(map_pos_to_gene(int(pos)))
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


def get_heatmap_y(parsed_gvf_dirs):
    """Get y axis values of heatmap cells.

    These are the VOC strains.

    :param parsed_gvf_dirs: A dictionary containing multiple merged
        ``get_parsed_gvf_dir`` return values.
    :type parsed_gvf_dirs: dict
    :return: List of y axis values
    :rtype: list[str]
    """
    ret = []
    for strain in parsed_gvf_dirs:
        ret.append(strain)
    return ret


def get_heatmap_z(parsed_gvf_dirs, heatmap_x_nt_pos):
    """Get z values of heatmap cells.

    These are the mutation frequencies, and the z values dictate the
    colours of the heatmap cells.

    :param parsed_gvf_dirs: A dictionary containing multiple merged
        ``get_parsed_gvf_dir`` return values.
    :type parsed_gvf_dirs: dict
    :param heatmap_x_nt_pos: ``get_heatmap_x_nt_pos`` return value
    :type heatmap_x_nt_pos: list[int]
    :return: List of z values
    :rtype: list[str]
    """
    ret = []
    for strain in parsed_gvf_dirs:
        row = []
        for pos in heatmap_x_nt_pos:
            cond = pos in parsed_gvf_dirs[strain] \
                   and not parsed_gvf_dirs[strain][pos]["hidden_cell"]
            if cond:
                row.append(parsed_gvf_dirs[strain][pos]["alt_freq"])
            else:
                row.append(None)
        ret.append(row)
    return ret


def get_heatmap_hover_text(parsed_gvf_dirs, heatmap_x_nt_pos):
    """Get hover text of heatmap cells.

    :param parsed_gvf_dirs: A dictionary containing multiple merged
        ``get_parsed_gvf_dir`` return values.
    :type parsed_gvf_dirs: dict
    :param heatmap_x_nt_pos: ``get_heatmap_x_nt_pos`` return value
    :type heatmap_x_nt_pos: list[int]
    :return: List of D3 formatted text values for each x y coordinate
        in ``heatmap_x_nt_pos``.
    :rtype: list[str]
    """
    ret = []
    for strain in parsed_gvf_dirs:
        row = []
        for pos in heatmap_x_nt_pos:
            if pos in parsed_gvf_dirs[strain]:
                cell_data = parsed_gvf_dirs[strain][pos]

                mutation_name = cell_data["mutation_name"]
                if not mutation_name:
                    mutation_name = "n/a"

                functions_str = ""
                for i, fn_category in enumerate(cell_data["functions"]):
                    if i == 7:
                        functions_str += "...click for more<br>"
                        break
                    functions_str += fn_category + "<br>"
                if not functions_str:
                    functions_str = "n/a"

                cell_text_str = "<b>Mutation name: %s</b><br>" \
                                "<br>" \
                                "Reference: %s<br>" \
                                "Alternate: %s<br>" \
                                "Alternate frequency: %s<br>" \
                                "<br>" \
                                "<b>Functions:</b> <br>%s"
                cell_text_params = (mutation_name,
                                    cell_data["ref"],
                                    cell_data["alt"],
                                    cell_data["alt_freq"],
                                    functions_str)
                row.append(cell_text_str % cell_text_params)
            else:
                row.append(None)
        ret.append(row)
    return ret


def get_heatmap_mutation_names(parsed_gvf_dirs, heatmap_x_nt_pos):
    """Get mutation names associated with heatmap cells.

    This is useful when allowing users to click on heatmap cells for
    mutation details.

    :param parsed_gvf_dirs: A dictionary containing multiple merged
        ``get_parsed_gvf_dir`` return values.
    :type parsed_gvf_dirs: dict
    :param heatmap_x_nt_pos: ``get_heatmap_x_nt_pos`` return value
    :type heatmap_x_nt_pos: list[int]
    :return: Mutation names for each x y coordinate in heatmap.
    :rtype: list[list[str]]
    """
    ret = []
    for strain in parsed_gvf_dirs:
        row = []
        for pos in heatmap_x_nt_pos:
            if pos in parsed_gvf_dirs[strain]:
                cell_data = parsed_gvf_dirs[strain][pos]
                mutation_name = cell_data["mutation_name"]
                if mutation_name:
                    row.append(mutation_name)
                else:
                    row.append(None)
            else:
                row.append(None)
        ret.append(row)
    return ret


def get_heatmap_mutation_fns(parsed_gvf_dirs, heatmap_x_nt_pos):
    """Get mutation fns associated with heatmap cells.

    This is useful when allowing users to click on heatmap cells for
    mutation details.

    :param parsed_gvf_dirs: A dictionary containing multiple merged
        ``get_parsed_gvf_dir`` return values.
    :type parsed_gvf_dirs: dict
    :param heatmap_x_nt_pos: ``get_heatmap_x_nt_pos`` return value
    :type heatmap_x_nt_pos: list[int]
    :return: Mutation functions for each x y coordinate in heatmap, as
        structured in dict format used by ``parsed_gvf_dirs``.
    :rtype: list[list[dict]]
    """
    ret = []
    for strain in parsed_gvf_dirs:
        row = []
        for pos in heatmap_x_nt_pos:
            if pos in parsed_gvf_dirs[strain]:
                cell_data = parsed_gvf_dirs[strain][pos]
                functions = cell_data["functions"]
                if functions:
                    row.append(functions)
                else:
                    row.append(None)
            else:
                row.append(None)
        ret.append(row)
    return ret


def get_insertions_x(parsed_gvf_dirs, heatmap_x_nt_pos, heatmap_y):
    """Get x coordinates of deletion markers to overlay in heatmap.

    These are the linear x coordinates used in the Plotly graph object.
    i.e., the indices of data["heatmap_x_nt_pos"]

    :param parsed_gvf_dirs: A dictionary containing multiple merged
        ``get_parsed_gvf_dir`` return values.
    :type parsed_gvf_dirs: dict
    :param heatmap_x_nt_pos: ``get_heatmap_x_nt_pos`` return value
    :type heatmap_x_nt_pos: list[int]
    :param heatmap_y: ``get_heatmap_y`` return value
    :type heatmap_y: list[str]
    :return: List of x coordinate values to display insertion markers
    :rtype: list[int]
    """
    ret = []
    for i, pos in enumerate(heatmap_x_nt_pos):
        for j, strain in enumerate(heatmap_y):
            if pos not in parsed_gvf_dirs[strain]:
                continue
            mutation_type = parsed_gvf_dirs[strain][pos]["mutation_type"]
            hidden_cell = parsed_gvf_dirs[strain][pos]["hidden_cell"]
            if mutation_type == "insertion" and not hidden_cell:
                ret.append(i)
    return ret


def get_insertions_y(parsed_gvf_dirs, heatmap_x_nt_pos, heatmap_y):
    """Get y coordinates of deletion markers to overlay in heatmap.

    These are the linear y coordinates used in the Plotly graph object.
    i.e., the indices of data["heatmap_y"]

    :param parsed_gvf_dirs: A dictionary containing multiple merged
        ``get_parsed_gvf_dir`` return values.
    :type parsed_gvf_dirs: dict
    :param heatmap_x_nt_pos: ``get_heatmap_x_nt_pos`` return value
    :type heatmap_x_nt_pos: list[int]
    :param heatmap_y: ``get_heatmap_y`` return value
    :type heatmap_y: list[str]
    :return: List of y coordinate values to display insertion markers
    :rtype: list[str]
    """
    ret = []
    for i, pos in enumerate(heatmap_x_nt_pos):
        for j, strain in enumerate(heatmap_y):
            if pos not in parsed_gvf_dirs[strain]:
                continue
            mutation_type = parsed_gvf_dirs[strain][pos]["mutation_type"]
            hidden_cell = parsed_gvf_dirs[strain][pos]["hidden_cell"]
            if mutation_type == "insertion" and not hidden_cell:
                ret.append(j)
    return ret


def get_deletions_x(parsed_gvf_dirs, heatmap_x_nt_pos, heatmap_y):
    """Get x coordinates of deletion markers to overlay in heatmap.

    These are the linear x coordinates used in the Plotly graph object.
    i.e., the indices of data["heatmap_x_nt_pos"]

    :param parsed_gvf_dirs: A dictionary containing multiple merged
        ``get_parsed_gvf_dir`` return values.
    :type parsed_gvf_dirs: dict
    :param heatmap_x_nt_pos: ``get_heatmap_x_nt_pos`` return value
    :type heatmap_x_nt_pos: list[int]
    :param heatmap_y: ``get_heatmap_y`` return value
    :type heatmap_y: list[str]
    :return: List of x coordinate values to display insertion markers
    :rtype: list[int]
    """
    ret = []
    for i, pos in enumerate(heatmap_x_nt_pos):
        for j, strain in enumerate(heatmap_y):
            if pos not in parsed_gvf_dirs[strain]:
                continue
            mutation_type = parsed_gvf_dirs[strain][pos]["mutation_type"]
            hidden_cell = parsed_gvf_dirs[strain][pos]["hidden_cell"]
            if mutation_type == "deletion" and not hidden_cell:
                ret.append(i)
    return ret


def get_deletions_y(parsed_gvf_dirs, heatmap_x_nt_pos, heatmap_y):
    """Get y coordinates of deletion markers to overlay in heatmap.

    These are the linear y coordinates used in the Plotly graph object.
    i.e., the indices of data["heatmap_y"]

    :param parsed_gvf_dirs: A dictionary containing multiple merged
        ``get_parsed_gvf_dir`` return values.
    :type parsed_gvf_dirs: dict
    :param heatmap_x_nt_pos: ``get_heatmap_x_nt_pos`` return value
    :type heatmap_x_nt_pos: list[int]
    :param heatmap_y: ``get_heatmap_y`` return value
    :type heatmap_y: list[str]
    :return: List of y coordinate values to display deletion markers
    :rtype: list[str]
    """
    ret = []
    for i, pos in enumerate(heatmap_x_nt_pos):
        for j, strain in enumerate(heatmap_y):
            if pos not in parsed_gvf_dirs[strain]:
                continue
            mutation_type = parsed_gvf_dirs[strain][pos]["mutation_type"]
            hidden_cell = parsed_gvf_dirs[strain][pos]["hidden_cell"]
            if mutation_type == "deletion" and not hidden_cell:
                ret.append(j)
    return ret


def get_tables(parsed_gvf_dirs):
    """Get table column data for each y axis value or strain.

    The columns are represented as lists.

    :param parsed_gvf_dirs: A dictionary containing multiple merged
        ``get_parsed_gvf_dir`` return values.
    :type parsed_gvf_dirs: dict
    :return: Dictionary with keys for each strain, and a list of lists
        values representing columns for each strain.
    :rtype: dict[str, list[list]]
    """
    ret = {}
    for strain in parsed_gvf_dirs:
        pos_col = []
        mutation_name_col = []
        ref_col = []
        alt_col = []
        alt_freq_col = []
        functions_col = []
        for pos in parsed_gvf_dirs[strain]:
            pos_col.append(pos)
            cell_data = parsed_gvf_dirs[strain][pos]
            mutation_name_col.append(cell_data["mutation_name"])
            ref_col.append(cell_data["ref"])
            alt_col.append(cell_data["alt"])
            alt_freq_col.append(cell_data["alt_freq"])
            functions_col.append([fn for fn in cell_data["functions"]])
        ret[strain] = [
            pos_col, mutation_name_col, ref_col, alt_col, alt_freq_col,
            functions_col
        ]
    return ret


def get_histogram_x(parsed_gvf_dirs):
    """Get x data values binned by Plotly when producing the histogram.

    This is just the positions containing mutations, with duplicates
    permitted for mutations shared by strains.

    :param parsed_gvf_dirs: A dictionary containing multiple merged
        ``get_parsed_gvf_dir`` return values.
    :type parsed_gvf_dirs: dict
    :return: List of x data values used in histogram view
    :rtype: list[str]
    """
    ret = []
    for strain in parsed_gvf_dirs:
        for pos in parsed_gvf_dirs[strain]:
            hidden_cell = parsed_gvf_dirs[strain][pos]["hidden_cell"]
            if not hidden_cell:
                ret.append(pos)
    return ret
