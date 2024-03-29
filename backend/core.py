import os
import re
import itertools
from math import ceil
from .helpers import sw, generic_open, _in
from .gen_response import (
    UpgradePlan,
    InvalidQueryString,
    InvalidFieldName,
    PageNotPassed,
    NotAValidFieldType,
    TypeDoesntConfirmDefination,
)
from collections import namedtuple
from functools import reduce
from operator import lt, gt, eq, ge, le
from werkzeug.exceptions import HTTPException


class Table:
    limit_database = 5
    limit_records = 100

    def __init__(self, tablename, columns, joiner="|"):
        """
        Title/Header/Column-Name for Table is passed as tuple.
        This table represent for any shape or size file database representation
        of the SQL type data.
            Fields:
            tablename: string -> "Users"
            columns: tuple(field_name:field_type) ->
                ("Name:str","Address:str")
            joiner: string -> "|" or "," etc...
        """
        if not tablename or not columns:
            raise HTTPException(f"Invalid tablename: `{tablename}`")
        self.tablename = tablename if "/" not in tablename else tablename.split("/")[-1]
        self.columns = columns
        self.last_pk = 1
        self.joiner = joiner
        self.filelocation = "database/" + tablename + ".txt"
        self._insert(*self.columns)

    def __str__(self):
        return f"<Table: {self.tablename}>"

    def __repr__(self):
        return f"<Table: {self.tablename}>"

    def __eq__(self, other):
        if self.filelocation == other.filelocation:
            return True
        else:
            return False

    def _insert(self, *args):
        """
        This method when worked to create fresh table, creates file and
        when working on existing file have read/write privilages.
        """
        if os.path.isfile(self.filelocation):
            pass
        else:
            with generic_open(self.filelocation, mode="w") as file:
                data = (
                    reduce(lambda x, y: x + self.joiner + str(y), args, "pk:int") + "\n"
                )
                file.write(data)

    @staticmethod
    def _features():
        """
        This method is used to update membership features to inform users of service.
        """
        return {
            "feat": ["Relational Database", "insert method to insert record"],
            "database_limit": Table.limit_database,
            "record_limit": Table.limit_records,
        }

    def insert(self, **kwargs):
        """
        Inserts record to the database when intialising it
        Converts all the field to `str(field)` before inserting into database.
        """
        if self.last_pk >= self.limit_records:
            raise UpgradePlan(
                f"Your membership allows `{self.limit_records}` whereas "
                f"currently you have `{self.last_pk}`."
            )
        with generic_open(self.filelocation, mode="a") as file:
            fields = list(map(lambda x: x.split(":")[0], self.columns))
            data = str(self.last_pk)
            data = (
                reduce(lambda x, y: x + self.joiner + str(kwargs[y]), fields, data)
                + "\n"
            )
            file.write(data)
        self.last_pk += 1
        return kwargs

    @classmethod
    def access_table(cls, tablename, columns=tuple(), joiner="|"):
        filename = "database/" + tablename + ".txt"
        file = generic_open(filename, mode="r")
        lines = file.readlines()
        cols = tuple(lines[0].split(joiner)[1:])
        obj = cls(tablename, cols, joiner)
        file.close()
        obj.last_pk = len(lines)
        return obj


class Paginator:
    def __init__(self, table, page, items_on_page=5):
        """
        Page for Paginator starts from `1` to last page where last record can be found.
        """
        self.table = table
        self.current_page = page
        self.items_on_page = items_on_page
        self.last = ceil((self.table.last_pk - 1) / self.items_on_page)
        self.first = 1 if self.last > 1 else None

    def _has_prev_page(self):
        if (self.current_page - 1) > 0:
            return self.current_page - 1
        else:
            return None

    def _has_next_page(self):
        if (self.current_page + 1) <= self.last:
            return self.current_page + 1
        else:
            return None

    def serve(self):
        if self.current_page <= 0 or self.current_page > self.last:
            raise HTTPException(
                f"Please make sure `page` is within `(1, {self.last})`."
            )

        start = (self.current_page - 1) * self.items_on_page
        end = self.current_page * self.items_on_page
        resp = dict()
        resp["data"] = []
        for item in itertools.islice(self.table._read(), start, end):
            resp["data"].append(item)
        resp["next"] = self._has_next_page()
        resp["prev"] = self._has_prev_page()
        resp["first"] = self.first
        resp["last"] = self.last
        return resp


