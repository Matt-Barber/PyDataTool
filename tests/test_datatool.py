""" Tests for the core DataTool module - can be run using nose / coverage """
import unittest
from . import mock_open
from dateutil.parser import parse
from ..datatool.config.exceptions import ConditionTypeError, FieldHeaderError
from ..datatool import DataTool
from ..datatool import converter
from unittest.mock import patch


class TestDataTool(unittest.TestCase):
    """ Unit tests built using the core unittest module """
    def setUp(self):
        """ Before each test create some core componants"""
        # Example CSV for reads
        self.csv_example = (
            "email, location, colour\n"
            "tony@stark.com, malibu, gold\n"
            "hulk@stark.com, malibu, green\n"
            "s.rodgers@avengers.com, new york, blue\n"
            "thor@asgard.com, asgard, red\n"
        )
        # Python3 mock_open doesn't support iteration - emulated
        self.mock_open = mock_open.generate(self.csv_example)
        # Used by stats - needs a reset mock_open
        self.mock_open_2 = mock_open.generate(self.csv_example)
        # Example Row
        self.row = converter.convert_to_dict(
            data="tony@stark.com, malibu, 31/05/1976, 37",
            terminator=',',
            encloser='\"',
            headers={
                'email': 0,
                'location': 1,
                'dob': 2,
                'age': 3
            }
        )

    def test_datatool_on_instantiation_sets_headers(self):
        """ As a user, when instantiating the object I want the headers to be
        automatically populated as an attribute"""
        with patch('builtins.open', self.mock_open):
            with patch('os.path.exists', return_value=True):
                datatool = DataTool(
                    filename='path/to/file.csv',
                    terminator=',',
                    encloser='\"'
                )
            self.assertDictEqual(
                datatool.headers,
                {
                    'email': 0,
                    'location': 1,
                    'colour': 2
                }
            )

    def test_datatool_on_instantiation_file_exception(self):
        """ As a user, if I instatiate the object with an invalid file,
        I'd like an appropriate error to be raised """
        with patch('os.path.exists', return_value=False):
            with self.assertRaises(AttributeError):
                DataTool(
                    filename='path/to/file.csv',
                    terminator=',',
                    encloser='\"'
                )

    def test_datatool_statistics_non_grouping_result_numeric(self):
        """ As a user, I want to be able to retrieve simple statistical
        data regarding a data file """
        with patch('builtins.open', self.mock_open):
            with patch('os.path.exists', return_value=True):
                datatool = DataTool(
                    filename='path/to/file.csv',
                    terminator=',',
                    encloser='\"'
                )
        with patch('builtins.open', self.mock_open_2):
            stats = datatool.statistics(
                field='location',
                search={
                    'regex': '.*'
                    },
                return_type='#'
            )
            self.assertDictEqual(
                stats,
                {
                    'data': {
                        'malibu': 2,
                        'new york': 1,
                        'asgard': 1
                    },
                }
            )

    def test_datatool_statistics_grouping_result_percentage(self):
        """ As a user, I want to be able to retrieve simple percentage based
        data regarding a data file """
        with patch('builtins.open', self.mock_open):
            with patch('os.path.exists', return_value=True):
                datatool = DataTool(
                    filename='path/to/file.csv',
                    terminator=',',
                    encloser='\"'
                )
        with patch('builtins.open', self.mock_open_2):
            stats = datatool.statistics(
                field='email',
                search={
                    'regex': r"@([a-z0-9]+(-[a-z0-9]+)*)\.+[a-z]{2,}$",
                    'group_idx': 0
                    },
                return_type='%'
            )
            self.assertDictEqual(
                stats,
                {
                    'data': {
                        'stark': 50.0,
                        'avengers': 25.0,
                        'asgard': 25.0
                    },
                }
            )

    def test_datatool_statistics_no_matches_found(self):
        """ As a user, I want a simple valid response,
        even if no repsonse are found"""
        with patch('builtins.open', self.mock_open):
            with patch('os.path.exists', return_value=True):
                datatool = DataTool(
                    filename='path/to/file.csv',
                    terminator=',',
                    encloser='\"'
                )
        with patch('builtins.open', self.mock_open_2):
            stats = datatool.statistics(
                field='email',
                search={
                    'regex': "123456",
                },
                return_type='#'
            )
            self.assertDictEqual(
                stats,
                {'data': {}},
            )

    def test_datatool_statistics_missing_field_exception(self):
        """ As a user, I want an error to be raised if I use a non existant
        field as a stat point """
        with patch('builtins.open', self.mock_open):
            with patch('os.path.exists', return_value=True):
                datatool = DataTool(
                    filename='path/to/file.csv',
                    terminator=',',
                    encloser='\"'
                )
        with patch('builtins.open', self.mock_open_2):
            with self.assertRaises(FieldHeaderError):
                datatool.statistics(
                    field='toast',
                    search={
                        'regex': '.*'
                    },
                    return_type='#'
                )

    def test_datatool_validate_query_returns_boolean(self):
        with patch('builtins.open', self.mock_open):
            with patch('os.path.exists', return_vaue=True):
                datatool = DataTool(
                    filename='path/to/file.csv',
                    terminator=',',
                    encloser='\"'
                )
        query = {
            'field': 'email',
            'condition': 'CONTAINS',
            'value': 'stark'
        }
        data_types = converter.convert_to_types(self.row)
        result = datatool._DataTool__validate_query(data_types, query)
        self.assertTrue(result)

    def test_datatool_validate_query_invalid_value_data_type(self):
        with patch('builtins.open', self.mock_open):
            with patch('os.path.exists', return_vaue=True):
                datatool = DataTool(
                    filename='path/to/file.csv',
                    terminator=',',
                    encloser='\"'
                )
        query = {
            'field': 'age',
            'condition': 'GREATER',
            'value': 'stark'
        }
        data_types = converter.convert_to_types(self.row)
        with self.assertRaises(ConditionTypeError):
            datatool._DataTool__validate_query(data_types, query)

    def test_datatool_validate_query_invalid_condition(self):
        with patch('builtins.open', self.mock_open):
            with patch('os.path.exists', return_vaue=True):
                datatool = DataTool(
                    filename='path/to/file.csv',
                    terminator=',',
                    encloser='\"'
                )
        query = {
            'field': 'age',
            'condition': 'YOUR MONEY OR YOUR LIFE',
            'value': 'stark'
        }
        data_types = converter.convert_to_types(self.row)
        with self.assertRaises(ValueError):
            datatool._DataTool__validate_query(data_types, query)


    # Process query is a private method - so exception handling is dealt with
    # Prior to reaching this point - only accesisble if the data is valid
    def test_datatool_process_query_string_returns_boolean(self):
        with patch('builtins.open', self.mock_open):
            with patch('os.path.exists', return_vaue=True):
                datatool = DataTool(
                    filename='path/to/file.csv',
                    terminator=',',
                    encloser='\"'
                )
        query = {
            'field': 'email',
            'condition': 'CONTAINS',
            'value': 'stark'
        }
        result = datatool._DataTool__process_query(self.row, query)
        self.assertTrue(result)

    def test_datatool_process_query_integer_returns_boolean(self):
        with patch('builtins.open', self.mock_open):
            with patch('os.path.exists', return_vaue=True):
                datatool = DataTool(
                    filename='path/to/file.csv',
                    terminator=',',
                    encloser='\"'
                )
        query = {
            'field': 'age',
            'condition': 'EQUALS',
            'value': '30'
        }
        result = datatool._DataTool__process_query(self.row, query)
        self.assertFalse(result)

    def test_datatool_process_query_date_returns_boolean(self):
        with patch('builtins.open', self.mock_open):
            with patch('os.path.exists', return_vaue=True):
                datatool = DataTool(
                    filename='path/to/file.csv',
                    terminator=',',
                    encloser='\"'
                )
        query = {
            'field': 'dob',
            'condition': 'BEFORE',
            'value': parse('21/08/2015')
        }
        result = datatool._DataTool__process_query(self.row, query)
        self.assertTrue(result)

    def test_datatool_query_single_where_condition(self):
        with patch('builtins.open', self.mock_open):
            with patch('os.path.exists', return_vaue=True):
                datatool = DataTool(
                    filename='path/to/file.csv',
                    terminator=',',
                    encloser='\"'
                )
        fields = ['email', 'colour']
        where = [
            {
                'field': 'email',
                'condition': 'contains',
                'value': 'stark'
            }
        ]

        match_all = True
        outfile = 'path/to/file'
        with patch('builtins.open', self.mock_open_2):
            result = datatool.query(fields, where, match_all, outfile)
            self.assertDictEqual(
                {
                    'data': {
                        'records': 2,
                        'filename':outfile
                    }
                }, result)

    def test_datatool_query_multi_where_condition_and_logic(self):
        with patch('builtins.open', self.mock_open):
            with patch('os.path.exists', return_vaue=True):
                datatool = DataTool(
                    filename='path/to/file.csv',
                    terminator=',',
                    encloser='\"'
                )
        fields = ['email', 'colour']
        where = [
            {
                'field': 'email',
                'condition': 'contains',
                'value': 'stark'
            },
            {
                'field': 'colour',
                'condition': 'equals',
                'value': 'gold'
            }
        ]
        match_all = True
        outfile = 'path/to/file'
        with patch('builtins.open', self.mock_open_2):
            result = datatool.query(fields, where, match_all, outfile)
            self.assertDictEqual(
                {
                    'data': {
                        'records': 1,
                        'filename':outfile
                    }
                }, result)

    def test_datatool_query_single_where_invalid_select_fields(self):
        with patch('builtins.open', self.mock_open):
            with patch('os.path.exists', return_vaue=True):
                datatool = DataTool(
                    filename='path/to/file.csv',
                    terminator=',',
                    encloser='\"'
                )
        fields = ['email', 'occupation']
        where = [
            {
                'field': 'location',
                'condition': 'equals',
                'value': 'malibu'
            }
        ]
        match_all = True
        outfile = 'path/to/file'
        with patch('builtins.open', self.mock_open):
            with self.assertRaises(FieldHeaderError):
                datatool.query(fields, where, match_all, outfile)

    def test_datatool_query_single_where_invalid_where_field(self):
        with patch('builtins.open', self.mock_open):
            with patch('os.path.exists', return_vaue=True):
                datatool = DataTool(
                    filename='path/to/file.csv',
                    terminator=',',
                    encloser='\"'
                )
        fields = ['email', 'colour']
        where = [
            {
                'field': 'occupation',
                'condition': 'equals',
                'value': 'hero'
            }
        ]
        match_all = True
        outfile = 'path/to/file'
        with patch('builtins.open', self.mock_open):
            with self.assertRaises(FieldHeaderError):
                datatool.query(fields, where, match_all, outfile)

    def test_datatool_query_single_where_invalid_where_condition(self):
        with patch('builtins.open', self.mock_open):
            with patch('os.path.exists', return_vaue=True):
                datatool = DataTool(
                    filename='path/to/file.csv',
                    terminator=',',
                    encloser='\"'
                )
        fields = ['email', 'colour']
        where = [
            {
                'field': 'location',
                'condition': 'matches',
                'value': 'malibu'
            }
        ]
        match_all = True
        outfile = 'path/to/file'
        with patch('builtins.open', self.mock_open):
            with self.assertRaises(ValueError):
                datatool.query(fields, where, match_all, outfile)
