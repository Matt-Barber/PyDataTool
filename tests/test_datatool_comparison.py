import unittest
from io import StringIO
from dateutil.parser import parse
from ..datatool import DataTool
from unittest.mock import patch


class TestDataToolComparison(unittest.TestCase):

    def compare_side_effect(self, *args):
        if args[0] == 'path/to/source':
            mock_obj = StringIO(self.csv_a)
        elif args[0] == 'path/to/compare':
            mock_obj = StringIO(self.csv_b)
        elif args[0] == 'path/to/output':
            mock_obj = StringIO('')
        return mock_obj

    def setUp(self):
        # Example CSV for reads
        self.csv_a = (
            "email, location, colour\n"
            "tony@stark.com, malibu, gold\n"
            "hulk@stark.com, malibu, green\n"
            "s.rodgers@avengers.com, new york, blue\n"
            "thor@asgard.com, asgard, red\n"
        )

        self.csv_b = (
            "email\t occupation\t location\t weapon\t iq level\n"
            "tony@stark.com\t hero\t malibu\t suit\t high\n"
            "hulk@stark.com\t hero\t malibu\t fists\t high\n"
            "s.rodgers@avengers.com\t new york\t hero\t sheild\t medium\n"
            "thor@asgard.com\t hero\t asgard\t hammer\t low\n"
            "loki@asgard.com\t anti-hero\t asgard\t mind powers\t high"
        )
        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', return_value=StringIO(self.csv_a)):
                self.source_data = DataTool(
                    filename = 'path/to/source',
                    terminator = ',',
                    encloser = '\"'
                )
            with patch('builtins.open', return_value=StringIO(self.csv_b)):
                self.compare_data = DataTool(
                    filename = 'path/to/compare',
                    terminator = '\t',
                    encloser = '\"'
                )

    def test_datatool_comparison_returns_new_data_file(self):
        return_fields = ['email', 'weapon']
        queries = [
            {
                'field': 'location',
                'condition': 'CONTAINS',
                'value': 'malibu'
            }
        ]
        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', side_effect=self.compare_side_effect):
                result = self.source_data.compare(
                    with_data=self.compare_data,
                    data_matches=True,
                    field_matches=['email'],
                    queries=queries,
                    return_data=return_fields,
                    outfile='path/to/output'
                )
                self.assertDictEqual(
                    {
                        'data': {
                            'records': 2,
                            'filename': 'path/to/output'
                        }
                    },
                    result
                )
