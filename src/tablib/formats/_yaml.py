""" Tablib - YAML Support.
"""

__lazy_modules__ = {"yaml"}

import yaml

import tablib

from ._text import has_line_break


class LineBreakDumper(yaml.SafeDumper):
    """Safe dumper which writes any string containing a line break as a
    double-quoted scalar.

    PyYAML's default emitter picks the single-quoted style for such a string
    when it is block-folded (``- {text: 'a\\n\\n    b'}``). That style relies on
    indentation to mark the line break, so a consumer which re-indents the
    document (for example when embedding it as a nested block) changes the
    value. Double quotes spell the line break as the ``\\n`` escape instead,
    which no re-indentation can alter. Strings without line breaks keep the
    exact style they had before.
    """

    def represent_str(self, data):
        style = '"' if has_line_break(data) else None
        return self.represent_scalar('tag:yaml.org,2002:str', data, style=style)


LineBreakDumper.add_representer(str, LineBreakDumper.represent_str)


def _dump(data):
    return yaml.dump(
        data,
        Dumper=LineBreakDumper,
        default_flow_style=None,
        allow_unicode=True,
        sort_keys=False,
    )


class YAMLFormat:
    title = 'yaml'
    extensions = ('yaml', 'yml')

    @classmethod
    def export_set(cls, dataset):
        """Returns YAML representation of Dataset."""
        return _dump(dataset._package())

    @classmethod
    def export_book(cls, databook):
        """Returns YAML representation of Databook."""
        return _dump(databook._package())

    @classmethod
    def import_set(cls, dset, in_stream):
        """Returns dataset from YAML stream."""

        dset.wipe()
        dset.dict = yaml.safe_load(in_stream)

    @classmethod
    def import_book(cls, dbook, in_stream):
        """Returns databook from YAML stream."""

        dbook.wipe()

        for sheet in yaml.safe_load(in_stream):
            data = tablib.Dataset()
            data.title = sheet['title']
            data.dict = sheet['data']
            dbook.add_sheet(data)

    @classmethod
    def detect(cls, stream):
        """Returns True if given stream is valid YAML."""
        try:
            _yaml = yaml.safe_load(stream)
            if isinstance(_yaml, (list, tuple, dict)):
                return True
            else:
                return False
        except (yaml.parser.ParserError, yaml.reader.ReaderError,
                yaml.scanner.ScannerError):
            return False
