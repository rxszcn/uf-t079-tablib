""" Tablib - reStructuredText Support
"""

__lazy_modules__ = {"itertools", "statistics", "textwrap", "tablib.formats._text"}

from itertools import zip_longest
from statistics import median
from textwrap import TextWrapper

from ._text import has_line_break, split_lines

JUSTIFY_LEFT = 'left'
JUSTIFY_CENTER = 'center'
JUSTIFY_RIGHT = 'right'
JUSTIFY_VALUES = (JUSTIFY_LEFT, JUSTIFY_CENTER, JUSTIFY_RIGHT)


def to_str(value):
    if isinstance(value, bytes):
        return value.decode('utf-8')
    return str(value)


def _max_word_len(text):
    """
    Return the length of the longest word in `text`.

    >>> _max_word_len('Python Module for Tabular Datasets')
    8
    """
    return max((len(word) for word in text.split()), default=0) if text else 0


def _max_line_len(text):
    """Length of the longest physical line in `text`.

    A cell containing line breaks is laid out on several lines, so its width
    is driven by its longest line rather than by the length of the whole
    string. Non-string values are measured as before.
    """
    if not isinstance(text, str):
        return len(text)
    if not has_line_break(text):
        return len(text)
    return max(len(line) for line in split_lines(text))


class ReSTFormat:
    title = 'rst'
    extensions = ('rst',)

    MAX_TABLE_WIDTH = 80  # Roughly. It may be wider to avoid breaking words.

    @classmethod
    def _get_column_string_lengths(cls, dataset):
        """
        Returns a list of string lengths of each column, and a list of
        maximum word lengths.

        For a cell containing line breaks the length of its longest line is
        used, since the cell is rendered on several lines.
        """
        if dataset.headers:
            # Headers are measured exactly as before; only a string header
            # with line breaks is measured by its longest line.
            column_lengths = [
                [_max_line_len(h) if isinstance(h, str) and has_line_break(h) else len(h)]
                for h in dataset.headers
            ]
            word_lens = [_max_word_len(h) for h in dataset.headers]
        else:
            column_lengths = [[] for _ in range(dataset.width)]
            word_lens = [0 for _ in range(dataset.width)]
        for row in dataset.dict:
            values = iter(row.values() if hasattr(row, 'values') else row)
            for i, val in enumerate(values):
                text = to_str(val)
                column_lengths[i].append(_max_line_len(text))
                word_lens[i] = max(word_lens[i], _max_word_len(text))
        return column_lengths, word_lens

    @classmethod
    def _wrap_cell(cls, wrapper, text):
        """Wrap one cell into the lines it occupies.

        A cell without line breaks is wrapped exactly as before. A cell with
        line breaks keeps them: every physical line is wrapped on its own and
        the lines are laid out one after another, so the line break is
        rendered as a line break instead of being collapsed into a space.
        """
        if not has_line_break(text):
            return wrapper.wrap(text)
        cell = []
        for line in split_lines(text):
            # ``wrap`` returns an empty list for a blank line; keep a blank
            # line so the cell's vertical extent matches its content.
            cell.extend(wrapper.wrap(line) or [''])
        return cell

    @classmethod
    def _row_to_lines(cls, values, widths, wrapper, sep='|', justify=JUSTIFY_LEFT):
        """
        Returns a table row of wrapped values as a list of lines
        """
        if justify not in JUSTIFY_VALUES:
            raise ValueError('Value of "justify" must be one of "{}"'.format(
                '", "'.join(JUSTIFY_VALUES)
            ))

        def just(text_, width_):
            if justify == JUSTIFY_LEFT:
                return text_.ljust(width_)
            elif justify == JUSTIFY_CENTER:
                return text_.center(width_)
            else:
                return text_.rjust(width_)
        lpad = sep + ' ' if sep else ''
        rpad = ' ' + sep if sep else ''
        pad = ' ' + sep + ' '
        cells = []
        for value, width in zip(values, widths):
            wrapper.width = width
            text = to_str(value)
            cell = cls._wrap_cell(wrapper, text)
            cells.append(cell)
        lines = zip_longest(*cells, fillvalue='')
        lines = (
            (just(cell_line, widths[i]) for i, cell_line in enumerate(line))
            for line in lines
        )
        lines = [''.join((lpad, pad.join(line), rpad)) for line in lines]
        return lines

    @classmethod
    def _get_column_widths(cls, dataset, max_table_width=MAX_TABLE_WIDTH, pad_len=3):
        """
        Returns a list of column widths proportional to the median length
        of the text in their cells.
        """
        str_lens, word_lens = cls._get_column_string_lengths(dataset)
        median_lens = [int(median(lens)) for lens in str_lens]
        total = sum(median_lens)
        if total > max_table_width - (pad_len * len(median_lens)):
            column_widths = (max_table_width * lens // total for lens in median_lens)
        else:
            column_widths = (lens for lens in median_lens)
        # Allow for separator and padding:
        column_widths = (w - pad_len if w > pad_len else w for w in column_widths)
        # Rather widen table than break words, but keep at least one character
        # so a column of only empty cells still has a valid, non-zero width:
        column_widths = [max(w, l, 1) for w, l in zip(column_widths, word_lens)]
        return column_widths

    @classmethod
    def export_set_as_simple_table(cls, dataset, column_widths=None):
        """
        Returns reStructuredText grid table representation of dataset.
        """
        lines = []
        wrapper = TextWrapper()
        if column_widths is None:
            column_widths = cls._get_column_widths(dataset, pad_len=2)
        border = '  '.join(['=' * w for w in column_widths])

        lines.append(border)
        if dataset.headers:
            lines.extend(cls._row_to_lines(
                dataset.headers,
                column_widths,
                wrapper,
                sep='',
                justify=JUSTIFY_CENTER,
            ))
            lines.append(border)
        for row in dataset.dict:
            values = iter(row.values() if hasattr(row, 'values') else row)
            lines.extend(cls._row_to_lines(values, column_widths, wrapper, ''))
        lines.append(border)
        return '\n'.join(lines)

    @classmethod
    def export_set_as_grid_table(cls, dataset, column_widths=None):
        """
        Returns reStructuredText grid table representation of dataset.


        >>> from tablib import Dataset
        >>> from tablib.formats import registry
        >>> bits = ((0, 0), (1, 0), (0, 1), (1, 1))
        >>> data = Dataset()
        >>> data.headers = ['A', 'B', 'A and B']
        >>> for a, b in bits:
        ...     data.append([bool(a), bool(b), bool(a * b)])
        >>> rst = registry.get_format('rst')
        >>> print(rst.export_set(data, force_grid=True))
        +-------+-------+-------+
        |   A   |   B   | A and |
        |       |       |   B   |
        +=======+=======+=======+
        | False | False | False |
        +-------+-------+-------+
        | True  | False | False |
        +-------+-------+-------+
        | False | True  | False |
        +-------+-------+-------+
        | True  | True  | True  |
        +-------+-------+-------+

        """
        lines = []
        wrapper = TextWrapper()
        if column_widths is None:
            column_widths = cls._get_column_widths(dataset)
        header_sep = '+=' + '=+='.join(['=' * w for w in column_widths]) + '=+'
        row_sep = '+-' + '-+-'.join(['-' * w for w in column_widths]) + '-+'

        lines.append(row_sep)

        if dataset.headers:
            lines.extend(cls._row_to_lines(
                dataset.headers,
                column_widths,
                wrapper,
                justify=JUSTIFY_CENTER,
            ))
            lines.append(header_sep)
        for row in dataset.dict:
            values = iter(row.values() if hasattr(row, 'values') else row)
            lines.extend(cls._row_to_lines(values, column_widths, wrapper))
            lines.append(row_sep)
        return '\n'.join(lines)

    @classmethod
    def _use_simple_table(cls, head0, col0, width0):
        """
        Use a simple table if the text in the first column is never wrapped


        >>> from tablib.formats import registry
        >>> rst = registry.get_format('rst')
        >>> rst._use_simple_table('menu', ['egg', 'bacon'], 10)
        True
        >>> rst._use_simple_table(None, ['lobster thermidor', 'spam'], 10)
        False

        """
        if head0 is not None:
            head0 = to_str(head0)
            if len(head0) > width0:
                return False
        for cell in col0:
            cell = to_str(cell)
            if len(cell) > width0:
                return False
        return True

    @classmethod
    def _has_line_breaks(cls, dataset):
        """True when any header or cell holds a line break.

        A simple table cannot express a cell spanning several lines, so a
        dataset with line breaks is always rendered as a grid table.
        """
        values = list(dataset.headers or ())
        for row in dataset.dict:
            values.extend(row.values() if hasattr(row, 'values') else row)
        return any(has_line_break(to_str(value)) for value in values)

    @classmethod
    def export_set(cls, dataset, **kwargs):
        """
        Returns reStructuredText table representation of dataset.

        Returns a simple table if the text in the first column is never
        wrapped, otherwise returns a grid table. A dataset whose cells
        contain line breaks always uses a grid table, where the line breaks
        are rendered as line breaks inside the cell instead of being
        collapsed into spaces.


        >>> from tablib import Dataset
        >>> bits = ((0, 0), (1, 0), (0, 1), (1, 1))
        >>> data = Dataset()
        >>> data.headers = ['A', 'B', 'A and B']
        >>> for a, b in bits:
        ...     data.append([bool(a), bool(b), bool(a * b)])
        >>> table = data.rst
        >>> table.split('\\n') == [
        ...     '=====  =====  =====',
        ...     '  A      B    A and',
        ...     '                B  ',
        ...     '=====  =====  =====',
        ...     'False  False  False',
        ...     'True   False  False',
        ...     'False  True   False',
        ...     'True   True   True ',
        ...     '=====  =====  =====',
        ... ]
        True

        """
        if not dataset.dict:
            return ''
        force_grid = kwargs.get('force_grid', False)
        max_table_width = kwargs.get('max_table_width', cls.MAX_TABLE_WIDTH)
        column_widths = cls._get_column_widths(dataset, max_table_width)

        use_simple_table = cls._use_simple_table(
            dataset.headers[0] if dataset.headers else None,
            dataset.get_col(0),
            column_widths[0],
        )
        if use_simple_table and not force_grid and not cls._has_line_breaks(dataset):
            return cls.export_set_as_simple_table(dataset, column_widths)
        else:
            return cls.export_set_as_grid_table(dataset, column_widths)

    @classmethod
    def export_book(cls, databook):
        """
        reStructuredText representation of a Databook.

        Tables are separated by a blank line. All tables use the grid
        format.
        """
        return '\n\n'.join(cls.export_set(dataset, force_grid=True)
                           for dataset in databook._datasets)
