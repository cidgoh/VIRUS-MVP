"""Functions for generating footer view."""

from dash import html
import dash_bootstrap_components as dbc


def get_footer_row_div(cidgoh_logo_path):
    """Get Dash Bootstrap Components row containing footer view.

    :param cidgoh_logo_path: Path to cidgoh logo
        TODO why does adding to definitions not work?
    :type cidgoh_logo_path: str
    :return: Dash Bootstrap Components row containing table
    :rtype: dbc.Row
    """
    all_labs = [
        "Saskatchewan - Roy Romanow Provincial Laboratory(RRPL)",
        "Nova Scotia Health Authority",
        "Alberta ProvLab North(APLN)",
        "Queen's University / Kingston Health Sciences Centre",
        "National Microbiology Laboratory(NML)",
        "BCCDC Public Health Laboratory",
        "Public Health Ontario(PHO)",
        "Newfoundland and Labrador - Eastern Health",
        "Unity Health Toronto",
        "Ontario Institute for Cancer Research(OICR)",
        "Manitoba Cadham Provincial Laboratory"
    ]

    ret = dbc.Row(
        [
            dbc.Col(
                html.A(
                    html.Img(src=cidgoh_logo_path,
                             style={"height": "15vh"}),
                    href="https://cidgoh.ca/",
                    target="_blank",
                    rel="noopener noreferrer"
                ),
                className="ms-2",
                width=2,
                xl=1
            ),
            dbc.Col(
                "The results here are in whole or part based upon data hosted "
                "at the Canadian VirusSeq Data Portal: "
                "https://virusseq-dataportal.ca/. We wish to acknowledge the "
                "following organisations/laboratories for contributing data "
                "to the Portal: Canadian Public Health Laboratory Network "
                "(CPHLN), CanCOGGeN VirusSeq, " + ", ".join(all_labs)[:-1]
                + ", and " + all_labs[-1] + ".",
            )
        ],
    )
        
    return ret
