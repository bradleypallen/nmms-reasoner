"""Semantic exit codes for the pyNMMS CLI.

Follows grep/diff/cmp convention:
    0 = success (derivable for ask)
    1 = error
    2 = not derivable (ask only)
"""

EXIT_SUCCESS = 0
EXIT_ERROR = 1
EXIT_NOT_DERIVABLE = 2
