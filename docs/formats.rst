.. _formats:

=======
Formats
=======

Tablib supports a wide variety of different tabular formats, both for input and
output. Moreover, you can :ref:`register your own formats <newformats>`.

.. _line-breaks:

Cell text and line breaks
=========================

A cell can hold any text, including line breaks. How a line break is carried
depends on what the target format can express, so the text formats are grouped
into three fidelity tiers. The tier decides what an export looks like and
whether an export can be imported back unchanged.

Exact fidelity
--------------

The format quotes or escapes cell values, so a line break is written verbatim
and an export followed by an import returns the original dataset. This applies
to ``csv`` and ``tsv`` (RFC 4180 quoting), ``json`` (``\n`` escapes), ``yaml``
(double-quoted scalars), ``html`` (text nodes) and ``sql`` (string literals,
export only). CSV, for example, quotes such a cell::

    id,text
    1,"a
    b"

YAML writes any string containing a line break as a double-quoted scalar, with
the line break spelled as the ``\n`` escape::

    - id: '1'
      text: "a\nb"

That is deliberate. PyYAML's default single-quoted style marks the line break
by indentation, so re-indenting the emitted document (for example when
embedding it in a larger YAML file) used to change the value. The ``\n``
escape is unaffected by re-indentation. Strings without line breaks keep the
style they always had.

Equivalent fidelity
-------------------

``jira`` and ``latex`` are line-oriented: one physical output line is one table
row, so a raw line break inside a cell would split the row and misalign the
columns downstream. The line break is therefore written with the notation the
format defines for a line break. The cell stays on one line and the table
structure survives.

``jira`` uses ``\\``, the Jira wiki markup notation for an explicit line
break::

    ||id||text||
    |1|a\\b|

``latex`` typesets such a cell with ``\shortstack``, with the lines separated
by ``\\``::

    1 & \shortstack{a \\ b} \\

The conversion is lossy: the notation is markup, not the original line break,
so an import cannot be offered. Reversing it means splitting on the two
characters ``\`` ``\`` (jira) or on the same pair inside ``\shortstack``
(latex) and treating the result as lines again.

Layout
------

``rst`` and ``cli`` render tables for people to read, not data to exchange. A
cell with line breaks is laid out over several output lines, so the line break
is preserved visually but the output no longer maps one output line to one
table row. ``rst`` switches from a simple table to a grid table for such a
dataset, because a simple table cannot hold a multi-line cell::

    +----+------+
    | id | text |
    +====+======+
    | 1  | a    |
    |    | b    |
    +----+------+

Line endings
------------

The line endings ``\n``, ``\r\n`` and ``\r`` are all treated as line breaks.
The exact-fidelity formats keep the characters as they are; the equivalent and
layout tiers normalise them to ``\n`` before converting. A cell without any
line break is exported byte for byte as it was before line-break handling
existed, in every format.

cli
===

The ``cli`` format is currently export-only. The exports produce a representation
table suited to a terminal.

When exporting to a CLI you can pass the table format  with the ``tablefmt``
parameter, the supported formats are::

    >>> import tabulate
    >>> list(tabulate._table_formats)
    ['simple', 'plain', 'grid', 'fancy_grid', 'github', 'pipe', 'orgtbl',
     'jira', 'presto', 'psql', 'rst', 'mediawiki', 'moinmoin', 'youtrack',
     'html', 'latex', 'latex_raw', 'latex_booktabs', 'tsv', 'textile']

For example::

    dataset.export("cli", tablefmt="github")
    dataset.export("cli", tablefmt="grid")

A cell containing line breaks is rendered by ``tabulate`` as a cell spanning
several lines in the table formats that support it. The result is a layout for
reading; see :ref:`line-breaks`.

This format is optional, install Tablib with ``pip install "tablib[cli]"`` to
make the format available.

csv
===

When you import CSV data, you can specify if the first line of your data source
is headers with the ``headers`` boolean parameter (defaults to ``True``)::

    import tablib

    tablib.import_set(your_data_stream, format='csv', headers=False)

It is also possible to provide the ``skip_lines`` parameter for the number of
lines that should be skipped before starting to read data.

.. versionchanged:: 3.1.0

    The ``skip_lines`` parameter was added.

When exporting with the ``csv`` format, the top row will contain headers, if
they have been set. Otherwise, the top row will contain the first row of the
dataset.

