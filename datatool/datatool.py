import os
import re
from . import converter
from .config.exceptions import ConditionTypeError, FieldHeaderError
from dateutil.parser import parse


class DataTool():
    headers = {}
    CONDITIONS = {
        'CONTAINS':
            lambda value, match_value: value.rfind(match_value) != -1,
        'EQUALS':
            lambda value, match_value: value == match_value,
        'GREATER':
            lambda value, match_value: value > match_value,
        'LESS':
            lambda value, match_value: value < match_value,
        'BEFORE':
            lambda value, match_value: value < match_value,
        'AFTER':
            lambda value, match_value: value > match_value,
        'BETWEEN':
            lambda value, match_value: True,
        'NOT':
            lambda value, match_value: value != match_value
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
            raise AttributeError('{} must exist'.format(self.filename))
        self.terminator = kwargs.get('terminator', ',')
        self.encloser = kwargs.get('encloser', '\"')
        with open(self.filename, 'r') as f:
            header_string = f.readline().strip()
        self.headers = converter.get_indexes(
            data=header_string,
            terminator=self.terminator,
            encloser=self.encloser
        )

    def statistics(self, field, search, return_type):
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
        :rtype dictionary
        """
        stats = {'data': {}}
        try:
            regex = re.compile(search['regex'])
        except:
            regex = re.compile('.*')
        with open(self.filename, 'r') as fp:
            fp.readline()
            for row_number, line in enumerate(fp):
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
                    if 'group_idx' in search.keys() and regex_result.groups() is not None:
                        result = regex_result.groups()[search['group_idx']]
                    elif regex_result.group() is not None:
                        result = regex_result.group()
                    else:
                        result = None
                    if result is not None:
                        stats['data'][result] = stats['data'].get(
                            result, 0
                        ) + 1

        if return_type is '%':
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
        queries = [queries] if not isinstance(queries, list) else queries
        def test(field, condition, value):
            data = (
                parse(row[field]) if condition in ('BEFORE', 'AFTER')
                else row[field]
            )
            return self.CONDITIONS[condition](data, value)
        query_results = map(lambda query: test(**query), [query for query in queries])
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
        if condition not in self.CONDITIONS:
            raise ValueError(
                'condition must be one of '.format(
                    ', '.join(self.CONDITIONS)
                )
            )
        elif condition in ('GREATER', 'LESS') and data_types.get(field) != 'numeric':
            raise ConditionTypeError('numeric', ['GREATER', 'LESS'])
        elif condition in ('BEFORE', 'AFTER') and data_types.get(field) != 'date':
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

    def query(self, fields, where, match_all, outfile, insert=False):
        """Executes a query on the datafile tied to the object, and creates a
        new file of the output

        :param fields, a list of fields to return from the source data file
        :param where, a list of dictionaries (or single dict), of clauses
        :param match_all, a boolean, True will match if the row meets all the
        clauses in the where
        :param outfile, the path to, and name to write the outfile to

        :rtype dictionary of filename and records affected
        """
        is_valid_field = lambda field: field in self.headers
        if not all(map(is_valid_field, (f for f in fields))):
            raise FieldHeaderError(fields, self.headers)
        where = [where] if isinstance(where, dict) else where
        row_struct = {
            'terminator': self.terminator,
            'encloser' : self.encloser,
            'headers' : self.headers
        }
        for query in where:
            field = query.get('field')
            if not is_valid_field(field):
                raise FieldHeaderError([field], self.headers)
            query['condition'] = query.get('condition').upper()
            try:
                query['value'] = parse(query.get('value'))
            except:
                pass
        query_result = {'data': {'filename': outfile, 'records': 0}}
        func = all if match_all else any
        write_lines = []
        with open(self.filename, 'r') as rf:
            handle_type = 'a+' if insert else 'w'
            if handle_type is 'w':
                write_lines.append(', '.join(fields))
            rf.readline()
            for line in rf:
                row = converter.convert_to_dict(data=line, **row_struct)
                if self.__process_line(row, where, func):
                    result = {field: row[field] for field in fields}
                    query_result['data']['records'] += 1
                    write_lines.append(
                        converter.convert_to_string(data=result, **row_struct)
                    )
                if len(write_lines) > 100:
                    self.__write_line(write_lines, outfile)
                    write_lines = []
        self.__write_line(write_lines, outfile)
        return query_result

    def __write_line(self, string_list, write_file):
        with open(write_file, 'a+') as wf:
            wf.write('\n'.join(string_list))
        return True

    def __process_compare(self, source_row, compare_row, match_fields, should_match):
        matched_data = all(
            source_row[field] == compare_row[field]
            for field in match_fields
        )
        return (
            True if matched_data and should_match
            or not matched_data and not should_match
            else False
        )

    def compare(self, with_data, field_matches, match_exists, queries, return_data, outfile):
        """Takes in another DataTool object as with data and executes a compare
        between the two, where a set of fields match, and given a query across
        these.

        :param with_data, a DataTool object to compare against
        :param field_matches, a list of fields to match on between the 2 DataTool
        objects (i.e. if both contain email you'd use ['email'])
        :param match_exists, a boolean either matching or non matching comparison
        :param queries, a list of dictionaries representing queries to run on the
        found data
        :param return_data, a list of fields to return, must exist in either
        the source or the compare CSV
        :param outfile, a string of a destination to write the output to

        :rtype dictionary of filename and records affected
        """
        result = {'data': {'filename': outfile, 'records': 0}}
        write_lines = []
        c_data = {
            'terminator': with_data.terminator,
            'encloser': with_data.encloser,
            'headers': with_data.headers
        }
        s_data = {
            'terminator': self.terminator,
            'encloser': self.encloser,
            'headers': self.headers
        }

        with open(with_data.filename, 'r') as cf:
            with open(self.filename, 'r') as sf:
                cf.readline()
                sf.readline()
                for c_line in cf:
                    c_row = converter.convert_to_dict(data=c_line, **c_data)
                    sf.seek(0)  # Reset the source file
                    for line in sf:

                        row = converter.convert_to_dict(data=line, **s_data)
                        if not self.__process_compare(row, c_row, field_matches, match_exists):
                            continue

                        # AND the query results
                        query_result = all(
                            [
                                self.__process_query(
                                    # select the row based on where the field is
                                    row=(
                                        row if query['field'] in self.headers
                                        else c_row
                                    ),
                                    queries=query
                                )
                                for query in queries
                            ]
                        )
                        if query_result:
                            # Create the dictionary from the two rows and return fields
                            write_row = {
                                field:(
                                    row[field] if field in row
                                    else c_row
                                )
                                for field in return_data
                            }
                            write_data = {
                                'data': write_row,
                                'terminator': self.terminator,
                                'encloser': self.encloser,
                                'headers': write_row
                            }
                            # Add them to the write lines list buffer
                            write_lines.append(
                                converter.convert_to_string(**write_data)
                            )
                            result['data']['records'] += 1

                            if len(write_lines) > 100:
                                self.__write_line(write_lines, outfile)
                                write_lines = []
        self.__write_line(write_lines, outfile)
        return result
