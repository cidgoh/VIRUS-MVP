"""Functions for generating toast views."""

import dash_bootstrap_components as dbc


def get_toast_row():
    """Get Dash Bootstrap Components row that contains toasts.

    :return: Dash Bootstrap Component row with toasts.
    :rtype: dbc.Row
    """
    ret = dbc.Row(
        dbc.Col(
            None,
            id="toast-col",
            width={"offset": 1, "size": 10}
        )
    )
    return ret


def get_toast(msg, header, color, duration):
    """Get toast div.

    @param msg: Message in toast body
    @type msg: str
    @param header: Message in toast header
    @type header: str
    @param color: Bootstrap color of icon in toast header
    @type color: str
    @param duration: Time in ms for toast before auto-dismissing
    @type duration: int
    @return: Toast with user-specified content
    @rtype: dbc.Toast
    """
    return dbc.Toast(
        msg,
        header=header,
        className="mt-1",
        dismissable=True,
        duration=duration,
        icon=color
    )
