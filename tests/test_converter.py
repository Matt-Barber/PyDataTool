import unittest
from ..datatool import converter


class TestConverter(unittest.TestCase):
    def setUp(self):
        self.valid_data = "test@test.com,weymouth,\"blue, red\""
        self.invalid_data = "test@test.com,weymouth,'blue, red'"
        self.valid_headers = "email, location, colour"
        self.invalid_headers = "email, occupation"

    def test_get__indexes_empty_data_returns_empty_dictionary(self):
        indexed_data = converter.get_indexes(
            data='',
            terminator=',',
            encloser='\"'
        )
        self.assertDictEqual(indexed_data, {})

    def test_get_indexes_returns_header_index_dictionary(self):
        indexed_data = converter.get_indexes(
            data='email, location, colour',
            terminator=',',
            encloser='\"'
        )
        self.assertDictEqual(
            indexed_data,
            {
                'email': 0,
                'location': 1,
                'colour': 2
            }
        )

    def test_convert_to_dict_invalid_headers(self):
        terminator = ','
        encloser = '\"'
        invalid_header_idx = converter.get_indexes(
            data=self.invalid_headers,
            terminator=terminator,
            encloser=encloser
        )
        with self.assertRaises(ValueError):
            converter.convert_to_dict(
                data=self.valid_data,
                terminator=terminator,
                encloser=encloser,
                headers=invalid_header_idx
            )

    def test_convert_to_dict_invalid_data(self):
        terminator = ','
        encloser = '\"'
        valid_header_idx = converter.get_indexes(
            data=self.valid_headers,
            terminator=terminator,
            encloser=encloser
        )
        with self.assertRaises(ValueError):
            converter.convert_to_dict(
                data=self.invalid_data,
                terminator=terminator,
                encloser=encloser,
                headers=valid_header_idx
            )

    def test_convert_to_dict_returns_dictionary(self):
        terminator = ','
        encloser = '\"'
        valid_header_idx = converter.get_indexes(
            data=self.valid_headers,
            terminator=terminator,
            encloser=encloser,
        )
        row = converter.convert_to_dict(
            data=self.valid_data,
            terminator=terminator,
            encloser=encloser,
            headers=valid_header_idx
        )
        self.assertDictEqual(
            row,
            {
                'colour': 'blue, red',
                'email': 'test@test.com',
                'location': 'weymouth'
            }
        )

    def test_convert_to_string_empty_dictionary_raises_exception(self):
        data = {}
        with self.assertRaises(AttributeError):
            converter.convert_to_string(
                data=data,
                terminator='\t',
                encloser='\"'
            )

    def test_convert_to_string_returns_string(self):
        data = {
            'email': 'test@test.com',
            'location': 'weymouth',
            'colour': 'blue\t red',
        }
        string = converter.convert_to_string(
            data=data,
            terminator='\t',
            encloser='|'
        )
        self.assertIn('test@test.com', string)
        self.assertIn('weymouth', string)
        self.assertIn('|blue\t red|', string)
        self.assertIn('\t', string)