class FormattedTable(Table):
    limit_database = 50
    limit_records = 1000

    def __init__(self, tablename, columns, joiner="|"):
        Table.__init__(self, tablename, columns, joiner="|")
        self.field_format = dict()
        self._type_selector()

    def _type_selector(self):
        """
        Exclusively used for the `FormattedTable` at creation time only.
        It defines the `type` of the field(s) of the Table.
        primitive types are (str, int, list, dict, float, bool, None)
        """
        self.field_format.update({"pk": int})
        for col in self.columns:
            title = col.split(":")[0]
            if "str" in col:
                self.field_format.update({title: str})
            elif "int" in col:
                self.field_format.update({title: int})
            elif "list" in col:
                self.field_format.update({title: list})
            elif "dict" in col:
                self.field_format.update({title: dict})
            elif "float" in col:
                self.field_format.update({title: float})
            elif "bool" in col.lower():
                self.field_format.update({title: bool})
            else:
                raise NotAValidFieldType(
                    f"The type for field '{title}' is not valid field"
                    "description. Please provide valid type description"
                    "[str, int, float. bool, list, dict]"
                )

    def _type_checking(self, **kwargs):
        """
        Exclusively used for the insertion of the record to the
        FormattedTable. Performs type checking of the record data with type
        parsed from the field defination. Prevents mismatched datatype entry
        in Table. Raises `TypeDoesntConfirmDefination` when datatypes don't
        match. Method ignores all the extra `kwargs` as long as `all` needed
        kwargs are passed.
        """
        _ = []
        for fields in tuple(self.field_format.keys())[1:]:
            try:
                if type(kwargs[fields]) == self.field_format[fields]:
                    pass
                else:
                    _.append(fields)
            except KeyError:
                raise HTTPException(f"Invalid request. Check fields: `{fields}`.")
        if _:
            raise TypeDoesntConfirmDefination(
                f"Invalid request. Field `{_}` has invalid value type."
            )

    def _type_compliable(self, **kwargs):
        for fields in tuple(self.field_format.keys())[1:]:
            try:
                if isinstance(kwargs[fields], self.field_format[fields]):
                    pass
                else:
                    kwargs[fields] = self.field_format[fields](kwargs[fields])
            except KeyError:
                raise HTTPException(f"""Invalid request. Check fields: `{fields}`.""")
            except ValueError:
                raise HTTPException(f"Field:`{fields}` is compliant to defination")

    @staticmethod
    def _features():
        """
        This method is used to update membership features to inform users of product.
        """
        parent_feat = Table._features()
        table_feat = {
            "feat": [
                "Type Compliant Database",
                "query method to lookup by one field",
                "delete method to delete record by `pk`",
                "Generator based memory-efficient and faster lookup and quering"
                " on multiple fields O(nlogn)",
            ],
            "database_limit": FormattedTable.limit_database,
            "record_limit": FormattedTable.limit_records,
        }
        table_feat["feat"].extend(parent_feat["feat"])
        return table_feat

    def _read(self):
        """
        This method access data in "r" mode and returns type compliant records.
        """
        lines = (
            line.rstrip()
            for line in generic_open(self.filelocation, "r")
            if line.strip() != ""
        )
        cols = (line.split("|") for line in lines)
        next(lines)  # Ommiting title_record
        types = tuple(self.field_format.values())

        obj = namedtuple(self.tablename, tuple(self.field_format.keys()))

        def object_generator():
            "To create object with field values casted to type defined."
            for value in cols:
                argu = []
                for index, item in enumerate(value):
                    argu.append(types[index](item))
                yield obj(*argu)

        return (obj for obj in object_generator())

    def read(self):
        return list(self._read())

    def get_records(self):
        return [
            line.rstrip() for line in generic_open(self.filelocation, "r").readlines()
        ]

    def query(self, **kwargs):
        """
        This method is here to provide one parameter lookup only.
        Should need to aggregate by more than one parameter,
        use `Table().aggregate` method instead.
        """
        if len(kwargs.keys()) >= 2:
            raise HTTPException(
                """Please use `Table().aggregate` methods for \
                refined aggregation.
                """
            )

        output = []
        for key in kwargs.keys():
            for item in self._read():
                if getattr(item, key) == kwargs[key]:
                    output.append(item)
                    break
        return output

    def delete(self, pk):
        if pk == 0:
            raise HTTPException(f"Can not delete pk:`{pk}`, since it is title record.")
        record = self.query(pk=pk)
        with generic_open(self.filelocation, "r+") as file:
            for _ in range(pk):
                file.readline()
            start = file.tell()
            file.readline()
            end = file.tell()
            size = end - start - 1
            file.seek(start)
            file.write(" " * size)
        return record

    def insert(self, **kwargs):
        """
        Unlike parent's insert method, this method does _type_checking
        before inserting record into
        """
        self._type_compliable(**kwargs)
        return Table.insert(self, **kwargs)

    def from_database(self):
        """
        Returns Type compliant to defination of Table output from the database.
        """
        obj = namedtuple(self.tablename, tuple(self.field_format.keys()))
        types_tuple = tuple(self.field_format.values())
        output = []
        records = (
            record
            for record in generic_open(self.filelocation, "r")
            if record.strip() != ""
        )
        next(records)  # title_line
        for record in records:
            args = []
            for index, val in enumerate(record.rstrip().split(self.joiner)):
                if types_tuple[index] != str:
                    val = types_tuple[index](val)
                args.append(val)
            instance = obj(*args)
            output.append(instance)
        return output


