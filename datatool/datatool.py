import os
import re
from . import converter
from .config.exceptions import ConditionTypeError, FieldHeaderError
from dateutil.parser import parse


class DataTool():
    headers = {}
    CONDITIONS = {
        'CONTAINS':
            lambda value, match_value:
                value.rfind(match_value) != -1,
        'EQUALS':
            lambda value, match_value:
                value == match_value,
        'GREATER':
            lambda value, match_value:
                value > match_value,
        'LESS':
            lambda value, match_value:
                value < match_value,
        'BEFORE':
            lambda value, match_value:
                value < match_value,
        'AFTER':
            lambda value, match_value:
                value > match_value,
        'BETWEEN':
            lambda value, match_value:
                True,
        'NOT':
            lambda value, match_value:
                value != match_value
    }

    def __init__(self, **kwargs):
        """Upon instantiation set the defaults for this object
            A datatool takes in a filename, a terminator for fields,
            and an encloser for multiple values

        :param filename, a path to a valid existing read File
        :param terminator, the string used to terminate fields in the File
        :param encloser, the string to enclose multiple values in a single
        field
        """
        try:
            self.filename = kwargs.get('filename')
        except:
            raise AttributeError('Filename kwarg must be provided')
        if not os.path.exists(self.filename):
            raise AttributeError('File must exist')
        self.terminator = kwargs.get('terminator', ',')
        self.encloser = kwargs.get('encloser', '\"')
        with open(self.filename, 'r') as f:
            header_string = f.readline().strip()
        self.headers = converter.get_indexes(
            data=header_string,
            terminator=self.terminator,
            encloser=self.encloser
        )

    def statistics(self, field, search, return_type, top):
        """ Calculates statistics for the data file provided during
        instantiation

        :param field, a valid field in the data file
        :param search, a dictionary of the search, required is the regex key
        and either a pattern or string value, optional is group_idx, an integer
        of the grouping to grab the result from e.g.
        {
            'regex': '.*'
        }
        :param result, a character to determine how to calculate the result,
        currently either %  for percent, or # for numeric
        :param top, an integer, how many results to show, group the others
        :rtype dictionary
        """
        stats = {'data': {}}
        try:
            regex = re.compile(search['regex'])
        except:
            raise TypeError('Regex must be supplied as a string / pattern')
        with open(self.filename, 'r') as f:
            f.readline()
            for row_number, line in enumerate(f):
                row = converter.convert_to_dict(
                    data=line,
                    terminator=self.terminator,
                    encloser=self.encloser,
                    headers=self.headers
                )
                try:
                    value = row[field]
                except:
                    raise FieldHeaderError(field, row.keys())
                # rewrite this......
                regex_result = regex.search(value)
                if regex_result is not None:
                    if (
                        'group_idx' in search.keys() and
                        regex_result.groups() is not None
                    ):
                        result = regex_result.groups()[search['group_idx']]
                    elif regex_result.group() is not None:
                        result = regex_result.group()
                    else:
                        result = None
                    if result is not None:
                        stats['data'][result] = stats['data'].get(
                            result, 0
                        ) + 1

        if return_type == '%':
            stats['data'].update(
                {
                    k: v*(100/(row_number+1))
                    for k, v in stats['data'].items()
                }
            )
        return stats

    def __process_query(self, row, queries, func=all):
        """[PRIVATE] Processes a query on a row of data
        :param row, a dictionary of headers and values for the row
        :param clause, a dictionary of the query, with the keys: field,
        condition and value e.g.
        {
            'field': 'email',
            'condition': 'contains',
            'value': 'gmail'
        }
        :rtype boolean
        """
        if isinstance(queries, dict):
            queries = [queries]
        query_results = []
        # Local variables are looked up quicker than global
        query_results_append = query_results.append
        for query in queries:
            condition = query.get('condition')
            field = query.get('field')
            if condition in ('BEFORE', 'AFTER'):
                row[field] = parse(row[field])  # bottle neck
            query_results_append(
                self.CONDITIONS[condition](row[field], query.get('value'))
            )
        return func(query_results)

    def __validate_query(self, data_types, query):
        """[PRIVATE] Validates a query against the datatypes for the Row

        :param data_types, a dictionary of headers and data types for that
        field
        :param query, a dictionary of the query, with the keys: field,
        condition and value e.g.
        {
            'field': 'email',
            'condition': 'contains',
            'value': 'gmail'
        }
        :rtype boolean
        """
        field = query.get('field')
        condition = query.get('condition')
        if condition not in self.CONDITIONS.keys():
            raise ValueError(
                'condition must be one of '.format(
                    ', '.join(self.CONDITIONS.keys())
                )
            )
        elif (
            condition in ('GREATER', 'LESS') and
            data_types.get(field) != 'numeric'
        ):
            raise ConditionTypeError('numeric', ['GREATER', 'LESS'])
        elif (
            condition in ('BEFORE', 'AFTER') and
            data_types.get(field) != 'date'
        ):
            raise ConditionTypeError('datetime', ['BEFORE', 'AFTER'])
        else:
            return True

    def __process_line(self, row, where, func):
        """[PRIVATE]Initially called by the query method - generates data types
        and validates the where queries before handing off via self assignment
        the query method - quicker than having an if statement and checking var
        in query

        :param row, a dictionary representing the data source as
        header, value pairs
        :param where, a list of queries to perform on the row
        :param func, a function, the any or all function - OR / AND bool logic

        :rtype boolean
        """
        data_types = converter.convert_to_types(row)
        for query in where:
            self.__validate_query(data_types, query)
        self.__process_line = self.__process_query
        return self.__process_query(row, where, func)

    def query(self, fields, where, match_all, outfile):
        """Executes a query on the datafile tied to the object, and creates a
        new file of the output

        :param fields, a list of fields to return from the source data file
        :param where, a list of dictionaries (or single dict), of clauses
        :param match_all, a boolean, True will match if the row meets all the
        clauses in the where
        :param outfile, the path to, and name to write the outfile to

        :rtype dictionary of filename and records affected
        """

        if isinstance(where, dict):
            where = [where]
        valid_return_fields = set(fields).issubset(set(self.headers.keys()))
        query_fields = []
        for query in where:
            query['condition'] = query.get('condition').upper()
            try:
                query['value'] = parse(query.get('value'))
            except:
                pass
            query_fields.append(query.get('field'))
        valid_query_fields = set(query_fields).issubset(
            set(self.headers.keys())
        )
        if not valid_return_fields:
            raise FieldHeaderError(fields, self.headers.keys())
        elif not valid_query_fields:
            raise FieldHeaderError(query_fields, self.headers.keys())
        else:
            query_result = {'data': {'filename': outfile, 'records': 0}}
            if match_all:
                func = all
            else:
                func = any
            with open(self.filename, 'r') as rf:
                with open(outfile, 'w') as wf:
                    wf.write(', '.join(fields) + '\n')
                    rf.readline()
                    for line in rf:
                        row = converter.convert_to_dict(
                            data=line,
                            terminator=self.terminator,
                            encloser=self.encloser,
                            headers=self.headers
                        )
                        if self.__process_line(row, where, func):
                            result = {}
                            result = {field: row[field] for field in fields}
                            query_result['data']['records'] += 1
                            write_line = converter.convert_to_string(
                                data=result,
                                terminator=',',
                                encloser='\"',
                                headers=[]
                            )
                            wf.write(write_line + '\n')

            return query_result
