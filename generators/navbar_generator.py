"""Functions for importing navbar."""

import dash_bootstrap_components as dbc
import dash_html_components as html

def get_navbar_row(cidgoh_logo_path):
    """Get Dash Bootstrap Components row containing navbar.

    :return: Dash Bootstrap Components row containing navbar.
    :rtype: dbc.Row
    """
    ret = dbc.Nav([
        dbc.NavItem(
            dbc.NavLink(
                html.Img(src=cidgoh_logo_path,
                         style={"height": "4vh"}),
                href="https://cidgoh.ca/",
                target="_blank"
            )
        ),
        dbc.NavItem(
            dbc.NavLink("TUTORIAL",
                        id="toggle-readme-link",
                        href="#")
        ),
        dbc.NavItem(
            dbc.NavLink("GITHUB",
                        href="https://github.com/cidgoh/VIRUS-MVP",
                        target="_blank")
        ),
        dbc.NavItem(
            dbc.NavLink("BACKEND WORKFLOW",
                        href="https://github.com/cidgoh/nf-ncov-voc",
                        target="_blank")
        ),
        dbc.NavItem(
            dbc.NavLink("CONTACT US",
                        href="https://cidgoh.ca/contact/",
                        target="_blank")
        )
    ], className="align-items-center justify-content-end")
    return dbc.Row(dbc.Col(ret, className="bg-light"))
