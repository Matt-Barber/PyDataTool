import csv
import io
from functools import wraps
from dateutil.parser import parse


def get_data_format_rules(func):
    """Decorator used to get and validate fields"""
    @wraps(func)
    def inner(*args, **kwargs):
        data = kwargs.get('data', False)
        if not data:
            raise AttributeError(
                (
                    "Data must be passed in the call to this function"
                )
            )
        terminator = kwargs.get('terminator', ',')
        encloser = kwargs.get('encloser', '\"')
        if not isinstance(data, str):
            headers = list(data)
        else:
            headers = kwargs.get('headers', False)
        if not headers:
            raise AttributeError(
                (
                    "A header dict must be passed in the call to this function"
                )
            )
        return func(
            data=data,  # args[0] is always self when called from class method
            terminator=terminator,
            encloser=encloser,
            headers=headers
        )
    return inner


def get_indexes(data, terminator, encloser):
    values = list(
        csv.reader(
            [data],
            delimiter=terminator,
            quotechar=encloser
        )
    ).pop()
    indexed_data = {
        field.strip(): idx for field, idx in zip(
            values,
            range(0, len(data))
        )
    }
    return indexed_data


@get_data_format_rules
def convert_to_dict(data, terminator, encloser, headers):
    """Converts string to ordered dict

    :param data: a string, containing the data to convert
    :param terminator, a terminator for fields in the string
    :param encloser, used to enclose multiple values in a field
    :param headers, a list of headers for the string

    :rtype OrderedDict
    """
    values = list(csv.reader(
        [data],
        delimiter=terminator,
        quotechar=encloser
    )).pop()
    if len(headers) != len(values):
        raise ValueError(
            (
                "Headers : {headers}, of size {header_count}, "
                "Values: {values}, of size {value_count}, "
                "The sizes must match."
            ).format(
                headers=headers,
                values=values,
                header_count=len(headers),
                value_count=len(values)
            )
        )
    dictionary = {}
    for k, v in headers.items():
        dictionary[k] = values[v].strip()
    return dictionary


@get_data_format_rules
def convert_to_string(data, terminator, encloser, headers=None):
    """Converts dict to a string

    :param data: An dict of key value pairs that make up the dictionary
    :param terminator: how to terminate the fields (i.e. comma)
    :param encloser: how to enclose multiple values in a single field
    :rtype string
    """
    string = io.StringIO()
    writer = csv.writer(
        string,
        quotechar=encloser,
        delimiter=terminator,
        quoting=csv.QUOTE_MINIMAL
    )
    writer.writerow(list(data.values()))
    return string.getvalue().strip()


def convert_to_types(converted_dict):
    """Converts a dictionary of headers and values to headers and types

    :param converted_dict, a dictionary of key values that represent a
    header and row values
    :rtype dictionary
    """
    type_dict = {}
    for key, value in converted_dict.items():
        try:
            parse(value)
            type_dict[key] = 'date'
        except ValueError:
            try:
                float(value)
                type_dict[key] = 'numeric'
            except ValueError:
                type_dict[key] = 'string'
    return type_dict
