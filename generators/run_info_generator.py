"""Functions for generating run info view."""

import dash_bootstrap_components as dbc
import dash_html_components as html

from definitions import RUN_INFO_DICT


def get_run_info_row():
    """Get Dash Bootstrap Components row containing run info view.

    :return: Dash Bootstrap Components row containing table
    :rtype: dbc.Row
    """
    ret = dbc.Row(
        dbc.Col(
            children=[
                html.H1("Run info"),
                html.Div(
                    [html.B("Run ID: "),
                     RUN_INFO_DICT["run_id"]]
                ),
                html.Div(
                    [html.B("Last updated: "),
                     RUN_INFO_DICT["last_updated"]]
                ),
                html.Div(
                    [html.B("Data source: "),
                     html.A(
                         RUN_INFO_DICT["data_source_name"],
                         href=RUN_INFO_DICT["data_source_url"],
                         target="_blank",
                         # https://bit.ly/3qQjB7Y
                         rel="noopener noreferrer"
                     )]
                ),
                html.Div(
                    [html.B("Reference genome: "),
                     "%s (%s)" % (RUN_INFO_DICT["reference_description"],
                                  RUN_INFO_DICT["reference_accession"]),]
                ),
                html.Div(
                    [html.B("Total genomes processed to date: "),
                     RUN_INFO_DICT["total_sequences_processed"]]
                ),
                html.Div(
                    [html.B("Genomes processed in this run: "),
                     RUN_INFO_DICT["new_sequences_in_run"]]
                ),
                html.Div(html.B("Notes:")),
                html.Ul(
                    [html.Li(e) for e in RUN_INFO_DICT["notes"]]
                ),
                html.Div(
                    ["➡️ Download the annotated mutation data in JSON format ",
                     html.A(
                         "here",
                         href="#",
                         id="download-mutation-index-link"
                     )]
                ),
                html.Div(html.I(
                    ["This file contains all annotated variants currently in "
                     "view, suitable for integration with downstream tools. "
                     "You can also download the JSON file for the ",
                     html.A(
                         "full dataset here",
                         href="#",
                         id="download-full-mutation-index-link"
                     )]
                ))
            ],
            width={"offset": 1},
        ), className="mb-4"
    )
    return ret