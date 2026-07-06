"""Example helper script shipped with the sample skill."""


def clean_headers(columns):
    return [c.strip().lower().replace(" ", "_") for c in columns]
