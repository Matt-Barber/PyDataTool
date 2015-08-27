#DataTools : Python

A set of tools to manipulate data files that consist of terminated and enclosed data separated by lines : CSV, TSV, you could even invent sandwich separated values! How cool is that?

##Motivation
I spend a lot of my time trying to handle data, big data, small data, neat data and terrible data. I tend to either have to write custom scripts on a per case basis, or load the data into an SQL table and manipulate that. Neither of these have been ideal scenarios - and excel tends to have something of a panic when it sees anything bigger than about 20mb (libre office fairs a little better - granted!).

As you can see from my repos I have experimented with this principal and NodeJS but Node is lacking features I like in a programming language, and this repo is already a far more mature development.

##Real applications
The main idea behind this was to create a usable resource to do (currently) two things. 1 - calculate statistics for the given file (regardless of the filesize from 10kb to 7gb and beyond), as well as to execute SQL inspired queries on the data.

##Example : Statistics
```
>>> from datatool.datatool import DataTool
>>> dt = DataTool(filename='./example.csv', terminator=',', encloser='\"')
>>>
>>> # Example Statistics query
>>> dt.statistics(
>>>    field='colour',  # look in the field colour
>>>    search={
>>>        'regex': '.*'  # Regex match using .* (the whole string)
>>>    },
>>>    return_type='%',  # Return the percentages
>>>    top=5  # Return the top 5 results ( + other grouping)
>>>)
>>>
{
  'data': {
      'red': 25.0,
      'blue': 50.0,
      'gold': 25.0
  }
}
```

##Example : Query
```
>>> from datatool.datatool import DataTool
>>> dt = DataTool(filename='./example.csv', terminator=',', encloser='\"')
>>>
>>> dt.query(
>>>    fields=['colour', 'location'], # Select the colour & location fields
>>>    where=[  # This is our query list
>>>        {
>>>            'field': 'location',  # look in the location field
>>>            'condition': 'contains',  # see if it contains
>>>            'value': 'Dorset'  # the value dorset
>>>        },
>>>        {
>>>            'field': 'dob',  # look in the date of birth field
>>>            'condition': 'after',  # see if the value is after
>>>            'value': '01/01/2001'  # the date 01/01/2001 (date interpretted)
>>>        }
>>>    ],
>>>    match_all=True,  # perform an AND on these queries
>>>    outfile='./example_output.csv'  # write file for the results
>>>)
>>>
{
  'data': {
      'records': 201,
      'filename': './example_output.csv',
  }
}
```

##Run time statistics (querying)
55mb ~ file with 250,000 + rows and 32 fields : 20 ~ seconds with 2 conditions
55mb ~ file with 250,000 + rows and 32 fields : 60 ~ seconds with 2 conditions (datetime conditions AFTER / BEFORE) - latency in parsing the datetime from string (I'm looking to optimise this)


#Instantiation
When creating a new DataTool supply the following kwargs.

- filename : a valid file that exists (i.e. CSV, TSV, TXT etc.)
- terminator : the character used to terminate a field (i.e. a comma)
- encloser : the character used to wrap multiple values in a field (i.e. a double quote)

#Statistics (DataTool.statistics)
When calling the statistics method you have the following kwargs.

- field : the field you want to retrieve statistics from
- search : a dictionary that composes the search
  - 1. regex (required) : either a string or pattern to search for (i.e. .\*)
  - 2. group_idx (optional) : an integer indicating which grouping to pull the regex result out of (i.e. if you were pulling the domain out of an email address)
- return_type : a character of data formatting for the result, either \# for number or \% for percentages
- top : an integer, how many results to return the rest being grouped under "other"


#Statistics (Current issues)
 - Can only search for one set of criteria (not query based currently)
 - top parameter is currently not implemented
 - regex / group_idx has been tested but may need further stress testing

#Query (DataTool.query)
When calling the query method you have the following kwargs
- fields : a list of the fields you'd like returned in the outfile - think the SELECT clause in SQL
- where : a list of dictionaries that make up the query, each dictionary must be composed of:
  - 1. field : the field you are querying (must exist in the source)
  - 2. condition: what condition you'd like to use for the query
  - 3. value : the value to match the field and condition against
- match_all : a boolean, if True will perform an AND on all queries in where, False === or
- outfile: a string, path to and name of the file to write the results to

##Query conditions
'CONTAINS', 'EQUALS', 'GREATER', 'LESS', 'BEFORE', 'AFTER', 'BETWEEN', 'NOT'

##Dependancies
The lovely dateutil module : [github!](https://github.com/dateutil/dateutil)

##Unit Tests
Please do try the unit tests, I'd recommend with coverage, nose and nose-timer:
```
# from the parent dir of the module
python -m nose --with-cover --cover-erase --cover-package=DataTool --with-timer
```

##Bugs
- Can only AND or NOT all the where conditions
- BETWEEN condition not implemented in query
- top attribute not implemented in statistics currently
- Quite a few, probably : please do let me know any that crop up

##Author
Me, Myself and I
