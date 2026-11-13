""" Tablib - Cell text fidelity rules for the text formats.

A dataset cell is plain text. That text may contain line breaks, written as
``\\n``, ``\\r\\n`` or ``\\r`` depending on where the data came from. A text
format can only carry a line break if it has a way to express one, and the
ways differ enough that a single rule cannot fit every format. Exports are
therefore grouped into fidelity tiers:

``EXACT``
    The format has quoting or escaping that can carry an arbitrary string
    value, so a cell keeps its line breaks verbatim and export/import round
    trips are lossless. Formats: ``csv``, ``tsv`` (RFC 4180 quoting), ``json``
    (``\\n`` escapes), ``yaml`` (double-quoted scalars), ``html`` (text nodes),
    ``sql`` (string literals; export-only).

``EQUIVALENT``
    The format is line oriented: one physical output line is one table row,
    so a raw line break inside a cell would split the row. The line break is
    instead written with the markup the format defines for a line break, and
    the conversion rule is documented in ``docs/formats.rst``. Formats:
    ``jira`` (``\\\\`` explicit line break), ``latex`` (``\\shortstack``).

``LAYOUT``
    The format is a rendered table for humans, not a data interchange
    format. Cells may span several output lines, but the original line
    breaks are layout, not data. Formats: ``rst`` (grid tables), ``cli``
    (``tabulate`` renders multi-line cells).

Formats that carry line breaks verbatim must not be changed into any of the
other tiers: CSV/TSV/JSON/YAML/HTML imports rely on the round trip. Formats in
the ``EQUIVALENT`` and ``LAYOUT`` tiers never promise a lossless round trip.

Line endings are normalised before any line break logic runs, so ``\\r\\n``
and ``\\r`` are treated exactly like ``\\n``. ``EXACT`` formats keep the
original characters because they never call ``split_lines``.
"""

FIDELITY_EXACT = 'exact'
FIDELITY_EQUIVALENT = 'equivalent'
FIDELITY_LAYOUT = 'layout'

#: Public mapping of every text export format to its fidelity tier. Kept in
#: sync with the rules implemented by the individual format modules.
FORMAT_FIDELITY = {
    'cli': FIDELITY_LAYOUT,
    'csv': FIDELITY_EXACT,
    'html': FIDELITY_EXACT,
    'jira': FIDELITY_EQUIVALENT,
    'json': FIDELITY_EXACT,
    'latex': FIDELITY_EQUIVALENT,
    'rst': FIDELITY_LAYOUT,
    'sql': FIDELITY_EXACT,
    'tsv': FIDELITY_EXACT,
    'yaml': FIDELITY_EXACT,
}

#: The notation Jira wiki markup defines for an explicit line break.
JIRA_LINE_BREAK = '\\\\'


def has_line_break(text):
    """Return True when ``text`` contains ``\\n`` or ``\\r``."""
    return '\r' in text or '\n' in text


def normalize_line_breaks(text):
    """Return ``text`` with every line ending spelled ``\\n``."""
    return text.replace('\r\n', '\n').replace('\r', '\n')


def split_lines(text):
    """Split ``text`` into physical lines, normalising line endings first.

    A trailing line break produces a final empty line, so
    ``split_lines('a\\nb\\n') == ['a', 'b', '']``. This keeps a cell that ends
    with a line break distinguishable from one that does not.
    """
    return normalize_line_breaks(text).split('\n')


def escape_line_breaks(text, separator):
    """Replace every line break in ``text`` with ``separator``.

    Used by line-oriented formats: the line break becomes a visible token on
    the same physical line instead of splitting the table row.
    """
    if not has_line_break(text):
        return text
    return separator.join(split_lines(text))
