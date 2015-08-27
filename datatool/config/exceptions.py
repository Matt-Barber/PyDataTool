import datetime


class Error(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return '[ERROR] [{datetime}]: {message}'.format(
            datetime=datetime.datetime.now(),
            message=self.message
        )


class ConditionTypeError(Error):
    def __init__(self, value_type, conditions, data_format=False):
        self.message = (
            'Value must be of {type} to use {conditions} '
        ).format(
            type=value_type,
            conditions=', '.join(conditions)
        )
        if data_format:
            for key, value in data_format.items():
                self.message += (
                    'and {var} should match {format} '
                ).format(
                    var=key,
                    format=value
                )


class FieldHeaderError(Error):
    def __init__(self, fields, headers):
        if not isinstance(fields, list):
            fields = [fields]
        self.message = (
            'Fields \"{field}\" do not exist in headers, '
            'data has \"{headers}\" headers'.format(
                field=", ".join(fields),
                headers=", ".join(headers)
            )
        )