When importing a CSV data source or exporting a dataset as CSV, you can pass any
parameter supported by the :py:func:`csv.reader` and :py:func:`csv.writer`
functions. For example::

    tablib.import_set(your_data_stream, format='csv', dialect='unix')

    dataset.export('csv', delimiter=' ', quotechar='|')

.. admonition:: Line endings

     Exporting uses \\r\\n line endings by default so, make sure to include
     ``newline=''`` otherwise you will get a blank line between each row
     when you open the file in Excel::

         with open('output.csv', 'w', newline='') as f:
             f.write(dataset.export('csv'))

     If you do not do this, and you export the file on Windows, your
     CSV file will open in Excel with a blank line between each row.

dbf
===

Import/export using the dBASE_ format.

.. admonition:: Binary Warning

    The ``dbf`` format contains binary data, so make sure to write in binary
    mode::

        with open('output.dbf', 'wb') as f:
            f.write(dataset.export('dbf')

.. _dBASE: https://en.wikipedia.org/wiki/DBase

df (DataFrame)
==============

Import/export using the pandas_ DataFrame format. This format is optional,
install Tablib with ``pip install "tablib[pandas]"`` to make the format available.

.. _pandas: https://pandas.pydata.org/

html
====

The exports produce an HTML page with the data in a ``<table>``. If headers have
been set, they will be used as table headers (``thead``).

When you import HTML, you can specify a specific table to import by providing
the ``table_id`` argument::

    import tablib

    tablib.import_set(your_html, format='html', table_id='some_table_id')

Otherwise, the first table found will be imported.

.. versionchanged:: 3.6.0

    The ability to import HTML was added. The dependency on MarkupPy was dropped.

jira
====

The ``jira`` format is currently export-only. Exports format the dataset
according to the Jira table syntax::

    ||heading 1||heading 2||heading 3||
    |col A1|col A2|col A3|
    |col B1|col B2|col B3|

A cell containing line breaks stays on one physical line; each line break is
written as ``\\``, the Jira notation for an explicit line break. See
:ref:`line-breaks`.

json
====

Import/export using the JSON_ format. If headers have been set, a JSON list of
objects will be returned. If no headers have been set, a JSON list of lists
(rows) will be returned instead.

Import assumes (for now) that headers exist.

.. _JSON: http://json.org/

latex
=====

Import/export using the LaTeX_ format. This format is export-only.
If a title has been set, it will be exported as the table caption.

A cell containing line breaks is typeset with ``\shortstack`` so that it does
not end the table row. See :ref:`line-breaks`.

.. _LaTeX: https://www.latex-project.org/

ods
===

Import/export data in OpenDocument Spreadsheet format.

.. versionadded:: 3.6.0

    Import functionality was added.

This format is optional, install Tablib with ``pip install "tablib[ods]"`` to
make the format available.

The ``import_set()`` method also supports a ``skip_lines`` parameter that you
can set to a number of lines that should be skipped before starting to read
data.

.. admonition:: Binary Warning

    :class:`Dataset.ods` contains binary data, so make sure to write in binary mode::

        with open('output.ods', 'wb') as f:
            f.write(data.ods)

rst
===

Export data as a reStructuredText_ table representation of a dataset. The
``rst`` format is export-only.

Exporting returns a simple table if the text in the first column is never
wrapped, otherwise returns a grid table::

    >>> from tablib import Dataset
    >>> bits = ((0, 0), (1, 0), (0, 1), (1, 1))
    >>> data = Dataset()
    >>> data.headers = ['A', 'B', 'A and B']
    >>> for a, b in bits:
    ...     data.append([bool(a), bool(b), bool(a * b)])
    >>> table = data.export('rst')
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

A dataset whose headers or cells contain line breaks always uses a grid table,
because a simple table cannot express a cell spanning several lines. The line
breaks are rendered as line breaks inside the cell instead of being collapsed
into spaces. See :ref:`line-breaks`.

.. _reStructuredText: http://docutils.sourceforge.net/rst.html

tsv
===

A variant of the csv_ format with tabulators as fields separators.

xls
===

Import/export data in Legacy Excel Spreadsheet representation.

This format is optional, install Tablib with ``pip install "tablib[xls]"`` to
make the format available.

Its ``import_set()`` method also supports a ``skip_lines`` parameter that you
can set to a number of lines that should be skipped before starting to read
data.

.. versionchanged:: 3.1.0

    The ``skip_lines`` parameter for ``import_set()`` was added.

.. note::

    XLS files are limited to a maximum of 65,000 rows. Use xlsx_ to avoid this
    limitation.

.. admonition:: Binary Warning

    The ``xls`` file format is binary, so make sure to write in binary mode::

        with open('output.xls', 'wb') as f:
            f.write(data.export('xls'))

xlsx
====

Import/export data in Excel 07+ Spreadsheet representation.

This format is optional, install Tablib with ``pip install "tablib[xlsx]"`` to
make the format available.

The ``import_set()`` and ``import_book()`` methods accept keyword
argument ``read_only``.  If its value is ``True`` (the default), the
XLSX data source is read lazily.  Lazy reading generally reduces time
and memory consumption, especially for large spreadsheets.  However,
it relies on the XLSX data source declaring correct dimensions.  Some
programs generate XLSX files with incorrect dimensions.  Such files
may need to be loaded with this optimization turned off by passing
``read_only=False``.

The ``import_set()`` method also supports a ``skip_lines`` parameter that you
can set to a number of lines that should be skipped before starting to read
data.

The ``export_set()`` method supports a ``column_width`` parameter. Depending
on the value passed, the column width will be set accordingly. It can be
either ``None``, an integer, or default "adaptive". If "adaptive" is passed,
the column width will be unique and will be calculated based on values' length.
For example::

    data = tablib.Dataset()
    data.export('xlsx', column_width='adaptive')

This works with ``Databook`` as well::

    data = tablib.Databook()
    data.export('xlsx', column_width='adaptive')

The adaptive width will be calculated for each sheet in the databook.

.. versionchanged:: 3.8.0
    The ``column_width`` parameter for ``export_set()`` was added.

.. versionchanged:: 3.1.0

    The ``skip_lines`` parameter for ``import_set()`` was added.

.. note::

    When reading an ``xlsx`` file containing formulas in its cells, Tablib will
    read the cell values, not the cell formulas.

.. versionchanged:: 2.0.0

    Reads cell values instead of formulas.

You can export data to xlsx format by calling :meth:`export('xlsx') <.export>`.
There are optional parameters to control the export.
For available parameters, see :meth:`tablib.formats._xlsx.XLSXFormat.export_set`.

.. admonition:: Binary Warning

    The ``xlsx`` file format is binary, so make sure to write in binary mode::

        with open('output.xlsx', 'wb') as f:
            f.write(data.export('xlsx'))

yaml
====

Import/export data in the YAML_ format.
When exporting, if headers have been set, a YAML list of objects will be
returned. If no headers have been set, a YAML list of lists (rows) will be
returned instead.

Import assumes (for now) that headers exist.

This format is optional, install Tablib with ``pip install "tablib[yaml]"`` to
make the format available.

.. _YAML: https://yaml.org

sql
===

.. versionadded:: 3.9.0

The ``sql`` format is export-only. It produces SQL INSERT statements (one per row)
assuming the target table already exists with the same columns.
The table name can be passed as an argument or will be taken from the dataset's title (or defaults to ``export_table``).
Columns can be passed as an argument or will be taken from the dataset's headers.
Values are rendered as ANSI SQL literals.
Additionally the argument ``commit`` can be passed to add a ``COMMIT;`` statement at the end.

- ``NULL`` for null values
- ``TRUE``/``FALSE`` for booleans
- ``DATE 'YYYY-MM-DD'`` for date values
- ``TIMESTAMP 'YYYY-MM-DD HH:MM:SS'`` for timestamp values
- Numeric literals for ints/floats/decimals
- Single-quoted strings with embedded quotes escaped

Example::

    import datetime
    from tablib import Dataset

    data = Dataset(title='users')
    data.headers = ['id', 'name', 'joined']
    data.append([1, 'Alice', datetime.date(2021,1,1)])

    print(data.export('sql'))
    print(data.export('sql', table='\"User_Updates\"', columns=['id', 'username', 'update_date'], commit=True))

Output::

    INSERT INTO users (id,name,joined) VALUES (1, 'Alice', DATE '2021-01-01');

    INSERT INTO "User_Updates" (id,username,update_date) VALUES (1, 'Alice', DATE '2021-01-01');
    COMMIT;
