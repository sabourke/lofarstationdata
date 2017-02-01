from __future__ import absolute_import
from casacore.tables import table, makescacoldesc, makearrcoldesc, maketabdesc
import numpy as np
import os
from .ms_table_defs import ms_table_defs

class DefinedTable(object):
    def __init__(self, tab_type, location="", out_name=None):
        self.type = tab_type
        if out_name is None:
            out_name = self.type
        if location != "":
            out_name = location + os.sep + out_name
        td = ms_table_defs[self.type]
        self.table = table(out_name, td["desc"], ack=False)
        self.table.putinfo(td["info"])
        self.table.putkeywords(td["keywords"])
        for col, keywords in td["col_keywords"].items():
            self.table.putcolkeywords(col, keywords)

class MeasurementSet(object):
    def _to_camel_case(self, snake_str):
        components = snake_str.split('_')
        return components[0].lower() + "".join(x.title() for x in components[1:])

    def __init__(self, msname):
        self.table = DefinedTable("MAIN", location=msname, out_name="").table
        self.main = self.table
        # TODO: Submit OrderedDict patch in tables.py
        sub_tables = [k for k in ms_table_defs if k != "MAIN"]
        for subt in sub_tables:
            self.table.putkeyword(subt, "Table: " + DefinedTable(subt, location=self.table.name()).table.name())
            setattr(self, self._to_camel_case(subt), table(self.table.getkeyword(subt), readonly=False, ack=False))
