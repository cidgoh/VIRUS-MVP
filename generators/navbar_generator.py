"""Functions for importing navbar."""

import dash_bootstrap_components as dbc
import dash_html_components as html
from flask import session

from definitions import VIRUS_REFERENCE_SEGMENT_DICT

def get_navbar_row(cidgoh_logo_path):
    """Get Dash Bootstrap Components row containing navbar.

    :return: Dash Bootstrap Components row containing navbar.
    :rtype: dbc.Row
    """
    [virus_dropdown, reference_dropdown, segment_dropdown] = \
        get_virus_reference_segment_navs()
    ret = dbc.Nav([
        virus_dropdown,
        reference_dropdown,
        segment_dropdown,
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
            dbc.NavLink("GENOMICS WORKFLOW",
                        href="https://github.com/cidgoh/nf-ncov-voc",
                        target="_blank")
        ),
        dbc.NavItem(
            dbc.NavLink("CONTACT US",
                        href="https://cidgoh.ca/contact/",
                        target="_blank")
        ),
        dbc.NavItem(
            dbc.NavLink(
                html.Img(src=cidgoh_logo_path,
                         style={"height": "4vh"}),
                href="https://cidgoh.ca/",
                target="_blank"
            )
        )
    ], className="align-items-center justify-content-end")
    return dbc.Row(dbc.Col(ret, className="bg-light border-bottom"))


def get_virus_reference_segment_navs():
    """TODO"""
    selected_virus = session.get("virus")
    virus_dropdown_item_list = []
    for virus in VIRUS_REFERENCE_SEGMENT_DICT:
        virus_dropdown_item = dbc.DropdownMenuItem(
            virus,
            id={"type": "virus-dropdown-menu-item", "index": virus}
        )
        if virus == selected_virus:
            virus_dropdown_item.active = True
        virus_dropdown_item_list.append(virus_dropdown_item)

    references_dict = VIRUS_REFERENCE_SEGMENT_DICT[selected_virus]
    selected_reference = session.get("reference")
    reference_dropdown_item_list = []
    for reference in references_dict:
        reference_dropdown_item = dbc.DropdownMenuItem(reference)
        if reference == selected_reference:
            reference_dropdown_item.active = True
        reference_dropdown_item_list.append(reference_dropdown_item)

    segments_list = references_dict[selected_reference]
    selected_segment = session.get("segment")
    segment_dropdown_item_list = []
    for segment in segments_list:
        segment_dropdown_item = dbc.DropdownMenuItem(segment)
        if segment == selected_segment:
            segment_dropdown_item.active = True
        segment_dropdown_item_list.append(segment_dropdown_item)

    virus_dropdown = dbc.DropdownMenu(label="VIRUS",
                                      children=virus_dropdown_item_list,
                                      nav=True,
                                      id="virus-dropdown-menu")
    reference_dropdown = dbc.DropdownMenu(label="REFERENCE",
                                          children=reference_dropdown_item_list,
                                          nav=True,
                                          id="reference-dropdown-menu")
    segment_dropdown = dbc.DropdownMenu(label="SEGMENT",
                                        children=segment_dropdown_item_list,
                                        nav=True,
                                        id="segment-dropdown-menu")

    return [virus_dropdown, reference_dropdown, segment_dropdown]