class AggregateOperations:
    def __init__(self):
        self.ops = []

    def add_operation(self, field, value=0, op="eq"):
        """
        All Aggregation operation defined here are performed on `int` and
        `str` data type. For specific Operations, raise specific errors
        to inform users of how use specific operation.
        """
        self.ops.append((field, value, op))
        return self

    def clear(self):
        self.ops = []


class AggregatableTable(FormattedTable):
    limit_database = 500
    limit_records = 10000

    def __init__(self, tablename, columns, joiner="|"):
        FormattedTable.__init__(self, tablename, columns)
        self.aggregate = AggregateOperations()

    def _filter_record(self, record):
        """
        Preforms all the logical operations defined below on one record at time.
        Returns: True/False
        """
        hashmap_operation = {
            "lt": lt,
            "gt": gt,
            "le": le,
            "ge": ge,
            "eq": eq,
            "sw": sw,
            "in": _in,
        }
        passed = True
        for f, v, o in self.aggregate.ops:
            if hashmap_operation[o](getattr(record, f), v):
                continue
            else:
                passed = False
                break
        if not passed:
            return False
        return True

    @staticmethod
    def _features():
        """
        This method is used to update membership features to inform users of product.
        """
        parent_feat = FormattedTable._features()
        table_feat = {
            "feat": [
                "Generator based memory-efficient and faster lookup and quering on"
                " multiple fields O(nlogn)",
            ],
            "database_limit": AggregatableTable.limit_database,
            "record_limit": AggregatableTable.limit_records,
        }
        table_feat["feat"].extend(parent_feat["feat"])
        return table_feat

    def execute(self):
        """
        Performs all the logical operation provided by user on Table.
        Returns list of the query matching records.
        """
        output = list(filter(lambda x: self._filter_record(x), self._read()))
        self.aggregate.clear()
        return output


class Process_QS:
    """
    This class takes `query string` from the URL in `str` format and processes
    it to serve `Pagination` or to process `URL Search Parameter`
    """

    def __init__(self, qs, table):
        self.qs = qs
        self.table = table

    def process_pagination_or_url_parameter(self):
        if not re.fullmatch("([\w]*-?[\w]*=[\w]*&?)+", self.qs):
            raise InvalidQueryString
        if "page" in self.qs:
            return self.process_pagination()
        else:
            return self.process_url_parameter()

    def process_url_parameter(self):
        operations = ("gt", "ge", "le", "lt", "eq", "ne", "sw", "in")
        for op in self.qs.split("&"):
            field_operation, _, val = op.partition("=")
            if _ != "=":
                raise InvalidQueryString(
                    """please make sure to pass search parameter
                    as `field_name-operation=value`"""
                )
            fi_op = field_operation.partition("-")
            field = fi_op[0]
            op = fi_op[-1] if fi_op[-1] else "eq"
            if op not in operations:
                raise HTTPException(
                    f"""Operation: `{op}` is not valid.
                    Please choose from `{operations}`"""
                )
            try:
                val = self.table.field_format[field](val)
                self.table.aggregate.add_operation(field, val, op)
            except KeyError:
                raise InvalidFieldName
            except AttributeError:
                raise UpgradePlan()
        return {"data": self.table.execute()}

    def process_pagination(self):
        query_param_kv = dict()
        for i in self.qs.split("&"):
            # str.partition("=") >>> ("page-size", "=", "23")
            _ = i.partition("=")
            try:
                query_param_kv.update({_[0]: int(_[2])})
            except ValueError:
                raise HTTPException(
                    f"""Value for `{_[0]}` must be of `int` type,
                    not `{type(_[2])}`."""
                )
        page = query_param_kv.get("page", None)
        page_size = query_param_kv.get("page-size", 10)
        if page is None:
            raise PageNotPassed(
                """For Pagination `page` is must needed parameter.
                For size of page, define `page-size`."""
            )
        try:
            return Paginator(self.table, page, page_size).serve()
        except AttributeError:
            raise UpgradePlan()

    def process(self):
        return self.process_pagination_or_url_parameter()
