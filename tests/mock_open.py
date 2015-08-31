from unittest.mock import mock_open


def generate(string):
    new_mock_open = mock_open(read_data=string)
    new_mock_open.return_value.__iter__ = lambda self: self
    new_mock_open.return_value.__next__ = lambda self: self.readline()
    return new_mock_open
