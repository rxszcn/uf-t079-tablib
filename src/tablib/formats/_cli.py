"""Tablib - Command-line Interface table export support.

   Generates a representation for CLI from the dataset.
   Wrapper for tabulate library.
"""

__lazy_modules__ = {"tabulate", "tablib.formats._text"}

from tabulate import tabulate as Tabulate

from ._text import has_line_break, normalize_line_breaks


class CLIFormat:
    """ Class responsible to export to CLI Format """
    title = 'cli'
    DEFAULT_FMT = 'plain'

    @staticmethod
    def _normalize(value):
        """Spell line breaks ``\\n`` so the layout does not depend on whether
        the cell was originally written with ``\\n``, ``\\r\\n`` or ``\\r``."""
        if isinstance(value, str) and has_line_break(value):
            return normalize_line_breaks(value)
        return value

    @classmethod
    def export_set(cls, dataset, **kwargs):
        """Returns CLI representation of a Dataset.

        Cells containing line breaks are rendered by ``tabulate`` as cells
        spanning several lines where the table format allows it. The result
        is a layout for reading, not a data interchange format.
        """
        if dataset.headers:
            kwargs.setdefault('headers', [cls._normalize(h) for h in dataset.headers])
        kwargs.setdefault('tablefmt', cls.DEFAULT_FMT)
        rows = [[cls._normalize(value) for value in row] for row in dataset]
        return Tabulate(rows, **kwargs)
